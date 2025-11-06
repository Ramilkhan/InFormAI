import streamlit as st
import pandas as pd
import os
from io import BytesIO

st.set_page_config(page_title="📋 Allocation Form", layout="wide")
st.title("📋 Dynamic Allocation Form System")

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

# Step 1: Upload existing Excel/CSV file
uploaded_file = st.file_uploader(
    "📂 Upload your existing Excel/CSV file (with headers)",
    type=["xlsx", "csv"]
)

if uploaded_file is not None:
    # Derive local filename dynamically
    base_name = os.path.splitext(uploaded_file.name)[0]
    LOCAL_FILE = f"{base_name}.xlsx"

    # Save uploaded file properly
    file_bytes = uploaded_file.read()

    if uploaded_file.name.endswith(".csv"):
        # Convert CSV → Excel
        df_csv = pd.read_csv(BytesIO(file_bytes))
        df_csv.to_excel(LOCAL_FILE, index=False, engine="openpyxl")
    else:
        # Save Excel file directly
        with open(LOCAL_FILE, "wb") as f:
            f.write(file_bytes)

    # Load headers for form
    df = pd.read_excel(LOCAL_FILE, engine="openpyxl", nrows=0)
    columns = df.columns.tolist()

    st.success(f"✅ Detected columns: {columns}")
    st.info(f"📁 All new data will be saved to: **{LOCAL_FILE}**")

    # Step 2: Dynamic form
    st.header("📝 Fill Allocation Form")

    with st.form("allocation_form"):
        form_data = {col: st.text_input(f"{col}") for col in columns}
        submitted = st.form_submit_button("Submit")

        if submitted:
            save_to_excel(form_data, LOCAL_FILE)
            st.json(form_data)

    # Step 3: Show current records
    try:
        preview_df = pd.read_excel(LOCAL_FILE, engine="openpyxl")
        st.subheader("📊 Current Records in File")
        st.dataframe(preview_df)
    except Exception as e:
        st.warning(f"⚠️ Could not preview Excel file: {e}")

else:
    st.info("⬆️ Please upload your Excel or CSV file to begin.")
