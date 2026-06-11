# ============================================================
# Developed by Michael N. Erzuah
# CONSTRUCTION PROGRESS TRACKER - STREAMLIT MVP
# Version 0.8.2
#
# Layout:
# 1. Schedule Summary
# 2. Progress Summary
# 3. Activity Progress Table
# 4. Filters
# 5. Activity Detail View
# ============================================================

import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(
    page_title="Construction Progress Tracker",
    layout="wide"
)

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
# HELPER FUNCTIONS
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


def normalize_critical_path(value):
    if pd.isna(value):
        return "No"

    value = str(value).strip().lower()

    true_values = [
        "yes",
        "y",
        "true",
        "1",
        "1.0",
        "critical",
        "critical path",
        "x"
    ]

    return "Yes" if value in true_values else "No"


def calculate_planned_progress(start_date, finish_date, today_date):
    start_date = start_date.date()
    finish_date = finish_date.date()

    if today_date < start_date:
        return 0.0

    if today_date > finish_date:
        return 100.0

    total_duration = (finish_date - start_date).days

    if total_duration <= 0:
        return 100.0

    elapsed_duration = (today_date - start_date).days
    planned_progress = (elapsed_duration / total_duration) * 100

    return round(planned_progress, 1)


def get_current_status(actual_progress, verification_status):
    if actual_progress == 0:
        return "Not Started"

    if actual_progress < 100:
        return f"{actual_progress}% Complete"

    if actual_progress == 100 and verification_status == "Verified":
        return "100% Complete - Verified"

    return "100% Complete - Pending Verification"


def apply_filters(
    df,
    discipline_filter,
    package_filter,
    location_filter,
    critical_path_filter,
    use_start_filter,
    start_date_filter,
    use_finish_filter,
    finish_date_filter
):
    filtered = df.copy()

    if use_start_filter:
        filtered = filtered[
            filtered["Start Date"].dt.date >= start_date_filter
        ]

    if use_finish_filter:
        filtered = filtered[
            filtered["Finish Date"].dt.date <= finish_date_filter
        ]

    if discipline_filter:
        filtered = filtered[
            filtered["Discipline"].astype(str).isin(discipline_filter)
        ]

    if package_filter:
        filtered = filtered[
            filtered["Package"].astype(str).isin(package_filter)
        ]

    if location_filter:
        filtered = filtered[
            filtered["WBS location"].astype(str).isin(location_filter)
        ]

    if critical_path_filter:
        filtered = filtered[
            filtered["Critical Path"].astype(str).isin(critical_path_filter)
        ]

    return filtered


def add_progress_placeholder_columns(df):
    progress_df = df.copy()
    today_date = date.today()

    progress_df["Planned Progress %"] = progress_df.apply(
        lambda row: calculate_planned_progress(
            row["Start Date"],
            row["Finish Date"],
            today_date
        ),
        axis=1
    )

    progress_df["Actual Progress %"] = 0
    progress_df["Verification Status"] = "Not Verified"
    progress_df["Constraints"] = "None"

    progress_df["Current Status"] = progress_df.apply(
        lambda row: get_current_status(
            row["Actual Progress %"],
            row["Verification Status"]
        ),
        axis=1
    )

    return progress_df


def build_activity_progress_table(progress_df):
    return progress_df[
        [
            "Activity ID",
            "Activity Name",
            "WBS location",
            "Discipline",
            "Package",
            "Start Date",
            "Finish Date",
            "Critical Path",
            "Planned Progress %",
            "Actual Progress %",
            "Verification Status",
            "Current Status",
            "Constraints"
        ]
    ].copy()


# ============================================================
# APP TITLE AND UPLOAD SECTION
# ============================================================

st.title("Construction Progress Tracker")
st.write("Schedule-based construction progress tracking MVP")

project_name = st.text_input("Project Name")

