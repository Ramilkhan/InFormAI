import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="📋 Allocation Form", layout="wide")
st.title("📋 Dynamic Allocation Form System")

# Step 1: Upload existing Excel/CSV file
uploaded_file = st.file_uploader(
    "Upload your existing Excel/CSV file (with column headers)",
    type=["xlsx", "csv"]
)

# Local filename for saving updates
LOCAL_FILE = "uploaded_allocation.xlsx"

def save_to_excel(record, file_path=LOCAL_FILE):
    """
    Appends a record (dict) into an existing Excel file.
    Creates 'ID' column if not present.
    """
    # ✅ Read or create DataFrame
    if os.path.exists(file_path):
        df = pd.read_excel(file_path, engine="openpyxl")
    else:
        df = pd.DataFrame(columns=["ID"] + list(record.keys()))

    # ✅ Generate new ID
    new_id = len(df) + 1
    record_with_id = {"ID": new_id, **record}

    # ✅ Append and save
    new_df = pd.concat([df, pd.DataFrame([record_with_id])], ignore_index=True)
    new_df.to_excel(file_path, index=False)

    st.success(f"✅ Record saved successfully with ID {new_id}")

if uploaded_file is not None:
    # Save uploaded file locally for reuse
    with open(LOCAL_FILE, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Detect column headers
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, nrows=0)
    else:
        df = pd.read_excel(uploaded_file, engine='openpyxl', nrows=0)

    columns = df.columns.tolist()
    st.success(f"Detected columns: {columns}")

    # Step 2: Generate input form
    st.header("📝 Fill Allocation Form")

    with st.form("allocation_form"):
        form_data = {}
        for col in columns:
            form_data[col] = st.text_input(f"{col}")

        submitted = st.form_submit_button("Submit")

        if submitted:
            save_to_excel(form_data)
            st.json(form_data)

    # Option to preview saved data
    if os.path.exists(LOCAL_FILE):
        st.subheader("📂 Current Records in File")
        st.dataframe(pd.read_excel(LOCAL_FILE))

else:
    st.warning("⬆️ Please upload your existing Excel file first.")
