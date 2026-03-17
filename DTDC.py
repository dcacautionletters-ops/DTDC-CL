import streamlit as st
import pandas as pd

st.set_page_config(page_title="Student Report Generator", layout="wide")

st.title("Final Student Report Generator 🎓")

# --- FILE UPLOAD SECTION ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Consolidated Attendance Report")
    shortage_file = st.file_uploader("Upload Attendance Report", type=['xlsx', 'csv'])
    # Instruction: Data starts from 4th row (index 3 in Python)
    skip_rows = st.number_input("Start reading Attendance from row:", min_value=1, value=4)

with col2:
    st.subheader("2. Master Database")
    master_file = st.file_uploader("Upload Master Database", type=['xlsx', 'csv'])

if shortage_file and master_file:
    try:
        # --- LOADING ATTENDANCE DATA ---
        # Note: 'usecols' helps us target specific Excel columns (A=0, B=1, etc.)
        # Column B=1, C=2, G=6
        df_att = pd.read_excel(shortage_file, skiprows=skip_rows-1)
        
        # --- LOADING MASTER DATABASE ---
        df_mast = pd.read_excel(master_file)

        # Helper to convert Excel columns (A, B, C...) to indices for safety if headers change
        # B=1, F=5, S=18, AD=29, AS=44, AT=45
        
        st.success("Files loaded successfully!")

        if st.button("Process & Generate Report"):
            # 1. Extract necessary info from Attendance Report
            # Matching Roll No (Col B), Name (Col C), Batch (Col G)
            # We assume the user selects columns or we use index
            att_data = df_att.iloc[:, [1, 2, 6]] 
            att_data.columns = ['Roll_No', 'Student_Name', 'Batch']

            # 2. Extract necessary info from Master Database
            # Roll (Col B/Index 1), Father (AD/29), Address (S/18), 
            # Student No (AS/44), Father No (AT/45)
            mast_subset = df_mast.iloc[:, [1, 29, 18, 45, 44]]
            mast_subset.columns = ['Roll_No', 'Father_Name', 'Address', 'Father_Phone', 'Student_Phone']

            # 3. Merge the Data
            final_df = pd.merge(att_data, mast_subset, on='Roll_No', how='inner')

            # 4. Format the Output exactly as requested
            # Sequence: Sl No, Batch, To name, Tracking ID, Roll no, Student name, complete address
            output_report = pd.DataFrame()
            output_report['Sl No'] = range(1, len(final_df) + 1)
            output_report['Batch'] = final_df['Batch']
            output_report['To name'] = final_df['Father_Name']
            output_report['Tracking ID'] = "" # Placeholder for manual entry
            output_report['Roll no'] = final_df['Roll_No']
            output_report['Student name'] = final_df['Student_Name']
            
            # Combine Address and Phone Numbers for a "Complete Address" field
            output_report['Complete Address'] = (
                final_df['Address'].astype(str) + 
                " | Father No: " + final_df['Father_Phone'].astype(str) + 
                " | Student No: " + final_df['Student_Phone'].astype(str)
            )

            st.subheader("Preview of New Report")
            st.dataframe(output_report)

            # 5. Export
            csv = output_report.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Final Report",
                data=csv,
                file_name="Final_Student_Report.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.info("Check if your columns match the expected positions (B, C, G, etc.)")
else:
    st.info("Please upload both files to generate the report.")
