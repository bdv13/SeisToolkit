import seistoolkit.utils as u


def main():
    """Separate files based on map-file."""
    u.separate_files(operation='move', input_type="names")


if __name__ == '__main__':
    main()