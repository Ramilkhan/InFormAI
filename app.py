!pip install pandas openpyxl ipywidgets --quiet

import pandas as pd
import ipywidgets as widgets
from IPython.display import display, clear_output
from google.colab import files
import os
import datetime

# File to store submitted records
output_file = "allocation_records.xlsx"

# Step 1: Upload Excel file with column headers
uploaded = files.upload()
for file_name in uploaded.keys():
    excel_file = file_name

# Read column headers
df = pd.read_excel(excel_file, engine='openpyxl', nrows=0)
columns = df.columns.tolist()
print(f"Detected columns: {columns}")

# Step 2: Create dynamic form widgets
inputs = {}
for col in columns:
    inputs[col] = widgets.Text(
        description=col,
        placeholder=f'Enter {col}',
        layout=widgets.Layout(width='50%')
    )

# Step 3: Display the form
form_items = [inputs[col] for col in columns]
submit_btn = widgets.Button(description="Submit", button_style='success')
output = widgets.Output()

# Step 4: Function to save data to Excel
def save_to_excel(record):
    # Check if file exists
    if os.path.exists(output_file):
        records_df = pd.read_excel(output_file, engine='openpyxl')
    else:
        # Initialize empty DataFrame with columns + ID
        records_df = pd.DataFrame(columns=['ID'] + columns)

    # Generate new ID
    new_id = len(records_df) + 1
    record_with_id = {'ID': new_id, **record}

    # Append and save
    records_df = records_df.append(record_with_id, ignore_index=True)
    records_df.to_excel(output_file, index=False)
    print(f"Record saved successfully with ID {new_id}")

# Step 5: Handle form submission
def on_submit(b):
    with output:
        clear_output()
        record = {col: inputs[col].value for col in columns}
        save_to_excel(record)
        print("Form submitted successfully!")
        display(record)

submit_btn.on_click(on_submit)
display(*form_items, submit_btn, output)
