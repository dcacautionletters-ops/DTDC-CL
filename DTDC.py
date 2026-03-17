import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Caution Letter Generator", layout="wide")

st.title("Caution Letter Data Generator ✉️")
st.markdown("This version removes duplicates to ensure **one row per student**.")

# --- FILE UPLOAD SECTION ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Attendance Report")
    shortage_file = st.file_uploader("Upload Attendance Report", type=['xlsx', 'csv'], key="att")
    skip_rows = st.number_input("Attendance data starts on row:", min_value=1, value=4)

with col2:
    st.subheader("2. Master Database")
    master_file = st.file_uploader("Upload Master Database", type=['xlsx', 'csv'], key="mast")

if shortage_file and master_file:
    try:
        # Load Attendance
        if shortage_file.name.endswith('.csv'):
            df_att_raw = pd.read_csv(shortage_file, skiprows=skip_rows-1)
        else:
            df_att_raw = pd.read_excel(shortage_file, skiprows=skip_rows-1)

        # Load Master
        if master_file.name.endswith('.csv'):
            df_mast_raw = pd.read_csv(master_file)
        else:
            df_mast_raw = pd.read_excel(master_file)

        if st.button("Generate Unique Caution List"):
            
            # 1. Extraction (Using your specific columns)
            # Att: B=1, C=2, G=6
            att_subset = df_att_raw.iloc[:, [1, 2, 6]].copy()
            att_subset.columns = ['Roll_No', 'Student_Name', 'Batch']

            # 2. REMOVE DUPLICATES HERE
            # This keeps only the first time a Roll Number appears
            att_subset = att_subset.drop_duplicates(subset=['Roll_No'], keep='first')

            # 3. Extraction Master: B=1, AD=29, S=18, AT=45, AS=44
            mast_subset = df_mast_raw.iloc[:, [1, 29, 18, 45, 44]].copy()
            mast_subset.columns = ['Roll_No', 'Father_Name', 'Address', 'Father_Phone', 'Student_Phone']

            # Clean Roll Nos for matching
            att_subset['Roll_No'] = att_subset['Roll_No'].astype(str).str.strip()
            mast_subset['Roll_No'] = mast_subset['Roll_No'].astype(str).str.strip()

            # 4. Merge
            merged_df = pd.merge(att_subset, mast_subset, on='Roll_No', how='left')

            # 5. Final Formatting
            final_report = pd.DataFrame()
            final_report['Sl No'] = range(1, len(merged_df) + 1)
            final_report['Batch'] = merged_df['Batch']
            final_report['To name'] = merged_df['Father_Name']
            final_report['Tracking ID'] = "" 
            final_report['Roll no'] = merged_df['Roll_No']
            final_report['Student name'] = merged_df['Student_Name']
            
            def format_address(row):
                addr = str(row['Address']) if pd.notnull(row['Address']) else ""
                f_phone = str(row['Father_Phone']) if pd.notnull(row['Father_Phone']) else ""
                s_phone = str(row['Student_Phone']) if pd.notnull(row['Student_Phone']) else ""
                return f"{addr} | Father No: {f_phone} | Student No: {s_phone}"

            final_report['complete address'] = merged_df.apply(format_address, axis=1)

            # 6. Excel Export Logic
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                final_report.to_excel(writer, index=False, sheet_name='Caution_List')
            excel_data = buffer.getvalue()

            # 7. Results
            st.success(f"Cleaned! Total unique students found: {len(final_report)}")
            st.dataframe(final_report, hide_index=True)

            st.download_button(
                label="Download Excel (Unique Students)",
                data=excel_data,
                file_name="Caution_Letter_Data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Something went wrong: {e}")
else:
    st.info("Upload files to generate the caution letter list.")
