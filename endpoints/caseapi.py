from .. import methods
from .baseapi import BaseApi

class CaseApi(BaseApi):
	def _defineLocalAttributes(self):
		self.local_api_filename = methods.api_files.getLocalFile('caseApi')
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
		return processed_response

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