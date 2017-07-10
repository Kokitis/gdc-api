import requests
import os
import datetime
import csv
import json
from pprint import pprint

now = datetime.datetime.now

from github import tabletools

if os.name == 'nt': #Windows
	gdc_location = "C:\\Users\\Deitrickc\\Downloads\\Genomic Programs\\gdc-client"
	gdc_program  = os.path.join(gdc_location, 'gdc-client.exe')
	histology_filename = "C:\\Users\\Deitrickc\\Documents\\UPMC Files\\Projects\\Genome Instability Project\\Clinical Data\\histology_diagnoses.txt"
	clinical_files = ["C:\\Users\\Deitrickc\\Documents\\UPMC Files\\Projects\\Genome Instability Project\\Clinical Data\\nationwidechildrens.org_clinical_patient_esca.tsv",
					  "C:\\Users\\Deitrickc\\Documents\\UPMC Files\\Projects\\Genome Instability Project\\Clinical Data\\20140110_STAD_Clinical_Data_Blacklisted_Cases_Removed.tsv"]
	#manifest file containing the locations of all downloaded files.
	file_locations_filename = "C:\\Users\\Deitrickc\\Documents\\UPMC Files\\Projects\\Genome Instability Project\\Data\\Sample Lists\\full_manifest.DELL_LMD.tsv"
	local_file_api_filename = os.path.join("/home/upmc/Documents/Variant_Discovery_Pipeline/", "0_config_files", "local_file_api.json") #Path to a local copy of the file api
	local_case_api_filename = os.path.join("/home/upmc/Documents/Variant_Discovery_Pipeline/", "0_config_files", "local_case_api.json") #Path to a local copy of the case api
else:
	clinical_files = []
	histology_filename = os.path.join("/home/upmc/Documents/Variant_Discovery_Pipeline/", "0_config_files", "histology_diagnosis.txt")
	gdc_location = "/home/upmc/Programs/gdc_data_transfer_tool"
	local_file_api_filename = os.path.join("/home/upmc/Documents/Variant_Discovery_Pipeline/", "0_config_files", "local_file_api.json") #Path to a local copy of the file api
	local_case_api_filename = os.path.join("/home/upmc/Documents/Variant_Discovery_Pipeline/", "0_config_files", "local_case_api.json") #Path to a local copy of the case api
	gdc_program  = os.path.join(gdc_location, 'gdc-client-2016-10-19')

#user_token = os.path.join(gdc_location, 'tokens', max(list(os.listdir(os.path.join(gdc_location, "tokens")))))

def _get_exome_targets(catalog_number):
	""" Maps an exome target url to a local file """
	if catalog_number is not None:
		exome_targets_folder = "/home/upmc/Documents/Reference/Exome_Targets/"
		_931070 = os.path.join(exome_targets_folder , "whole_exome_agilent_1.1_refseq_plus_3_boosters.targetIntervals.bed")
		_6465692001 = os.path.join(exome_targets_folder , "SeqCap_EZ_Exome_v3_capture.bed")
		catalog_nnumber = '|'.join([i for i in catalog_number.split('|') if i != ['NA']])

		local_files = {
			#Custom V2 Exome Bait, 48 RXN X 16 tubes
			'931070': _931070,
			#Nimblegen SeqCap EZ Human Exome Library v3.0
			'06465692001': _6465692001
		}
		catalog_number = max(catalog_number.split('|'), key = lambda s: len(s))
		targets = local_files.get(catalog_number)
	else:
		targets = None

	return targets

def getFileLocation(io, col = 'id'):
	""" Retrieves the physical location of a file from an annotated manifest file.
		Parameters
		---------
			io: string
				A file id, patient barcode, or other way of selecting rows from the manifest file.
			col: {id, 'barcode', 'category', 'patient', 'sample type'}; default 'id'
				The column of the manifest file to search in.
	"""
	all_file_locations, all_file_locations_columns = tabletools.readCSV(file_locations_filename, True)
	rows = [i for i in all_file_locations if i[col] == io]

	if len(rows) == 1:
		rows = rows[0]
	elif len(rows) == 0:
		rows = {c: "" for c in all_file_locations_columns}
	return rows

