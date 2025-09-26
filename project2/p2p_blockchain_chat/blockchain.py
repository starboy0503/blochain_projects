import json,time,hashlib
from typing import List,Dict

MINING_DIFFICULTY=3

class Block:
    def __init__(self,index,timestamp,transactions:List[Dict],prev_hash,nonce=0):
        self.index=index
        self.timestamp=timestamp
        self.transactions=transactions
        self.prev_hash=prev_hash
        self.nonce=nonce
        self.hash=self.compute_hash()
    
    def compute_hash(self):
        block_string=json.dumps({
            'index':self.index,
            'timestamp':self.timestamp,
            'transaction':self.transactions,
            'prev_hash':self.prev_hash,
            'nonce':self.nonce
        },sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self):
        return{
            'index':self.index,
            'timestamp':self.timestamp,
            'transaction':self.transactions,
            'prev_hash':self.prev_hash,
            'nonce':self.nonce,
            'hash':self.hash
        }
    
class Blockchain:
        def __init__(self):
            self.chain:List[Block]=[]
            self.pending_transactions:List[Dict]=[]
            self.create_genesis()
        
        def create_genesis(self):
            genesis=Block(0,time.time(),[],"0",0)
            genesis.hash=genesis.compute_hash()
            self.chain.append(genesis)
        
        def last_block(self):
            return self.chain[-1]
        
        def add_transaction(self,tx:Dict):
            self.pending_transactions.append(tx)

        def proof_of_work(self,block: Block):
            target='0'*MINING_DIFFICULTY
            while not block.compute_hash().startswith(target):
                block.nonce+=1
            block.hash=block.compute_hash()
            return block.hash
        
        def mine(self):
            if not self.pending_transactions:
                return None
            new_block=Block(self.last_block().index+1, time.time(),
                            self.pending_transactions.copy(),self.last_block().hash,0)
            self.proof_of_work(new_block)
            self.chain.append(new_block)
            self.pending_transactions=[]
            return new_block.to_dict()
        
        def is_valid_chain(self,chain_data:List[Dict])->bool:
            prev=None
            for idx,blk in enumerate(chain_data):
                b_hash=blk['hash']

                recomputed=hashlib.sha256(json.dumps({
                    'index':blk['index'],
                    'timestamp':blk['timestamp'],
                    'transactions':blk['transactions'],
                    'prev_hash':blk['prev_hash'],
                    'nonce':blk['nonce']
                },sort_keys=True).encode()).hexdigest()
                if recomputed!=b_hash:
                    return False
                if idx>0:
                    if blk['prev_hash']!=chain_data[idx-1]['hash']:
                        return False
                    if not b_hash.startswith('0'*MINING_DIFFICULTY):
                        return False
            return True
        
        def replace_chain(self,new_chain:List[Dict]):
            if len(new_chain)>len(self.chain) and self.is_valid_chain(new_chain):
                self.chain=[Block(b['index'],b['timestamp'], b['transactions'], b['prev_hash'], b['nonce']) for b in new_chain]
                for i , b in enumerate(self.chain):
                    b.hash=new_chain[i]['hash']
                return True
            return False
        