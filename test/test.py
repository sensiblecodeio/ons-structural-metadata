import unittest.mock
import unittest
from io import StringIO
from datetime import datetime
import check_structural_metadata


class TestStructuralMetadataChecker(unittest.TestCase):
    @unittest.mock.patch('sys.stdout', new_callable=StringIO)
    @unittest.mock.patch('check_structural_metadata.datetime')
    def test_no_issues(self, mock_datetime, mock_stdout):
        self.maxDiff = 1000
        mock_datetime.now.return_value = datetime(1970, 1, 1)

        expected_lines = """--------------------------------------------------------------------------------
- check_structural_metadata.py v1.0.0 01/01/1970 00:00:00
-
- This script performs basic checks on the internal consistency of structural
- metadata for the 2021 census as stored in CSV format.
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
- Read test/data/good/Classification.csv
- Identify all classifications.
- Check for duplicate Classification_Mnemonic values.
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
- Read test/data/good/Category.csv
- Identify categories associated with each classification.
- Check that each Classification_Mnemonic has entry in Classification.csv
- Check for duplicate category codes on a per classification basis.
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
- Read test/data/good/Category_Mapping.csv
- Identify category mappings associated with each classification.
- Check that each Classification_Mnemonic has entry in Category.csv
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
- Checking that same Codebook_Mnemonic is used for all rows in
- Category_Mapping.csv with the same Classification_Mnemonic
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
- When Parent_Classification_Mnemonic is not specified in Classification.csv
- check that the Source_Value equals the Target_Value for every category
- in Category_Mapping.csv.
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
- Check that for a given Classification_Mnemonic the set of Target_Value values
- in Category_Mapping.csv is the same as the set of Category_Code values
- in Classification.csv
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
- Checking for unique category labels in Category.csv on a per classification
- basis
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
- Validate internal consistency of Source_Value entries for each
- Classification_Mnemonic within Category_Mapping.csv
-
- Category codes for a classification are identified as the set of Target_Value
- values for a given Classification_Mnemonic. For every classification that has a
- parent then:
-   * Each Source_Value in the mapping must be a category code in the parent
-   * There must be a single mapping record for each Source_Value
-   * Every parent category code must be mapped
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
- Checking for consistent labels between Category.csv and Category_Mapping.csv
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
PASS: No errors detected
--------------------------------------------------------------------------------
""".splitlines()

        with unittest.mock.patch('sys.argv', ['test', '-i', 'test/data/good']):
            ret_code = check_structural_metadata.main()
            self.assertEqual(ret_code, 0)
            output_lines = mock_stdout.getvalue().splitlines()
            self.assertEqual(len(output_lines), len(expected_lines))
            for idx, line in enumerate(output_lines):
                self.assertEqual(line.strip(), expected_lines[idx].strip(), msg=f'on line {idx}')

    @unittest.mock.patch('sys.stdout', new_callable=StringIO)
    @unittest.mock.patch('check_structural_metadata.datetime')
    def test_with_errors(self, mock_datetime, mock_stdout):
        self.maxDiff = 1000
        mock_datetime.now.return_value = datetime(1970, 1, 1)

        expected_lines = """--------------------------------------------------------------------------------
- check_structural_metadata.py v1.0.0 01/01/1970 00:00:00
-
- This script performs basic checks on the internal consistency of structural
- metadata for the 2021 census as stored in CSV format.
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
- Read test/data/bad/Classification.csv
- Identify all classifications.
- Check for duplicate Classification_Mnemonic values.
--------------------------------------------------------------------------------

ERROR: Duplicate_Entry: Duplicate Classification_Mnemonic in Category.csv

--------------------------------------------------------------------------------
- Read test/data/bad/Category.csv
- Identify categories associated with each classification.
- Check that each Classification_Mnemonic has entry in Classification.csv
- Check for duplicate category codes on a per classification basis.
--------------------------------------------------------------------------------

ERROR: Not_In_Classification: Classification_Mnemonic specified in Category.csv not found in Classification.csv
ERROR: Duplicate_Codes: duplicate code specified in Category.csv: C1

--------------------------------------------------------------------------------
- Read test/data/bad/Category_Mapping.csv
- Identify category mappings associated with each classification.
- Check that each Classification_Mnemonic has entry in Category.csv
--------------------------------------------------------------------------------

ERROR: Not_In_Category: Classification_Mnemonic specified in Category_Mapping.csv not found in Category.csv

--------------------------------------------------------------------------------
- Checking that same Codebook_Mnemonic is used for all rows in
- Category_Mapping.csv with the same Classification_Mnemonic
--------------------------------------------------------------------------------

ERROR: Different_Codebook_Mnemonic: different values of Codebook_Mnemonic specified for same Classification_Mnemonic

--------------------------------------------------------------------------------
- When Parent_Classification_Mnemonic is not specified in Classification.csv
- check that the Source_Value equals the Target_Value for every category
- in Category_Mapping.csv.
--------------------------------------------------------------------------------

ERROR: Different_Source_Target: different Source_Value and Target_Value specified on 2/3 rows
ERROR: Different_Source_Target_Zeros: different Source_Value and Target_Value specified on 3/3 rows
ERROR: Different_Code_Target_Zeros: different Source_Value and Target_Value specified on 3/3 rows

--------------------------------------------------------------------------------
- Check that for a given Classification_Mnemonic the set of Target_Value values
- in Category_Mapping.csv is the same as the set of Category_Code values
- in Classification.csv
--------------------------------------------------------------------------------

ERROR: Different_Code_Target: different set of Category_Code values in Category.csv and Target_Value values in Category_Mapping.csv
  - In Category.csv but not Category_Mapping.csv: ['2', '3']
  - In Category_Mapping.csv but not Category.csv: ['4', '5']

ERROR: Invalid_Source: different set of Category_Code values in Category.csv and Target_Value values in Category_Mapping.csv
  - In Category.csv but not Category_Mapping.csv: ['A', 'B', 'C']
  - In Category_Mapping.csv but not Category.csv: ['1', '2', '3']

ERROR: Invalid_Source_Parent: different set of Category_Code values in Category.csv and Target_Value values in Category_Mapping.csv
  - In Category.csv but not Category_Mapping.csv: ['1', '2', '3']
  - In Category_Mapping.csv but not Category.csv: ['A', 'B', 'C']


--------------------------------------------------------------------------------
- Checking for unique category labels in Category.csv on a per classification
- basis
--------------------------------------------------------------------------------

ERROR: Duplicate_Labels: multiple categories with the same External_Category_Label_English: ['En1']
ERROR: Duplicate_Labels: multiple categories with the same Internal_Category_Label_English: ['En1']
ERROR: Duplicate_Labels multiple categories with the same External_Category_Label_Welsh: ['Cy1']

--------------------------------------------------------------------------------
- Validate internal consistency of Source_Value entries for each
- Classification_Mnemonic within Category_Mapping.csv
-
- Category codes for a classification are identified as the set of Target_Value
- values for a given Classification_Mnemonic. For every classification that has a
- parent then:
-   * Each Source_Value in the mapping must be a category code in the parent
-   * There must be a single mapping record for each Source_Value
-   * Every parent category code must be mapped
--------------------------------------------------------------------------------

ERROR: Invalid_Source: set of values for Source_Value do not match the set of values for Target_Values for the Parent_Classification_Mnemonic: Invalid_Source_Parent
  - Multiple entry for Source_Value:             ['A']
  - Source_Value is not Target_Value of parent:  ['3']
  - No entry for Target_Value of parent:         ['B', 'C']

ERROR: Invalid_Source_Zeros: set of values for Source_Value do not match the set of values for Target_Values for the Parent_Classification_Mnemonic: Invalid_Source_Parent_Zeros
  - Source_Value is not Target_Value of parent:  ['01', '03', '2']
  - No entry for Target_Value of parent:         ['02', '3']

--------------------------------------------------------------------------------
- Checking for consistent labels between Category.csv and Category_Mapping.csv
--------------------------------------------------------------------------------

ERROR: Different_Labels: has different labels specified in Category.csv and Category_Mapping.csv
  - Internal_Category_Label_English and Internal_Mapping_Label_English differ for 2 category
    - Category_Code: "2" Internal_Category_Label_English: "EnInt2" Internal_Mapping_Label_English: "EnIntA"
    - Category_Code: "3" Internal_Category_Label_English: "EnInt3" Internal_Mapping_Label_English: "EnIntB"
  - External_Category_Label_English and External_Mapping_Label_English differ for 2 category
    - Category_Code: "2" External_Category_Label_English: "EnExt2" External_Mapping_Label_English: "EnExtA"
    - Category_Code: "3" External_Category_Label_English: "EnExt3" External_Mapping_Label_English: "EnExtB"
  - External_Category_Label_Welsh and External_Mapping_Label_Welsh differ for 2 categories
    - Category_Code: "2" External_Category_Label_Welsh: "Cy2" External_Mapping_Label_Welsh: "CyA"
    - Category_Code: "3" External_Category_Label_Welsh: "Cy3" External_Mapping_Label_Welsh: "CyB"

--------------------------------------------------------------------------------
FAIL: Errors detected in 14 classifications:
['Different_Code_Target', 'Different_Code_Target_Zeros', 'Different_Codebook_Mnemonic', 'Different_Labels', 'Different_Source_Target', 'Different_Source_Target_Zeros', 'Duplicate_Codes', 'Duplicate_Entry', 'Duplicate_Labels', 'Invalid_Source', 'Invalid_Source_Parent', 'Invalid_Source_Zeros', 'Not_In_Category', 'Not_In_Classification']
--------------------------------------------------------------------------------
""".splitlines()

        with unittest.mock.patch('sys.argv', ['test', '-i', 'test/data/bad']):
            ret_code = check_structural_metadata.main()
            self.assertEqual(ret_code, -1)
            output_lines = mock_stdout.getvalue().splitlines()
            self.assertEqual(len(output_lines), len(expected_lines))
            for idx, line in enumerate(output_lines):
                self.assertEqual(line.strip(), expected_lines[idx].strip())

    @unittest.mock.patch('sys.stdout', new_callable=StringIO)
    @unittest.mock.patch('check_structural_metadata.datetime')
    def test_with_leading_zeros_ignored(self, mock_datetime, mock_stdout):
        self.maxDiff = 1000
        mock_datetime.now.return_value = datetime(1970, 1, 1)

        expected_lines = """--------------------------------------------------------------------------------
- check_structural_metadata.py v1.0.0 01/01/1970 00:00:00
-
- This script performs basic checks on the internal consistency of structural
- metadata for the 2021 census as stored in CSV format.
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
- Read test/data/bad/Classification.csv
- Identify all classifications.
- Check for duplicate Classification_Mnemonic values.
--------------------------------------------------------------------------------

ERROR: Duplicate_Entry: Duplicate Classification_Mnemonic in Category.csv

--------------------------------------------------------------------------------
- Read test/data/bad/Category.csv
- Identify categories associated with each classification.
- Check that each Classification_Mnemonic has entry in Classification.csv
- Check for duplicate category codes on a per classification basis.
--------------------------------------------------------------------------------

ERROR: Not_In_Classification: Classification_Mnemonic specified in Category.csv not found in Classification.csv
ERROR: Duplicate_Codes: duplicate code specified in Category.csv: C1

--------------------------------------------------------------------------------
- Read test/data/bad/Category_Mapping.csv
- Identify category mappings associated with each classification.
- Check that each Classification_Mnemonic has entry in Category.csv
--------------------------------------------------------------------------------

ERROR: Not_In_Category: Classification_Mnemonic specified in Category_Mapping.csv not found in Category.csv

--------------------------------------------------------------------------------
- Checking that same Codebook_Mnemonic is used for all rows in
- Category_Mapping.csv with the same Classification_Mnemonic
--------------------------------------------------------------------------------

ERROR: Different_Codebook_Mnemonic: different values of Codebook_Mnemonic specified for same Classification_Mnemonic

--------------------------------------------------------------------------------
- When Parent_Classification_Mnemonic is not specified in Classification.csv
- check that the Source_Value equals the Target_Value for every category
- in Category_Mapping.csv.
--------------------------------------------------------------------------------

ERROR: Different_Source_Target: different Source_Value and Target_Value specified on 2/3 rows

--------------------------------------------------------------------------------
- Check that for a given Classification_Mnemonic the set of Target_Value values
- in Category_Mapping.csv is the same as the set of Category_Code values
- in Classification.csv
--------------------------------------------------------------------------------

ERROR: Different_Code_Target: different set of Category_Code values in Category.csv and Target_Value values in Category_Mapping.csv
  - In Category.csv but not Category_Mapping.csv: ['2', '3']
  - In Category_Mapping.csv but not Category.csv: ['4', '5']

ERROR: Invalid_Source: different set of Category_Code values in Category.csv and Target_Value values in Category_Mapping.csv
  - In Category.csv but not Category_Mapping.csv: ['A', 'B', 'C']
  - In Category_Mapping.csv but not Category.csv: ['1', '2', '3']

ERROR: Invalid_Source_Parent: different set of Category_Code values in Category.csv and Target_Value values in Category_Mapping.csv
  - In Category.csv but not Category_Mapping.csv: ['1', '2', '3']
  - In Category_Mapping.csv but not Category.csv: ['A', 'B', 'C']


--------------------------------------------------------------------------------
- Checking for unique category labels in Category.csv on a per classification
- basis
--------------------------------------------------------------------------------

ERROR: Duplicate_Labels: multiple categories with the same External_Category_Label_English: ['En1']
ERROR: Duplicate_Labels: multiple categories with the same Internal_Category_Label_English: ['En1']
ERROR: Duplicate_Labels multiple categories with the same External_Category_Label_Welsh: ['Cy1']

--------------------------------------------------------------------------------
- Validate internal consistency of Source_Value entries for each
- Classification_Mnemonic within Category_Mapping.csv
-
- Category codes for a classification are identified as the set of Target_Value
- values for a given Classification_Mnemonic. For every classification that has a
- parent then:
-   * Each Source_Value in the mapping must be a category code in the parent
-   * There must be a single mapping record for each Source_Value
-   * Every parent category code must be mapped
--------------------------------------------------------------------------------

ERROR: Invalid_Source: set of values for Source_Value do not match the set of values for Target_Values for the Parent_Classification_Mnemonic: Invalid_Source_Parent
  - Multiple entry for Source_Value:             ['A']
  - Source_Value is not Target_Value of parent:  ['3']
  - No entry for Target_Value of parent:         ['B', 'C']

ERROR: Invalid_Source_Zeros: set of values for Source_Value do not match the set of values for Target_Values for the Parent_Classification_Mnemonic: Invalid_Source_Parent_Zeros
  - Multiple entry for Source_Value:             ['1']

--------------------------------------------------------------------------------
- Checking for consistent labels between Category.csv and Category_Mapping.csv
--------------------------------------------------------------------------------

ERROR: Different_Labels: has different labels specified in Category.csv and Category_Mapping.csv
  - Internal_Category_Label_English and Internal_Mapping_Label_English differ for 2 category
    - Category_Code: "2" Internal_Category_Label_English: "EnInt2" Internal_Mapping_Label_English: "EnIntA"
    - Category_Code: "3" Internal_Category_Label_English: "EnInt3" Internal_Mapping_Label_English: "EnIntB"
  - External_Category_Label_English and External_Mapping_Label_English differ for 2 category
    - Category_Code: "2" External_Category_Label_English: "EnExt2" External_Mapping_Label_English: "EnExtA"
    - Category_Code: "3" External_Category_Label_English: "EnExt3" External_Mapping_Label_English: "EnExtB"
  - External_Category_Label_Welsh and External_Mapping_Label_Welsh differ for 2 categories
    - Category_Code: "2" External_Category_Label_Welsh: "Cy2" External_Mapping_Label_Welsh: "CyA"
    - Category_Code: "3" External_Category_Label_Welsh: "Cy3" External_Mapping_Label_Welsh: "CyB"

--------------------------------------------------------------------------------
FAIL: Errors detected in 12 classifications:
['Different_Code_Target', 'Different_Codebook_Mnemonic', 'Different_Labels', 'Different_Source_Target', 'Duplicate_Codes', 'Duplicate_Entry', 'Duplicate_Labels', 'Invalid_Source', 'Invalid_Source_Parent', 'Invalid_Source_Zeros', 'Not_In_Category', 'Not_In_Classification']
--------------------------------------------------------------------------------
""".splitlines()

        with unittest.mock.patch('sys.argv', ['test', '-i', 'test/data/bad', '--zeros']):
            ret_code = check_structural_metadata.main()
            self.assertEqual(ret_code, -1)
            output_lines = mock_stdout.getvalue().splitlines()
            self.assertEqual(len(output_lines), len(expected_lines))
            for idx, line in enumerate(output_lines):
                self.assertEqual(line.strip(), expected_lines[idx].strip())
