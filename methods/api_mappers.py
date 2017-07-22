from .api_files import *
from ..github import tabletools
def barcodeToUuid(barcodes):
	""" Converts a patient barcode or sample barcode into the corresponding uuid.
	"""

	if isinstance(barcodes, str):
		barcodes = [barcodes]

	barcode_type = 'case' if len(barcodes[0]) == 12 else 'sample'
	
	clinical_files = getLocalFile('clinical')
	clinical_data = _attemptRead(clinical_files, op = 'and')

	if barcode_type == 'case':
		uuids = [(row['bcr_patient_barcode'], row['bcr_patient_uuid']) for row in clinical_data if row['bcr_patient_barcode'] in barcodes]
	else: 
		raise NotImplementedError()

	if len(uuids) == 1: uuids = uuids[0]

	return uuids

def getHistology(identifier):
	histology_table = tabletools.Table(getLocalFile('histology'))

	for row in histology_table:
		if identifier in row.values:
			result = row['histology']
			break
	else:
		result = "unknown"

	return result
