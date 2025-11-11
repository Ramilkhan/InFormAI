import streamlit as st
import pandas as pd
import os
import uuid

# --- Page Config ---
st.set_page_config(page_title="Dynamic Form Generator", layout="wide")

# --- Constants ---
ADMIN_PASSWORD = "admin123"  # change this to your desired password
FORM_FOLDER = "forms_data"
if not os.path.exists(FORM_FOLDER):
    os.makedirs(FORM_FOLDER)

# --- Session State ---
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "form_id" not in st.session_state:
    st.session_state.form_id = None

# --- ADMIN LOGIN FUNCTION ---
def admin_login():
    st.title("🔐 Admin Login")
    password = st.text_input("Enter admin password:", type="password")
    if st.button("Login"):
        if password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.success("✅ Logged in as Admin!")
            st.experimental_rerun()  # <--- important for re-render
        else:
            st.error("❌ Incorrect password!")

# --- FILE UPLOAD SECTION ---
def upload_files():
    st.header("📂 Upload Excel/CSV Files")
    form_file = st.file_uploader("Upload Form Template (Excel/CSV)", type=["xlsx", "csv"])
    employee_file = st.file_uploader("Upload Employee List (Excel/CSV)", type=["xlsx", "csv"])

    if form_file and employee_file:
        try:
            # Read form template
            form_df = pd.read_csv(form_file) if form_file.name.endswith(".csv") else pd.read_excel(form_file)
            employees_df = pd.read_csv(employee_file) if employee_file.name.endswith(".csv") else pd.read_excel(employee_file)

            st.session_state.form_template = form_df
            st.session_state.employee_list = employees_df

            st.success("✅ Files uploaded successfully!")
        except Exception as e:
            st.error(f"Error reading files: {e}")

# --- FORM INTERFACE ---
def show_form_interface():
    st.header("🧾 Form Preview / Creation")
    if "form_template" in st.session_state:
        form_df = st.session_state.form_template
        form_data = {}

        st.info("Enter example data (Admin view):")
        for col in form_df.columns:
            form_data[col] = st.text_input(f"{col}")

        if st.button("💾 Submit Form Data"):
            form_id = str(uuid.uuid4())
            st.session_state.form_id = form_id
            file_path = os.path.join(FORM_FOLDER, f"{form_id}.csv")
            pd.DataFrame([form_data]).to_csv(file_path, index=False)
            st.success(f"Form saved successfully! ✅")
            st.info(f"Form ID: `{form_id}`")

# --- SHAREABLE LINK ---
def generate_form_link():
    if st.session_state.form_id:
        st.header("🔗 Shareable Form Link")
        base_url = st.secrets.get("BASE_URL", "http://localhost:8501")
        form_link = f"{base_url}?form_id={st.session_state.form_id}"
        st.code(form_link, language="text")

# --- EMPLOYEE FORM VIEW ---
def employee_form_submission():
    st.title("📝 Employee Form Submission")
    form_id = st.experimental_get_query_params().get("form_id", [None])[0]

    if form_id:
        file_path = os.path.join(FORM_FOLDER, f"{form_id}.csv")
        if os.path.exists(file_path):
            form_df = pd.read_csv(file_path)
            form_data = {}
            for col in form_df.columns:
                form_data[col] = st.text_input(f"{col}")
            if st.button("Submit Form"):
                submission_file = os.path.join(FORM_FOLDER, f"{form_id}_responses.csv")
                if os.path.exists(submission_file):
                    existing_df = pd.read_csv(submission_file)
                    existing_df = pd.concat([existing_df, pd.DataFrame([form_data])])
                else:
                    existing_df = pd.DataFrame([form_data])
                existing_df.to_csv(submission_file, index=False)
                st.success("✅ Form submitted successfully!")
        else:
            st.error("Invalid or expired form link.")
    else:
        st.warning("No form ID found in the URL!")

# --- DOWNLOAD RESPONSES ---
def download_responses():
    st.header("📥 Download Submitted Responses")
    files = [f for f in os.listdir(FORM_FOLDER) if "_responses.csv" in f]

    if files:
        selected = st.selectbox("Select form to download:", files)
        if st.button("⬇️ Download CSV"):
            df = pd.read_csv(os.path.join(FORM_FOLDER, selected))
            st.download_button(
                label="Download Responses",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=selected,
                mime="text/csv",
            )
    else:
        st.info("No form submissions yet.")

# --- MAIN LOGIC ---
query_params = st.experimental_get_query_params()
if "form_id" in query_params:
    employee_form_submission()
else:
    if not st.session_state.admin_logged_in:
        admin_login()
    else:
        with st.sidebar:
            st.title("⚙️ Admin Panel")
            st.success("✅ Logged in")
            option = st.radio(
                "Select Action:",
                ["Upload Files", "Preview / Create Form", "Generate Link", "Download Responses"]
            )

        if option == "Upload Files":
            upload_files()
        elif option == "Preview / Create Form":
            show_form_interface()
        elif option == "Generate Link":
            generate_form_link()
        elif option == "Download Responses":
            download_responses()
