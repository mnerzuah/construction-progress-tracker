# ============================================================
# Developed by Michael N. Erzuah
# CONSTRUCTION PROGRESS TRACKER - STREAMLIT MVP
# Version 0.6
# ============================================================

import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Construction Progress Tracker",
    layout="wide"
)

# ============================================================
# 1. REQUIRED AND OPTIONAL SCHEDULE FIELDS
# ============================================================

REQUIRED_COLUMNS = [
    "Activity ID",
    "WBS location",
    "Activity Name",
    "Discipline",
    "Package",
    "Start Date",
    "Finish Date"
]

OPTIONAL_COLUMNS = ["Critical"]

# ============================================================
# 2. COLUMN ALIASES FOR AUTO-DETECTION
# ============================================================

COLUMN_ALIASES = {
    "Activity ID": ["Activity ID", "ActivityID", "Activity Id", "Task ID", "ID", "Activity Code"],
    "WBS location": ["WBS location", "WBS Location", "WBS", "Location", "Area", "Zone", "Room", "Floor"],
    "Activity Name": ["Activity Name", "Task Name", "Name", "Activity", "Description", "Activity Description"],
    "Discipline": ["Discipline", "Trade", "Scope", "Workstream"],
    "Package": ["Package", "Work Package", "Bid Package", "Trade Package"],
    "Start Date": ["Start Date", "Start", "Planned Start", "Baseline Start", "Early Start"],
    "Finish Date": ["Finish Date", "Finish", "End Date", "Planned Finish", "Baseline Finish", "Early Finish"],
    "Critical": ["Critical", "Critical Path", "Is Critical"]
}

# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def normalize_column_name(name):
    return str(name).strip().lower().replace("_", " ")


def auto_detect_column(uploaded_columns, target_field):
    normalized_uploaded = {
        normalize_column_name(col): col
        for col in uploaded_columns
    }

    for alias in COLUMN_ALIASES.get(target_field, []):
        normalized_alias = normalize_column_name(alias)

        if normalized_alias in normalized_uploaded:
            return normalized_uploaded[normalized_alias]

    return None


# ============================================================
# 4. APP TITLE AND PROJECT INPUT
# ============================================================

st.title("Construction Progress Tracker")
st.write("Schedule-based construction progress tracking MVP")

project_name = st.text_input("Project Name")

if project_name:
    st.success(f"Project Loaded: {project_name}")

# ============================================================
# 5. UPLOAD REQUIREMENTS NOTE
# ============================================================

st.info(
    """
    **Schedule upload requirement:** Your schedule must contain the following mandatory fields,
    either with the exact names or with columns that can be mapped manually:

    - Activity ID
    - WBS location / Location / Area
    - Activity Name
    - Discipline / Trade
    - Package / Work Package
    - Start Date
    - Finish Date

    Optional field:

    - Critical
    """
)

# ============================================================
# 6. FILE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "Upload Schedule File",
    type=["xlsx", "xls", "csv"]
)

# ============================================================
# 7. MAIN APP LOGIC
# ============================================================

