import methods.api_files

from .baseapi import BaseApi



class FileApi(BaseApi):
	def _defineLocalAttributes(self):
		self.local_api_filename = methods.api_files.getLocalFile('fileApi')
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

		histology = methods.getHistology(case_uuid)

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
