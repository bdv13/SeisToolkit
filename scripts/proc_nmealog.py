import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timezone
from pathlib import Path
from typing import TypeVar

import seistoolkit.utils as u
from seistoolkit.geometry import (
    NMEALogStats,
    get_utm_zone,
    nmea_to_decimal,
    wgs84_to_utm,
)

OUTPUT_FIELDS = (
    ("DATE", "{date}"),
    ("TIMESTAMP", "{time}"),
    ("YEAR", "{year}"),
    ("JD", "{jd}"),
    ("HOUR", "{hour}"),
    ("MIN", "{minute}"),
    ("SEC", "{second}"),
    ("GPS_LAT", "{lat:.9f}"),
    ("GPS_LON", "{lon:.9f}"),
    ("UTM_ZONE", "{utm_zone}"),
    ("GPS_X", "{utm_x:.3f}"),
    ("GPS_Y", "{utm_y:.3f}"),
    ("HEADING", "{heading:06.2f}"),
    ("SPEED", "{speed:.1f}"),
)

GPS_QUALITY = {0: "No fix", 1: "GPS", 2: "DGPS", 3: "RTK fix", 4: "RTK float"}
HEX_RE = re.compile(r"^[0-9A-Fa-f]{2}$")
T = TypeVar("T")


@dataclass
class GGA:
    time: time | None
    lat: float
    lon: float
    quality: str
    satellites: int | None
    hdop: float | None
    altitude: float | None
    geoid_separation: float | None


@dataclass
class RMC:
    timestamp: datetime
    lat: float
    lon: float
    speed: float | None
    course: float | None


def _get_output_header() -> str:
    return " ".join(header for header, _ in OUTPUT_FIELDS) + "\n"


