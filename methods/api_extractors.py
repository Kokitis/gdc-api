"""
	Methods to scrape specific information from api requests.
"""

import os
import re
from pprint import pprint

def extractFileInfo(case_file):
	""" Attempts to extract the outputs from the different callers.
	"""

	file_name = case_file['file_name']
	file_type = os.path.splitext(file_name)[1][1:].upper()
	data_type = case_file['data_type'] # 'Aggregated Somatic Mutation'
	submitter_id = case_file['submitter_id']

	file_caller = _extractFileCaller(case_file)

	result = {
		'fileName': file_name,
		'fileType': file_type,
		'dataType': data_type,
		'submitterId': submitter_id,
		#'status': file_status,
		'caller': file_caller
	}
	return result

def _extractFileCaller(case_file):
	""" Extracts the name of the caller used to generate the file, if applicable. """

	data_type = case_file['data_type']
	#file_name = case_file['file_name']
	submitter = case_file['submitter_id']

	if data_type == 'Aggregated Somatic Mutations':
		regex = "TCGA-ESCA-(?P<caller>[a-z]+)[.]"
		string = submitter
	elif data_type == 'Annotated Somatic Mutation':
		regex = "(?P<caller>[a-z]+)_annotated$"
		string = submitter 
	elif data_type == 'Raw Simple Somatic Mutation':
		regex = "_(?P<caller>[a-z]+)$"
		string = submitter 
	else:
		regex = string = None

	if regex:

		match = re.search(regex, string)
		match = match.groupdict()
		caller = match['caller']
	else:
		caller = None
	return caller

def extractFile(case_info, data_type, by, string):
	""" Extract information for a file based on the supplied values. 
		Parameters
		----------
			case_info: dict
				response from the api
			data_type: string
				* 'Raw Simple Somatic Mutation', 'raw'
				* 'Annotated Somatic Mutation', 'vep'
				* 'Aggregated Somatic Mutation'	'maf'
			by: {'file_name', 'id', 'caller'}
				The criteria to search through.
			string:
				The criteria to match the file on.
				* 'file_name': string
				* 'id': string
				* 'caller': {'muse', 'mutect', 'somaticsniper', 'varscan'}

	"""
	if 'files' in case_info:
		case_info = case_info['files']

	if data_type == 'raw': data_type = 'Raw Simple Somatic Mutation'
	elif data_type == 'vep': data_type = 'Annotated Somatic Mutation'
	elif data_type == 'maf': data_type = 'Aggregated Somatic Mutation'

	for case_file in case_info:
		file_info = extractFileInfo(case_file)
		if file_info['dataType'] != data_type: continue
		if by == 'id':
			text = file_info['fileId']
		elif by == 'file_name':
			text = file_info['fileName']
		elif by == 'caller':
			text = file_info['caller']
		else:
			message = "'{}' is not a searchable 'by' value ('id', 'filename', 'caller')".format(by)
			raise KeyError(message)
		status = text == string
		if status:
			break
	else:
		file_info = None

	return file_info

if __name__ == "__main__":
	test_case_id = '0500f1a6-a528-43f3-b035-12d3b7c99c0f'
	#case_info = access.request(test_case_id, 'cases')

	for case_file in case_info['files']:
		#file_info = _extractFileInfo(case_file)
		file_info = {
			'dataType:': case_file['data_type'],
			'fileName': case_file['file_name'],
			'submitterId': case_file['submitter_id']
		}
		print(case_file['file_name'])
		for k, v in file_info:
			print("\t{}\t{}".format(k, v))
	
