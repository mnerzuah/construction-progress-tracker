# ============================================================
# Developed by Michael N. Erzuah
# CONSTRUCTION PROGRESS TRACKER - STREAMLIT MVP
# Version 0.4
#
# Current features:
# 1. Project name input
# 2. Schedule upload
# 3. Mandatory field notice
# 4. Auto-detect schedule fields
# 5. Manual field mapping if auto-detection fails
# 6. Optional Critical column handling
# 7. Schedule cleaning
# 8. Schedule summary metrics
# 9. Validated schedule filtering
# ============================================================


# ============================================================
# 1. IMPORT LIBRARIES
# ============================================================

import streamlit as st
import pandas as pd


# ============================================================
# 2. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Construction Progress Tracker",
    layout="wide"
)


# ============================================================
# 3. REQUIRED AND OPTIONAL SCHEDULE FIELDS
# Update this section if your required schedule template changes.
# ============================================================

REQUIRED_COLUMNS = [
    "Activity ID",
    "WBS location",
    "Activity Name",
    "Discipline",
    "Package",
    "Start",
    "Finish"
]

OPTIONAL_COLUMNS = [
    "Critical"
]


# ============================================================
# 4. COLUMN NAME ALIASES FOR AUTO-DETECTION
# Add more possible schedule column names here over time.
# ============================================================

COLUMN_ALIASES = {
    "Activity ID": [
        "Activity ID", "ActivityID", "Activity Id", "Task ID", "TaskID",
        "ID", "Activity Code", "Act ID"
    ],
    "WBS location": [
        "WBS location", "WBS Location", "WBS", "Location", "Area",
        "Zone", "Room", "Floor", "Work Area"
    ],
    "Activity Name": [
        "Activity Name", "Task Name", "Name", "Activity", "Description",
        "Activity Description", "Task Description"
    ],
    "Discipline": [
        "Discipline", "Trade", "Scope", "Workstream"
    ],
    "Package": [
        "Package", "Work Package", "Bid Package", "Trade Package",
        "Subcontract Package"
    ],
    "Start": [
        "Start", "Start Date", "Planned Start", "Baseline Start",
        "Early Start"
    ],
    "Finish": [
        "Finish", "Finish Date", "End Date", "Planned Finish",
        "Baseline Finish", "Early Finish"
    ],
    "Critical": [
        "Critical", "Critical Path", "Is Critical"
    ]
}


# ============================================================
# 5. HELPER FUNCTION - NORMALIZE COLUMN NAMES
# Makes matching less sensitive to spaces and capitalization.
# ============================================================

def normalize_column_name(name):
    return str(name).strip().lower().replace("_", " ")


# ============================================================
# 6. HELPER FUNCTION - AUTO-DETECT COLUMN
# Tries to match required app fields to uploaded schedule headings.
# ============================================================

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
# 7. APP TITLE AND INTRO
# ============================================================

st.title("Construction Progress Tracker")

st.write(
    "Schedule-based construction progress tracking MVP"
)


# ============================================================
# 8. PROJECT NAME INPUT
# Later this will become project creation / project selection.
# ============================================================

project_name = st.text_input(
    "Project Name"
)

if project_name:
    st.success(
        f"Project Loaded: {project_name}"
    )


