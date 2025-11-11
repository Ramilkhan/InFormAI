import streamlit as st
import pandas as pd
import os
import uuid

# --- Config ---
st.set_page_config(page_title="Dynamic Form Generator", layout="wide")

# --- Constants ---
ADMIN_PASSWORD = "admin123"  # Change this
FORM_FOLDER = "forms_data"
if not os.path.exists(FORM_FOLDER):
    os.makedirs(FORM_FOLDER)

# --- Session State ---
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "forms" not in st.session_state:
    st.session_state.forms = {}  # Stores form data

# --- Helper Functions ---
def admin_login():
    st.subheader("Admin Login")
    password = st.text_input("Enter admin password:", type="password")
    if st.button("Login"):
        if password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.success("Logged in as Admin!")
        else:
            st.error("Incorrect password!")

def upload_files():
    st.subheader("Upload Excel Files")
    form_file = st.file_uploader("Upload Form Template Excel", type=["xlsx", "csv"])
    employee_file = st.file_uploader("Upload Employee List Excel", type=["xlsx", "csv"])
    
    if form_file and employee_file:
        try:
            if form_file.name.endswith(".csv"):
                form_df = pd.read_csv(form_file)
            else:
                form_df = pd.read_excel(form_file)

            if employee_file.name.endswith(".csv"):
                employees_df = pd.read_csv(employee_file)
            else:
                employees_df = pd.read_excel(employee_file)

            st.session_state.form_template = form_df
            st.session_state.employee_list = employees_df
            st.success("Files uploaded successfully!")
        except Exception as e:
            st.error(f"Error reading files: {e}")

def generate_form():
    st.subheader("Form Preview / Admin Fill")
    if "form_template" in st.session_state:
        form_df = st.session_state.form_template
        form_data = {}
        for col in form_df.columns:
            form_data[col] = st.text_input(f"{col}")
        if st.button("Save Form"):
            form_id = str(uuid.uuid4())
            st.session_state.forms[form_id] = form_df
            form_file_path = os.path.join(FORM_FOLDER, f"{form_id}.csv")
            form_df.to_csv(form_file_path, index=False)
            st.success(f"Form saved with ID: {form_id}")
            # Generate shareable link
            base_url = st.secrets.get("BASE_URL", "https://your-deployed-app.streamlit.app")
            shareable_link = f"{base_url}?form_id={form_id}"
            st.text_input("Shareable Form Link:", shareable_link, key=form_id)

def employee_form():
    query_params = st.experimental_get_query_params()
    form_id = query_params.get("form_id", [None])[0]
    if form_id:
        form_file = os.path.join(FORM_FOLDER, f"{form_id}.csv")
        if os.path.exists(form_file):
            form_df = pd.read_csv(form_file)
            st.subheader("Employee Form")
            submission = {}
            for col in form_df.columns:
                submission[col] = st.text_input(f"{col}")
            if st.button("Submit"):
                submission_file = os.path.join(FORM_FOLDER, f"{form_id}_responses.csv")
                if os.path.exists(submission_file):
                    existing = pd.read_csv(submission_file)
                    existing = pd.concat([existing, pd.DataFrame([submission])])
                else:
                    existing = pd.DataFrame([submission])
                existing.to_csv(submission_file, index=False)
                st.success("Form submitted successfully!")
        else:
            st.error("Invalid Form ID!")

def download_responses():
    st.subheader("Download Responses")
    response_files = [f for f in os.listdir(FORM_FOLDER) if "_responses.csv" in f]
    if response_files:
        file = st.selectbox("Select Form Responses", response_files)
        if st.button("Download CSV"):
            df = pd.read_csv(os.path.join(FORM_FOLDER, file))
            df.to_csv(file, index=False)
            st.success(f"Downloaded {file}")
    else:
        st.info("No submissions yet.")

# --- Main ---
query_params = st.experimental_get_query_params()
if "form_id" in query_params:
    employee_form()
else:
    if not st.session_state.admin_logged_in:
        admin_login()
    else:
        st.success("Welcome, Admin!")
        upload_files()
        if "form_template" in st.session_state:
            generate_form()
            download_responses()
