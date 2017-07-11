
from github import tabletools
from pprint import pprint


def _attemptRead(fns, op = 'or'):
	final_table = list()
	for fn in fns:
		try:
			table = tabletools.readCSV(fn)
		except FileNotFoundError:
			continue

		if op == 'or':
			final_table = table
			break
		elif op == 'and':
			final_table += table
		else:
			message = "'{}' is not a valid operation ('or', 'and')".format(op)
			raise KeyError(message)


	if len(final_table) == 0:
		print("The local files could not be found.")
	return final_table

def barcodeToUuid(barcodes):
	""" Converts a patient barcode or sample barcode into the corresponding uuid.
	"""

	if isinstance(barcodes, str):
		barcodes = [barcodes]

	barcode_type = 'case' if len(barcodes[0]) == 12 else 'sample'
	
	clinical_files = getLocalFiles('clinical')
	clinical_data = _attemptRead(clinical_files, op = 'and')

	if barcode_type == 'case':
		uuids = [(row['bcr_patient_barcode'], row['bcr_patient_uuid']) for row in clinical_data if row['bcr_patient_barcode'] in barcodes]

	elif barcode_type == 'sample':
		raise NotImplementedError()

	if len(uuids) == 1: uuids = uuids[0]

	return uuids

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

def generateSampleList():
	pass

def generateManifestFile():
	pass

def _generateFileIdMap():
	""" A two-colomn table matching a file id with a file name """
	pass

def getLocalFiles(name, read = False):
	if name == 'clinical':
		filename = [
			"C:\\Users\\Deitrickc\\Documents\\Projects\\Genome Project\\Data\\Clinical Data\\nationwidechildrens.org_clinical_patient_esca.tsv",
			"C:\\Users\\Deitrickc\\Documents\\Projects\\Genome Project\\Data\\Clinical Data\\20140110_STAD_Clinical_Data_Blacklisted_Cases_Removed.tsv"
		]
	elif name == 'histology':
		filename = "data/histology_diagnoses.tsv"
	elif name == 'caseApi':
		filename = "/home/upmc/Documents/Variant_Discovery_Pipeline/0_config_fileslocal_case_api.json"
	elif name == 'fileApi':
		filename = "/home/upmc/Documents/Variant_Discovery_Pipeline/0_config_files/local_file_api.json"
	elif name == 'localManifestFile':
		filename = "data/all_tcga_esca_and_tcga_stad_manifest.tsv"
	else:
		message = "'{}' does not refere to a local api file.".format(name)
		raise KeyError(message)

	if read:
		result = _attemptRead(filename)
	else:
		result = filename

	return result

if __name__ == "__main__":
	test_barcode = 'TCGA-2H-A9GF'
	result = getFileIds(test_barcode)
	pprint(result)
