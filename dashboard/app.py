import streamlit as st
import sqlite3
import pandas as pd

conn = sqlite3.connect("grants.db")
df = pd.read_sql_query("SELECT title, score, ai_reason, first_seen, link FROM seen_grants ORDER BY first_seen DESC", conn)
st.title("🧬 Grant AI Monitor")
st.dataframe(df)
st.bar_chart(df["score"])
