import streamlit as st
import pandas as pd
import json
from uuid import uuid4
import smtplib
from email.mime.text import MIMEText

def read_form_file(uploaded_file):
    # read Excel/CSV
    if uploaded_file.name.lower().endswith(('.xlsx', '.xls')):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)
    # replace NaN with None
    df = df.where(pd.notnull(df), None)
    return df

def build_form_schema(df: pd.DataFrame):
    schema = {
        "form_id": str(uuid4()),
        "columns": []
    }
    for col in df.columns:
        dtype = df[col].dtype
        if pd.api.types.is_integer_dtype(dtype):
            t = "integer"
        elif pd.api.types.is_float_dtype(dtype):
            t = "number"
        elif pd.api.types.is_bool_dtype(dtype):
            t = "boolean"
        else:
            t = "string"
        schema["columns"].append({"name": col, "type": t})
    return schema

def send_form_link(emails, link, smtp_config):
    subject = "Please fill the form"
    body = f"Dear employee,\n\nPlease fill the form at the following link:\n{link}\n\nThanks"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_config["from"]
    for to in emails:
        msg["To"] = to
        with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as s:
            s.starttls()
            s.login(smtp_config["user"], smtp_config["password"])
            s.sendmail(smtp_config["from"], to, msg.as_string())

# Streamlit UI
st.title("Admin Panel")
uploaded = st.file_uploader("Upload Excel/CSV to create new form", type=["xlsx","csv"])
if uploaded is not None:
    try:
        df = read_form_file(uploaded)
        st.write("Columns detected:", df.columns.tolist())

        schema = build_form_schema(df)
        # dump schema to JSON safely
        schema_json = json.dumps(schema, default=str)
        st.write(schema_json)  # for debug

        # create form link based on schema (your logic)
        form_link = f"https://yourapp.com/fill_form/{schema['form_id']}"
        st.success(f"Form created: {form_link}")

        # send link to employees
        # (assuming you already have employees list in another sheet)
        # For demonstration:
        # employees_df = ...
        # send_form_link(employees_df["email"].tolist(), form_link, smtp_config)

    except Exception as e:
        st.error(f"Error processing file: {e}")
