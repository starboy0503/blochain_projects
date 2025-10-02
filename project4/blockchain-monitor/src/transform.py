import sys, os
sys.path.append(os.path.dirname(__file__))
from datetime import datetime

def transform_block_data(block):
    return{
        "block_number": block.number,
        "block_hash": block.hash.hex(),
        "parent_hash": block.parentHash.hex(),
        "timestamp": datetime.utcfromtimestamp(block.timestamp),
        "tx_count":len(block.transactions),
        "gas_used": block.gasUsed,
        "gas_limit": block.gasLimit,
        "base_fee":getattr(block,"baseFeePerGas",None)
    }

def transform_transaction(block):
    rows=[]
    for tx in block.transactions:
        rows.append({
            "tx_hash": tx.hash.hex(),
            "block_number": block.number,
            "from_address": tx['from'],
            "to_address": tx['to'],
            "value": tx.value,
            "gas": tx.gas,
            "gas_price": tx.gasPrice,
            "nonce": tx.nonce,
            "tx_index": tx.transactionIndex
        })
        return rows