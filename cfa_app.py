import streamlit as st
import json
import random
import os
import sqlite3
import pandas as pd

st.set_page_config(page_title="CFA Practice App", layout="wide")
st.title("📊 CFA Practice App 2.0")

# Load Questions JSON
def load_questions():
    with open("questions.json", "r") as f:
        data = json.load(f)
    return data["questions"]

questions = load_questions()
topics = sorted(set(q["topic"] for q in questions))
difficulties = sorted(set(q["difficulty"] for q in questions))

# SQLite DB setup
def init_db():
    conn = sqlite3.connect("results.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS results (
                username TEXT, 
                question_id TEXT, 
                correct INTEGER, 
                flagged INTEGER DEFAULT 0
                )''')
    conn.commit()
    return conn

db_conn = init_db()

# Sidebar login
username = st.sidebar.text_input("Enter your name", help="To begin practicing, type your name and hit Enter.")
if not username:
    st.info("To begin practicing, type your name and hit Enter.")
    st.stop()

if "started" not in st.session_state:
    if st.sidebar.button("\U0001F680 Start App"):
        st.session_state.started = True
    else:
        st.markdown("### Welcome to CFA Practice App 2.0!")
        st.markdown("To begin, enter your name in the sidebar and click 'Start App'.")
        st.stop()

st.success(f"Welcome, {username}! \U0001F389")
st.markdown("To begin, choose **Practice** or **Mock Exam** from the menu on the left. You can track your results afterward in the **Progress** tab.")

mode = st.sidebar.radio("Choose Mode", ["Practice", "Mock Exam", "Progress"])

# PRACTICE MODE
if mode == "Practice":
    st.header("\U0001F3AF Practice Questions")
    selected_topic = st.selectbox("Select Topic", topi
