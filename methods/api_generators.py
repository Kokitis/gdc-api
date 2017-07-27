import os
from ..access import request
from ..github import tabletools
from pprint import pprint

def generateSampleList(folder, filename = None, filter = "Esophagus Adenocarcinoma, NOS"):
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

		case_information[patient_barcode][sample_type] = info


	table = list()
	for patient_barcode, data in case_information.items():
		tumor_info = data.get('Primary Tumor')
		blood_normal = data.get('Blood Derived Normal')
		tissue_normal = data.get('Solid Tissue Normal')

		if not tumor_info: continue
		if tumor_info['histology'] != filter: continue
		if blood_normal:
			matched_normal = blood_normal
		elif tissue_normal:
			matched_normal = tissue_normal
		else:
			continue

		row = {
			'CaseID': 		tumor_info['caseId'],
			'ExomeTargets': "/home/upmc/Documents/Reference/Capture_Targets/SeqCap_EZ_Exome_v3_capture.hg38_GDC_official.bed",
			'Histology': 	tumor_info['histology'],
			'NormalBAM': 	matched_normal['location'],
			'NormalID': 	matched_normal['sampleBarcode'],
			'NormalType': 	matched_normal['sampleType'],
			'NormalUUID': 	matched_normal['fileId'],
			'PatientID': 	patient_barcode,
			'SampleID': 	tumor_info['sampleBarcode'],
			'SampleUUID': 	tumor_info['fileId'],
			'TumorBAM': 	tumor_info['location'],
			'Use': 			'yes'
		}
		table.append(row)

	if filename:
		_table = tabletools.pandas.DataFrame(table)
		_table = tabletools.Table(_table)
		_table.save(filename)


	return table

def generateManifestFile():
	pass

def generateFileIdMap():
	""" A two-colomn table matching a file id with a file name """
	pass