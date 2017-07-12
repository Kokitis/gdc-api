from .api_files import *

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
	else:
		uuids = []
	elif barcode_type == 'sample':
		raise NotImplementedError()

	if len(uuids) == 1: uuids = uuids[0]

	return uuids