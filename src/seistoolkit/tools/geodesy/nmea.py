from dataclasses import dataclass


@dataclass
class NMEALogStats:
    """Dataclass to collect NMEA log statistics."""

    # Line statistics
    total: int = 0

    # Message counters
    gga_count: int = 0
    zda_count: int = 0
    rmc_count: int = 0
    hdt_count: int = 0
    vtg_count: int = 0
    others_count: int = 0

    # Skipped lines
    invalid: int = 0
    missing_data: int = 0

    # Errors
    zda_errors: int = 0
    hdt_errors: int = 0
    vtg_errors: int = 0
    rmc_errors: int = 0
    gga_errors: int = 0

    @property
    def parse_errors(self) -> int:
        return (
            self.zda_errors
            + self.hdt_errors
            + self.vtg_errors
            + self.rmc_errors
            + self.gga_errors
        )

    @property
    def skipped(self) -> int:
        return self.invalid + self.parse_errors + self.missing_data

    @property
    def skipped_percent(self) -> float:
        if self.total == 0:
            return 0.0
        return self.skipped / self.total * 100

    def print_stats(self):
        print(f"Total: {self.total}")
        print(f"GGA: {self.gga_count}")
        print(f"ZDA: {self.zda_count}")
        print(f"RMC: {self.rmc_count}")
        print(f"HDT: {self.hdt_count}")
        print(f"VTG: {self.vtg_count}")
        print(f"Other: {self.others_count}")
        print()
        print(f"Skipped: {self.skipped} ({self.skipped_percent:.2f}%)")
        print(f"Invalid: {self.invalid}")
        print(f"Missing: {self.missing_data}")
        print(
            f"Parse issues: {self.parse_errors} "
            f"GGA: {self.gga_errors}, "
            f"ZDA: {self.zda_errors}, "
            f"RMC: {self.rmc_errors}, "
            f"HDT: {self.hdt_errors}, "
            f"VTG: {self.vtg_errors}"
        )
        print()
