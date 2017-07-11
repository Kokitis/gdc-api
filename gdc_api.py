import json
from collections import defaultdict
from pprint import pprint
import os
import requests
import utilities
local_file_api_filename = ""
local_case_api_filename = ""

class BaseApi:
	def __init__(self):
		self._null_result = None
		self._empty_resut = "unknown" # default value when the value doesn't have a value
		self._defineLocalAttributes()
		self.local_files = self._loadLocalApiFiles()

	def __call__(self, uuid):
		uuid = uuid.lower()
		response = self.apiRequest(uuid)
		return response

	def _loadLocalApiFiles(self):
		if os.path.exists(self.local_api_filename):
			with open(local_file_api_filename, 'r') as api_file:
				local_api = json.loads(api_file.read())
		else:
			local_api = defaultdict(lambda: None)

		return local_api

	def rawRequest(self, uuid, parameters = None):
		url = 'https://gdc-api.nci.nih.gov/{endpoint}/{uuid}'.format(
			endpoint = self.endpoint,
			uuid = uuid
		)

		if parameters is None:
			parameters = self.default_parameters

		raw_response = requests.get(url, parameters)
		return raw_response

	def apiRequest(self, uuid, parameters = None):
		raw_response = self.rawRequest(uuid, parameters)

		if raw_response.status_code != 200:
			response = self.local_api.get(uuid)
			if response is None:
				message = "UUID '{}' does not exist in endpoint '{}'".format(uuid, self.endpoint)
				raise ValueError(message)
		else:
			raw_response = raw_response.json()['data']
			response = self.processApiResponse(raw_response)

		return raw_response

	def processApiResponse(self, raw_response):
		raise NotImplementedError()

class FileApi(BaseApi):
	def _defineLocalAttributes(self):
		self.local_api_filename = local_file_api_filename
		self.endpoint = 'files'
		all_expand_fields = [
			'analysis', 'analysis.metadata.read_groups', 'analysis.input_files', 
			'annotations', 'archive', 'associated_entities', 'cases', 'cases.annotations',
			'cases.demographic', 'cases.diagnoses', 'cases.family_histories', 'cases.project',
			'cases.samples', 'cases.samples', 'downstream_analyses.output_files', 'center'
		]
		self.default_parameters = {
			'expand': ','.join(all_expand_fields)
		}
	def processApiResponse(self, raw_response):
		_relevant_case = self._getCaseInformation(raw_response)
		sample_information = self._getSampleInformation(_relevant_case, raw_response)
		read_groups = self._getRelevantReadGroups(raw_response)
		index_file = self._getMatchingIndexFile(raw_response)

		default_values = self._processApiResponseDefaultValues(
			_relevant_case,
			sample_information,
			index_file,
			read_groups
		)
		_relevant_case = default_values['caseInfo']
		sample_information = default_values['sampleInfo']
		index_file = default_values['indexInfo']
		read_groups = default_values['readGroups']


		common_information = self._getCommonInformation(
			raw_response, 
			_relevant_case, 
			sample_information,
			index_file
		)

		processed_response = raw_response
		processed_response['basic_info'] = common_information

		return processed_response
	@staticmethod
	def _processApiResponseDefaultValues(case_info, sample_info, index_info, read_groups):
		_default_value = None
		if not case_info:
			case_info = {
				'case_id': _default_value,
				'submitter_id': _default_value
			}

		if not sample_info:
			sample_info = {
				'sampleBarcode': _default_value,
				'sampleType': _default_value
			}
		if not index_info:
			index_info = {
				'file_id': _default_value,
				'file_name': _default_value,
				'md5sum': _default_value
			}
		if not read_groups:
			read_groups = None 

		result = {
			'caseInfo': case_info,
			'sampleInfo': sample_info,
			'indexInfo': index_info,
			'readGroups': read_groups
		}
		return result

	def _getSampleInformation(self, case_info, response):
		_default_value = 'unknown'
		if case_info and 'samples' in case_info.keys(): #make sure case is not None (it was found)
			sample_info = case_info['samples'][0]

			sample_type = sample_info.get('sample_type', _default_value)
			sample_barcode = sample_info.get('submitter_id', _default_value)
		else:
			sample_type = _default_value
			sample_barcode = _default_value

		result = {
			'sampleType': sample_type,
			'sampleBarcode': sample_barcode
		}
		return result


	def _getCaseInformation(self, response):
		if 'cases' in response.keys():
			case_info = response['cases'][0]
		else:
			case_info = None
		return case_info

	def _getRelevantReadGroups(self, response):
		try:
			read_groups = response['analysis']['metadata']['read_groups'][0]
		except KeyError:
			read_groups = {}

		return read_groups
	def _getMatchingIndexFile(self, response):
		if 'index_files' in response:
			index_file = response['index_files'][0]
		else:
			index_file = None

		return index_file
	def _getCommonInformation(self, response, case_info, sample_info, index_file):
		_default_value = None
		if case_info:
			case_uuid = case_info['case_id']
			patient_barcode = case_info['submitter_id']
		else:
			case_uuid = _default_value
			patient_barcode = _default_value
		if index_file:
			index_file_id = index_file['file_id']
			index_file_name=index_file['file_name']
			index_file_md5 = index_file['md5sum']
		else:
			index_file_id = index_file_name = index_file_md5 = None

		histology = utilities.getHistology(case_uuid)

		infodict = {
		#---------------- Basic file info ----------------
			'fileSize': response['file_size'],
			'fileId': response['file_id'],
			'fileName': response['file_name'],
			'fileType': response['file_type'],
			'fileFormat': response['file_format'],
			#------------------- sample info -----------------
			'sampleBarcode': sample_info['sampleBarcode'],
			'sampleType': sample_info['sampleType'], #tissue type
			'genomeBuild': "GRCh38.p0",
			'genomeName': "GRCh38.d1.vd1",
			#---------------- Basic case info ----------------
			'caseId': case_uuid,
			'histology': histology,
			'patientBarcode': patient_barcode,
			#--------------- Probe Targets info --------------
			#'exome targets link': read_groups.get('target_capture_kit_target_region', None),
			#'exome targets file': _default_value
			#'capture kit catalog number': read_groups.get('target_capture_kit_catalog_number', ""),
			#'capture kit name': read_groups.get('target_capture_kit_name', _default_value).replace('\n', ''),
			#Index Files
			'indexId': index_file_id,
			'indexName': index_file_name,
			'indexMd5sum': index_file_md5
		}
		return infodict
	def _getFileInformation(self, response):

		file_type = response['file_type']
		file_size = response['file_size']

		result = {

		}
		return result

