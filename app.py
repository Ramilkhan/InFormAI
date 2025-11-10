import streamlit as st
import pandas as pd
import os
from io import BytesIO
import smtplib
from email.mime.text import MIMEText

# ---------------- CONFIG ----------------
st.set_page_config(page_title="📋 FORM GENERATOR", layout="wide")

# --- Admin password via Streamlit Secrets ---
try:
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except KeyError:
    st.error("⚠️ ADMIN_PASSWORD not set in Streamlit Secrets")
    ADMIN_PASSWORD = None

EMPLOYEE_FILE = "employees.xlsx"
BASE_URL = "https://yourappname.streamlit.app"  # replace after deployment

# ---------------- HELPER FUNCTIONS ----------------
def send_form_link(email_list, form_link):
    """Send form link via Gmail SMTP."""
    sender = "your_email@gmail.com"           # your Gmail
    password = "your_app_password"            # 16-char App Password
    
    subject = "📝 New Data Entry Form"
    body = f"Hello,\n\nPlease fill out this form:\n{form_link}\n\nThank you!"
    
    for recipient in email_list:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender, password)
                server.sendmail(sender, recipient, msg.as_string())
        except Exception as e:
            st.error(f"❌ Could not send to {recipient}: {e}")

def save_record(record, file_path):
    """Append data to an Excel file safely."""
    if os.path.exists(file_path):
        df = pd.read_excel(file_path, engine="openpyxl")
    else:
        df = pd.DataFrame(columns=["ID"] + list(record.keys()))
    record["ID"] = len(df) + 1
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_excel(file_path, index=False, engine="openpyxl")

# ---------------- LOAD EMPLOYEES ----------------
if os.path.exists(EMPLOYEE_FILE):
    employees_df = pd.read_excel(EMPLOYEE_FILE)
    employees_df.columns = employees_df.columns.str.strip().str.lower()
else:
    employees_df = pd.DataFrame(columns=["name", "email", "whatsapp"])
    st.warning("⚠️ employees.xlsx not found!")

# ---------------- PAGE LOGIC ----------------
query_params = st.experimental_get_query_params()
form_name = query_params.get("form", [None])[0]

if form_name:
    # ----------- EMPLOYEE VIEW -----------
    st.title("📝 Fill the Form")
    file_path = f"{form_name}.xlsx"

    if not os.path.exists(file_path):
        st.error("⚠️ Form not found or expired.")
    else:
        df = pd.read_excel(file_path, nrows=0, engine="openpyxl")
        columns = df.columns.tolist()

        with st.form("employee_form"):
            form_data = {col: st.text_input(col) for col in columns}
            submitted = st.form_submit_button("Submit")

            if submitted:
                save_record(form_data, file_path)
                st.success("✅ Your response has been recorded. Thank you!")

else:
    # ----------- ADMIN PANEL -----------
    st.title("🔐 Admin Panel")
    
    pw = st.text_input("Enter admin password", type="password")
    
    if pw and ADMIN_PASSWORD and pw == ADMIN_PASSWORD:
        st.success("Welcome, Admin!")
        
        uploaded_file = st.file_uploader("📂 Upload Excel/CSV to create new form", type=["xlsx", "csv"])
        
        if uploaded_file is not None:
            base_name = os.path.splitext(uploaded_file.name)[0]
            LOCAL_FILE = f"{base_name}.xlsx"
            
            file_bytes = uploaded_file.read()
            if uploaded_file.name.endswith(".csv"):
                df_csv = pd.read_csv(BytesIO(file_bytes))
                df_csv.to_excel(LOCAL_FILE, index=False, engine="openpyxl")
            else:
                with open(LOCAL_FILE, "wb") as f:
                    f.write(file_bytes)
            
            st.success(f"✅ Form '{base_name}' created successfully!")
            form_link = f"{BASE_URL}/?form={base_name}"
            st.code(form_link, language="text")
            
            # --- EMAIL AUTOMATION ---
            if not employees_df.empty and "email" in employees_df.columns:
                emails = employees_df["email"].dropna().tolist()
                if st.button("📧 Send form link to all employees"):
                    send_form_link(emails, form_link)
                    st.success("✅ Emails sent to all employees.")
            else:
                st.warning("⚠️ No valid employee emails found in employees.xlsx")
        
        # --- Show Employee List ---
        st.subheader("👥 Employee List")
        st.dataframe(employees_df)
    
    elif pw:
        st.error("❌ Incorrect password")
    else:
        st.info("Please enter admin password to continue.")
