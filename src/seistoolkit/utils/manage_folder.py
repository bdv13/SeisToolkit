import shutil
from pathlib import Path


def create_folder(folder_name: str, path: Path) -> Path:
    """Create folder in selected directory and return it path."""
    folder_path = path / folder_name
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path


def delete(path: Path) -> None:
    """Delete a file or directory (recursively)."""
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    if path.is_file() or path.is_symlink():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    else:
        raise ValueError(f"Unsupported path type: {path}")
