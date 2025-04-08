import streamlit as st
import json
import random
import sqlite3
import pandas as pd

st.set_page_config(page_title="CFA Study App", layout="wide")
st.title("📊 CFA Practice App 2.0")

# Load questions
with open("questions.json", "r") as f:
    questions = json.load(f)["questions"]

# SQLite DB setup
def init_db():
    conn = sqlite3.connect("results.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS results (        username TEXT,         question_id TEXT,         correct INTEGER,         flagged INTEGER DEFAULT 0    )")
    conn.commit()
    return conn

db_conn = init_db()

# User login
username = st.sidebar.text_input("Enter your name", help="To begin practicing, type your name and hit Enter.")
if not username:
    st.info("To begin practicing, type your name and hit Enter.")
    st.stop()
st.success(f"Welcome, {username}! 🎉")
st.markdown("Choose **Practice** or **Mock Exam** from the sidebar. Your results will be tracked.")

# Mode selection
mode = st.sidebar.radio("Choose Mode", ["Practice", "Mock Exam", "Progress"])
topics = sorted(set(q["topic"] for q in questions))
difficulties = sorted(set(q["difficulty"] for q in questions))

if mode == "Practice":
    st.header("🎯 Practice Questions")
    topic = st.selectbox("Select Topic", topics)
    difficulty = st.selectbox("Select Difficulty", difficulties)
    qlist = [q for q in questions if q["topic"] == topic and q["difficulty"] == difficulty]
    if not qlist:
        st.warning("No questions available for this selection.")
    else:
        q = random.choice(qlist)
        st.subheader(q["question"])
        selection = st.radio("Choose an answer:", q["options"], index=None, key=q["id"])
        if st.button("Submit"):
            if selection:
                correct = q["correct_answer"]
                if selection == correct:
                    st.success("Correct! ✅")
                else:
                    st.error(f"Incorrect ❌. Correct answer: {correct}")
                if q.get("explanation"):
                    st.info(q["explanation"])
                c = db_conn.cursor()
                c.execute("INSERT INTO results (username, question_id, correct) VALUES (?, ?, ?)",
                          (username, q["id"], int(selection == correct)))
                db_conn.commit()
            else:
                st.warning("Please select an answer before submitting.")

elif mode == "Progress":
    st.header("📈 Progress Tracker")
    df = pd.read_sql_query("SELECT * FROM results WHERE username = ?", db_conn, params=(username,))
    if df.empty:
        st.info("No progress to show yet.")
    else:
        st.metric("Questions Attempted", len(df))
        st.metric("Correct Answers", df['correct'].sum())
        st.metric("Accuracy (%)", round(df['correct'].mean() * 100, 2))
