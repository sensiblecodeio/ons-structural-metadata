import glob
import os
import csv
import logging
import sys



def isnum(s):
    try:
        x=int(s)
    except ValueError:
        return False
    return True

STRIP_WHITESPACE = True
STRIP_LEADING_ZEROS = True

def normalize(s):
    if STRIP_WHITESPACE:
        s = s.strip()
    if STRIP_LEADING_ZEROS:
        if isnum(s):
            s = str(int(s))
    return s

def parse_range(r):
    values = []
    for a in r.split(','):
        b = a.split('>',1)
        if len(b) == 1:
            values.append(normalize(b[0]))
        else:
            values.extend([str(v) for v in list(range(int(b[0]), int(b[1])+1))])
    return values

def main():
    classifications = dict()
    with open('src/Classification.csv', newline='') as infile:
        reader = csv.DictReader(infile, delimiter=',')
        for row in reader:
            classification_mnemonic = row['Classification_Mnemonic']
            if classification_mnemonic in classifications:
                print(f'Duplicate classification in Category.csv: {classification_mnemonic}')
                continue
            classifications[classification_mnemonic] = row

    categories = dict()
    with open('src/Category.csv', newline='') as infile:
        reader = csv.DictReader(infile, delimiter=',')
        for row in reader:
            classification_mnemonic = row['Classification_Mnemonic']
            if classification_mnemonic not in categories:
                if classification_mnemonic not in classifications:
                    print(f'{classification_mnemonic} specified in Category.csv not found in Classification.csv')
                categories[classification_mnemonic] = dict()
            code = row['Category_Code']
            if code in categories[classification_mnemonic]:
                print(f'Duplicate code for {classification}: {code} in Category.csv')
            categories[classification_mnemonic][code] = row

    category_mappings = dict()
    with open('src/Category_Mapping.csv', newline='') as infile:
        reader = csv.DictReader(infile, delimiter=',')
        for row in reader:
            classification_mnemonic = row['Classification_Mnemonic']
            if classification_mnemonic == 'moving_group_size_10000a':
                continue
            if classification_mnemonic not in classifications:
                print(f'{classification_mnemonic} specified in Category_Mapping.csv not found in Category.csv')
            if classification_mnemonic not in category_mappings:
                category_mappings[classification_mnemonic] = list()
            category_mappings[classification_mnemonic].append(row)

    print('--------------------------------------------------------------------------------')
    print('Checking that all same Codebook_Mnemonic is used for all rows in')
    print('Category_Mapping.csv with the same Classification_Mnemonic')
    print('--------------------------------------------------------------------------------')
    print()
    for classification_mnemonic, mappings in category_mappings.items():
        if classification_mnemonic not in classifications:
            continue
        classification = classifications[classification_mnemonic]
        if not classification['Parent_Classification_Mnemonic'].strip() :
            codebook_mnemonic = mappings[0]['Codebook_Mnemonic']
            for mapping in mappings:
                if mapping['Codebook_Mnemonic'] != codebook_mnemonic:
                    print(f'Different values of Codebook_Mnemonic used for {classification_mnemonic} in Category_Mapping.csv')
                    break


    print('--------------------------------------------------------------------------------')
    print('When Parent_Classification_Mnemonic is not specified in Classification.csv')
    print('check that the Source_Value equals the Target_Value for every category.')
    print('--------------------------------------------------------------------------------')
    print()

    source_codes = dict()
    for classification_mnemonic, mappings in category_mappings.items():
        if classification_mnemonic not in classifications:
            continue
        classification = classifications[classification_mnemonic]
        if not classification['Parent_Classification_Mnemonic'].strip():
            num_differences = 0
            normalized_source_codes = set()
            for mapping in mappings:
                source = normalize(mapping['Source_Value'])
                target = normalize(mapping['Target_Value'])
                normalized_source_codes.add(source)
                if source != target:
                    num_differences+=1
            if num_differences:
                source_codes[classification_mnemonic] = normalized_source_codes
                print(f'{classification_mnemonic} has different Source_Value and Target_Value in {num_differences}/{len(mappings)} rows')
                parent_of = [c['Classification_Mnemonic'] for c in classifications.values() if c['Parent_Classification_Mnemonic'] == classification_mnemonic]
                if parent_of:
                    print(f'  {classification_mnemonic} is the parent of {parent_of}')
                print()

    print('Classifications with no parent mapped from raw codes:')
    for classification_mnemonic in source_codes:
        print(classification_mnemonic)

    print('--------------------------------------------------------------------------------')
    print('Checking that all Target_Value codes in Category_Mapping.csv are known codes')
    print('for the Classification_Mnemonic as read from Category.csv.')
    print('--------------------------------------------------------------------------------')
    print()
    classifications_with_unknown_target = dict()
    for classification_mnemonic, mappings in category_mappings.items():
        classification_cats = categories[classification_mnemonic]
        normalized_cats = [normalize(c) for c in classification_cats]
        unknown_codes = set()
        for mapping in mappings:
            target_value = mapping['Target_Value']
            normalized_target_value = normalize(target_value)
            if normalized_target_value not in normalized_cats:
                if classification_mnemonic not in classifications_with_unknown_target:
                    classifications_with_unknown_target[classification_mnemonic] = list()
                classifications_with_unknown_target[classification_mnemonic].append(target_value)

    for classification_mnemonic, unknown_codes in classifications_with_unknown_target.items():
        print(f'Category_Mapping.csv contains unknown Target_Value for {classification_mnemonic}: {unknown_codes}')
        print(f'Valid codes for {classification_mnemonic} are: {categories[classification_mnemonic].keys()}')
        print()



    print('--------------------------------------------------------------------------------')
    print('Checking that all Source_Value codes in Category_Mapping.csv are known codes')
    print('for the Parent_Classification_Mnemonic as read from Category.csv.')
    print('Classifications without a Parent_Classification_Mnemonic are excluded.')
    print('--------------------------------------------------------------------------------')
    print()
    unknown_codes = dict()
    children_with_raw_codes = set()
    for classification_mnemonic, mappings in category_mappings.items():
        if classification_mnemonic not in classifications:
            continue
        classification = classifications[classification_mnemonic]
        parent_mnemonic = classification['Parent_Classification_Mnemonic'].strip()
        if not parent_mnemonic:
            continue

        classification_cats = [normalize(c) for c in categories[parent_mnemonic]]
        for mapping in mappings:
            for sv in parse_range(mapping['Source_Value']):
                missing = False
                if parent_mnemonic in source_codes:
                    children_with_raw_codes.add(classification_mnemonic)
                    if sv not in source_codes[parent_mnemonic]:
                        missing = True
                elif sv not in classification_cats:
                    missing = True

                if missing:
                    if parent_mnemonic not in unknown_codes:
                        unknown_codes[parent_mnemonic] = set()
                    unknown_codes[parent_mnemonic].add(sv)

    for parent_mnemonic,codes in unknown_codes.items():
        print(f'Category_Mapping.csv contains unknown Source_Value for {parent_mnemonic}: {codes}')
        if parent_mnemonic in source_codes:
            print(f'Valid raw codes for {parent_mnemonic} are: {list(source_codes[parent_mnemonic])}')
        else:
            print(f'Valid codes for {parent_mnemonic} are: {list(categories[parent_mnemonic].keys())}')
        print()

    if children_with_raw_codes:
        print(f'Classifications mapped from raw codes:')
        for classification_mnemonic in children_with_raw_codes:
            print(classification_mnemonic)



    print('--------------------------------------------------------------------------------')
    print('Checking for unique category labels in Category.csv')
    print('--------------------------------------------------------------------------------')
    print()
    for classification_mnemonic, cats in categories.items():
        label_ext = list()
        label_int = list()
        label_cy = list()
        for category in cats.values():
            label_ext.append(category['External_Category_Label_English'])
            label_int.append(category['Internal_Category_Label_English'])
            label_cy.append(category['External_Category_Label_Welsh'])
        if len(label_ext) != len(set(label_ext)):
            dupes = [l for l in set(label_ext) if label_ext.count(l) > 1]
            print(f'{classification_mnemonic} has multiple categories with the same External_Category_Label_English: {dupes}')
            print()
        if len(label_int) != len(set(label_int)):
            dupes = [l for l in set(label_int) if label_int.count(l) > 1]
            print(f'{classification_mnemonic} has multiple categories with the same Internal_Category_Label_English: {dupes}')
            print()
        if len(label_cy) != len(set(label_cy)):
            dupes = [l for l in set(label_cy) if label_cy.count(l) > 1]
            print(f'{classification_mnemonic} has multiple categories with the same External_Category_Label_Welsh: {dupes}')
            print()


    print('--------------------------------------------------------------------------------')
    print('Checking for label consistentcy between Category.csv and Category_Mapping.csv')
    print('--------------------------------------------------------------------------------')
    print()
    for classification_mnemonic, mappings in category_mappings.items():
        unique_mappings = list()
        unique_target_values = set()
        unique_source_values = set()
        for mapping in mappings:
            unique_mappings.append((mapping['Target_Value'], mapping['Source_Value']))
            unique_target_values.add(mapping['Target_Value'])
            unique_source_values.add(mapping['Source_Value'])
        if len(unique_mappings) != len(set(unique_mappings)):
            print(f'Duplicate mappings found in Category_Mapping.csv for {classification_mnemonic}')
        if classification_mnemonic not in categories:
            print(f'<{classification_mnemonic}>')
            continue

        if classification_mnemonic not in classifications:
            continue
        if classification_mnemonic in source_codes or classifications[classification_mnemonic]['Parent_Classification_Mnemonic'] in source_codes:
            continue

        if len(unique_target_values) != len(categories[classification_mnemonic]):
            print(f'Incorrect number of target values found in Category_Mapping.csv for {classification_mnemonic}')
            print(f'Expected: {[c["Category_Code"] for c in categories[classification_mnemonic].values()]}')
            print(f'Found: {unique_target_values}')
            print()
        all_source_values = list()
        for tv in unique_source_values:
            all_source_values.extend(parse_range(tv))
        if len(all_source_values) != len(set(all_source_values)):
            dupes = [c for c in set(all_source_values) if all_source_values.count(c) > 1]
            print(f'Duplicate source values found in Category_Mapping.csv for {classification_mnemonic}: {dupes}')
            print()

        parent = classifications[classification_mnemonic]['Parent_Classification_Mnemonic']
        if parent and len(set(all_source_values)) < len(categories[parent]):
            print(f'Too few source values supplied for {classification_mnemonic}')
            print(f'Missing code for {parent}: {categories[parent].keys()-set(all_source_values)}')
            print()

        if parent and len(set(all_source_values)) > len(categories[parent]):
            print(f'Too many source values supplied for {classification_mnemonic}')
            print(f'Missing code for {parent}: {set(all_source_values) - categories[parent].keys()}')
            print()
 

    print('--------------------------------------------------------------------------------')
    print('Checking for unique category labels in Category.csv')
    print('--------------------------------------------------------------------------------')
    print()

    f_int = open('internal_english_inconsistent_labels.csv', 'w')
    writer_int = csv.writer(f_int)
    writer_int.writerow([
        'Classification_Mnemonic',
        'Code',
        'Internal_Category_Label_English',
        'Internal_Mapping_Label_English',
    ])

    f_ext = open('external_english_inconsistent_labels.csv', 'w')
    writer_ext = csv.writer(f_ext)
    writer_ext.writerow([
        'Classification_Mnemonic',
        'Code',
        'External_Category_Label_English',
        'External_Mapping_Label_English',
    ])

    f_cy = open('external_welsh_inconsistent_labels.csv', 'w')
    writer_cy = csv.writer(f_cy)
    writer_cy.writerow([
        'Classification_Mnemonic',
        'Code',
        'External_Category_Label_Welsh',
        'External_Mapping_Label_Welsh',
    ])

    for classification_mnemonic, mappings in category_mappings.items():
        cats = categories[classification_mnemonic]
        different_int_labels = set()
        different_ext_labels = set()
        different_welsh_labels = set()
        for m in mappings:
            if not cats.get(m['Target_Value'], None):
                continue
            int_map_en = m['Internal_Mapping_Label_English']
            int_cat_en = cats[m['Target_Value']]['Internal_Category_Label_English']
            if int_map_en != int_cat_en:
                different_int_labels.add((m['Target_Value'], int_cat_en, int_map_en))

            ext_map_en = m['External_Mapping_Label_English']
            ext_cat_en = cats[m['Target_Value']]['External_Category_Label_English']
            if ext_map_en != ext_cat_en:
                different_ext_labels.add((m['Target_Value'], ext_cat_en, ext_map_en))

            ext_map_cy = m['External_Mapping_Label_Welsh']
            ext_cat_cy = cats[m['Target_Value']]['External_Category_Label_Welsh']
            if ext_map_cy.strip() != ext_cat_cy.strip():
                different_welsh_labels.add((m['Target_Value'], ext_cat_cy, ext_map_cy))

        if different_int_labels:
            print(f'{classification_mnemonic} has different values of Internal_Category_Label_English and Internal_Mapping_Label_English')
            print()
            for l in different_int_labels:
                writer_int.writerow([classification_mnemonic, l[0], l[1], l[2]])

        if different_ext_labels:
            print(f'{classification_mnemonic} has different values of External_Category_Label_English and External_Mapping_Label_English')
            print()
            for l in different_ext_labels:
                writer_ext.writerow([classification_mnemonic, l[0], l[1], l[2]])

        if different_welsh_labels:
            print(f'{classification_mnemonic} has different values of External_Category_Label_Welsh and External_Mapping_Label_Welsh')
            print()
            for l in different_welsh_labels:
                writer_cy.writerow([classification_mnemonic, l[0], l[1], l[2]])

    f_int.close()
    f_ext.close()
    f_cy.close()


    for classification_mnemonic, classification in classifications.items():
        if classification_mnemonic not in categories:
            print(f'No entries in Category.csv for {classification_mnemonic}')
        if classification['Parent_Classification_Mnemonic'] and classification_mnemonic not in category_mappings:
            print(f'No entries in Category_Mapping.csv for {classification_mnemonic}')


if __name__ == '__main__':
    main()
