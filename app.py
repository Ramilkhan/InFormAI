import streamlit as st
import pandas as pd
import os
from io import BytesIO

st.set_page_config(page_title="📋 FORM GENERATOR", layout="wide")

st.title("📋 FORM GENERATOR")
st.write("Upload an Excel or CSV file to generate a data entry form. Submissions are saved automatically.")

# --- Load Employee Data ---
EMPLOYEE_FILE = "employees.xlsx"

if os.path.exists(EMPLOYEE_FILE):
    employees_df = pd.read_excel(EMPLOYEE_FILE)
else:
    employees_df = pd.DataFrame(columns=["Name", "Email", "WhatsApp"])
    st.warning("⚠️ Employee file not found. Please make sure employees.xlsx is in the project folder.")

# --- Show Employee List ---
st.sidebar.header("👥 Employees")
st.sidebar.dataframe(employees_df)

# --- File Upload ---
uploaded_file = st.file_uploader("📂 Upload Excel or CSV file", type=["xlsx", "csv"])

if "data" not in st.session_state:
    st.session_state.data = None

if uploaded_file is not None:
    base_name = os.path.splitext(uploaded_file.name)[0]
    LOCAL_FILE = f"{base_name}.xlsx"

    # Save upload to local session
    file_bytes = uploaded_file.read()
    if uploaded_file.name.endswith(".csv"):
        df_csv = pd.read_csv(BytesIO(file_bytes))
        df_csv.to_excel(LOCAL_FILE, index=False, engine="openpyxl")
    else:
        with open(LOCAL_FILE, "wb") as f:
            f.write(file_bytes)

    df = pd.read_excel(LOCAL_FILE, engine="openpyxl", nrows=0)
    columns = df.columns.tolist()

    st.session_state.data = {"file": LOCAL_FILE, "columns": columns}
    st.success("✅ File uploaded successfully!")

if st.session_state.data:
    LOCAL_FILE = st.session_state.data["file"]
    columns = st.session_state.data["columns"]

    st.header("📝 Fill the Form")
    with st.form("entry_form"):
        form_data = {col: st.text_input(col) for col in columns}
        submitted = st.form_submit_button("Submit")

        if submitted:
            df = pd.read_excel(LOCAL_FILE, engine="openpyxl")
            new_id = len(df) + 1
            record = {"ID": new_id, **form_data}
            df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
            df.to_excel(LOCAL_FILE, index=False, engine="openpyxl")
            st.success(f"✅ Saved successfully with ID {new_id}")

    st.subheader("📊 Current Records")
    st.dataframe(pd.read_excel(LOCAL_FILE, engine="openpyxl"))
else:
    st.info("⬆️ Please upload a file to start.")
