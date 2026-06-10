# ============================================================
# Developed by Michael N. Erzuah
#CONSTRUCTION PROGRESS TRACKER - STREAMLIT MVP
# Version 0.3
#
# Current features:
# 1. Project name input
# 2. Schedule upload
# 3. Required field validation
# 4. Optional Critical column handling
# 5. Schedule cleaning
# 6. Schedule summary metrics
# 7. Validated schedule filtering
#    - Discipline
#    - Package
#    - Location / WBS
#    - Start date
#    - Finish date
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
# Update this section if your schedule template changes.
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
# 4. APP TITLE AND INTRO
# ============================================================

st.title("Construction Progress Tracker")

st.write(
    "Schedule-based construction progress tracking MVP"
)


# ============================================================
# 5. PROJECT NAME INPUT
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
# 6. SCHEDULE FILE UPLOAD
# User uploads Excel or CSV schedule export.
# ============================================================

uploaded_file = st.file_uploader(
    "Upload Schedule File",
    type=["xlsx", "xls", "csv"]
)


# ============================================================
# 7. READ UPLOADED SCHEDULE
# This block reads the uploaded file into a Pandas DataFrame.
# ============================================================

if uploaded_file is not None:

    try:
        if uploaded_file.name.lower().endswith(".csv"):
            schedule = pd.read_csv(uploaded_file)
        else:
            schedule = pd.read_excel(uploaded_file)

        st.success("Schedule uploaded successfully")


        # ====================================================
        # 8. ORIGINAL SCHEDULE PREVIEW
        # Shows the raw uploaded schedule before validation.
        # ====================================================

        st.subheader("Original Schedule Preview")

        st.dataframe(
            schedule.head(20),
            use_container_width=True
        )


        # ====================================================
        # 9. REQUIRED FIELD VALIDATION
        # The app stops if any required field is missing.
        # ====================================================

        missing_columns = [
            col for col in REQUIRED_COLUMNS
            if col not in schedule.columns
        ]

        if missing_columns:
            st.error("Schedule is missing required fields:")

            for col in missing_columns:
                st.write(f"- {col}")

            st.stop()

        else:
            st.success("All required fields are present")


        # ====================================================
        # 10. OPTIONAL FIELD HANDLING
        # Critical is optional. If missing, create blank column.
        # ====================================================

        for col in OPTIONAL_COLUMNS:
            if col not in schedule.columns:
                schedule[col] = ""


        # ====================================================
        # 11. KEEP ONLY MVP COLUMNS
        # This simplifies the working schedule table.
        # ====================================================

        schedule = schedule[
            REQUIRED_COLUMNS + OPTIONAL_COLUMNS
        ].copy()


        # ====================================================
        # 12. DATE CLEANING
        # Converts Start and Finish fields into true dates.
        # Invalid dates become blank and are removed later.
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
        # 13. REMOVE INVALID ROWS
        # Rows missing required information are removed.
        # ====================================================

        schedule = schedule.dropna(
            subset=REQUIRED_COLUMNS
        )


        # ====================================================
        # 14. EMPTY SCHEDULE CHECK
        # Prevents app from continuing if everything was removed.
        # ====================================================

        if schedule.empty:
            st.error(
                "No valid activities found after cleaning the schedule."
            )
            st.stop()


        # ====================================================
        # 15. SCHEDULE SUMMARY METRICS
        # High-level counts from the validated schedule.
        # ====================================================

        st.subheader("Schedule Summary")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Activities",
            len(schedule)
        )

        col2.metric(
            "Disciplines",
            schedule["Discipline"].nunique()
        )

        col3.metric(
            "Packages",
            schedule["Package"].nunique()
        )

        col4.metric(
            "Locations / WBS Groups",
            schedule["WBS location"].nunique()
        )


        # ====================================================
        # 16. FILTER SECTION HEADER
        # Users can narrow the validated schedule.
        # ====================================================

        st.subheader("Filter Validated Schedule")


        # ====================================================
        # 17. DISCIPLINE FILTER
        # Allows one or more disciplines to be selected.
        # ====================================================

        discipline_options = sorted(
            schedule["Discipline"]
            .dropna()
            .astype(str)
            .unique()
        )

        discipline_filter = st.multiselect(
            "Filter by Discipline",
            discipline_options
        )


        # ====================================================
        # 18. PACKAGE FILTER
        # Allows one or more packages to be selected.
        # ====================================================

        package_options = sorted(
            schedule["Package"]
            .dropna()
            .astype(str)
            .unique()
        )

        package_filter = st.multiselect(
            "Filter by Package",
            package_options
        )


        # ====================================================
        # 19. LOCATION / WBS FILTER
        # This is not always a room.
        # It may be a zone, floor, area, system, or WBS group.
        # ====================================================

        location_options = sorted(
            schedule["WBS location"]
            .dropna()
            .astype(str)
            .unique()
        )

        location_filter = st.multiselect(
            "Filter by Location / WBS",
            location_options
        )


        # ====================================================
        # 20. DATE FILTERS
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
        # 21. APPLY FILTERS
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
        # 22. FILTERED RESULTS SUMMARY
        # Shows how many activities remain after filtering.
        # ====================================================

        st.write(
            f"Filtered Activities: {len(filtered_schedule)}"
        )


        # ====================================================
        # 23. FILTERED VALIDATED SCHEDULE TABLE
        # Main table shown to user.
        # ====================================================

        st.subheader("Validated Schedule")

        st.dataframe(
            filtered_schedule,
            use_container_width=True
        )


        # ====================================================
        # 24. DOWNLOAD FILTERED SCHEDULE
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
    # 25. ERROR HANDLING
    # Shows readable error if upload or processing fails.
    # ========================================================

    except Exception as e:
        st.error("Could not read schedule file")
        st.write(e)


# ============================================================
# 26. EMPTY STATE
# Message shown before user uploads a schedule.
# ============================================================

else:
    st.info(
        "Upload an Excel or CSV schedule file to begin."
    )
