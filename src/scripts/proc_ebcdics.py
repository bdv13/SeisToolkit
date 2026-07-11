from pathlib import Path

from stk.headers import format_text_hdr, get_text_enc
from stk.utils import select_folder


def process_ebcdic_hdrs(folder_path=None):
    """Convert exported EBCDIC header files into UTF-8 text files."""

    if not folder_path:
        folder_path = Path(select_folder())

    output_folder = folder_path / "output"
    output_folder.mkdir(exist_ok=True)

    file_paths = [
        f
        for f in folder_path.iterdir()
        if f.is_file() and f.name.lower().endswith(".ebcdic")
    ]

    for file_path in file_paths:
        with open(file_path, "rb") as f:
            text_hdr = f.read()

        enc = get_text_enc(text_hdr)
        text = text_hdr.decode(enc, errors="replace")
        text = format_text_hdr(text)

        output_path = output_folder / f"{file_path.stem}.txt"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)


if __name__ == "__main__":
    process_ebcdic_hdrs()
    print("Done!", end="\n")
