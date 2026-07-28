import re
from datetime import datetime as dt, time, date, timezone as tz
from typing import Optional, TypeVar, Callable
from dataclasses import dataclass
from pathlib import Path

import stk.utils as u
from stk.geometry import get_utm_zone, nmea_to_decimal, wgs84_to_utm

GPS_QUALITY = {
    0: 'No fix',
    1: 'GPS',
    2: 'DGPS',
    3: 'RTK fixed',
    4: 'RTK float'
}

OUTPUT_HDRS = [
    "DATE",
    "TIMESTAMP",
    "YEAR",
    "JD",
    "HOUR",
    "MIN",
    "SEC",
    "LAT",
    "LON",
    "UTM_ZONE",
    "X",
    "Y",
    "COG",
    "SPEED",
]

@dataclass
class GGA:
    time: Optional[time]
    lat: float
    lon: float
    quality: str
    satellites: Optional[int]
    hdop: Optional[float]
    altitude: Optional[float]
    geoid_separation: Optional[float]

@dataclass
class RMC:
    timestamp: dt
    lat: float
    lon: float
    speed: Optional[float]
    course: Optional[float]

T = TypeVar("T")
HEX_RE = re.compile(r"^[0-9A-Fa-f]{2}$")

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


def _parse_time(value: str) -> Optional[time]:
    """Parse an NMEA0183 time string into a time object."""
    if not value:
        return None

    for fmt in ("%H%M%S.%f", "%H%M%S"):
        try:
            return dt.strptime(value, fmt).time()
        except ValueError:
            pass

    return None


def _parse_date(value: str) -> Optional[date]:
    """Parse an NMEA0183 date string."""
    if not value:
        return None

    for fmt in ("%d%m%y", "%d%m%Y"):
        try:
            return dt.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


def _parse_value(value: str, converter: Callable[[str], T]) -> Optional[T]:
    """Parse NMEA0183 value using given converter."""
    if not value:
        return None
    try:
        return converter(value)
    except (ValueError, TypeError):
        return None


def parse_hdt(packets: list[str]) -> Optional[float]:
    """Parse an NMEA0183 HDT packet into vessel's true heading."""
    if len(packets) < 2:
        return None
    return _parse_value(packets[1], float)


def parse_zda(packets: list[str]) -> Optional[dt]:
    """Parse an NMEA0183 ZDA packet into a Python datetime object."""
    try:
        t = _parse_time(packets[1])
        if t is None:
            return None

        year = _parse_value(packets[4], int)
        month = _parse_value(packets[3], int)
        day = _parse_value(packets[2], int)

        if None in (year, month, day):
            return None

        d = date(year, month, day)

        return dt.combine(d, t, tzinfo=tz.utc)

    except (IndexError, ValueError):
        return None


def parse_gga(packets: list[str]) -> Optional[GGA]:
    """Parse an NMEA0183 GGA packet."""
    try:
        t = _parse_time(packets[1])
        if t is None:
            return None

        lat = round(nmea_to_decimal(packets[2], packets[3]), 10)
        lon = round(nmea_to_decimal(packets[4], packets[5]), 10)

        quality_code = _parse_value(packets[6], int)
        quality = (
            GPS_QUALITY.get(quality_code, "Unknown")
            if quality_code is not None
            else "Unknown"
        )

        satellites = _parse_value(packets[7], int)
        hdop = _parse_value(packets[8], float)
        altitude = _parse_value(packets[9], float)
        geoid_separation = _parse_value(packets[11], float)

        return GGA(
            time=t,
            lat=lat,
            lon=lon,
            quality=quality,
            satellites=satellites,
            hdop=hdop,
            altitude=altitude,
            geoid_separation=geoid_separation,
        )

    except (IndexError, ValueError, TypeError):
        return None


def parse_rmc(packets: list[str]) -> Optional[RMC]:
    """Parse an NMEA0183 RMC packet."""
    try:
        t = _parse_time(packets[1])
        if t is None:
            return None

        d = _parse_date(packets[9])
        if d is None:
            return None

        rmc_datetime = dt.combine(d, t, tzinfo=tz.utc)

        lat = round(nmea_to_decimal(packets[3], packets[4]), 10)
        lon = round(nmea_to_decimal(packets[5], packets[6]), 10)

        speed_knots = _parse_value(packets[7], float)
        cog = _parse_value(packets[8], float)

        return RMC(
            timestamp=rmc_datetime,
            lat=lat,
            lon=lon,
            speed=speed_knots,
            course=cog,
        )

    except (IndexError, ValueError, TypeError):
        return None


