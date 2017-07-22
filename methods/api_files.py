
import os
from ..github import tabletools

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

def getLocalFile(name, read = False):
	if os.name == 'nt':
		_user_folder_key = 'USERPROFILE'
	else:
		_user_folder_key = 'HOME'
	user_folder = os.getenv(_user_folder_key)

	local_folder = os.path.dirname(os.path.dirname(__file__))

	if name == 'clinical':
		filename = [
			"C:\\Users\\Deitrickc\\Documents\\Projects\\Genome Project\\Data\\Clinical Data\\nationwidechildrens.org_clinical_patient_esca.tsv",
			"C:\\Users\\Deitrickc\\Documents\\Projects\\Genome Project\\Data\\Clinical Data\\20140110_STAD_Clinical_Data_Blacklisted_Cases_Removed.tsv"
		]

	elif name == 'histology':
		filename = os.path.join(local_folder, "data/histology_diagnoses.xlsx")
	elif name == 'caseApi':
		filename = "/home/upmc/Documents/Variant_Discovery_Pipeline/0_config_fileslocal_case_api.json"
	elif name == 'fileApi':
		filename = "/home/upmc/Documents/Variant_Discovery_Pipeline/0_config_files/local_file_api.json"
	elif name == 'localManifestFile':
		filename = "data/all_tcga_esca_and_tcga_stad_manifest.tsv"
	elif name == 'program':
		filename = os.path.join(user_folder, 'Programs', 'gdc-client', 'gdc-client_v1.2.0')

	elif name == 'token':

		folder = os.path.join(user_folder, 'Programs', 'gdc-client')
		try:
			tokens = [fn for fn in os.listdir(folder) if 'token' in fn]
		except FileNotFoundError:
			tokens = []

		if len(tokens) == 0:
			filename = 'token.txt'
		else:
			filename = max(tokens) # token files sort themselves by date of download.

		filename = os.path.join(folder, filename)

	else:
		message = "'{}' does not refere to a local api file.".format(name)
		raise KeyError(message)

	if read:
		result = _attemptRead(filename)
	else:
		result = filename

	return result