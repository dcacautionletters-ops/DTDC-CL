import streamlit as st
import pandas as pd
import io

# Set page configuration
st.set_page_config(page_title="Student Report Generator", layout="wide")

st.title("Final Student Report Generator 🎓")
st.markdown("""
This app merges **Attendance Shortage** data with **Master Database** details and exports to **Excel**.
""")

# --- FILE UPLOAD SECTION ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Attendance Report")
    shortage_file = st.file_uploader("Upload Attendance Report (XLSX/CSV)", type=['xlsx', 'csv'], key="att")
    skip_rows = st.number_input("Attendance data starts on row (Instruction: 4):", min_value=1, value=4)

with col2:
    st.subheader("2. Master Database")
    master_file = st.file_uploader("Upload Master Database (XLSX/CSV)", type=['xlsx', 'csv'], key="mast")
    skip_rows_master = st.number_input("Master data starts on row:", min_value=1, value=1)

if shortage_file and master_file:
    try:
        # --- LOADING DATA ---
        if shortage_file.name.endswith('.csv'):
            df_att_raw = pd.read_csv(shortage_file, skiprows=skip_rows-1)
        else:
            df_att_raw = pd.read_excel(shortage_file, skiprows=skip_rows-1)

        if master_file.name.endswith('.csv'):
            df_mast_raw = pd.read_csv(master_file, skiprows=skip_rows_master-1)
        else:
            df_mast_raw = pd.read_excel(master_file, skiprows=skip_rows_master-1)

        if st.button("Process & Generate Excel Report"):
            
            # --- DATA EXTRACTION ---
            # Attendance: Roll No (B=1), Name (C=2), Batch (G=6)
            att_subset = df_att_raw.iloc[:, [1, 2, 6]].copy()
            att_subset.columns = ['Roll_No', 'Student_Name', 'Batch']

            # Master: Roll (B=1), Father (AD=29), Address (S=18), Father No (AT=45), Student No (AS=44)
            mast_subset = df_mast_raw.iloc[:, [1, 29, 18, 45, 44]].copy()
            mast_subset.columns = ['Roll_No', 'Father_Name', 'Address', 'Father_Phone', 'Student_Phone']

            # Data Cleaning: Remove spaces/convert to string for matching
            att_subset['Roll_No'] = att_subset['Roll_No'].astype(str).str.strip()
            mast_subset['Roll_No'] = mast_subset['Roll_No'].astype(str).str.strip()

            # --- MERGING ---
            merged_df = pd.merge(att_subset, mast_subset, on='Roll_No', how='left')

            # --- FINAL REPORT FORMATTING ---
            final_report = pd.DataFrame()
            final_report['Sl No'] = range(1, len(merged_df) + 1)
            final_report['Batch'] = merged_df['Batch']
            final_report['To name'] = merged_df['Father_Name'] # From Master AD
            final_report['Tracking ID'] = "" 
            final_report['Roll no'] = merged_df['Roll_No']
            final_report['Student name'] = merged_df['Student_Name'] # From Attendance C
            
            # Complete Address formula: Address (S) + Father No (AT) + Student No (AS)
            def format_address(row):
                addr = str(row['Address']) if pd.notnull(row['Address']) else ""
                f_phone = str(row['Father_Phone']) if pd.notnull(row['Father_Phone']) else ""
                s_phone = str(row['Student_Phone']) if pd.notnull(row['Student_Phone']) else ""
                return f"{addr} | Father No: {f_phone} | Student No: {s_phone}"

            final_report['complete address'] = merged_df.apply(format_address, axis=1)

            # --- EXCEL CONVERSION ---
            # We use an in-memory buffer to create the Excel file
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                final_report.to_excel(writer, index=False, sheet_name='Report')
                # No need to manually save, 'with' context handle it
            
            excel_data = buffer.getvalue()

            # --- DISPLAY & DOWNLOAD ---
            st.success(f"Processing Complete! {len(final_report)} records ready.")
            st.dataframe(final_report, hide_index=True)

            st.download_button(
                label="Download Final Report (Excel)",
                data=excel_data,
                file_name="Student_Attendance_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Error: {e}")
        st.info("Check if Column B contains Roll Numbers in both files.")
else:
    st.info("Please upload both files to generate the Excel report.")
