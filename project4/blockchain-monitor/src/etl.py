import sys, os
sys.path.append(os.path.dirname(__file__))
import time
import logging
from extract import get_latest_block_number, get_block
from transform import transform_block_data as transform_block
from transform import transform_transaction as transform_transactions
from load import load_block, load_transactions
from config import POLL_INTERVAL_SECONDS

logging.basicConfig(level=logging.INFO)
last_seen=None


def run():
    global last_seen
    while True:
        try:
            latest = get_latest_block_number()
            if last_seen is None:
                start = max(0, latest - 5)
            else:
                start = last_seen + 1

            for bn in range(start, latest + 1):
                block = get_block(bn, full_transactions=True)
                block_data = transform_block(block)
                txs = transform_transactions(block)
                load_block(block_data)
                load_transactions(txs)
                logging.info(f"Ingested block {bn} with {len(txs)} txs")
                last_seen = bn

        except Exception as e:
            logging.exception("ETL error: %s", e)
        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    run()