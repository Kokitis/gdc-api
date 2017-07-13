from endpoints import CaseApi, FileApi
from methods import *
from pprint import pprint
pprint(dir())

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

def generateCommand(uuid, **kwargs):
	""" Generates a command which may be used to run the gdc-client downloader. 
		Parameters
		----------
			uuid: str
				The id to download.
		Keyword Arguments
		-----------------
			folder: string [DIR]
				The folder to download the files to. Defaults to the current working directory.
	"""


	program_location = getLocalFile('program')
	token_location = getLocalFile('token')

	command = """{program} download {uuid} --token {token}""".format(
		program = program_location,
		uuid = uuid,
		token = token_location
	)

	if 'folder' in kwargs:
		command += " --dir " + kwargs['folder']

	return command