if project_name:
    st.success(f"Project Loaded: {project_name}")

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

    - Critical Path
    """
)

uploaded_file = st.file_uploader(
    "Upload Schedule File",
    type=["xlsx", "xls", "csv"]
)


# ============================================================
# MAIN APP LOGIC
# ============================================================

if uploaded_file is not None:

    try:
        # ====================================================
        # READ SCHEDULE FILE
        # ====================================================

        if uploaded_file.name.lower().endswith(".csv"):
            raw_schedule = pd.read_csv(uploaded_file)
        else:
            raw_schedule = pd.read_excel(uploaded_file)

        st.success("Schedule uploaded successfully")

        uploaded_columns = list(raw_schedule.columns)

        # ====================================================
        # AUTO-DETECT OR MANUAL MAP COLUMNS
        # ====================================================

        detected_mapping = {
            field: auto_detect_column(uploaded_columns, field)
            for field in REQUIRED_COLUMNS + OPTIONAL_COLUMNS
        }

        all_required_detected = all(
            detected_mapping[field] is not None
            for field in REQUIRED_COLUMNS
        )

        if all_required_detected:
            st.success("Required fields were auto-detected successfully. Schedule is valid.")
            final_mapping = detected_mapping.copy()

        else:
            st.warning(
                "Some required fields were not auto-detected. Review the full schedule preview and map the fields manually."
            )

            st.subheader("Original Schedule Preview")
            st.dataframe(raw_schedule, use_container_width=True)

            st.subheader("Map Schedule Fields")

            column_choices_required = ["-- Select Column --"] + uploaded_columns
            column_choices_optional = ["-- Not Provided --"] + uploaded_columns

            final_mapping = {}

            for field in REQUIRED_COLUMNS:
                detected_col = detected_mapping.get(field)

                default_index = (
                    column_choices_required.index(detected_col)
                    if detected_col in uploaded_columns
                    else 0
                )

                final_mapping[field] = st.selectbox(
                    f"{field} *",
                    column_choices_required,
                    index=default_index,
                    key=f"map_{field}"
                )

            for field in OPTIONAL_COLUMNS:
                detected_col = detected_mapping.get(field)

                default_index = (
                    column_choices_optional.index(detected_col)
                    if detected_col in uploaded_columns
                    else 0
                )

                final_mapping[field] = st.selectbox(
                    "Critical Path (optional)",
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

            st.success("Schedule fields mapped successfully.")

        # ====================================================
        # BUILD STANDARDIZED SCHEDULE
        # ====================================================

        schedule = pd.DataFrame()

        for field in REQUIRED_COLUMNS:
            schedule[field] = raw_schedule[final_mapping[field]]

        for field in OPTIONAL_COLUMNS:
            if final_mapping.get(field) in [None, "-- Not Provided --"]:
                schedule[field] = ""
            else:
                schedule[field] = raw_schedule[final_mapping[field]]

        schedule["Start Date"] = pd.to_datetime(
            schedule["Start Date"],
            errors="coerce"
        )

        schedule["Finish Date"] = pd.to_datetime(
            schedule["Finish Date"],
            errors="coerce"
        )

        schedule["Critical Path"] = schedule["Critical"].apply(
            normalize_critical_path
        )

        schedule = schedule.drop(
            columns=["Critical"]
        )

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
        # SCHEDULE SUMMARY
        # ====================================================

        st.subheader("Schedule Summary")

        sched_col1, sched_col2, sched_col3, sched_col4, sched_col5 = st.columns(5)

        sched_col1.metric("Total Activities", len(schedule))
        sched_col2.metric("Disciplines", schedule["Discipline"].nunique())
        sched_col3.metric("Packages", schedule["Package"].nunique())
        sched_col4.metric("Locations / WBS Groups", schedule["WBS location"].nunique())
        sched_col5.metric(
            "Critical Path Activities",
            len(schedule[schedule["Critical Path"] == "Yes"])
        )

        # ====================================================
        # DEFAULT FILTER VALUES
        # Filters appear after the first Activity Progress Table.
        # ====================================================

        min_start_date = schedule["Start Date"].min().date()
        max_finish_date = schedule["Finish Date"].max().date()

        discipline_filter = []
        package_filter = []
        location_filter = []
        critical_path_filter = []
        use_start_filter = False
        use_finish_filter = False
        start_date_filter = min_start_date
        finish_date_filter = max_finish_date

        filtered_schedule = apply_filters(
            schedule,
            discipline_filter,
            package_filter,
            location_filter,
            critical_path_filter,
            use_start_filter,
            start_date_filter,
            use_finish_filter,
            finish_date_filter
        )

        progress_summary = add_progress_placeholder_columns(
            filtered_schedule
        )

        activity_progress_table = build_activity_progress_table(
            progress_summary
        )

        # ====================================================
        # PROGRESS SUMMARY
        # ====================================================

        st.markdown("---")
        st.subheader("Progress Summary")

        total_activities = len(progress_summary)
        average_planned_progress = round(progress_summary["Planned Progress %"].mean(), 1)
        average_actual_progress = round(progress_summary["Actual Progress %"].mean(), 1)

        not_started_count = len(
            progress_summary[progress_summary["Current Status"] == "Not Started"]
        )

        in_progress_count = len(
            progress_summary[
                progress_summary["Current Status"].str.contains("% Complete")
            ]
        )

        pending_verification_count = len(
            progress_summary[
                progress_summary["Current Status"] == "100% Complete - Pending Verification"
            ]
        )

        verified_count = len(
            progress_summary[
                progress_summary["Current Status"] == "100% Complete - Verified"
            ]
        )

        constraints_count = len(
            progress_summary[
                progress_summary["Constraints"].astype(str).str.strip().str.lower() != "none"
            ]
        )

        prog_col1, prog_col2, prog_col3, prog_col4 = st.columns(4)

        prog_col1.metric("Total Activities", total_activities)
        prog_col2.metric("Average Planned Progress", f"{average_planned_progress}%")
        prog_col3.metric("Average Actual Progress", f"{average_actual_progress}%")
        prog_col4.metric("Not Started", not_started_count)

        prog_col5, prog_col6, prog_col7, prog_col8 = st.columns(4)

        prog_col5.metric("In Progress", in_progress_count)
        prog_col6.metric("100% Pending Verification", pending_verification_count)
        prog_col7.metric("100% Verified", verified_count)
        prog_col8.metric("Activities with Constraints", constraints_count)

        # ====================================================
        # ACTIVITY PROGRESS TABLE
        # First full table shown before filters.
        # ====================================================

        st.subheader("Activity Progress Table")

        st.dataframe(
            activity_progress_table,
            use_container_width=True
        )

        # ====================================================
        # FILTERS
        # Filters appear below the table and update the same table.
        # ====================================================

        st.markdown("---")
        st.subheader("Filters")

        date_col1, date_col2 = st.columns(2)

        with date_col1:
            use_start_filter = st.checkbox(
                "Filter by Start Date",
                value=False
            )

            start_date_filter = st.date_input(
                "Start Date From",
                value=min_start_date,
                disabled=not use_start_filter
            )

        with date_col2:
            use_finish_filter = st.checkbox(
                "Filter by Finish Date",
                value=False
            )

            finish_date_filter = st.date_input(
                "Finish Date To",
                value=max_finish_date,
                disabled=not use_finish_filter
            )

        date_filtered_options = apply_filters(
            schedule,
            [],
            [],
            [],
            [],
            use_start_filter,
            start_date_filter,
            use_finish_filter,
            finish_date_filter
        )

        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            discipline_filter = st.multiselect(
                "Filter by Discipline",
                sorted(date_filtered_options["Discipline"].dropna().astype(str).unique())
            )

            location_filter = st.multiselect(
                "Filter by Location / WBS",
                sorted(date_filtered_options["WBS location"].dropna().astype(str).unique())
            )

        with filter_col2:
            package_filter = st.multiselect(
                "Filter by Package",
                sorted(date_filtered_options["Package"].dropna().astype(str).unique())
            )

            critical_path_filter = st.multiselect(
                "Filter by Critical Path",
                sorted(date_filtered_options["Critical Path"].dropna().astype(str).unique())
            )

        filtered_schedule = apply_filters(
            schedule,
            discipline_filter,
            package_filter,
            location_filter,
            critical_path_filter,
            use_start_filter,
            start_date_filter,
            use_finish_filter,
            finish_date_filter
        )

        filtered_progress_summary = add_progress_placeholder_columns(
            filtered_schedule
        )

        filtered_activity_progress_table = build_activity_progress_table(
            filtered_progress_summary
        )

        st.write(f"Filtered Activities: {len(filtered_activity_progress_table)}")

        st.subheader("Activity Progress Table")

        st.dataframe(
            filtered_activity_progress_table,
            use_container_width=True
        )

        # ====================================================
        # DOWNLOAD FILTERED ACTIVITY PROGRESS TABLE
        # ====================================================

        filtered_csv = filtered_activity_progress_table.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="Download Activity Progress Table",
            data=filtered_csv,
            file_name="activity_progress_table.csv",
            mime="text/csv"
        )

        # ====================================================
        # ACTIVITY DETAIL VIEW
        # ====================================================

        st.markdown("---")
        st.subheader("Activity Detail View")

        if filtered_activity_progress_table.empty:
            st.warning("No activities available for detail view. Adjust the filters above.")

        else:
            filtered_activity_progress_table["Activity Selector"] = (
                filtered_activity_progress_table["Activity ID"].astype(str)
                + " | "
                + filtered_activity_progress_table["Activity Name"].astype(str)
                + " | "
                + filtered_activity_progress_table["WBS location"].astype(str)
            )

            selected_activity_label = st.selectbox(
                "Select Activity for Detail View",
                filtered_activity_progress_table["Activity Selector"].tolist()
            )

            selected_activity = filtered_activity_progress_table[
                filtered_activity_progress_table["Activity Selector"] == selected_activity_label
            ].iloc[0]

            detail_col1, detail_col2, detail_col3 = st.columns(3)

            with detail_col1:
                st.write("**Activity ID:**")
                st.write(selected_activity["Activity ID"])

                st.write("**Activity Name:**")
                st.write(selected_activity["Activity Name"])

                st.write("**Critical Path:**")
                st.write(selected_activity["Critical Path"])

            with detail_col2:
                st.write("**Discipline:**")
                st.write(selected_activity["Discipline"])

                st.write("**Package:**")
                st.write(selected_activity["Package"])

                st.write("**Location / WBS:**")
                st.write(selected_activity["WBS location"])

            with detail_col3:
                st.write("**Start Date:**")
                st.write(selected_activity["Start Date"].date())

                st.write("**Finish Date:**")
                st.write(selected_activity["Finish Date"].date())

                st.write("**Current Status:**")
                st.write(selected_activity["Current Status"])

                st.write("**Constraints:**")
                st.write(selected_activity["Constraints"])

    except Exception as e:
        st.error("Could not read schedule file")
        st.write(e)

else:
    st.info("Upload an Excel or CSV schedule file to begin.")
