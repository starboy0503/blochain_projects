import sys, os
sys.path.append(os.path.dirname(__file__))

from web3 import Web3
from config import WEB3_PROVIDER

# Connect to blockchain node
w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))

def get_latest_block_number():
    """Return the latest block number on chain"""
    return w3.eth.block_number

def get_block(block_number, full_transactions=False):
    """Fetch block data from blockchain"""
    return w3.eth.get_block(block_number, full_transactions=full_transactions)