if uploaded_file is not None:

    try:
        if uploaded_file.name.lower().endswith(".csv"):
            raw_schedule = pd.read_csv(uploaded_file)
        else:
            raw_schedule = pd.read_excel(uploaded_file)

        st.success("Schedule uploaded successfully")

        # ====================================================
        # 8. AUTO-DETECT COLUMNS
        # ====================================================

        uploaded_columns = list(raw_schedule.columns)

        detected_mapping = {
            field: auto_detect_column(uploaded_columns, field)
            for field in REQUIRED_COLUMNS + OPTIONAL_COLUMNS
        }

        all_required_detected = all(
            detected_mapping[field] is not None
            for field in REQUIRED_COLUMNS
        )

        # ====================================================
        # 9. IF AUTO-DETECTED, SKIP RAW PREVIEW AND MAPPER
        # ====================================================

        if all_required_detected:
            st.success(
                "Required fields were auto-detected successfully. Preview and field mapping skipped."
            )

            final_mapping = detected_mapping.copy()

        # ====================================================
        # 10. IF NOT AUTO-DETECTED, SHOW FULL PREVIEW AND MAPPER
        # ====================================================

        else:
            st.warning(
                "Some required fields were not auto-detected. Review the full schedule preview and map the fields manually."
            )

            st.subheader("Original Schedule Preview")

            st.dataframe(
                raw_schedule,
                use_container_width=True
            )

            st.subheader("Map Schedule Fields")

            st.write(
                "Select the schedule column that corresponds to each required app field."
            )

            column_choices_required = ["-- Select Column --"] + uploaded_columns
            column_choices_optional = ["-- Not Provided --"] + uploaded_columns

            final_mapping = {}

            for field in REQUIRED_COLUMNS:
                detected_col = detected_mapping.get(field)

                if detected_col in uploaded_columns:
                    default_index = column_choices_required.index(detected_col)
                else:
                    default_index = 0

                final_mapping[field] = st.selectbox(
                    f"{field} *",
                    column_choices_required,
                    index=default_index,
                    key=f"map_{field}"
                )

            for field in OPTIONAL_COLUMNS:
                detected_col = detected_mapping.get(field)

                if detected_col in uploaded_columns:
                    default_index = column_choices_optional.index(detected_col)
                else:
                    default_index = 0

                final_mapping[field] = st.selectbox(
                    f"{field} (optional)",
                    column_choices_optional,
                    index=default_index,
                    key=f"map_{field}"
                )

            missing_mapped_fields = [
                field for field in REQUIRED_COLUMNS
                if final_mapping[field] == "-- Select Column --"
            ]

            if missing_mapped_fields:
                st.warning("Map all required fields before the schedule can be validated.")

                for field in missing_mapped_fields:
                    st.write(f"- {field}")

                st.stop()

        # ====================================================
        # 11. BUILD STANDARDIZED SCHEDULE
        # ====================================================

        schedule = pd.DataFrame()

        for field in REQUIRED_COLUMNS:
            schedule[field] = raw_schedule[final_mapping[field]]

        for field in OPTIONAL_COLUMNS:
            if final_mapping.get(field) in [None, "-- Not Provided --"]:
                schedule[field] = ""
            else:
                schedule[field] = raw_schedule[final_mapping[field]]

        # ====================================================
        # 12. DATE CLEANING
        # ====================================================

        schedule["Start Date"] = pd.to_datetime(
            schedule["Start Date"],
            errors="coerce"
        )

        schedule["Finish Date"] = pd.to_datetime(
            schedule["Finish Date"],
            errors="coerce"
        )

        # ====================================================
        # 13. REMOVE INVALID ROWS
        # ====================================================

        schedule = schedule.dropna(
            subset=REQUIRED_COLUMNS
        )

        if schedule.empty:
            st.error(
                "No valid activities found after cleaning the schedule. Check your field mapping and date columns."
            )
            st.stop()

        st.success("Schedule validated successfully")

        # ====================================================
        # 14. SCHEDULE SUMMARY
        # ====================================================

        st.subheader("Schedule Summary")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Activities", len(schedule))
        col2.metric("Disciplines", schedule["Discipline"].nunique())
        col3.metric("Packages", schedule["Package"].nunique())
        col4.metric("Locations / WBS Groups", schedule["WBS location"].nunique())

        # ====================================================
        # 15. FILTER VALIDATED SCHEDULE
        # ====================================================

        st.subheader("Filter Validated Schedule")

        discipline_filter = st.multiselect(
            "Filter by Discipline",
            sorted(schedule["Discipline"].dropna().astype(str).unique())
        )

        package_filter = st.multiselect(
            "Filter by Package",
            sorted(schedule["Package"].dropna().astype(str).unique())
        )

        location_filter = st.multiselect(
            "Filter by Location / WBS",
            sorted(schedule["WBS location"].dropna().astype(str).unique())
        )

        min_start_date = schedule["Start Date"].min().date()
        max_finish_date = schedule["Finish Date"].max().date()

        date_col1, date_col2 = st.columns(2)

        with date_col1:
            start_date_filter = st.date_input(
                "Start Date From",
                value=min_start_date
            )

        with date_col2:
            finish_date_filter = st.date_input(
                "Finish Date To",
                value=max_finish_date
            )

        filtered_schedule = schedule.copy()

        if discipline_filter:
            filtered_schedule = filtered_schedule[
                filtered_schedule["Discipline"].astype(str).isin(discipline_filter)
            ]

        if package_filter:
            filtered_schedule = filtered_schedule[
                filtered_schedule["Package"].astype(str).isin(package_filter)
            ]

        if location_filter:
            filtered_schedule = filtered_schedule[
                filtered_schedule["WBS location"].astype(str).isin(location_filter)
            ]

        filtered_schedule = filtered_schedule[
            (filtered_schedule["Start Date"].dt.date >= start_date_filter)
            &
            (filtered_schedule["Finish Date"].dt.date <= finish_date_filter)
        ]

        # ====================================================
        # 16. DISPLAY VALIDATED SCHEDULE
        # ====================================================

        st.write(f"Filtered Activities: {len(filtered_schedule)}")

        st.subheader("Validated Schedule")

        st.dataframe(
            filtered_schedule,
            use_container_width=True
        )

        # ====================================================
        # 17. DOWNLOAD FILTERED SCHEDULE
        # ====================================================

        filtered_csv = filtered_schedule.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Filtered Schedule",
            data=filtered_csv,
            file_name="filtered_validated_schedule.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error("Could not read schedule file")
        st.write(e)

else:
    st.info("Upload an Excel or CSV schedule file to begin.")
