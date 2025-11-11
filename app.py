import streamlit as st
import pandas as pd
import uuid
import os
import io
import smtplib
from email.message import EmailMessage
from datetime import datetime

st.set_page_config(page_title="Admin Panel - Dynamic Form Generator", layout="wide")

# --- Helpers ---
def load_forms():
    if os.path.exists("forms.xlsx"):
        return pd.read_excel("forms.xlsx")
    return pd.DataFrame(columns=["form_id", "title", "columns", "created_at"])

def save_forms(df):
    df.to_excel("forms.xlsx", index=False)

def load_responses(form_id):
    path = f"responses_{form_id}.xlsx"
    if os.path.exists(path):
        return pd.read_excel(path)
    return pd.DataFrame()

def save_response(form_id, data):
    df = load_responses(form_id)
    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    df.to_excel(f"responses_{form_id}.xlsx", index=False)

def send_emails(emails, subject, body, smtp_host, smtp_port, username, password, sender, use_tls=True):
    sent = 0
    for email in emails:
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = email
            msg.set_content(body)
            server = smtplib.SMTP(smtp_host, smtp_port)
            if use_tls:
                server.starttls()
            if username:
                server.login(username, password)
            server.send_message(msg)
            server.quit()
            sent += 1
        except Exception as e:
            st.warning(f"Failed to send to {email}: {e}")
    return sent

# --- Sidebar Navigation ---
st.sidebar.title("🔐 Admin Panel")
page = st.sidebar.radio("Go to", ["Create Form", "View Forms", "Fill Form"])

# --- Session State ---
if "forms" not in st.session_state:
    st.session_state.forms = load_forms()

# --- CREATE FORM ---
if page == "Create Form":
    st.title("📂 Upload Excel/CSV to Create New Form")
    title = st.text_input("Form Title")
    upload = st.file_uploader("Upload Excel or CSV file", type=["xlsx", "xls", "csv"])

    st.write("---")
    st.subheader("📧 Optional: Send form link via Email")
    smtp_host = st.text_input("SMTP Host", placeholder="smtp.gmail.com")
    smtp_port = st.number_input("SMTP Port", 587)
    username = st.text_input("SMTP Username")
    password = st.text_input("SMTP Password", type="password")
    sender = st.text_input("Sender Email")
    emails_text = st.text_area("Employee Emails (comma or newline separated)")

    if st.button("Generate Form"):
        if upload and title:
            ext = upload.name.split(".")[-1].lower()
            if ext == "csv":
                df = pd.read_csv(upload, nrows=0)
            else:
                df = pd.read_excel(upload, nrows=0)
            columns = list(df.columns)
            form_id = uuid.uuid4().hex
            created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            # Save form metadata
            forms_df = load_forms()
            new_row = pd.DataFrame([{
                "form_id": form_id,
                "title": title,
                "columns": ",".join(columns),
                "created_at": created_at
            }])
            forms_df = pd.concat([forms_df, new_row], ignore_index=True)
            save_forms(forms_df)
            st.session_state.forms = forms_df

            form_link = f"?page=Fill%20Form&form_id={form_id}"
            full_link = f"{st.request.url_root}{form_link}"
            st.success("✅ Form created successfully!")
            st.markdown(f"**Form Link:** [Open Form]({full_link})")

            # Optional email sending
            if emails_text.strip() and smtp_host and sender:
                emails = [e.strip() for e in emails_text.replace(",", "\n").splitlines() if e.strip()]
                subject = f"Please fill out: {title}"
                body = f"Hello,\n\nPlease fill out this form:\n{full_link}\n\nThank you!"
                sent = send_emails(emails, subject, body, smtp_host, smtp_port, username, password, sender)
                st.info(f"📤 Emails sent: {sent}")
        else:
            st.warning("Please provide a title and file.")

# --- VIEW FORMS ---
elif page == "View Forms":
    st.title("📋 All Created Forms")
    forms_df = load_forms()
    if not forms_df.empty:
        st.dataframe(forms_df)
        selected = st.selectbox("Select a form to view submissions", forms_df["title"])
        form_row = forms_df[forms_df["title"] == selected].iloc[0]
        form_id = form_row["form_id"]
        resp_df = load_responses(form_id)
        st.subheader("📥 Form Responses")
        if not resp_df.empty:
            st.dataframe(resp_df)
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                resp_df.to_excel(writer, index=False)
            st.download_button("⬇️ Download Responses", data=buf.getvalue(),
                               file_name=f"responses_{form_id}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("No responses yet.")
    else:
        st.info("No forms created yet.")

# --- FILL FORM ---
elif page == "Fill Form":
    st.title("📝 Fill Form")
    form_id = st.experimental_get_query_params().get("form_id", [None])[0]
    if not form_id:
        st.warning("Form ID not provided. Use a valid form link.")
    else:
        forms_df = load_forms()
        if form_id not in forms_df["form_id"].values:
            st.error("Form not found.")
        else:
            form = forms_df[forms_df["form_id"] == form_id].iloc[0]
            st.subheader(form["title"])
            cols = form["columns"].split(",")
            data = {}
            for c in cols:
                data[c] = st.text_input(c)
            if st.button("Submit"):
                data["Submitted_At"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                save_response(form_id, data)
                st.success("✅ Your response has been recorded.")
