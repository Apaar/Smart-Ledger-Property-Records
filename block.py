import hashlib


class Block:
	"""Simple block object. In this example, each block contains
		transactional data.
	"""
	def __init__(self, index, timestamp, data, previous_hash, nonce):
		self.index = index
		self.timestamp = timestamp
		self.data = data
		self.previous_hash = previous_hash
		self.nonce = nonce
		self.hash = self.hash_block()

	def hash_block(self):
		# hashes this block's data
		sha = hashlib.sha256()
		sha.update(
			str(self.index).encode('utf-8') +
			str(self.timestamp).encode('utf-8') +
			str(self.data).encode('utf-8') +
			str(self.previous_hash).encode('utf-8') +
			str(self.nonce).encode('utf-8')
		)
		return sha.hexdigest()
