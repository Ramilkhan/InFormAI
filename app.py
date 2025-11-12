import streamlit as st
import pandas as pd
import os
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Page Config ---
st.set_page_config(page_title="Dynamic Form Generator", layout="wide")

# --- Constants ---
ADMIN_PASSWORD = "admin123"
FORM_FOLDER = "forms_data"
if not os.path.exists(FORM_FOLDER):
    os.makedirs(FORM_FOLDER)

# --- Session State ---
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "form_id" not in st.session_state:
    st.session_state.form_id = None
if "form_template" not in st.session_state:
    st.session_state.form_template = None
if "employee_list" not in st.session_state:
    st.session_state.employee_list = None


# --- EMAIL SENDER ---
def send_form_link_to_employees(share_link, employees_df):
    try:
        smtp_server = st.secrets["SMTP_SERVER"]
        smtp_port = st.secrets["SMTP_PORT"]
        email_sender = st.secrets["EMAIL_SENDER"]
        email_password = st.secrets["EMAIL_PASSWORD"]

        # Find column containing email addresses
        email_col = [c for c in employees_df.columns if "email" in c.lower()]
        if not email_col:
            st.warning("⚠️ No column found containing 'email'.")
            return
        email_col = email_col[0]
        recipients = employees_df[email_col].dropna().unique().tolist()
        if not recipients:
            st.warning("⚠️ No valid email addresses found.")
            return

        # Compose the email
        subject = "Please Fill Out the Company Form"
        body = f"""Dear Employee,

You are requested to fill out the form using the link below:

{share_link}

Thank you,
HR Department
"""

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_sender, email_password)

        for recipient in recipients:
            msg = MIMEMultipart()
            msg["From"] = email_sender
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            server.sendmail(email_sender, recipient, msg.as_string())

        server.quit()
        st.success(f"✅ Form link sent successfully to {len(recipients)} employees!")
    except Exception as e:
        st.error(f"❌ Email sending failed: {e}")


# --- ADMIN LOGIN ---
def admin_login():
    st.title("🔐 Admin Login")
    password = st.text_input("Enter admin password:", type="password")
    if st.button("Login"):
        if password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.success("✅ Logged in successfully!")
            st.rerun()
        else:
            st.error("❌ Incorrect password!")


# --- FILE UPLOAD ---
def upload_files():
    st.header("📂 Upload Excel/CSV Files")
    form_file = st.file_uploader("Upload Form Template (Excel/CSV)", type=["xlsx", "csv"])
    employee_file = st.file_uploader("Upload Employee List (Excel/CSV)", type=["xlsx", "csv"])

    if form_file and employee_file:
        try:
            form_df = pd.read_csv(form_file) if form_file.name.endswith(".csv") else pd.read_excel(form_file)
            employees_df = pd.read_csv(employee_file) if employee_file.name.endswith(".csv") else pd.read_excel(employee_file)

            st.session_state.form_template = form_df
            st.session_state.employee_list = employees_df
            st.success("✅ Files uploaded successfully!")

        except Exception as e:
            st.error(f"Error reading files: {e}")


# --- FORM CREATION ---
def show_form_interface():
    st.header("🧾 Form Preview / Shareable Link")

    if st.session_state.form_template is not None:
        form_df = st.session_state.form_template

        st.subheader("📋 Form Preview")
        st.dataframe(form_df)

        if st.button("💾 Generate Shareable Link & Email Employees"):
            form_id = str(uuid.uuid4())
            st.session_state.form_id = form_id
            form_path = os.path.join(FORM_FOLDER, f"{form_id}.csv")
            form_df.to_csv(form_path, index=False)
            st.success("✅ Form saved successfully!")

            # Public base URL
            base_url = st.secrets.get("BASE_URL", "https://informai-9owst2mknhnbtf9ukychaq.streamlit.app")
            share_link = f"{base_url}?form_id={form_id}"

            st.markdown("### 🔗 Shareable Form Link:")
            st.code(share_link, language="text")

            if st.session_state.employee_list is not None:
                send_form_link_to_employees(share_link, st.session_state.employee_list)
            else:
                st.warning("⚠️ Please upload employee list first.")
    else:
        st.info("Please upload a form template first.")


# --- EMPLOYEE FORM VIEW ---
def employee_form_submission():
    st.title("📝 Employee Form Submission")

    query_params = st.experimental_get_query_params()
    form_id = query_params.get("form_id", [None])[0]

    if form_id:
        form_path = os.path.join(FORM_FOLDER, f"{form_id}.csv")
        if os.path.exists(form_path):
            form_df = pd.read_csv(form_path)
            form_data = {}

            st.info("Please fill in the form below:")
            for col in form_df.columns:
                form_data[col] = st.text_input(f"{col}")

            if st.button("Submit Form"):
                responses_path = os.path.join(FORM_FOLDER, f"{form_id}_responses.csv")
                if os.path.exists(responses_path):
                    existing = pd.read_csv(responses_path)
                    existing = pd.concat([existing, pd.DataFrame([form_data])], ignore_index=True)
                else:
                    existing = pd.DataFrame([form_data])
                existing.to_csv(responses_path, index=False)
                st.success("✅ Form submitted successfully!")
        else:
            st.error("Invalid or expired form link.")
    else:
        st.warning("No form ID found in URL!")


# --- DOWNLOAD RESPONSES ---
def download_responses():
    st.header("📥 Download Form Responses")
    files = [f for f in os.listdir(FORM_FOLDER) if "_responses.csv" in f]

    if files:
        selected = st.selectbox("Select form:", files)
        if st.button("⬇️ Download CSV"):
            df = pd.read_csv(os.path.join(FORM_FOLDER, selected))
            st.download_button(
                "Download Responses",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=selected,
                mime="text/csv",
            )
    else:
        st.info("No responses yet.")


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
            action = st.radio("Select Action:", ["Upload Files", "Preview / Create Form", "Download Responses"])

        if action == "Upload Files":
            upload_files()
        elif action == "Preview / Create Form":
            show_form_interface()
        elif action == "Download Responses":
            download_responses()