def _parse_date(value: str) -> date | None:
    """Convert DDMMYY or DDMMYYYY string to date object."""
    if not value:
        return None

    for fmt in ("%d%m%y", "%d%m%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


def _parse_time(value: str) -> time | None:
    """Convert HHMMSS.ssssss or HHMMSS string to time object."""
    if not value:
        return None

    for fmt in ("%H%M%S.%f", "%H%M%S"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue

    return None


def _parse_value(value: str, converter: Callable[[str], T]) -> T | None:
    """Convert string value using the specified converter."""
    if not value:
        return None

    try:
        return converter(value)
    except ValueError, TypeError:
        return None


def _get_nmea_message_type(sentence: str) -> str:
    """Extract the message type from an NMEA 0183 sentence."""
    return sentence.split("*")[0][-3:]


def _get_packets(line: str, separator: str = ",") -> list[str]:
    """Split NMEA sentence into fields."""
    return line.strip().split(separator)


def _check_checksum(line: str) -> bool:
    if "*" not in line:
        return True

    try:
        data, checksum = line.strip().split("*", 1)
    except ValueError:
        return False

    checksum = checksum[:2]

    if not HEX_RE.fullmatch(checksum):
        return False

    value = 0
    for char in data[1:]:
        value ^= ord(char)

    return value == int(checksum, 16)


def _is_valid_nmea(sentence: str) -> bool:
    """Check whether an NMEA 0183 sentence is valid."""
    return (
        bool(sentence)
        and sentence.startswith("$")
        and _check_checksum(sentence)
    )


def parse_hdt(fields: Sequence[str]) -> float | None:
    """Parse an NMEA 0183 HDT sentence into vessel true heading in degrees."""
    if len(fields) < 2:
        return None

    return _parse_value(fields[1], float)


def parse_zda(fields: Sequence[str]) -> datetime | None:
    """Parse an NMEA 0183 ZDA sentence and return a UTC datetime."""
    try:
        parsed_time = _parse_time(fields[1])
        if parsed_time is None:
            return None

        year = _parse_value(fields[4], int)
        month = _parse_value(fields[3], int)
        day = _parse_value(fields[2], int)

        if None in (year, month, day):
            return None

        parsed_date = date(year, month, day)

        return datetime.combine(parsed_date, parsed_time, tzinfo=timezone.utc)

    except IndexError, ValueError:
        return None


def parse_gga(fields: Sequence[str]) -> GGA | None:
    """Parse an NMEA 0183 GGA sentence into a GGA object."""
    try:
        gga_time = _parse_time(fields[1])
        if gga_time is None:
            return None

        lat = round(nmea_to_decimal(fields[2], fields[3]), 10)
        lon = round(nmea_to_decimal(fields[4], fields[5]), 10)

        quality_code = _parse_value(fields[6], int)
        quality = GPS_QUALITY.get(quality_code, "Unknown")

        return GGA(
            time=gga_time,
            lat=lat,
            lon=lon,
            quality=quality,
            satellites=_parse_value(fields[7], int),
            hdop=_parse_value(fields[8], float),
            altitude=_parse_value(fields[9], float),
            geoid_separation=_parse_value(fields[11], float),
        )

    except IndexError, ValueError, TypeError:
        return None


def parse_rmc(fields: Sequence[str]) -> RMC | None:
    """Parse an NMEA 0183 RMC sentence into an RMC object."""
    try:
        if fields[2] != "A":
            return None

        rmc_time = _parse_time(fields[1])
        if rmc_time is None:
            return None

        rmc_date = _parse_date(fields[9])
        if rmc_date is None:
            return None

        lat = round(nmea_to_decimal(fields[3], fields[4]), 10)
        lon = round(nmea_to_decimal(fields[5], fields[6]), 10)

        return RMC(
            timestamp=datetime.combine(
                rmc_date, rmc_time, tzinfo=timezone.utc
            ),
            lat=lat,
            lon=lon,
            speed=_parse_value(fields[7], float),
            course=_parse_value(fields[8], float),
        )

    except IndexError, ValueError, TypeError:
        return None


def nmea_parser(log_path: Path, output_path: Path) -> None:
    """Parse NMEA log file using GGA, ZDA, HDT sentences."""

    stats = NMEALogStats()

    with (
        open(log_path, "r", encoding="latin-1") as fin,
        open(output_path, "w", encoding="utf-8") as fout,
    ):
        current_date: date | None = None
        current_heading: float | None = None
        current_speed: float | None = None

        fout.write(_get_output_header())

        for line in fin:
            stats.total += 1

            if not _is_valid_nmea(line):
                stats.invalid += 1
                continue

            packets = _get_packets(line)
            msg_type = _get_nmea_message_type(packets[0])

            if msg_type == "ZDA":
                stats.zda_count += 1
                zda = parse_zda(packets)

                if zda is not None:
                    current_date = zda.date()
                else:
                    stats.zda_errors += 1

                continue

            if msg_type == "HDT":
                stats.hdt_count += 1
                heading = parse_hdt(packets)

                if heading is not None:
                    current_heading = heading
                else:
                    stats.hdt_errors += 1

                continue

            if msg_type == "RMC":
                stats.rmc_count += 1
                rmc = parse_rmc(packets)

                if rmc is None:
                    stats.rmc_errors += 1
                else:
                    current_speed = rmc.speed

                continue

            if msg_type != "GGA":
                stats.others_count += 1
                continue

            stats.gga_count += 1

            gga = parse_gga(packets)

            if gga is None or gga.time is None:
                stats.gga_errors += 1
                continue

            if current_date is None:
                stats.missing_data += 1
                continue

            ts = datetime.combine(current_date, gga.time, tzinfo=UTC)

            utm_zone = get_utm_zone(gga.lat, gga.lon)
            utm_x, utm_y = wgs84_to_utm(gga.lat, gga.lon, utm_zone)

            heading = current_heading if current_heading is not None else 0.0
            speed = current_speed if current_speed is not None else 0.0

            fout.write(
                f"{ts:%Y-%m-%d} "
                f"{ts:%H:%M:%S}.{gga.time.microsecond // 1000:03d} "
                f"{ts.year} "
                f"{ts.timetuple().tm_yday} "
                f"{ts.hour} "
                f"{ts.minute} "
                f"{ts.second} "
                f"{gga.lat:.9f} "
                f"{gga.lon:.9f} "
                f"{utm_zone} "
                f"{utm_x:.3f} "
                f"{utm_y:.3f} "
                f"{heading:06.2f} "
                f"{speed:.1f}\n"
            )

    print(f"File name: {output_path.stem}")
    stats.print_stats()
    print("-" * 15, end="\n\n")


@u.timer
def batch_nmea_parser() -> None:
    """Parse multiple NMEA0183 log files."""

    logs_folder = u.select_folder()
    log_paths = u.get_paths(logs_folder, (".nmea",))
    output_folder = u.create_folder("parsed_logs", logs_folder)

    files_total = len(log_paths)
    files_counter = 1
    for log_path in log_paths:
        output_path = output_folder / f"{log_path.stem}_parsed.txt"
        print(f"Processing... (File {files_counter} of {files_total})")
        nmea_parser(log_path, output_path)
        files_counter += 1

    print("Merging files into one file ...")
    u.merge_txt_files(
        folder=output_folder,
        output_name='gps_logs_120726-160726',
        has_header=True,
        add_source_file=True,
        source_file_sep=" ",
    )


if __name__ == "__main__":
    print()
    print("Please select folder with NMEA logs (.nmea)", end="\n\n")
    batch_nmea_parser()
    print(
        f"Done! Completed in {batch_nmea_parser.elapsed_time:.3f} sec",
        end="\n\n",
    )
