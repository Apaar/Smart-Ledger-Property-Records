import types
import hashlib

class ProofOfWork:
	def __init__(self, func=None):
		if func is not None:
			self.execute = types.MethodType(func, self)

	def execute(self):
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

def execute_alternate1(self):
	print('Alternate Proof of Work 1')
	nonce = None
	incrementor = 0
	NUM_ZEROES = 5
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

