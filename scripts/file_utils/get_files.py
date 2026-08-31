from seistoolkit.utils import get_files


def main():
    get_files(
        file_formats=('.txt',),
        output_type='names',
        export=True
    )


if __name__ == "__main__":
    main()
    print('Done!')
