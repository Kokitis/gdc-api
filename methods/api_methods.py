
from github import tabletools
from pprint import pprint

def getFileIds(identifiers):
	if not isinstance(identifiers, (list, set)):
		identifiers = {identifiers}
	else:
		identifiers = set(identifiers)

	manifest_filename = getLocalFiles('localManifestFile')
	manifest_table = tabletools.Table(manifest_filename)

	result = list()
	for index, row in manifest_table:
		common_values = set(row.values) & identifiers
		if len(common_values) != 0: result.append(row.to_dict())

	return result


def getClinicalInformation():
		clinical_filenames = getLocalFiles('clinical')
		clinical_files = _attemptRead(clinical_filenames, op = 'and')

		return clinical_files

if __name__ == "__main__":
	test_barcode = 'TCGA-2H-A9GF'
	result = getFileIds(test_barcode)
	pprint(result)
