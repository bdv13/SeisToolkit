from pathlib import Path
from datetime import date, datetime

import stk.utils as u
from stk.geometry import nmea_to_decimal, get_utm_zone, wgs84_to_utm


def parse_gga(packet):
    try:
        if packet[1] == "":
            return None

        lat = round(nmea_to_decimal(packet[2], packet[3]), 10)
        lon = round(nmea_to_decimal(packet[4], packet[5]), 10)

        try:
            t = datetime.strptime(packet[1], "%H%M%S.%f").time()
        except ValueError:
            t = datetime.strptime(packet[1], "%H%M%S").time()

        return lat, lon, t

    except (IndexError, ValueError):
        return None


def parse_zda(packet):
    try:
        day = int(packet[2])
        month = int(packet[3])
        year = int(packet[4])

        return date(year, month, day)

    except (IndexError, ValueError):
        return None

@u.timer
def main():

    file_path = Path(u.get_file())
    output_path = file_path.parent / f"{file_path.stem}_parsed.txt"

    current_date = None

    with open(file_path, "r", encoding="latin-1") as fin, \
         open(output_path, "w", encoding="utf-8") as fout:

        fout.write("DATE TIME YEAR JD HOUR MIN SEC LAT LON UTM_ZONE X Y\n")

        for line in fin:
            line = line.strip()
            if not line:
                continue

            packet = line.split(',')

            if not line.startswith("$"):
                continue

            msg_type = packet[0].split('*')[0][-3:]

            if msg_type == "ZDA":
                dt = parse_zda(packet)
                if dt:
                    current_date = dt

            elif msg_type == "GGA":
                result = parse_gga(packet)

                if result and current_date:

                    lat, lon, t = result

                    full_dt = datetime.combine(current_date, t)

                    year = full_dt.year
                    jd = full_dt.timetuple().tm_yday

                    hour = full_dt.hour
                    minute = full_dt.minute
                    second = full_dt.second

                    utm_zone = get_utm_zone(lat, lon)
                    utm_x, utm_y = wgs84_to_utm(lat, lon, utm_zone)

                    fout.write(
                        f"{full_dt.strftime('%Y-%m-%d %H:%M:%S')} "
                        f"{year} "
                        f"{jd} "
                        f"{hour} "
                        f"{minute} "
                        f"{second} "
                        f"{lat:.6f} "
                        f"{lon:.6f} "
                        f"{utm_zone} "
                        f"{utm_x:.2f} "
                        f"{utm_y:.2f}\n"
                    )


if __name__ == "__main__":
    print()
    print("Please select NMEA log file", end="\n\n")
    main()
    print(f"Done! Complited in {main.elapsed_time:.3f} sec", end="\n\n")
