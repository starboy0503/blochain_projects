import sys, os
sys.path.append(os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import sqlite3
from config import DB_PATH

def load_data(n=20):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM blocks ORDER BY block_number DESC LIMIT ?"
    df = pd.read_sql(query, conn, params=(n,))
    conn.close()
    return df

def load_top_senders():
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT "from_address", COUNT(*) as cnt
    FROM transactions
    GROUP BY "from_address"
    ORDER BY cnt DESC
    LIMIT 10
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

st.title("🔗 Blockchain Realtime Dashboard")

blocks = load_data()
if blocks.empty:
    st.warning("⚠️ No block data yet. Run ETL first.")
else:
    st.write("## Latest Blocks", blocks)

    st.metric("Latest Block", int(blocks.iloc[0]['block_number']))
    st.metric("Avg TXs/Block", round(blocks['tx_count'].mean(), 2))

    st.line_chart(blocks.set_index('block_number')['tx_count'])

    senders = load_top_senders()
    st.write("### Top Senders")
    st.bar_chart(senders.set_index("from_address")['cnt'])