class CaseApi(BaseApi):
	def _defineLocalAttributes(self):
		self.local_api_filename = local_case_api_filename
		self.endpoint = 'cases'
		self.default_parameters = {
			'expand': ','.join(
				[
					'samples', 'files', 'files.cases.samples',
					'summary', 'exposures', 'diagnoses', 'demographic'
				]
			)
		}

	def processApiResponse(self, raw_response):
		all_case_files = self._getCaseFiles(raw_response)
		all_case_files = {k:len(v) for k,v in all_case_files.items()}

		common_information = self._getCommonInformation(raw_response, all_case_files)
		common_information['fileCount'] = all_case_files
		processed_response = raw_response
		processed_response['basic_info'] = common_information

	def _processApiResponseDefaultValues(self):
		pass

	def _getCaseFiles(self, case_info):
		file_list = case_info['files']
		case_files = dict()

		for fn in file_list:
			data_category = fn.get('data_category')
			if data_category:
				if data_category not in case_files:
					case_files[data_category] = list()
				case_files[data_category].append(fn)

		return case_files

	def _getCommonInformation(self, response, case_files):

		common_info = {
			'caseId': response['case_id'],
			'primarySite': response['primary_site']
		}

		return common_info

def request(uuid, endpoint):

	if endpoint == 'files':
		response = FILE_API(uuid)
	elif endpoint == 'cases':
		response = CASE_API(uuid)
	else:
		message = "Endpoint muse be either 'cases' or 'files' ('{}')".format(endpoint)
		raise ValueError(message)

	return response

FILE_API = FileApi()
CASE_API = CaseApi()


if __name__ == "__main__":
	#test_file_uuid = "579bce59-438b-4ee2-b199-a91de73bca0e"
	test_file_uuid = "e929e62c-9f23-46f3-a6f6-ca1246c0f8a6"
	test_case_uuid = "0500f1a6-a528-43f3-b035-12d3b7c99c0f"
	test_endpoint = "cases"
	response = request(test_case_uuid, test_endpoint)

	pprint(response)