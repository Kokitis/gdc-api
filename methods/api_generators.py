import os
from ..access import request
from ..github import tabletools

def generateSampleList(folder, filename = None):
	""" Takes either a list of ids or a folder name """
	if isinstance(folder, str):
		ids = list(os.listdir(folder))
	else:
		ids = folder

	case_information = dict()

	for file_id in ids:
		response = request(file_id, 'files')
		info = response['basic_info']
		info['location'] = os.path.join(folder, info['fileId'], info['fileName'])

		patient_barcode = info['patientBarcode']
		sample_type = info['sampleType']
		if patient_barcode not in case_information:
			case_information[patient_barcode] = dict()

		case_information[patient_barcode]['sampleType'] = info


	table = list()
	for patient_barcode, data in case_information.items():
		tumor_info = data.get('Primary Tumor')
		blood_normal = data.get('Blood Derived Normal')
		tissue_normal = data.get('Tissue Derived Normal')
		print('yes')
		if blood_normal:
			matched_normal = blood_normal
		elif tissue_normal:
			matched_normal = tissue_normal
		else:
			continue

		row = {
			'CaseID': 		tumor_info['caseId'],
			'ExomeTargets': "",
			'Histology': 	info['sampleType'],
			'NormalBAM': 	matched_normal['location'],
			'NormalID': 	matched_normal['fileId'],
			'NormalType': 	matched_normal['sampleType'],
			'NormalUUID': 	matched_normal['fileId'],
			'PatientID': 	patient_barcode,
			'SampleID': 	tumor_barcode['sampleBarcode'],
			'TumorBAM': 	tumor_info['location'],
			'Use': 			'yes'
		}
		table.append(row)

	if filename:
		_table = tabletools.Table(table)
		_table.save(filename)


	return table

def generateManifestFile():
	pass

def generateFileIdMap():
	""" A two-colomn table matching a file id with a file name """
	pass