def barcodeToUuid(barcodes):
	""" Converts a patient barcode or sample barcode into the corresponding uuid.
	"""

	if isinstance(barcodes, str):
		barcodes = [barcodes]
	ids = list()

	barcode_type = 'case' if len(barcodes[0]) == 12 else 'sample'

	clinical_data = list()
	for fn in clinical_files:
		clinical_data += tabletools.readCSV(fn)

	if barcode_type == 'case':
		uuids = [row['bcr_patient_uuid'] for row in clinical_data if row['bcr_patient_barcode'] in barcodes]
	elif barcode_type == 'sample':
		pass

	return uuids

class APIError(BaseException):
	pass

class GDCAPI:
	def __init__(self):

		
		self.histology_filename = histology_filename

		self.local_file_api, self.local_case_api = self.loadLocalApiFiles()
		#self.full_manifest = self._load_file_locations()
		self.histology = self._load_histology()
	def __call__(self, uuid, endpoint):
		response = self.request(uuid, endpoint)
		return response

	######################## API REQUEST METHODS #######################
	def _load_histology(self):
		"""
			Returns
			-------
				histology: dict<case_uuid: histology>
		"""
		
		if os.path.isfile(self.histology_filename):
			with open(self.histology_filename, 'r') as file1:
				reader = list(csv.reader(file1, delimiter = '\t'))
			#reader = loadCSV(self.histology_filename)
			reader = [(i[0].lower(), i[1]) for i in reader]
			reader = dict(reader)
		else:
			print("Failed to load the histology file.")
			print("Location: ", self.histology_filename)
			reader = dict()
			#raise Error
		return reader
	@staticmethod
	def loadLocalApiFiles():
		with open(local_file_api_filename, 'r') as file1:
			local_file_api = json.loads(file1.read())

		with open(local_case_api_filename, 'r') as file2:
			local_case_api = json.loads(file2.read())

		return local_file_api, local_case_api
	def request(self, uuid, endpoint):
		""" Sends a request to the GDC API.
			Parameters
			----------
				id: string [UUID]
					The UUID of a file, case, or project.
				endpoint: {'files', 'cases', 'projects'}
					Endpoint for the request.
			Returns
			-------
				response: dict<>
		"""
		uuid = uuid.lower().strip()
		if endpoint == 'files':
			response = self.file_endpoint(uuid)
		elif endpoint == 'cases':
			response = self.case_endpoint(uuid)
		else:
			response = self.project_endpoint(uuid)

		return response
		
	def file_endpoint(self, uuid, use_local = False):
		""" Requests information about a file from the GDC API
			Parameters
			----------
				file_id: string
					The uuid for the file
				legacy: bool; default False
					Whether to use to GDC legacy archive
				fields: list<string>
					A list of fields to request. Only pass top-level variables,
					all subvariables will be returned.
					Available top-level fields:
						associated_entities 4
						downstream_analyses 28
						metadata_files      16
						analysis            65
						annotations         17
						index_files         17
						archive             15
						center               6
						cases              300 (Currently not supported)
			Returns
			-------
				* 'access': string
				* 'acl':    list<string>
				* 'analysis': dict<>
				* 'associated_entities': list<dict>
				* 'basic_info': dict<>
					* 'aligned_reads': list<dict>
						* 'barcode': string [Sample Barcode]
						* 'category': string [Histology]
						* 'experimental_strategy': string
						* 'filename'
						* 'id'
						* 'md5'
						* 'patient': string [Patient Barcode]
						* 'size': int
						* 'state': string
						* 'tissue': string {'Primary Tumor', 'Solid Tissue Normal', 'Blood Derived Normal', 'Metastatic'}
					* 'barcode': string [the sample barcode]
					* 'capture kit catalog number': string
					* 'capture kit name': string
					* 'case_id': string [Case UUID]
					* 'exome targets link': string [""]
					* 'file_id': string [file UUID]
					* 'file_name': string
					* 'file_size': int
					* 'genome_build': string
					* 'reference_name': string
					* 'index_id': string
					* 'index_md5sum': string
					* 'patient_id': string [Patient Barcode]
					* 'sample_type': string {'Primary Tumor', 'Solid Tissue Normal', 'Blood Derived Normal', 'Metastatic'}
				* 'cases': list<dict>
				* 'created_datetime': string
				* 'data_category': string {'Raw Sequencing Data'}
				* 'data_format': string {'BAM'}
				* 'data_type': string   {'Aligned Reads'}
				* 'downstream_analyses': list<dict<>>
				* 'experimental_strategy': string ['WXS']
				* 'file_id': string
				* 'file_name': string
				* 'file_size': int
				* 'file_state': string
				* 'index_files': list<dict<>>
				* 'md5sum': string [UUID]
				* 'platform': string
				* 'state': string
				* 'submitter_id': string [UUID]
				* 'type': string ['aligned_reads']
				* 'updated_datetime': string
		"""

		all_expand_fields = ['analysis', 'analysis.metadata.read_groups', 'analysis.input_files', 
							 'annotations', 'archive', 'associated_entities', 'cases', 'cases.annotations',
							 'cases.demographic', 'cases.diagnoses', 'cases.family_histories', 'cases.project',
							 'cases.samples', 'cases.samples', 'downstream_analyses.output_files', 'center']
		parameters = {
			'expand': ','.join(all_expand_fields)
		}

		#----------------------- Send the request to the GDC Server --------------------------
		response = self._request(uuid, endpoint = 'files', parameters = parameters, use_local = use_local)
			
		
		#response = response['data']
		response['basic_info'] = self.file_basic_info(response)
		return response

	def file_basic_info(self, response):
		case = response.get('cases', [dict()])[0]
		
		if 'samples' in case.keys():
			sample = case['samples'][0]
		sample_type = sample.get('sample_type', "Unknown")
		sample_barcode = sample.get('submitter_id', "Unknown")

		try:
			read_groups = response['analysis']['metadata']['read_groups'][0]
		except:
			read_groups = {}

		try:
			index_file = response['index_files'][0]
		except:
			index_file = {}

		file_info = {
			#---------------- Basic file info ----------------
			'file_size': response['file_size'],
			'file_id': response['file_id'],
			'file_name': response['file_name'],
			#------------------- sample info -----------------
			'sample_barcode': sample_barcode,
			'sample_type': sample_type, #tissue type
			'genome_build': "GRCh38.p0",
			'genome_name': "GRCh38.d1.vd1",
			#---------------- Basic case info ----------------
			'case_id': case.get('case_id'),
			'histology': self.histology.get(case.get('case_id', "Unknown")),
			'patient_barcode': case.get('submitter_id'),
			#--------------- Probe Targets info --------------
			#'exome targets link': read_groups.get('target_capture_kit_target_region', None),
			'exome targets file': _get_exome_targets(read_groups.get('target_capture_kit_catalog_number', "")),
			#'capture kit catalog number': read_groups.get('target_capture_kit_catalog_number', ""),
			'capture kit name': read_groups.get('target_capture_kit_name', "").replace('\n', ''),
			#Index Files
			'index_id': index_file.get('file_id'),
			'index_name': index_file.get('file_name'),
			'index_md5sum': index_file.get('md5sum')
		}
		return file_info

	def case_endpoint(self, uuid, use_local = False):
		""" Retrieves information from the GDC API concerning a specific case
		Parameters
		----------
			case_id: string
				The uuid linked to the case
			fields: list<string>; default None
				Any fields to retrieve. Accepts upper-level arguments and
				finds all lower-level arguments automatically.
			expand: 'Full', list<string>; default 'Full'
				A list of sections to expand on. 'Full' retrieves expanded sections
				for all headers that are compatible with the service
		Returns
		----------
			case_info: dict<>
				The information for the case.
				Top-level keys:
				* case_info: Basic info concerning the case
				* 'aliquot_ids':           list<string>
				* 'analyte_ids':           list<string>
				* 'basic_info':            dict<>
					* 'aligned_reads': list<>
					* 'case_id': string
					* 'file_count': int
					* 'file_size':  int
					* 'histology':  string
				* 'case_id':               string
				* 'created_datetime':      string, None
				* 'demographic':           dict<>
					* 'created_datetime': None
					* 'demographic_id':   string
					* 'ethnicity':        string
					* 'gender':           string ['female', 'male']
					* 'race':             string
					* 'state':            None
					* 'submitter_id':     string
					* 'updated_datetime': string [ISO datetime]
					* 'year_of_birth':    int
					* 'year_of_death':    int, None
				* 'diagnoses':             list<dict<>>
				* 'exposures':             list<dict<>>
				* 'files':                 list<dict<>>
					* 'access': string ['open', 'controlled']
					* 'acl': list<string>
					* 'created_datetime':  string
					* 'data_category':     string
					* 'data_format':       string
					* 'data_type':         string
					* 'experimental_strategy': string
					* 'file_id': string
					* 'file_name': string
					* 'file_size': int
					* 'file_state': string
					* 'md5sum': string
					* 'platform': string
					* 'state': string
					* 'submitter_id': string
					* 'type': string
					* 'updated_datetime': string
				* 'portion_ids':           list<string>
				* 'sample_ids':            list<string>
				* 'samples':               list<dict<>>
					* 'composition':        None
					* 'created_datetime':   None
					* 'current_weight':     None
					* 'days_to_collection': None
					* 'freezing_method':    None
					* 'initial_weight':     None
					* 'intermediate_dimension': string
					* 'is_ffpe':            bool
					* 'longest_dimension':  string
					* 'oct_embedded':       None
					* 'pathology_report_uuid': string
					* 'preservation_method':None
					* 'sample_id':          string
					* 'sample_type':        string ['Primary Tumor']
					* 'sample_type_id':     string [INT]
					* 'shortest_dimension': string
					* 'submitter_id':       string [TCGA SAMPLE BARCODE]
				* 'slide_ids':             list<string>
				* 'state': None
				* 'submitter_aliquote_ids':list<string>
				* 'submitter_analyte_ids': list<string>
				* 'submitter_id': string
				* 'submitter_portion_ids': list<string>
				* 'submitter_sample_ids':  list<string>
				* 'submitter_slide_ids':   list<string>
				* 'summary': dict<>
					* 'file_count': int
					* 'file_size':  int [bytes]
				* 'updated_datetime': string [ISO Datetime]
		"""


		parameters = {
			'expand': ','.join(['samples', 'files', 'files.cases.samples','summary', 'exposures', 'diagnoses', 'demographic'])
		}
		#----------------------- Send the request to the GDC Server --------------------------
		response = self._request(uuid, endpoint = 'cases', parameters = parameters, use_local = use_local)

		cancer_type = self.histology.get(uuid, "UNKNOWN")
		samples = self._parse_case_samples(response)
		#response['files'] = bam_files
		#case_files = generate_manifest_file([response])
		#case_files = [file_api(i['sample_id']) for i in response['samples']]
		
		#samples = choose_samples(case_files, response)
		case_files = []
		#samples = []

		case_info = {
			'case_id': response['case_id'],
			'file_count': response['summary']['file_count'],
			'file_size': response['summary']['file_size'],
			'patient_barcode': response['submitter_id'],
			'samples': samples,
			'histology': cancer_type
		}
		response['basic_info'] = case_info
		return response

	def _parse_case_samples(self, case_data):
		files = case_data['files']
		#for f in files:
		#   print(f['data_category'], f.get('experimental_strategy'))
		bam_files = [i for i in files if (i.get('data_category') == 'Raw Sequencing Data' and i.get('experimental_strategy') in {"WXS", "WES", "WGS"})]

		samples = dict()
		for f in bam_files:
			f['basic_info'] = self.file_basic_info(f)
			#pprint(f['basic_info'])
			samples[f['basic_info']['sample_type']] = f
		if len(samples) == 0:
			print("The relevant samples were not found!")
			for f in files:
				print(f['data_category'], f.get('experimental_strategy'))

		return samples

	def project_endpoint(self, uuid):
		pass

	def _request(self, uuid, endpoint, parameters, use_local = False):
		if use_local:
			try:
				response = self._offlineRequest(uuid, endpoint)
			except:
				response = self._onlineRequest(uuid, endpoint, parameters)
		else:
			try:
				response = self._onlineRequest(uuid, endpoint, parameters)
			except:
				response = self._offlineRequest(uuid, endpoint)

		return response
	

	def _onlineRequest(self, uuid, endpoint, parameters):
		url = 'https://gdc-api.nci.nih.gov/{endpoint}/{uuid}'.format(
			endpoint = endpoint,
			uuid = uuid)
		response = requests.get(url, parameters)
		if response.status_code != 200:
			self._raise_invalid_response_error(uuid, endpoint, response)
			raise ValueError()
		response = response.json()
		#pprint(response)
		if 'data' in response:
			response = response['data']
		return response

	def _offlineRequest(self, uuid, endpoint):
		if endpoint == 'files':
			response = self.local_file_api[uuid]
		else:
			response = self.local_case_api[uuid]

		return response
	@staticmethod
	def _raise_invalid_response_error(uuid, endpoint, response):
		print("ERROR: The api returned an invalid response!")
		print("\tEndpoint: ", endpoint)
		print("\tUUID: ", uuid)
		print("\tStatus Code: ", response.status_code)
		pprint(response.json())
	##################### API USE CASE METHODS ##########################



	def generate_sample_list(self, case_ids, filename = None):
		""" Generates a sample list from the passed ids
			Parameters
			----------
				ids: string
					Either case ids for patient barcodes.
		"""

		if 'TCGA' in case_ids[0]:
			case_ids = self.BarcodeToUuid(case_ids)

		sample_list = list()
		for index, case_id in enumerate(case_ids):
			print("{0} of {1}: {2}".format(index+1, len(case_ids), case_id))
			case_data = self(case_id, 'cases')
			samples = case_data['basic_info']['samples']

			if 'Blood Derived Normal' in samples.keys():
				normal_type = 'Blood Derived Normal'
			else:
				normal_type = 'Solid Tissue Normal'

			try:
				tumor = samples['Primary Tumor']['basic_info']
				tumor_location = self.get_file_location(tumor['file_id'])
			except:
				tumor = dict()
				tumor_location = ""
			try:
				normal = samples[normal_type]['basic_info']
				normal_location = self.get_file_location(normal['file_id'])
				normal_type = normal['sample_type']
			except:
				normal = dict()
				normal_location = ""
				normal_type = ""

			ref_id = "c2526f96-6d13-480c-9609-7d50a2bd29c8"
			if tumor.get('file_id') == ref_id and False:
				pprint(tumor)
				print("Location: ", tumor_location)
				raise Error
			
			#exome_targets = "/home/upmc/Documents/Reference/Capture_Targets/"
			capture_targets_folder = "/home/upmc/Documents/Reference/Capture_Targets/"
			if case_data['basic_info']['histology'] in {"Esophagus Adenocarcinoma, NOS", "Esophagus Squamous Cell Carcinoma"}:
				exome_targets = os.path.join(capture_targets_folder, "SeqCap_EZ_Exome_v3_GRCh38_UCSCBrowser_capture_targets.bed")
			else:
				exome_targets = os.path.join(capture_targets_folder, "whole_exome_agilent_1.1_refseq_plus_3_boosters.targetIntervals.hg38.list")
			sample = {
				'CaseID':  case_data['case_id'],
				'SampleID':  tumor.get('sample_barcode'),
				'SampleUUID':tumor.get('file_id'),
				'NormalID':  normal.get('sample_barcode'),
				'NormalUUID':normal.get('file_id'),
				'PatientID': case_data['submitter_id'],
				'TumorBAM':  tumor_location,
				'NormalBAM': normal_location,
				'NormalType': normal_type,
				'ExomeTargets': exome_targets,
				#'Genome Type': T['experimental_strategy'],
				'Histology': case_data['basic_info']['histology']
			}
			sample_list.append(sample)
		sample_list = sorted(sample_list, key = lambda s: s['PatientID'])
		truncated_sample_list = [i for i in sample_list if (i['NormalBAM'] != "" and i['TumorBAM'] != "")]

		if filename is not None:
			with open(filename, 'w', newline = "") as file1:
				writer = csv.DictWriter(file1, delimiter = "\t", fieldnames = sorted(sample_list[0].keys()))
				writer.writeheader()
				writer.writerows(sample_list)
			truncated_filename = os.path.splitext(filename)[0] + '.truncated.tsv'
			with open(truncated_filename, 'w', newline = "") as file2:
				writer = csv.DictWriter(file2, delimiter = "\t", fieldnames = sorted(truncated_sample_list[0].keys()))
				writer.writeheader()
				writer.writerows(truncated_sample_list)
		return sample_list

	def generate_manifest_file(self, ids, endpoint, filename = None, debug = False):
		""" Generates a manifest file for all genome files attached to the provided case_ids.
			Parameters
			----------
				ids: list<string>
					A list of either case_ids.
				endpoint: {'cases', 'files'}
			Returns
			-------
				manifest: list<dict>
					A list of the relevant fields used to generate a manifest file.
					* 'id':         string
					* 'filename':   string
					* 'md5':        string
					* 'size':       int
					* 'state':      string
					* 'patient':    string
					* 'category':   string
					* 'tissue':     string
					* 'barcode':    string
		"""
		manifest = list()
		if endpoint == 'cases':
			print("Parsing cases...")
			files = list()
			for case_id in ids:
				case_info = self(case_id, 'cases')
				case_files = list(case_info['basic_info']['samples'].values())
				files += case_files

		elif endpoint == 'files':
			print("Parsing files")
			files = [self(i, 'files') for i in ids]
		else:
			print("Either file ids or case ids are required to generate a manifest file!")
			
		for index, read in enumerate(files):
			print("{0} of {1}".format(index+1, len(files)))
			basic_info = read['basic_info']
			fields = {
				'id': basic_info['file_id'],
				'filename': basic_info['file_name'],
				'md5': read['md5sum'],
				'size': read['file_size'],
				'state': read['file_state'],
				'patient': basic_info['patient_barcode'],
				'histology': basic_info.get('histology'),
				'sample_type': basic_info['sample_type'],
				'barcode': basic_info['sample_barcode'],
			}
			manifest.append(fields)

		if filename is not None:
			with open(filename, 'w', newline = "") as file1:
				fieldnames = ["id", "filename", "md5",  "size", "state"]
				_excluded = set(manifest[0].keys()) - set(fieldnames)
				fieldnames += sorted(_excluded)
				writer = csv.DictWriter(file1, delimiter = '\t', fieldnames = fieldnames)
				writer.writeheader()
				writer.writerows(manifest)
		return manifest

	def generate_local_api(self, case_ids):
		""" Saves/updates a local version of the api."""
		local_case_api = dict()
		local_file_api = dict()
		file_ids = list()
		for index, case_id in enumerate(case_ids):
			print("Case {0} of {1}".format(index+1, len(case_ids)))
			case_data = self(case_id, "cases")

			local_case_api[case_id] = case_data
			#pprint(case_data['files'])
			file_ids += [i['file_id'] for i in case_data['files'] if i['data_category'] == 'Raw Sequencing Data']

		for index, file_id in enumerate(file_ids):
			print("File {0} of {1}".format(index+1, len(file_ids)))
			file_data = self(file_id, "files")
			local_file_api[file_id] = file_data

		local_case_api_filename = os.path.join(os.getcwd(), "local_case_api.json")
		local_file_api_filename = os.path.join(os.getcwd(), "local_file_api.json")
		
		with open(local_case_api_filename, 'w') as file1:
			file1.write(json.dumps(local_case_api, sort_keys = True, indent = 4))
		with open(local_file_api_filename, 'w') as file1:
			file1.write(json.dumps(local_file_api, sort_keys = True, indent = 4))

############################ Compatability Methods ########################################
_api = GDCAPI()
"""
def file_api(file_id):
	response = _api(file_id, "files")
	return response

def case_api (case_id):
	response = _api(case_id, "files")
"""


#Updated Version
isMain = __name__ == "__main__"
if isMain:
	if False:
		case_id  = "6969fe5a-5993-48e5-95c5-c5c7d3d08205"
		#file_id  = "2d4f1ce4-4613-403a-90ec-fd6a551b6487"
		file_id  = "9e692097-1f84-4a25-ad73-50a5522db60e"
		index_id = "4570dd4d-9234-4d37-b8d0-66d37594e3f1"
		stomach_case_id = "00781a96-4068-427c-a9c5-584d167c3dea"

		api = GDCAPI()
		response = api(file_id, 'files')
		pprint(response)
		#pprint(case_api(case_id))
		#pprint(case_api(case_id))




