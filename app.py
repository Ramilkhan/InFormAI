import streamlit as st
import pandas as pd
import os
import uuid

# --- Page Config ---
st.set_page_config(page_title="Dynamic Form Generator", layout="wide")

# --- Constants ---
ADMIN_PASSWORD = "admin123"  # Change this to your secure password
FORM_FOLDER = "forms_data"
if not os.path.exists(FORM_FOLDER):
    os.makedirs(FORM_FOLDER)

# --- Session State ---
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "form_id" not in st.session_state:
    st.session_state.form_id = None
if "employee_list" not in st.session_state:
    st.session_state.employee_list = pd.DataFrame()

# --- Admin Login ---
def admin_login():
    st.subheader("Admin Login")
    password = st.text_input("Enter admin password:", type="password")
    if st.button("Login"):
        if password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.success("Logged in as Admin!")
        else:
            st.error("Incorrect password!")

# --- Upload Excel Files ---
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

# --- Generate Form ---
def show_form_interface():
    st.subheader("Form Preview / Fill")
    if "form_template" in st.session_state:
        form_df = st.session_state.form_template
        form_data = {}
        for col in form_df.columns:
            form_data[col] = st.text_input(f"{col}")
        if st.button("Submit Form Data (Admin View)"):
            form_id = str(uuid.uuid4())
            st.session_state.form_id = form_id
            file_path = os.path.join(FORM_FOLDER, f"{form_id}.csv")
            pd.DataFrame([form_data]).to_csv(file_path, index=False)
            st.success(f"Data saved! Form ID: {form_id}")
            st.info(f"File path: {file_path}")

# --- Generate Shareable Link ---
def generate_form_link():
    if st.session_state.form_id:
        st.subheader("Shareable Form Link")
        form_link = f"{st.secrets.get('BASE_URL', 'http://localhost:8501')}?form_id={st.session_state.form_id}"
        st.text_input("Copy this link:", form_link)

# --- Employee Form Submission ---
def employee_form_submission():
    st.subheader("Employee Form")
    form_id = st.experimental_get_query_params().get("form_id", [None])[0]
    if form_id:
        file_path = os.path.join(FORM_FOLDER, f"{form_id}.csv")
        if os.path.exists(file_path):
            form_df = pd.read_csv(file_path)
            form_data = {}
            for col in form_df.columns:
                form_data[col] = st.text_input(f"{col}")
            if st.button("Submit"):
                submission_file = os.path.join(FORM_FOLDER, f"{form_id}_responses.csv")
                if os.path.exists(submission_file):
                    existing_df = pd.read_csv(submission_file)
                    existing_df = pd.concat([existing_df, pd.DataFrame([form_data])])
                else:
                    existing_df = pd.DataFrame([form_data])
                existing_df.to_csv(submission_file, index=False)
                st.success("Form submitted successfully!")
        else:
            st.error("Invalid Form ID!")

# --- Download Responses ---
def download_responses():
    st.subheader("Download Submitted Responses")
    files = [f for f in os.listdir(FORM_FOLDER) if "_responses.csv" in f]
    if files:
        file_to_download = st.selectbox("Select Form to Download", files)
        if st.button("Download CSV"):
            df = pd.read_csv(os.path.join(FORM_FOLDER, file_to_download))
            df.to_csv(file_to_download, index=False)
            st.success(f"Downloaded {file_to_download}")
    else:
        st.info("No submissions yet.")

# --- Main ---
query_params = st.experimental_get_query_params()
if "form_id" in query_params:
    employee_form_submission()
else:
    if not st.session_state.admin_logged_in:
        admin_login()
    else:
        st.success("Welcome, Admin!")
        upload_files()
        if "form_template" in st.session_state:
            show_form_interface()
            generate_form_link()
            download_responses()
