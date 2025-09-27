import time, hashlib, json

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_votes = []
        self.create_block(previous_hash="1")  # Genesis block

    def create_block(self, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'votes': self.current_votes,
            'previous_hash': previous_hash,
            'hash': ''
        }
        block['hash'] = self.hash(block)
        self.current_votes = []
        self.chain.append(block)
        return block

    def add_vote(self, voter_id, candidate):
        # Prevent double voting
        for block in self.chain:
            for vote in block['votes']:
                if vote['voter_id'] == voter_id:
                    return False
        for vote in self.current_votes:
            if vote['voter_id'] == voter_id:
                return False

        self.current_votes.append({
            'voter_id': voter_id,
            'candidate': candidate
        })
        return True

    def mine_block(self):
        if not self.current_votes:
            return None
        return self.create_block(self.chain[-1]['hash'])

    def hash(self, block):
        block_copy = block.copy()
        block_copy['hash'] = ''
        return hashlib.sha256(json.dumps(block_copy, sort_keys=True).encode()).hexdigest()

    def get_tally(self):
        tally = {}
        for block in self.chain:
            for vote in block['votes']:
                tally[vote['candidate']] = tally.get(vote['candidate'], 0) + 1
        return tally
