from flask import Flask
from flask import request
import datetime
import requests
import hashlib
from requests.exceptions import ConnectionError
import json
from block import Block

# --------------------------------------------------------
#  node-specific initialization parameters
this_nodes_transactions = []
PORT = 8080
peer_nodes = [
    "http://localhost:8060"
    , "http://localhost:8070"
    # , "http://localhost:8090"
    ]
miner_address = 'http://localhost:' + str(PORT)

# --------------------------------------------------------
# "private" functions
# TODO: break out into another .py for legibility

def _proof_of_work(previous_hash):
    """
    Uses `previous_hash` to solve for a `nonce`, where the resulting
        hash starts with a number of zero bits ( NUM_ZEROES ).

    Returns
        nonce : int
    """
    nonce = None
    incrementor = 0
    NUM_ZEROES = 5

    # increment nonce until solution is found
    while not nonce:
        sha = hashlib.sha256()
        sha.update(
            str(previous_hash).encode('utf-8') +
            str(incrementor).encode('utf-8')
            )
        challenge_hash = sha.hexdigest()
        if str(challenge_hash[:NUM_ZEROES]) == '0' * NUM_ZEROES:
            nonce = incrementor
        else:
            incrementor += 1
    return nonce

def _find_new_chains():
    """Finds other chains, using `peer_nodes`.

    Returns
        other_chains : list of blockchains to be checked for validity

    Except
        ConnectionError : on request failure
    """
    # retrieve other nodes' blockchains
    other_chains = []
    for node_url in peer_nodes:
        try:
            block = requests.get(node_url + "/blocks").content
            block = json.loads(block)
            other_chains.append(block)
        except ConnectionError:
            pass
    return other_chains

def _consensus():
    """Called on server start. Looks for alternative blockchains.

    Returns
        chain_to_return : list, determined to be strongest valid blockchain
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

# --------------------------------------------------------
# REST API
node = Flask(__name__)

@node.route('/transaction', methods=['POST'])
def transaction():
    """Posts transactions to the blockchain

    json : {"to":"some_address","from":"my_address","amount":3}
    """
    # TODO: verify tx and broadcast to other nodes
    if request.method == 'POST':
        new_transaction = request.get_json()
        this_nodes_transactions.append(new_transaction)
        print("FROM: {}".format(new_transaction['from'].encode('ascii',
                                                                'replace')))
        print("TO: {}".format(new_transaction['to'].encode('ascii','replace')))
        print("AMOUNT: {}\n".format(new_transaction['amount']))
        return '~ transaction successful ~'

@node.route('/mine', methods=['GET'])
def mine():
    """Performs work. Becomes swoll. Miner gets rewarded.

    Raises
        ValueError : when `mine()` is called on an empty `blockchain`
    """
    MINER_REWARD = 1
    global this_nodes_transactions

    # verifies non-empty blockchain
    if not blockchain:
        msg = "Empty blockchain."
        raise ValueError(msg)
    # if not this_nodes_transactions:
    #     msg = "Empty transaction list."
    #     raise ValueError(msg)

    last_block = blockchain[len(blockchain) - 1]
    # perform proof of work function
    _previous_hash = last_block['hash']
    _nonce = _proof_of_work(_previous_hash)
    # reward miner
    this_nodes_transactions.append( {'from':'network', 'to':miner_address,
        'amount':MINER_REWARD} )
    # generate new block's data, empty local transaction list
    _data = {'transactions':this_nodes_transactions}
    _index = int(last_block['index']) + 1
    _timestamp = str(datetime.datetime.now())
    mined_block = Block(index=_index, timestamp=_timestamp, data=_data,
        previous_hash=_previous_hash, nonce=_nonce)
    this_nodes_transactions = []

    mined_block_data = {'index':mined_block.index,
        'timestamp':mined_block.timestamp,
        'data':mined_block.data,
        'nonce':mined_block.nonce,
        'previous_hash':mined_block.previous_hash,
        'hash':mined_block.hash}
    blockchain.append(mined_block_data)

    # inform client of mining's completion
    mined = json.dumps(mined_block_data)
    print(mined+'\n')
    return mined

@node.route('/blocks', methods=['GET'])
def get_blocks():
    blocks = json.dumps(blockchain)
    print(blocks+'\n')
    return blocks

# --------------------------------------------------------
# server initialization details
blockchain = _consensus()
# create first block if no other blockchain is available
if not blockchain:
    def create_initial_block():
        b = Block(index=0, timestamp=str(datetime.datetime.now()),
            data='initial block',
            previous_hash='0', nonce=1)

        return {'index':b.index,
            'timestamp':b.timestamp,
            'data':b.data,
            'nonce':b.nonce,
            'previous_hash':b.previous_hash,
            'hash':b.hash}

    blockchain = [create_initial_block()]
# run node
node.run(host='0.0.0.0', port=PORT, threaded=True, debug=False)
