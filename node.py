from flask import Flask, Response
from flask import request
import requests
import json
import datetime
import hashlib
from requests.exceptions import ConnectionError
from block import Block
import sys
import atexit
import property
import pow


def _to_url(pair):
	'''
	Utility function to convert a tuple of
	(ip, port) to http://ip:port

	Returns:
		str of the form http://ip:port
	'''
	return 'http://{}:{}'.format(pair[0], pair[1])


# No port provided, show error message and quit
if len(sys.argv) != 2:
	print("Usage:")
	print("python {} <port>".format(sys.argv[0]))
	print("Example:\npython {} 8080".format(sys.argv[0]))
	sys.exit(0)

this_pair = ("localhost", int(sys.argv[1]))

# Node-specific initialization parameters
this_nodes_transactions = []
peer_nodes = list()
if this_pair[1] != 8080:
	peer_nodes.append(('localhost', 8080))
miner_address = _to_url(this_pair)


def _proof_of_work(previous_hash):
	strategy = ProofOfWork()
	# strategy = ProofOfWork(execute_alternate1)
	return strategy.execute()
	


def _find_new_chains():
	"""
	Finds other chains, using `peer_nodes`.

	Returns
		other_chains : list of blockchains to be checked for validity

	Except
		ConnectionError : on request failure
	"""
	other_chains = []
	for node in peer_nodes:
		try:
			block = requests.get(_to_url(node) + "/blocks").json()
			other_chains.append(block)
		except ConnectionError:
			print("Connection to {} failed, skipping..".format(_to_url(node)))
	return other_chains


def _consensus():
	"""
	Called on server start. Looks for alternative blockchains.

	Returns
		chain_to_return : list, determined to be a valid blockchain
		with highest PoW
	"""
	other_chains = _find_new_chains()
	# initialize an empty chain, in case consensus criteria is not met
	chain_to_return = []
	if other_chains:
		for chain in other_chains:
			if len(chain_to_return) < len(chain):
				chain_to_return = chain
	# longest chain wins!
	return chain_to_return


'''
ReST Functionality
'''

node = Flask(__name__)


@node.route('/update/peer', methods=['POST'])
def notice_peer():
	'''
	Update peer nodes list; Passive
	'''
	_data = request.get_json()
	peer_nodes.append((_data['ip'], _data['port']))
	return Response(
		status=200
	)


@node.route('/broadcast/peer', methods=['POST'])
def push_peer():
	'''
	Updates peer nodes list; Active
	Forces other nodes to update passively
	Input:
		{'ip': <ip>, 'port': <port>}

	Returns:
		Response 200
	'''
	_data = request.get_json()
	_ip = _data['ip']
	_port = _data['port']
	for peer in peer_nodes:
		requests.post(
			_to_url(peer) + '/update/peer',
			data={'ip': _ip, 'port': _port}
		)
	peer_nodes.append((_ip, _port))
	return Response(
		status=200
	)


@node.route('/push/block', methods=['GET'])
def mine_notification():
	'''
	Block was mined; Update chain
	'''
	global blockchain
	blockchain = _consensus()
	return Response(status=200)


def broadcast_mine():
	'''
	Notifies other peers about a successful block mine
	'''
	for peer in peer_nodes:
		print("Broadcasting to {} peers".format(len(peer_nodes)))
		requests.get(_to_url(peer) + '/push/block')


def verify_key(txn, check):
	'''
	Verify transaction against accepted keys.
	Input:
		transaction JSON
		Verified Key JSON
	Output:
		Boolean value denoting successful verification
	'''
	# print("verify_key called with ", txn, "Check", check)
	verifystatus = False
	checkvalue = check.pop('checkvalue')
	# print("dict items: ", check.items())
	for key, values in check.items():
		if txn.__contains__(key):
			verifystatus = True
			if checkvalue and not (txn[key] in values):
				verifystatus = False
	return verifystatus


def _txn(new_transaction):
	'''
	Verify if required keys are present
	Skip any extra data
	'''
	trusted_keys = [
		{
			'type': [
				'list',
				'buy',
				'sell'
			],
			'checkvalue': True
		},
		{
			'from': [],
			'to': [],
			'checkvalue': False
		},
		{
			'input': [],
			'output': [],
			'checkvalue': False
		}
	]
	for check in trusted_keys:
			if not verify_key(new_transaction, check):
				return Response(
					status=400
				)
	this_nodes_transactions.append(new_transaction)
	return Response(
		status=200
	)


@node.route('/transaction', methods=['POST'])
def transaction():
	"""
	Posts transactions to the pending list.
	"""
	new_transaction = request.get_json()
	# print("transaction//INPUT///", new_transaction)
	return _txn(new_transaction)


