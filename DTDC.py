import streamlit as st
import pandas as pd

# Set page configuration
st.set_page_config(page_title="Student Report Generator", layout="wide")

st.title("Final Student Report Generator 🎓")
st.markdown("""
This app merges **Attendance Shortage** data with **Master Database** details.
- **Attendance:** Uses Roll No (Col B), Name (Col C), and Batch (Col G).
- **Master:** Matches Roll No (Col B) to fetch Father Name (Col AD), Address (Col S), and Phone Numbers (Col AT, AS).
""")

# --- FILE UPLOAD SECTION ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Attendance Report")
    shortage_file = st.file_uploader("Upload Attendance Report (XLSX/CSV)", type=['xlsx', 'csv'], key="att")
    # Flexibility for data starting row
    skip_rows = st.number_input("Attendance data starts on row (usually 4):", min_value=1, value=4)

with col2:
    st.subheader("2. Master Database")
    master_file = st.file_uploader("Upload Master Database (XLSX/CSV)", type=['xlsx', 'csv'], key="mast")
    # Usually master data starts at row 1 (no skipping needed typically)
    skip_rows_master = st.number_input("Master data starts on row:", min_value=1, value=1)

if shortage_file and master_file:
    try:
        # --- LOADING ATTENDANCE DATA ---
        if shortage_file.name.endswith('.csv'):
            df_att_raw = pd.read_csv(shortage_file, skiprows=skip_rows-1)
        else:
            df_att_raw = pd.read_excel(shortage_file, skiprows=skip_rows-1)

        # --- LOADING MASTER DATABASE ---
        if master_file.name.endswith('.csv'):
            df_mast_raw = pd.read_csv(master_file, skiprows=skip_rows_master-1)
        else:
            df_mast_raw = pd.read_excel(master_file, skiprows=skip_rows_master-1)

        if st.button("Process & Generate Final Report"):
            
            # --- DATA EXTRACTION (Using 0-based indexing for Excel Columns) ---
            # Attendance: B=1, C=2, G=6
            # We use .iloc to pick specific columns regardless of their header names
            att_subset = df_att_raw.iloc[:, [1, 2, 6]].copy()
            att_subset.columns = ['Roll_No', 'Student_Name', 'Batch']

            # Master: B=1, S=18, AD=29, AS=44, AT=45
            # Note: Indexing A=0, B=1 ... S=18, AD=29, AS=44, AT=45
            mast_subset = df_mast_raw.iloc[:, [1, 29, 18, 45, 44]].copy()
            mast_subset.columns = ['Roll_No', 'Father_Name', 'Address', 'Father_Phone', 'Student_Phone']

            # Convert Roll Numbers to string and strip spaces to ensure a perfect match
            att_subset['Roll_No'] = att_subset['Roll_No'].astype(str).str.strip()
            mast_subset['Roll_No'] = mast_subset['Roll_No'].astype(str).str.strip()

            # --- MERGING ---
            # Match Roll No from Attendance with Roll No from Master
            merged_df = pd.merge(att_subset, mast_subset, on='Roll_No', how='left')

            # --- FINAL REPORT FORMATTING ---
            # Columns: Sl No, Batch, To name, Tracking ID, Roll no, Student name, complete address
            final_report = pd.DataFrame()
            final_report['Sl No'] = range(1, len(merged_df) + 1)
            final_report['Batch'] = merged_df['Batch']
            final_report['To name'] = merged_df['Father_Name']
            final_report['Tracking ID'] = ""  # Empty as requested
            final_report['Roll no'] = merged_df['Roll_No']
            final_report['Student name'] = merged_df['Student_Name']
            
            # Building the complete address string: Address + Father No + Student No
            def format_address(row):
                addr = str(row['Address']) if pd.notnull(row['Address']) else ""
                f_phone = str(row['Father_Phone']) if pd.notnull(row['Father_Phone']) else "N/A"
                s_phone = str(row['Student_Phone']) if pd.notnull(row['Student_Phone']) else "N/A"
                return f"{addr} | Father No: {f_phone} | Student No: {s_phone}"

            final_report['complete address'] = merged_df.apply(format_address, axis=1)

            # --- DISPLAY & DOWNLOAD ---
            st.success(f"Processing Complete! Found {len(final_report)} matching records.")
            
            # hide_index=True prevents the "double serial number" in the browser preview
            st.subheader("Preview (Showing first 50 rows)")
            st.dataframe(final_report.head(50), hide_index=True)

            # CSV Download - index=False prevents the extra serial number in the file
            csv = final_report.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Final Report as CSV",
                data=csv,
                file_name="Consolidated_Student_Contacts.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"An error occurred during processing: {e}")
        st.info("Tip: Ensure both files have a 'Roll No' in Column B.")
else:
    st.info("Please upload both the Attendance Report and the Master Database to begin.")
