from seistoolkit.utils import merge_txt


def main():
    merge_txt(
        output_name='merged',
        has_header=True,
        add_source_file=True,
        source_file_sep=' ',
    )


if __name__ == "__main__":
    main()
    print('Done!')