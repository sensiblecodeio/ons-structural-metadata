# ons-structural-metadata

## Introduction

`check_structural_metadata.py` can be used to perform basic validation of the structural metadata in `Classification.csv`, `Category.csv` and `Category_Mapping.csv`.
It is not a full QA suite and only performs limited checks.
Primarily it checks the consistency of codes and labels for mappings between a parent classification and a derived classification.

## Running

It is run by invoking the script with `python3` (some systems may require the use of `python` instead),
and supplying an input directory with the `-i` option:
```
python3 check_structural_metadata.py -i <input_directory>
```

The repository contains some sample source files that are used in testing.
To run the script against these files:
```
python3 check_structural_metadata.py -i test/data/bad
```

The output provides descriptions of the checks being performed and detailed information about any errors detected.

### Ignoring leading zeros

All classification codes are strings, although many codes are string representations of numbers.
This means that `001` is a different code from `1`.
There are some issues within the metadata due to inconsistent usage of leading zeros.
A `--zeros` flag can be used to ignore these inconsistencies
i.e. `001` and `1` will be treated as being equivalent.
This flag is only intended for debug purposes as each code must be specified with the correct format wherever it is used.

To run checks without leading zeros ignored:
```
python3 check_structural_metadata.py -i <input_directory> --zeros
```

## Testing

The repository contains some simple tests that can be used to validate that the checks behave as expected.
To run:
```
python3 -m unittest -v
```