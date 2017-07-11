from endpoints import CaseApi, FileApi
from api_methods import *

FILE_API = FileApi()
CASE_API = CaseApi()

def _idType(string):
	if string.startswith('TCGA'):
		string_type = 'barcode'
	else:
		string_type = 'uuid'
	return string_type

def request(uuid, endpoint):
	""" Sends a request to the GDC api and returns the result.
		Parameters
			uuid: string
		endpoint: {'cases', 'files'}
			The endpoint to search under.
	"""
	identifier_type = _idType(uuid)
	if identifier_type == 'barcode':
		uuid = barcodeToUuid(uuid)[1]
	
	if endpoint == 'files':
		response = FILE_API(uuid)
	elif endpoint == 'cases':
		response = CASE_API(uuid)
	else:
		message = "Endpoint muse be either 'cases' or 'files' ('{}')".format(endpoint)
		raise ValueError(message)

	return response

if __name__ == "__main__":
	test_barcode = "TCGA-2H-A9GF"
	pprint(request(test_barcode, 'cases'))