@node.route('/mine', methods=['GET'])
def mine():

	global this_nodes_transactions

	# verifies non-empty blockchain
	if not blockchain:
		return Response(
			'{"message": "Chain does not exist."}',
			status=500,
			mimetype='application/json'
		)
	if not this_nodes_transactions:
		return Response(
			'{"message": "No transactions to mine."}',
			status=503,
			mimetype='application/json'
		)

	last_block = blockchain[len(blockchain) - 1]
	# perform proof of work function
	_previous_hash = last_block['hash']
	_nonce = _proof_of_work(_previous_hash)
	# generate new block's data, empty local transaction list
	_data = {'transactions': list(this_nodes_transactions)}
	_index = int(last_block['index']) + 1
	_timestamp = str(datetime.datetime.now())
	mined_block = Block(
		index=_index, timestamp=_timestamp, data=_data,
		previous_hash=_previous_hash, nonce=_nonce)
	this_nodes_transactions = list()

	mined_block_data = {
		'index': mined_block.index,
		'timestamp': mined_block.timestamp,
		'data': mined_block.data,
		'nonce': mined_block.nonce,
		'previous_hash': mined_block.previous_hash,
		'hash': mined_block.hash}
	blockchain.append(mined_block_data)
	broadcast_mine()
	# inform client of mining's completion
	return Response(json.dumps(mined_block_data), status=200, mimetype='application/json')


@node.route('/unspent', methods=['GET'])
def list_unspent():
	'''
	Get unspent transactions from blockchain
	'''
	return property._get_owner_list()


@node.route('/blocks', methods=['GET'])
def get_blocks():
	blocks = json.dumps(blockchain)
	return blocks


# <todoh>


@node.route('/list', methods=['POST'])
def list_property():
	txndata = request.get_json()
	# print("INPUT// ", txndata)
	if not property.owns(txndata['to'], txndata['pid']):
		return Response(
			'{"message": "Property owned by someone else."}',
			status=403,
			mimetype='application/json'
		)
	ownerlist = property._get_owner_list()
	if txndata['pid'] in ownerlist.keys():
		# Item already listed
		return Response(
			'{"message": "Property already listed."}',
			status=400,
			mimetype='application/json'
		)

	txnreq = _txn(
		{
			'type': 'list',
			'from': 'network',
			'to': txndata['to'],
			'input': list(),
			'output': [{
				'pid': txndata['pid'],
			}]
		}
	)
	if txnreq.status_code == 200:
		property.add_prop(txndata['pid'], txndata['pname'])
		property.add_owner(txndata['to'], txndata['pid'])
		return Response(
			status=200
		)
	return Response(
		'{"message": "Unable to complete txn."}',
		status=500,
		mimetype='application/json'
	)


@node.route('/buy', methods=['POST'])
def buy_property():
	txndata = request.get_json()
	if not property.owns(txndata['from'], txndata['pid']):
		return Response(
			'{"message": "Seller does not own the property"}',
			status=400,
			mimetype='application/json'
		)
	txnreq = _txn(
		{
			'type': 'buy',
			'from': txndata['from'],
			'to': txndata['to'],
			'input': [{
				'pid': txndata['pid'],
			}],
			'output': list()
		}
	)
	if txnreq.status_code == 200:
		property.add_owner(txndata['to'], txndata['pid'])
		return Response(
			status=200
		)
	return Response(
		'{"message": "Unable to complete txn."}',
		status=500,
		mimetype='application/json'
	)


@node.route('/sell', methods=['POST'])
def sell_property():
	txndata = request.get_json()
	if not property.owns(txndata['from'], txndata['pid']):
		return Response(
			'{"message": "Seller does not own the property"}',
			status=400,
			mimetype='application/json'
		)
	txnreq = _txn(
		{
			'type': 'sell',
			'from': txndata['from'],
			'to': txndata['to'],
			'input': list(),
			'output': [{
				'pid': txndata['pid'],
			}]
		}
	)
	if txnreq.status_code == 200:
		property.add_owner(txndata['to'], txndata['pid'])
		return str({
			"status": "ok",
			"response": 200
		})
	return Response(
		'{"message": "Unable to complete txn."}',
		status=500,
		mimetype='application/json'
	)


# </todoh>


blockchain = list()
if len(peer_nodes) == 0:
	blockchain = property.load_map('blockchain')
else:
	blockchain = _consensus()
# create first block if no other blockchain is available
if not blockchain:
	def create_initial_block():
		b = Block(
			index=0, timestamp=str(datetime.datetime.now()),
			data='initial block',
			previous_hash='0', nonce=1)

		return {
			'index': b.index,
			'timestamp': b.timestamp,
			'data': b.data,
			'nonce': b.nonce,
			'previous_hash': b.previous_hash,
			'hash': b.hash}

	blockchain = [create_initial_block()]
atexit.register(property.save_map, 'blockchain', blockchain)
atexit.register(property.save_prop_state)

# run node
node.run(host=this_pair[0], port=this_pair[1], threaded=True, debug=False)