def parse_nmea_rmc(file_path: Path, output_path: Path) -> None:
    """Parse NMEA log file using RMC string only."""
    total = 0
    skipped = 0
    bad_checksum = 0

    with (
        open(file_path, "r", encoding="latin-1") as fin,
        open(output_path, "w", encoding="utf-8") as fout,
    ):

        fout.write(" ".join(OUTPUT_HDRS) + "\n")

        for line in fin:
            if not line.startswith("$"):
                skipped += 1
                continue

            if not _check_checksum(line):
                skipped += 1
                bad_checksum += 1
                continue

            packets = line.strip().split(",")
            msg_type = packets[0].split("*")[0][-3:]

            if msg_type == "RMC":
                total += 1
                rmc = parse_rmc(packets)

                if rmc is None:
                    skipped += 1
                    continue

                utm_zone = get_utm_zone(rmc.lat, rmc.lon)
                utm_x, utm_y = wgs84_to_utm(rmc.lat, rmc.lon, utm_zone)

                ts = rmc.timestamp

                course = rmc.course if rmc.course is not None else 0.0
                speed = rmc.speed if rmc.speed is not None else 0.0

                fout.write(
                    f"{ts:%Y-%m-%d} "
                    f"{ts:%H:%M:%S}.{ts.microsecond // 1000:03d} "
                    f"{ts.year} "
                    f"{ts.timetuple().tm_yday} "
                    f"{ts.hour} "
                    f"{ts.minute} "
                    f"{ts.second} "
                    f"{rmc.lat:.9f} "
                    f"{rmc.lon:.9f} "
                    f"{utm_zone} "
                    f"{utm_x:.3f} "
                    f"{utm_y:.3f} "
                    f"{course:06.2f} "
                    f"{speed:.1f}\n"
                )

    print(
        f"File name: {file_path.stem}\n\n"
        f"Total RMC strings: {total}. "
        f"Total Skipped: {skipped}. "
        f"- Bad checksum: {bad_checksum}"
    )


def parse_nmea_gga_zda_hdt(file_path: Path, output_path: Path) -> None:
    """Parse NMEA log file using GGA, ZDA, HDT sentences."""
    total = 0
    skipped = 0
    bad_checksum = 0
    no_dt_hdt = 0

    with (
        open(file_path, "r", encoding="latin-1") as fin,
        open(output_path, "w", encoding="utf-8") as fout,
    ):

        current_date: date | None = None
        current_hdt: float | None = None

        fout.write(" ".join(OUTPUT_HDRS) + "\n")

        for line in fin:
            if not line.startswith("$"):
                skipped += 1
                continue

            if not _check_checksum(line):
                skipped += 1
                bad_checksum += 1
                continue

            packets = line.strip().split(",")
            msg_type = packets[0].split("*")[0][-3:]

            if msg_type == "ZDA":
                zda = parse_zda(packets)
                if zda is not None:
                    current_date = zda.date()
                continue

            if msg_type == "HDT":
                heading = parse_hdt(packets)
                if heading is not None:
                    current_hdt = heading
                continue

            if msg_type != "GGA":
                continue

            total += 1

            gga = parse_gga(packets)

            if gga is None or gga.time is None:
                skipped += 1
                continue

            if current_date is None or current_hdt is None:
                skipped += 1
                no_dt_hdt += 1
                continue

            ts = dt.combine(current_date, gga.time, tzinfo=tz.utc)

            utm_zone = get_utm_zone(gga.lat, gga.lon)
            utm_x, utm_y = wgs84_to_utm(gga.lat, gga.lon, utm_zone)

            course = current_hdt
            speed = 0.0

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
                f"{course:06.2f} "
                f"{speed:.1f}\n"
            )

    print(
        f"File name: {file_path.stem}\n"
        f"Total GGA (position) strings: {total}.\n"
        f"Total Skipped: {skipped}.\n"
        f"- Bad checksum: {bad_checksum}\n"
        f"- No Date (ZDA) or HDT (HDT): {no_dt_hdt}\n\n"
    )


@u.timer
def batch_nmea_parser(
    parser: Callable[[Path, Path], None] = parse_nmea_gga_zda_hdt,
    logs_folder: Path | None = None,
    output_folder: Path | None = None
):
    """Batch NMEA0183 logs parsering."""
    if not logs_folder:
        logs_folder = u.select_folder()
    if not output_folder:
        output_folder = u.create_folder('parsed_logs', logs_folder)

    log_paths = u.get_paths(logs_folder, ('.nmea',))

    proc_total = len(log_paths)
    proc_count = 1
    for log_path in log_paths:
        output_path = output_folder / f"{log_path.stem}_parsed.txt"
        print(f"Processing... (File {proc_count} of {proc_total})")
        parser(log_path, output_path)
        proc_count += 1


if __name__ == "__main__":
    print()
    print("Please select folder with NMEA logs", end="\n\n")
    batch_nmea_parser()
    print(f"Done! Completed in {batch_nmea_parser.elapsed_time:.3f} sec", end="\n\n")
