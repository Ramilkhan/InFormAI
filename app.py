import streamlit as st
import pandas as pd
import os
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========== CONFIG ==========
st.set_page_config(page_title="📋 INFORM.AI Form Portal", layout="wide")

# Load secrets safely
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin123")
SMTP_EMAIL = st.secrets.get("SMTP_EMAIL", "")
SMTP_PASS = st.secrets.get("SMTP_PASS", "")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Folders
os.makedirs("forms", exist_ok=True)
os.makedirs("submissions", exist_ok=True)

# ========== ADMIN LOGIN ==========
st.title("🔐 Admin Panel")

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if not st.session_state.is_admin:
    password = st.text_input("Enter admin password", type="password")
    if st.button("Login"):
        if password == ADMIN_PASSWORD:
            st.session_state.is_admin = True
            st.success("Welcome, Admin!")
        else:
            st.error("❌ Incorrect password.")
    st.stop()

# ========== ADMIN PANEL ==========
st.success("Welcome, Admin!")

uploaded_file = st.file_uploader("📂 Upload Excel/CSV to create new form", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # Read and sanitize data
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        df = df.fillna("")  # 🔥 Fix NaN error

        # Save the uploaded file
        form_name = os.path.splitext(uploaded_file.name)[0]
        form_path = f"forms/{form_name}.xlsx"
        df.to_excel(form_path, index=False)

        st.success(f"✅ Form '{form_name}' created successfully!")

        # Generate unique form link
        form_id = str(uuid.uuid4())
        form_link = f"{st.request.url_root}?form_id={form_id}".replace("///", "//")

        # Save link mapping
        mapping_path = "forms/mapping.csv"
        if os.path.exists(mapping_path):
            mapping_df = pd.read_csv(mapping_path).fillna("")  # 🔥 Fix NaN error
        else:
            mapping_df = pd.DataFrame(columns=["form_id", "form_name", "file_path", "link"])

        new_entry = pd.DataFrame([{
            "form_id": form_id,
            "form_name": form_name,
            "file_path": form_path,
            "link": form_link
        }])

        mapping_df = pd.concat([mapping_df, new_entry], ignore_index=True)
        mapping_df.to_csv(mapping_path, index=False)

        st.markdown(f"🔗 **Form Link:** [Open Form]({form_link})")

        # Upload employee list (optional)
        emp_file = st.file_uploader("👥 Upload Employee List (with Email column)", type=["xlsx", "csv"])
        if emp_file:
            if emp_file.name.endswith(".csv"):
                employees_df = pd.read_csv(emp_file)
            else:
                employees_df = pd.read_excel(emp_file)
            employees_df = employees_df.fillna("")  # 🔥 Fix NaN error

            if "Email" not in employees_df.columns:
                st.error("❌ Missing 'Email' column in employee list.")
            else:
                emails = employees_df["Email"].dropna().tolist()
                st.write(f"📧 {len(emails)} employees detected.")

                # Send form link via email
                if SMTP_EMAIL and SMTP_PASS:
                    with st.spinner("Sending form links..."):
                        try:
                            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                            server.starttls()
                            server.login(SMTP_EMAIL, SMTP_PASS)

                            for email in emails:
                                msg = MIMEMultipart()
                                msg["From"] = SMTP_EMAIL
                                msg["To"] = email
                                msg["Subject"] = f"Form Invitation: {form_name}"
                                body = f"Dear Employee,\n\nPlease fill out the form at the link below:\n{form_link}\n\nBest Regards,\nAdmin"
                                msg.attach(MIMEText(body, "plain"))
                                server.send_message(msg)

                            server.quit()
                            st.success("✅ Form links emailed to all employees.")
                        except Exception as e:
                            st.error(f"Email send failed: {e}")
                else:
                    st.warning("⚠️ SMTP credentials not found in secrets.")

    except Exception as e:
        st.error(f"Error processing file: {e}")

# ========== FORM VIEW ==========
if "form_id" in st.query_params:
    st.title("📋 Form Submission")
    form_id = st.query_params["form_id"]

    # Load form mapping
    if os.path.exists("forms/mapping.csv"):
        mapping_df = pd.read_csv("forms/mapping.csv").fillna("")  # 🔥 Fix NaN error
        match = mapping_df[mapping_df["form_id"] == form_id]
        if not match.empty:
            file_path = match.iloc[0]["file_path"]
            form_name = match.iloc[0]["form_name"]
            df = pd.read_excel(file_path).fillna("")  # 🔥 Fix NaN error

            st.subheader(f"Form: {form_name}")

            user_input = {}
            with st.form("data_entry_form"):
                for col in df.columns:
                    user_input[col] = st.text_input(f"{col}")
                submitted = st.form_submit_button("Submit")

            if submitted:
                new_row = pd.DataFrame([user_input])
                output_file = f"submissions/{form_name}_responses.xlsx"

                if os.path.exists(output_file):
                    existing = pd.read_excel(output_file).fillna("")  # 🔥 Fix NaN error
                    combined = pd.concat([existing, new_row], ignore_index=True)
                else:
                    combined = new_row

                combined.to_excel(output_file, index=False)
                st.success("✅ Response submitted successfully!")

        else:
            st.error("❌ Invalid or expired form link.")
    else:
        st.error("❌ No forms found in the system.")

# ========== DOWNLOAD SUBMISSIONS ==========
st.markdown("---")
st.header("📥 Download Submissions")

subs = [f for f in os.listdir("submissions") if f.endswith(".xlsx")]
if subs:
    for f in subs:
        with open(f"submissions/{f}", "rb") as file:
            st.download_button(f"Download {f}", data=file, file_name=f)
else:
    st.info("No submissions yet.")
