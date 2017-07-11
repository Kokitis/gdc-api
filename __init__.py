from endpoints import CaseApi, FileApi

FILE_API = fileFileApi()
CASE_API = CaseApi()

def request(uuid, endpoint):

	if endpoint == 'files':
		response = FILE_API(uuid)
	elif endpoint == 'cases':
		response = CASE_API(uuid)
	else:
		message = "Endpoint muse be either 'cases' or 'files' ('{}')".format(endpoint)
		raise ValueError(message)

	return response

