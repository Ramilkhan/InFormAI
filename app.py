import streamlit as st
import pandas as pd
import os
from io import BytesIO

# --- Streamlit Page Config ---
st.set_page_config(page_title="📋 FORM GENERATOR", layout="wide")

# --- Title and Intro ---
st.title("📋 FORM GENERATOR")
st.write("Upload your existing Excel or CSV file to dynamically generate a data entry form. All new submissions will be saved back into the same file.")

# --- Helper Function ---
def save_to_excel(record, file_path):
    """Append a record to an existing Excel file or create it if missing."""
    if os.path.exists(file_path):
        df = pd.read_excel(file_path, engine="openpyxl")
    else:
        df = pd.DataFrame(columns=["ID"] + list(record.keys()))

    new_id = len(df) + 1
    record_with_id = {"ID": new_id, **record}
    df = pd.concat([df, pd.DataFrame([record_with_id])], ignore_index=True)

    df.to_excel(file_path, index=False, engine="openpyxl")
    st.success(f"✅ Record saved successfully with ID {new_id}")

# --- Step 1: File Upload ---
uploaded_file = st.file_uploader(
    "📂 Upload your existing Excel or CSV file (with headers)",
    type=["xlsx", "csv"]
)

if uploaded_file is not None:
    # Dynamically set file name
    base_name = os.path.splitext(uploaded_file.name)[0]
    LOCAL_FILE = f"{base_name}.xlsx"

    # Save uploaded file properly
    file_bytes = uploaded_file.read()

    if uploaded_file.name.endswith(".csv"):
        # Convert CSV → Excel format
        df_csv = pd.read_csv(BytesIO(file_bytes))
        df_csv.to_excel(LOCAL_FILE, index=False, engine="openpyxl")
    else:
        # Save Excel file directly
        with open(LOCAL_FILE, "wb") as f:
            f.write(file_bytes)

    # Extract column headers
    df = pd.read_excel(LOCAL_FILE, engine="openpyxl", nrows=0)
    columns = df.columns.tolist()

    st.success(f"✅ Detected columns: {columns}")
    st.info(f"📁 All new form entries will be saved to: **{LOCAL_FILE}**")

    # --- Step 2: Dynamic Form ---
    st.header("📝 FORM ENTRY SECTION")

    with st.form("data_entry_form"):
        form_data = {col: st.text_input(f"{col}") for col in columns}
        submitted = st.form_submit_button("Submit")

        if submitted:
            save_to_excel(form_data, LOCAL_FILE)
            st.json(form_data)

    # --- Step 3: Data Preview ---
    try:
        preview_df = pd.read_excel(LOCAL_FILE, engine="openpyxl")
        st.subheader("📊 Current Records in File")
        st.dataframe(preview_df)
    except Exception as e:
        st.warning(f"⚠️ Could not preview Excel file: {e}")

else:
    st.info("⬆️ Please upload your Excel or CSV file to begin generating your form.")
