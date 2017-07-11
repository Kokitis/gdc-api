import json
from collections import defaultdict
from pprint import pprint
import os
import requests

class BaseApi:
	def __init__(self):
		self._null_result = None
		self._empty_resut = "unknown" # default value when the value doesn't have a value
		self._defineLocalAttributes()
		self.local_api = self._loadLocalApiFiles()

	def __call__(self, uuid):
		uuid = uuid.lower()
		response = self.apiRequest(uuid)

		return response

	def _loadLocalApiFiles(self):
		if os.path.exists(self.local_api_filename):
			with open(self.local_api_filename, 'r') as api_file:
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

		return response

	def processApiResponse(self, raw_response):
		raise NotImplementedError()

