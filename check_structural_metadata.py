"""
Basic consistency checks on structural metadata CSV files.

This script performs a limited set of checks. It is intended to aid in the preparation of
consistent metadata but does not constitute a full suite of QA tests.
"""
import os
import sys
import csv
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime


VERSION = 'v1.0.0'


def isnum(value):
    """Check if value represents a number."""
    try:
        int(value)
    except ValueError:
        return False
    return True


class Checker:
    """Check structural metadata."""
    def __init__(self, input_dir, ignore_leading_zeros, max_elements):
        """Initialise Checker."""
        self.ignore_leading_zeros = ignore_leading_zeros
        self.max_elements = max_elements if max_elements > 0 else 0
        self.classifications_with_errs = set()

        filename = os.path.join(input_dir, 'Classification.csv')
        print()
        print('--------------------------------------------------------------------------------')
        print(f'- Read {filename}')
        print('- Identify all classifications.')
        print('- Check for duplicate Classification_Mnemonic values.')
        print('--------------------------------------------------------------------------------')
        print()
        self.classifications = dict()
        with open(filename, newline='') as infile:
            reader = csv.DictReader(infile, delimiter=',')
            for row in reader:
                classification_mnemonic = row['Classification_Mnemonic']
                if not classification_mnemonic:
                    continue
                if classification_mnemonic in self.classifications:
                    print(f'ERROR: {classification_mnemonic}: Duplicate Classification_Mnemonic '
                          'in Category.csv')
                    self.classifications_with_errs.add(classification_mnemonic)
                    continue
                self.classifications[classification_mnemonic] = row

        filename = os.path.join(input_dir, 'Category.csv')
        print()
        print('--------------------------------------------------------------------------------')
        print(f'- Read {filename}')
        print('- Identify categories associated with each classification.')
        print('- Check that each Classification_Mnemonic has entry in Classification.csv')
        print('- Check for duplicate category codes on a per classification basis.')
        print('--------------------------------------------------------------------------------')
        print()
        self.categories = dict()
        with open(filename, newline='') as infile:
            reader = csv.DictReader(infile, delimiter=',')
            for row in reader:
                classification_mnemonic = row['Classification_Mnemonic']
                if not classification_mnemonic:
                    continue
                if classification_mnemonic not in self.categories:
                    if classification_mnemonic not in self.classifications:
                        print(f'ERROR: {classification_mnemonic}: Classification_Mnemonic '
                              'specified in Category.csv not found in Classification.csv')
                        self.classifications_with_errs.add(classification_mnemonic)
                    self.categories[classification_mnemonic] = dict()
                code = row['Category_Code']
                if code in self.categories[classification_mnemonic]:
                    print(f'ERROR: {classification_mnemonic}: duplicate code specified in '
                          f'Category.csv: {code}')
                    self.classifications_with_errs.add(classification_mnemonic)
                self.categories[classification_mnemonic][code] = row

        filename = os.path.join(input_dir, 'Category_Mapping.csv')
        print()
        print('--------------------------------------------------------------------------------')
        print(f'- Read {filename}')
        print('- Identify category mappings associated with each classification.')
        print('- Check that each Classification_Mnemonic has entry in Category.csv')
        print('--------------------------------------------------------------------------------')
        print()
        self.category_mappings = dict()
        with open(filename, newline='') as infile:
            reader = csv.DictReader(infile, delimiter=',')
            for row in reader:
                classification_mnemonic = row['Classification_Mnemonic']
                if not classification_mnemonic:
                    continue
                if classification_mnemonic not in self.classifications:
                    print(f'ERROR: {classification_mnemonic}: Classification_Mnemonic specified '
                          'in Category_Mapping.csv not found in Category.csv')
                    self.classifications_with_errs.add(classification_mnemonic)
                if classification_mnemonic not in self.category_mappings:
                    self.category_mappings[classification_mnemonic] = list()
                self.category_mappings[classification_mnemonic].append(row)

    def check_codebook_mnemonic(self):
        print()
        print('--------------------------------------------------------------------------------')
        print('- Checking that same Codebook_Mnemonic is used for all rows in')
        print('- Category_Mapping.csv with the same Classification_Mnemonic')
        print('--------------------------------------------------------------------------------')
        print()
        for classification_mnemonic, mappings in self.category_mappings.items():
            if classification_mnemonic not in self.classifications:
                continue
            classification = self.classifications[classification_mnemonic]
            if not classification['Parent_Classification_Mnemonic'].strip():
                codebook_mnemonic = mappings[0]['Codebook_Mnemonic']
                for mapping in mappings:
                    if mapping['Codebook_Mnemonic'] != codebook_mnemonic:
                        print(f'ERROR: {classification_mnemonic}: different values of '
                              'Codebook_Mnemonic specified for same Classification_Mnemonic')
                        self.classifications_with_errs.add(classification_mnemonic)
                        continue

    def check_identity_mappings(self):
        print()
        print('--------------------------------------------------------------------------------')
        print('- When Parent_Classification_Mnemonic is not specified in Classification.csv')
        print('- check that the Source_Value equals the Target_Value for every category')
        print('- in Category_Mapping.csv.')
        print('--------------------------------------------------------------------------------')
        print()
        for classification_mnemonic, mappings in self.category_mappings.items():
            if classification_mnemonic not in self.classifications:
                continue
            classification = self.classifications[classification_mnemonic]
            if not classification['Parent_Classification_Mnemonic'].strip():
                num_differences = 0
                for mapping in mappings:
                    if self.normalize(mapping['Source_Value']) != \
                            self.normalize(mapping['Target_Value']):
                        num_differences += 1
                if num_differences:
                    print(f'ERROR: {classification_mnemonic}: different Source_Value and '
                          f'Target_Value specified on {num_differences}/{len(mappings)} rows')
                    self.classifications_with_errs.add(classification_mnemonic)
                    continue

    def check_category_consistency(self):
        print()
        print('--------------------------------------------------------------------------------')
        print('- Check that for a given Classification_Mnemonic the set of Target_Value values')
        print('- in Category_Mapping.csv is the same as the set of Category_Code values')
        print('- in Classification.csv')
        print('--------------------------------------------------------------------------------')
        print()
        for classification_mnemonic, mappings in self.category_mappings.items():
            if classification_mnemonic not in self.categories:
                continue
            target_values = set()
            classification_cats = self.categories[classification_mnemonic]
            normalized_cats = {self.normalize(c) for c in classification_cats}
            for mapping in mappings:
                target_value = mapping['Target_Value']
                target_values.add(self.normalize(target_value))

            if target_values != normalized_cats:
                print(f'ERROR: {classification_mnemonic}: different set of Category_Code values '
                      'in Category.csv and Target_Value values in Category_Mapping.csv')
                print(f'  - In Category.csv but not Category_Mapping.csv: '
                      f'{self.limited_sorted_list(normalized_cats - target_values)}')
                print(f'  - In Category_Mapping.csv but not Category.csv: '
                      f'{self.limited_sorted_list(target_values - normalized_cats)}')
                print()
                self.classifications_with_errs.add(classification_mnemonic)

    def check_unique_labels(self):
        print()
        print('--------------------------------------------------------------------------------')
        print('- Checking for unique category labels in Category.csv on a per classification')
        print('- basis')
        print('--------------------------------------------------------------------------------')
        print()
        for classification_mnemonic, cats in self.categories.items():
            label_ext = list()
            label_int = list()
            label_cy = list()
            for category in cats.values():
                label_ext.append(category['External_Category_Label_English'])
                label_int.append(category['Internal_Category_Label_English'])
                label_cy.append(category['External_Category_Label_Welsh'])
            if len(label_ext) != len(set(label_ext)):
                dupes = [l for l in set(label_ext) if label_ext.count(l) > 1]
                print(f'ERROR: {classification_mnemonic}: multiple categories with the same '
                      f'External_Category_Label_English: {dupes}')
                self.classifications_with_errs.add(classification_mnemonic)
            if len(label_int) != len(set(label_int)):
                dupes = [l for l in set(label_int) if label_int.count(l) > 1]
                print(f'ERROR: {classification_mnemonic}: multiple categories with the same '
                      f'Internal_Category_Label_English: {dupes}')
                self.classifications_with_errs.add(classification_mnemonic)
            if len(label_cy) != len(set(label_cy)):
                dupes = [l for l in set(label_cy) if label_cy.count(l) > 1]
                print(f'ERROR: {classification_mnemonic} multiple categories with the same '
                      f'External_Category_Label_Welsh: {dupes}')
                self.classifications_with_errs.add(classification_mnemonic)

    def check_source_values(self):
        print()
        print('--------------------------------------------------------------------------------')
        print('- Validate internal consistency of Source_Value entries for each')
        print('- Classification_Mnemonic within Category_Mapping.csv')
        print('- ')
        print('- Category codes for a classification are identified as the set of Target_Value')
        print('- values for a given Classification_Mnemonic. For every classification that has a')
        print('- parent then:')
        print('-   * Each Source_Value in the mapping must be a category code in the parent')
        print('-   * There must be a single mapping record for each Source_Value')
        print('-   * Every parent category code must be mapped')
        print('--------------------------------------------------------------------------------')
        print()
        target_values = dict()
        for classification_mnemonic, mappings in self.category_mappings.items():
            target_values[classification_mnemonic] = set()
            for mapping in mappings:
                target_value = mapping['Target_Value']
                normalized_target_value = self.normalize(target_value)
                target_values[classification_mnemonic].add(normalized_target_value)

        for classification_mnemonic, mappings in self.category_mappings.items():
            if classification_mnemonic not in self.classifications:
                continue
            classification = self.classifications[classification_mnemonic]
            parent_mnemonic = classification['Parent_Classification_Mnemonic'].strip()
            if not parent_mnemonic:
                continue

            parent_target_values = target_values[parent_mnemonic]
            source_values = list()
            for mapping in mappings:
                for source_value in self.parse_range(mapping['Source_Value']):
                    source_values.append(source_value)

            dupes = set([sv for sv in source_values if source_values.count(sv) > 1])
            unmapped_codes = parent_target_values - set(source_values)
            unknown_codes = set(source_values) - parent_target_values

            if dupes or unknown_codes or unmapped_codes:
                print(f'ERROR: {classification_mnemonic}: set of values for Source_Value do not '
                      'match the set of values for Target_Values for the '
                      f'Parent_Classification_Mnemonic: {parent_mnemonic}')
                if dupes:
                    print('  - Multiple entry for Source_Value:             '
                          f'{self.limited_sorted_list(dupes)}')
                if unknown_codes:
                    print('  - Source_Value is not Target_Value of parent:  '
                          f'{self.limited_sorted_list(unknown_codes)}')
                if unmapped_codes:
                    print('  - No entry for Target_Value of parent:         '
                          f'{self.limited_sorted_list(unmapped_codes)}')
                print()
                self.classifications_with_errs.add(classification_mnemonic)

    def check_consistent_labels(self):
        print('--------------------------------------------------------------------------------')
        print('- Checking for consistent labels between Category.csv and Category_Mapping.csv')
        print('--------------------------------------------------------------------------------')
        print()

        for classification_mnemonic, mappings in self.category_mappings.items():
            if classification_mnemonic not in self.categories:
                continue
            cats = self.categories[classification_mnemonic]
            different_int_labels = set()
            different_ext_labels = set()
            different_welsh_labels = set()
            for mapping in mappings:
                if not cats.get(mapping['Target_Value'], None):
                    continue
                int_map_en = mapping['Internal_Mapping_Label_English']
                int_cat_en = cats[mapping['Target_Value']]['Internal_Category_Label_English']
                if int_map_en.strip() != int_cat_en.strip():
                    different_int_labels.add((mapping['Target_Value'], int_cat_en, int_map_en))

                ext_map_en = mapping['External_Mapping_Label_English']
                ext_cat_en = cats[mapping['Target_Value']]['External_Category_Label_English']
                if ext_map_en.strip() != ext_cat_en.strip():
                    different_ext_labels.add((mapping['Target_Value'], ext_cat_en, ext_map_en))

                ext_map_cy = mapping['External_Mapping_Label_Welsh']
                ext_cat_cy = cats[mapping['Target_Value']]['External_Category_Label_Welsh']
                if ext_map_cy.strip() != ext_cat_cy.strip():
                    different_welsh_labels.add((mapping['Target_Value'], ext_cat_cy, ext_map_cy))

            if different_int_labels or different_ext_labels or different_welsh_labels:
                print(f'ERROR: {classification_mnemonic}: has different labels specified in '
                      'Category.csv and Category_Mapping.csv')
                if different_int_labels:
                    print('  - Internal_Category_Label_English and Internal_Mapping_Label_English '
                          f'differ for {len(different_int_labels)} category')
                    for label in sorted(different_int_labels)[0:self.max_elements]:
                        print(f'    - Category_Code: "{label[0]}" '
                              f'Internal_Category_Label_English: "{label[1]}" '
                              f'Internal_Mapping_Label_English: "{label[2]}"')
                    if len(different_int_labels) > self.max_elements:
                        print(f'    - PLUS {len(different_int_labels) - self.max_elements} others')

                if different_ext_labels:
                    print('  - External_Category_Label_English and External_Mapping_Label_English '
                          f'differ for {len(different_ext_labels)} category')
                    for label in sorted(different_ext_labels)[0:self.max_elements]:
                        print(f'    - Category_Code: "{label[0]}" '
                              f'External_Category_Label_English: "{label[1]}" '
                              f'External_Mapping_Label_English: "{label[2]}"')
                    if len(different_ext_labels) > self.max_elements:
                        print(f'    - PLUS {len(different_ext_labels) - self.max_elements} others')

                if different_welsh_labels:
                    print('  - External_Category_Label_Welsh and External_Mapping_Label_Welsh '
                          f'differ for {len(different_welsh_labels)} categories')
                    for label in sorted(different_welsh_labels)[0:self.max_elements]:
                        print(f'    - Category_Code: "{label[0]}" '
                              f'External_Category_Label_Welsh: "{label[1]}" '
                              f'External_Mapping_Label_Welsh: "{label[2]}"')
                    if len(different_welsh_labels) > self.max_elements:
                        print(f'    - PLUS {len(different_welsh_labels) - self.max_elements} '
                              'others')
                print()
                self.classifications_with_errs.add(classification_mnemonic)

    def normalize(self, code):
        """
        Normalize a category code.

        Strip leading/trailing whitespace and ignore leading zeros if the code is a string
        representation of a number and args.zeros is set.
        """
        code = code.strip()
        if self.ignore_leading_zeros and isnum(code):
            code = str(int(code))
        return code

    def parse_range(self, code_range):
        """
        Parse the code_range and return a normalized range of codes in the range.

        e.g.
        '1>4' returns ['1', '2', '3', '4']
        '01>04' returns ['01', '02', '03', '04'] if args.zeros is False
        '01>04' returns ['1', '2', '3', '4'] if args.zeros is True
        """
        codes_in_range = []
        range_limits = code_range.split('>', 1)
        if len(range_limits) == 1:
            codes_in_range.append(self.normalize(range_limits[0]))
        else:
            # zero fill each code in the range to the length of the first code value. This
            # will preserve the leading zeros formatting for codes within the range.
            codes_in_range.extend(
                [self.normalize(str(v).zfill(len(range_limits[0].strip()))) for v in
                 list(range(int(range_limits[0]), int(range_limits[1]) + 1))])
        return codes_in_range

    def limited_sorted_list(self, values):
        """Return a string representation of values containing at most self.max_elements."""
        if len(values) <= self.max_elements:
            return f'{sorted(values)}'
        return f'{sorted(values)[0:self.max_elements]} + {len(values)-self.max_elements} more'


