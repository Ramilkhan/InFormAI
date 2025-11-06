import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Excel Form Editor", page_icon="📋", layout="centered")

st.title("📋 Excel-Based Form & Editor")
st.write("Upload an Excel or CSV file to create and edit records dynamically.")

# --- Step 1: Upload file ---
uploaded_file = st.file_uploader("Upload Excel or CSV file", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    # Read uploaded file into DataFrame
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file, engine="openpyxl")

    # If file has no ID column, add one
    if "ID" not in df.columns:
        df.insert(0, "ID", range(1, len(df) + 1))

    columns = [c for c in df.columns if c != "ID"]
    st.success(f"Detected columns: {columns}")

    st.divider()

    # --- Mode Selection ---
    mode = st.radio("Select Mode", ["➕ Add New Record", "✏️ Edit Existing Record"], horizontal=True)

    if mode == "➕ Add New Record":
        st.subheader("Add New Record")

        with st.form("add_form"):
            inputs = {col: st.text_input(f"{col}", placeholder=f"Enter {col}") for col in columns}
            submitted = st.form_submit_button("Submit")

        if submitted:
            new_id = df["ID"].max() + 1 if not df.empty else 1
            record = {"ID": new_id, **{col: inputs[col] for col in columns}}
            df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)

            # Save changes to same file in memory
            output = io.BytesIO()
            if uploaded_file.name.endswith(".csv"):
                df.to_csv(output, index=False)
                mime = "text/csv"
            else:
                df.to_excel(output, index=False, engine="openpyxl")
                mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            st.success(f"✅ Record added successfully with ID {new_id}")
            st.json(record)

            st.download_button(
                label="📥 Download Updated File",
                data=output.getvalue(),
                file_name=uploaded_file.name,
                mime=mime,
            )

    elif mode == "✏️ Edit Existing Record":
        st.subheader("Edit Existing Record")

        record_id = st.number_input("Enter Record ID to Edit", min_value=1, step=1)

        # Check if ID exists
        if record_id in df["ID"].values:
            record = df.loc[df["ID"] == record_id].iloc[0].to_dict()

            with st.form("edit_form"):
                inputs = {
                    col: st.text_input(f"{col}", value=str(record[col]) if pd.notna(record[col]) else "")
                    for col in columns
                }
                submitted_edit = st.form_submit_button("Save Changes")

            if submitted_edit:
                for col in columns:
                    df.loc[df["ID"] == record_id, col] = inputs[col]

                # Save to memory
                output = io.BytesIO()
                if uploaded_file.name.endswith(".csv"):
                    df.to_csv(output, index=False)
                    mime = "text/csv"
                else:
                    df.to_excel(output, index=False, engine="openpyxl")
                    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                st.success(f"✅ Record with ID {record_id} updated successfully!")
                st.json({**{"ID": record_id}, **inputs})

                st.download_button(
                    label="📥 Download Updated File",
                    data=output.getvalue(),
                    file_name=uploaded_file.name,
                    mime=mime,
                )
        else:
            st.warning("⚠️ Record ID not found in the uploaded file.")

else:
    st.info("👆 Please upload an Excel or CSV file to begin.")
