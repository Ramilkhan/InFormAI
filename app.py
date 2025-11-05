import streamlit as st
import pandas as pd
import os

# Output Excel file
OUTPUT_FILE = "allocation_records.xlsx"

st.set_page_config(page_title="Excel Form Generator", page_icon="📋", layout="centered")

st.title("📋 Excel-Based Form Entry")
st.write("Upload an Excel or CSV file to automatically create a form for data entry.")

# --- Step 1: Upload file ---
uploaded_file = st.file_uploader("Upload Excel or CSV file", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    # Detect file type and read columns
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, nrows=0)
    else:
        df = pd.read_excel(uploaded_file, nrows=0)

    columns = df.columns.tolist()
    st.success(f"Detected columns: {columns}")

    st.divider()
    st.subheader("Fill in the details below:")

    # --- Step 2: Dynamic form creation ---
    inputs = {}
    with st.form("data_entry_form"):
        for col in columns:
            # Basic text input for all columns (can be extended later)
            inputs[col] = st.text_input(f"{col}", placeholder=f"Enter {col}")
        submitted = st.form_submit_button("Submit")

    # --- Step 3: Save data ---
    if submitted:
        # Check if output file exists
        if os.path.exists(OUTPUT_FILE):
            records_df = pd.read_excel(OUTPUT_FILE, engine='openpyxl')
        else:
            records_df = pd.DataFrame(columns=['ID'] + columns)

        # Generate new ID
        new_id = len(records_df) + 1
        record_with_id = {'ID': new_id, **{col: inputs[col] for col in columns}}

        # Convert to DataFrame and append
        record_df = pd.DataFrame([record_with_id])
        records_df = pd.concat([records_df, record_df], ignore_index=True)

        # Save to Excel
        records_df.to_excel(OUTPUT_FILE, index=False)

        st.success(f"✅ Record saved successfully with ID {new_id}")
        st.json(record_with_id)

        # Optional download button
        with open(OUTPUT_FILE, "rb") as f:
            st.download_button(
                label="📥 Download Updated Excel",
                data=f,
                file_name=OUTPUT_FILE,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

else:
    st.info("👆 Please upload an Excel or CSV file to begin.")