# ============================================================
# 9. SCHEDULE UPLOAD REQUIREMENTS NOTE
# This tells users what their schedule must contain.
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
    - Start
    - Finish

    Optional field:

    - Critical
    """
)


# ============================================================
# 10. SCHEDULE FILE UPLOAD
# User uploads Excel or CSV schedule export.
# ============================================================

uploaded_file = st.file_uploader(
    "Upload Schedule File",
    type=["xlsx", "xls", "csv"]
)


# ============================================================
# 11. READ UPLOADED SCHEDULE
# This block reads the uploaded file into a Pandas DataFrame.
# ============================================================

if uploaded_file is not None:

    try:
        if uploaded_file.name.lower().endswith(".csv"):
            raw_schedule = pd.read_csv(uploaded_file)
        else:
            raw_schedule = pd.read_excel(uploaded_file)

        st.success("Schedule uploaded successfully")


        # ====================================================
        # 12. ORIGINAL SCHEDULE PREVIEW
        # Shows the raw uploaded schedule before validation.
        # ====================================================

        st.subheader("Original Schedule Preview")

        st.dataframe(
            raw_schedule.head(20),
            use_container_width=True
        )


        # ====================================================
        # 13. AUTO-DETECT SCHEDULE COLUMNS
        # Attempts to find matching columns automatically.
        # ====================================================

        uploaded_columns = list(raw_schedule.columns)

        detected_mapping = {}

        for field in REQUIRED_COLUMNS + OPTIONAL_COLUMNS:
            detected_mapping[field] = auto_detect_column(
                uploaded_columns,
                field
            )


        # ====================================================
        # 14. MANUAL FIELD MAPPING
        # Users confirm or manually map fields.
        # ====================================================

        st.subheader("Map Schedule Fields")

        st.write(
            "Confirm the detected columns below. If a field was not detected, select the correct schedule column manually."
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


        # ====================================================
        # 15. VALIDATE MANUAL MAPPING
        # Required fields must all be mapped before proceeding.
        # ====================================================

        missing_mapped_fields = [
            field for field in REQUIRED_COLUMNS
            if final_mapping[field] == "-- Select Column --"
        ]

        if missing_mapped_fields:
            st.warning(
                "Map all required fields before the schedule can be validated."
            )

            for field in missing_mapped_fields:
                st.write(f"- {field}")

            st.stop()


        # ====================================================
        # 16. BUILD STANDARDIZED SCHEDULE
        # Converts user-selected columns into app-required names.
        # ====================================================

        schedule = pd.DataFrame()

        for field in REQUIRED_COLUMNS:
            schedule[field] = raw_schedule[final_mapping[field]]

        for field in OPTIONAL_COLUMNS:
            if final_mapping[field] == "-- Not Provided --":
                schedule[field] = ""
            else:
                schedule[field] = raw_schedule[final_mapping[field]]


        # ====================================================
        # 17. DATE CLEANING
        # Converts Start and Finish fields into true dates.
        # ====================================================

        schedule["Start"] = pd.to_datetime(
            schedule["Start"],
            errors="coerce"
        )

        schedule["Finish"] = pd.to_datetime(
            schedule["Finish"],
            errors="coerce"
        )


        # ====================================================
        # 18. REMOVE INVALID ROWS
        # Rows missing required information are removed.
        # ====================================================

        schedule = schedule.dropna(
            subset=REQUIRED_COLUMNS
        )


        # ====================================================
        # 19. EMPTY SCHEDULE CHECK
        # Prevents app from continuing if everything was removed.
        # ====================================================

        if schedule.empty:
            st.error(
                "No valid activities found after cleaning the schedule. Check your field mapping and date columns."
            )
            st.stop()


        # ====================================================
        # 20. VALIDATION SUCCESS MESSAGE
        # Confirms the schedule is ready for filtering.
        # ====================================================

        st.success("Schedule validated successfully")


        # ====================================================
        # 21. SCHEDULE SUMMARY METRICS
        # High-level counts from the validated schedule.
        # ====================================================

        st.subheader("Schedule Summary")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Activities", len(schedule))
        col2.metric("Disciplines", schedule["Discipline"].nunique())
        col3.metric("Packages", schedule["Package"].nunique())
        col4.metric("Locations / WBS Groups", schedule["WBS location"].nunique())


        # ====================================================
        # 22. FILTER SECTION HEADER
        # Users can narrow the validated schedule.
        # ====================================================

        st.subheader("Filter Validated Schedule")


        # ====================================================
        # 23. DISCIPLINE FILTER
        # Allows one or more disciplines to be selected.
        # ====================================================

        discipline_options = sorted(
            schedule["Discipline"].dropna().astype(str).unique()
        )

        discipline_filter = st.multiselect(
            "Filter by Discipline",
            discipline_options
        )


        # ====================================================
        # 24. PACKAGE FILTER
        # Allows one or more packages to be selected.
        # ====================================================

        package_options = sorted(
            schedule["Package"].dropna().astype(str).unique()
        )

        package_filter = st.multiselect(
            "Filter by Package",
            package_options
        )


        # ====================================================
        # 25. LOCATION / WBS FILTER
        # This is not always a room.
        # ====================================================

        location_options = sorted(
            schedule["WBS location"].dropna().astype(str).unique()
        )

        location_filter = st.multiselect(
            "Filter by Location / WBS",
            location_options
        )


        # ====================================================
        # 26. DATE FILTERS
        # User controls schedule window by Start and Finish dates.
        # ====================================================

        min_start_date = schedule["Start"].min().date()
        max_finish_date = schedule["Finish"].max().date()

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


        # ====================================================
        # 27. APPLY VALIDATED SCHEDULE FILTERS
        # This section applies all selected filters.
        # ====================================================

        filtered_schedule = schedule.copy()

        if discipline_filter:
            filtered_schedule = filtered_schedule[
                filtered_schedule["Discipline"]
                .astype(str)
                .isin(discipline_filter)
            ]

        if package_filter:
            filtered_schedule = filtered_schedule[
                filtered_schedule["Package"]
                .astype(str)
                .isin(package_filter)
            ]

        if location_filter:
            filtered_schedule = filtered_schedule[
                filtered_schedule["WBS location"]
                .astype(str)
                .isin(location_filter)
            ]

        filtered_schedule = filtered_schedule[
            (
                filtered_schedule["Start"].dt.date >= start_date_filter
            )
            &
            (
                filtered_schedule["Finish"].dt.date <= finish_date_filter
            )
        ]


        # ====================================================
        # 28. FILTERED RESULTS SUMMARY
        # Shows how many activities remain after filtering.
        # ====================================================

        st.write(
            f"Filtered Activities: {len(filtered_schedule)}"
        )


        # ====================================================
        # 29. FILTERED VALIDATED SCHEDULE TABLE
        # Main table shown to user.
        # ====================================================

        st.subheader("Validated Schedule")

        st.dataframe(
            filtered_schedule,
            use_container_width=True
        )


        # ====================================================
        # 30. DOWNLOAD FILTERED SCHEDULE
        # Allows user to export the filtered results.
        # ====================================================

        filtered_csv = filtered_schedule.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="Download Filtered Schedule",
            data=filtered_csv,
            file_name="filtered_validated_schedule.csv",
            mime="text/csv"
        )


    # ========================================================
    # 31. ERROR HANDLING
    # Shows readable error if upload or processing fails.
    # ========================================================

    except Exception as e:
        st.error("Could not read schedule file")
        st.write(e)


# ============================================================
# 32. EMPTY STATE
# Message shown before user uploads a schedule.
# ============================================================

else:
    st.info(
        "Upload an Excel or CSV schedule file to begin."
    )
