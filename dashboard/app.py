import streamlit as st
import sqlite3
import pandas as pd

conn = sqlite3.connect("grants.db")

df = pd.read_sql("SELECT * FROM grants", conn)

st.title("🧬 Grant AI Monitor")

st.dataframe(df)

st.bar_chart(df["score"])
