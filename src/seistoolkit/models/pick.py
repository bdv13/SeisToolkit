import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(slots=True)
class Pick:
    """Seismic picks container."""

    hdrs: dict[str, list[int]]
    twt_ms: np.ndarray

    @property
    def size(self) -> int:
        return len(self.twt_ms)

    def _validate_hdrs(self, *hdrs):
        for hdr in hdrs:
            if hdr not in self.hdrs:
                raise KeyError(f"Header '{hdr}' is not found!")
            if len(self.hdrs[hdr]) != self.size:
                raise ValueError(f"{hdr} has wrong length!")

    @staticmethod
    def import_txt(
        file_path: Path,
        hdrs_cols: tuple[int | str, ...],
        data_col: int | str,
    ) -> "Pick":
        """Create Pick from a tab-separated text file."""
        with open(file_path, newline="", encoding="utf-8-sig") as file:
            rows = csv.reader(file, delimiter="\t")
            header = next(rows, None)

            if not header:
                raise ValueError("Text file has no header")

            header = [name.strip() for name in header]
            if len(header) != len(set(header)):
                raise ValueError("Text file header contains duplicate names")

            def column_index(column: int | str) -> int:
                if isinstance(column, str):
                    try:
                        return header.index(column)
                    except ValueError as error:
                        raise ValueError(
                            f"Column '{column}' is not found"
                        ) from error

                if not 0 <= column < len(header):
                    raise ValueError(f"Column index {column} is out of range")
                return column

            hdr_indices = [column_index(column) for column in hdrs_cols]
            time_index = column_index(data_col)
            hdr_values: dict[str, list[int]] = {
                header[index]: [] for index in hdr_indices
            }
            twt_ms = []

            for line_number, row in enumerate(rows, start=2):
                if not row or not any(value.strip() for value in row):
                    continue
                if len(row) != len(header):
                    raise ValueError(
                        f"Line {line_number} has {len(row)} columns; "
                        f"expected {len(header)}"
                    )

                try:
                    for index in hdr_indices:
                        hdr_values[header[index]].append(int(row[index]))
                    twt_ms.append(float(row[time_index]))
                except ValueError as error:
                    raise ValueError(
                        f"Invalid value on line {line_number}"
                    ) from error

        return Pick(hdrs=hdr_values, twt_ms=np.asarray(twt_ms))

    def export_rdx_pick(
        self,
        hdr1: str,
        hdr2: str,
        output_path: Path,
    ) -> None:
        """Export picks to RadExPro txt format."""

        self._validate_hdrs(hdr1, hdr2)

        with open(output_path, "w", encoding="utf-8") as f:
            # write file header:
            f.write(f"{hdr1}:{hdr2}\n")

            # write values:
            for val1, val2, twt in zip(
                self.hdrs[hdr1],
                self.hdrs[hdr2],
                self.twt_ms,
            ):
                f.write(f"{val1:15d}:{val2:15d}{twt:15.4f}\n")
