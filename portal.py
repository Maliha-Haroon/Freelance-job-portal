import streamlit as st
import sqlite3
import pandas as pd

# ---------------- Database Setup ----------------
conn = sqlite3.connect('freelancer_portal.db', check_same_thread=False)
c = conn.cursor()

def create_tables():
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    role TEXT CHECK(role IN ('client','freelancer'))
                )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    description TEXT,
                    category TEXT,
                    budget REAL,
                    deadline TEXT,
                    client_id INTEGER,
                    FOREIGN KEY (client_id) REFERENCES users(id)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS proposals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER,
                    freelancer_id INTEGER,
                    bid REAL,
                    cover_letter TEXT,
                    status TEXT CHECK(status IN ('Pending', 'Accepted', 'Rejected')),
                    FOREIGN KEY (job_id) REFERENCES jobs(id),
                    FOREIGN KEY (freelancer_id) REFERENCES users(id)
                )''')
    conn.commit()

create_tables()

# ---------------- User Management ----------------
def register_user(username, password, role):
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone()

# ---------------- Job Posting ----------------
def post_job(title, desc, cat, budget, deadline, client_id):
    c.execute("INSERT INTO jobs (title, description, category, budget, deadline, client_id) VALUES (?, ?, ?, ?, ?, ?)",
              (title, desc, cat, budget, deadline, client_id))
    conn.commit()

def get_jobs():
    c.execute("SELECT j.id, j.title, j.description, j.budget, u.username FROM jobs j JOIN users u ON j.client_id = u.id")
    return c.fetchall()

def apply_proposal(job_id, freelancer_id, bid, letter):
    c.execute("INSERT INTO proposals (job_id, freelancer_id, bid, cover_letter, status) VALUES (?, ?, ?, ?, 'Pending')",
              (job_id, freelancer_id, bid, letter))
    conn.commit()

# ---------------- Streamlit UI ----------------
st.title("🧑‍💻 Freelancer Job Portal")

menu = ["Home", "Register", "Login"]
choice = st.sidebar.selectbox("Menu", menu)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

if choice == "Register":
    st.subheader("Create Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["client", "freelancer"])
    if st.button("Register"):
        if register_user(username, password, role):
            st.success("Registered successfully!")
        else:
            st.error("Username already exists!")

elif choice == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.success(f"Welcome {user[1]}!")
        else:
            st.error("Invalid credentials")

# ---------------- Logged-In Dashboard ----------------
if st.session_state.logged_in:
    user = st.session_state.user
    st.sidebar.success(f"Logged in as {user[1]} ({user[3]})")
    
    if user[3] == "client":
        st.subheader("📌 Post a Job")
        title = st.text_input("Job Title")
        desc = st.text_area("Description")
        cat = st.text_input("Category")
        budget = st.number_input("Budget", min_value=0.0)
        deadline = st.date_input("Deadline")
        if st.button("Post Job"):
            post_job(title, desc, cat, budget, deadline.strftime("%Y-%m-%d"), user[0])
            st.success("Job posted successfully!")

    elif user[3] == "freelancer":
        st.subheader("📝 Available Jobs")
        jobs = get_jobs()
        df = pd.DataFrame(jobs, columns=["ID", "Title", "Description", "Budget", "Posted By"])
        st.dataframe(df)

        job_id = st.number_input("Apply to Job ID", min_value=1, step=1)
        bid = st.number_input("Your Bid", min_value=0.0)
        letter = st.text_area("Cover Letter")
        if st.button("Submit Proposal"):
            apply_proposal(job_id, user[0], bid, letter)
            st.success("Proposal submitted!")

# Optional: Add logout
if st.session_state.logged_in:
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.experimental_rerun()
