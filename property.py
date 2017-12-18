'''
Property Mapping Service
	Maps property ID with Owner Name
'''
import requests
import os
import json
import hashlib

_owner_map = dict()
_prop_map = dict()


def get_blocks():
	'''
	Wrapper to return current blockchain
	'''
	return requests.get("http://0.0.0.0:8080/blocks").json()


def load_map(filename, folder='data'):
	'''
	Loads a mapping file if there exists one;
	Returns an empty dictionary otherwise.
	'''
	filepath = os.path.join(folder, filename + '.json')
	mapping = dict()
	if os.path.exists(filepath):
		with open(filepath) as mapfile:
			mapping = json.load(mapfile)

	return mapping


def save_prop_state():
	if not os.path.exists('data'):
		os.mkdir('data')
	save_map('own_map', _owner_map)
	save_map('prop_map', _prop_map)


def save_map(filename, mapping, folder='data'):
	'''
	Saves mapping information to persistent storage
	'''
	filepath = os.path.join(folder, filename + '.json')
	with open(filepath, 'w') as mapfile:
		json.dump(mapping, mapfile, indent='\t')


def add_owner(owner, pid):
	_owner_map[pid] = owner


def add_prop(pid, pname):
	_prop_map[pid] = pname


def get_pid(pname):
	return hashlib.sha256(pname.encode('utf-8')).hexdigest()


def _get_owner_list():
	blockchain = get_blocks()
	properties = dict()

	for block in blockchain[1:]:
		block = block['data']['transactions']

		for transaction in block:
			if transaction['type'] in ['list', 'sell']:
				txnoutlist = transaction['output'][0]

				if not properties.__contains__(txnoutlist['pid']):
					properties[txnoutlist['pid']] = list()

				properties[txnoutlist['pid']].append(transaction['to'])

			elif transaction['type'] == 'buy':
				txninlist = transaction['input'][0]

				if not properties.__contains__(txninlist['pid']):
					properties[txninlist['pid']] = list()

				properties[txninlist['pid']].append(transaction['to'])

	return properties


def get_full_title_map():
	return _prop_map


def get_owner_map():
	return _owner_map


def owns(ownerid, propid):
	'''
	Returns boolean value denoting
	whether propid is owned by ownerid
	'''
	global _owner_map
	try:
		return _owner_map[propid] == ownerid
	except KeyError:
		return True


_owner_map = load_map('own_map')
_prop_map = load_map('prop_map')