def main():
    """Perform basic validation of structural metadata."""
    parser = ArgumentParser(description='Check structural metadata')

    parser.add_argument('--zeros',
                        action='store_true',
                        help='Ignore leading zeros')

    parser.add_argument('-i', '--input-dir',
                        type=str,
                        required=True,
                        help='Input directory containing CSV files to check')

    parser.add_argument('-m', '--max-elements',
                        type=int,
                        default=10,
                        help='Maximum number of elements to output in length limited lists')

    args = parser.parse_args()

    print('--------------------------------------------------------------------------------')
    print(f'- {Path(__file__).name} {VERSION} {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
    print('-')
    print('- This script performs basic checks on the internal consistency of structural')
    print('- metadata for the 2021 census as stored in CSV format.')
    print('--------------------------------------------------------------------------------')
    print()

    checker = Checker(args.input_dir, args.zeros, args.max_elements)
    checker.check_codebook_mnemonic()
    checker.check_identity_mappings()
    checker.check_category_consistency()
    checker.check_unique_labels()
    checker.check_source_values()
    checker.check_consistent_labels()

    if checker.classifications_with_errs:
        print('--------------------------------------------------------------------------------')
        print(f'FAIL: Errors detected in {len(checker.classifications_with_errs)} '
              'classifications:')
        print(f'{sorted(checker.classifications_with_errs)}')
        print('--------------------------------------------------------------------------------')
        return -1

    print('--------------------------------------------------------------------------------')
    print(f'PASS: No errors detected')
    print('--------------------------------------------------------------------------------')
    return 0


if __name__ == '__main__':
    sys.exit(main())
