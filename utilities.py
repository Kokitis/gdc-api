
from github import tabletools



def _attemptRead(fns, op = 'or'):
	final_table = list()
	for fn in fns:
		try:
			table = tabletools.readCSV(fn)
			if op == 'or':
				final_table = table
				break
			elif op == 'and':
				final_table += table
			else:
				message = "'{}' is not a valid operation ('or', 'and')".format(op)
				raise KeyError(message)
		except FileNotFoundError:
			pass

	if len(table) == 0:
		print("The local files could not be found.")

	return table

def barcodeToUuid(barcodes):
	""" Converts a patient barcode or sample barcode into the corresponding uuid.
	"""

	if isinstance(barcodes, str):
		barcodes = [barcodes]

	ids = list()

	barcode_type = 'case' if len(barcodes[0]) == 12 else 'sample'

	clinical_data = _attemptRead(clinical_files)

	if barcode_type == 'case':
		uuids = [(row['bcr_patient_barcode'], row['bcr_patient_uuid']) for index, row in clinical_data if row['bcr_patient_barcode'] in barcodes]
	elif barcode_type == 'sample':
		pass

	return uuids

def getClinicalInformation():
		clinical_filenames = getLocalFiles('clinical')
		clinical_files = _attempRead(clinical_filenames, op = 'and')

		return clinical_files

def generateSampleList():
	pass

def generateHistologyFile():
	pass

def getLocalFiles(name, read = False):
	if name == 'clinical':
		filenames = [
			"C:\\Users\\Deitrickc\\Documents\\UPMC Files\\Projects\\Genome Instability Project\\Clinical Data\\nationwidechildrens.org_clinical_patient_esca.tsv",
			"C:\\Users\\Deitrickc\\Documents\\UPMC Files\\Projects\\Genome Instability Project\\Clinical Data\\20140110_STAD_Clinical_Data_Blacklisted_Cases_Removed.tsv"
		]
	elif name == 'histology':
		filenames = [
			"C:\\Users\\Deitrickc\\Documents\\UPMC Files\\Projects\\Genome Instability Project\\Clinical Data\\histology_diagnoses.txt",
			"/home/upmc/Documents/Variant_Discovery_Pipeline/0_config_files/histology_diagnosis.txt"
		]
	elif name == 'caseApi':
		filenames = "/home/upmc/Documents/Variant_Discovery_Pipeline/0_config_fileslocal_case_api.json"
	elif name == 'fileApi':
		filenames = "/home/upmc/Documents/Variant_Discovery_Pipeline/0_config_files/local_file_api.json"

	if read:
		result = _attemptRead(filenames)
	else:
		result = filenames

	return result
