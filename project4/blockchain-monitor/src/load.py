import sys, os
sys.path.append(os.path.dirname(__file__))
import sqlite3
import pandas as pd
from config import DB_PATH


def load_block(block_dict):
    conn=sqlite3.connect(DB_PATH)
    df=pd.DataFrame([block_dict])
    df.to_sql("blocks",conn,if_exists="append",index=False)
    conn.close()

def load_transactions(tx_rows):
    if not tx_rows:
        return
    conn=sqlite3.connect(DB_PATH)
    df=pd.DataFrame(tx_rows)
    df.to_sql("transactions",conn,if_exists="append",index=False)
    conn.close()