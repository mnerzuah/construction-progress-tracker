# ============================================================
# Developed by Michael N. Erzuah
# CONSTRUCTION PROGRESS TRACKER - STREAMLIT MVP
# Version 0.8
#
# Main changes in this version:
# 1. Critical renamed to Critical Path
# 2. Critical Path standardized to Yes / No
# 3. Added Critical Path filter
# 4. Removed Validated Schedule display table
# 5. Added Progress Summary section
# 6. Added Activity Progress Table
# 7. Actual Progress is placeholder 0% until Version 0.9
# 8. Verification Status is placeholder until Version 1.0
# ============================================================

import streamlit as st
import pandas as pd
from datetime import date

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

    if value in true_values:
        return "Yes"

    return "No"


def apply_date_filters(df, use_start_filter, start_date_filter, use_finish_filter, finish_date_filter):
    filtered = df.copy()

    if use_start_filter:
        filtered = filtered[
            filtered["Start Date"].dt.date >= start_date_filter
        ]

    if use_finish_filter:
        filtered = filtered[
            filtered["Finish Date"].dt.date <= finish_date_filter
        ]

    return filtered


def get_dynamic_options(
    df,
    target_column,
    selected_disciplines,
    selected_packages,
    selected_locations,
    selected_critical_paths,
    use_start_filter,
    start_date_filter,
    use_finish_filter,
    finish_date_filter
):
    temp_df = df.copy()

    temp_df = apply_date_filters(
        temp_df,
        use_start_filter,
        start_date_filter,
        use_finish_filter,
        finish_date_filter
    )

    if target_column != "Discipline" and selected_disciplines:
        temp_df = temp_df[temp_df["Discipline"].astype(str).isin(selected_disciplines)]

    if target_column != "Package" and selected_packages:
        temp_df = temp_df[temp_df["Package"].astype(str).isin(selected_packages)]

    if target_column != "WBS location" and selected_locations:
        temp_df = temp_df[temp_df["WBS location"].astype(str).isin(selected_locations)]

    if target_column != "Critical Path" and selected_critical_paths:
        temp_df = temp_df[temp_df["Critical Path"].astype(str).isin(selected_critical_paths)]

    return sorted(
        temp_df[target_column]
        .dropna()
        .astype(str)
        .unique()
    )


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

    - Critical Path
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
        # 9. AUTO-DETECTION OR MANUAL MAPPING
        # ====================================================

        if all_required_detected:
            st.success(
                "Required fields were auto-detected successfully. Schedule is valid."
            )

            final_mapping = detected_mapping.copy()

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
        # 10. BUILD STANDARDIZED SCHEDULE
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
        # 11. DATE CLEANING
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
        # 12. CRITICAL PATH CLEANING
        # ====================================================

        schedule["Critical Path"] = schedule["Critical"].apply(
            normalize_critical_path
        )

        schedule = schedule.drop(
            columns=["Critical"]
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

        summary_col1, summary_col2, summary_col3, summary_col4, summary_col5 = st.columns(5)

        summary_col1.metric("Total Activities", len(schedule))
        summary_col2.metric("Disciplines", schedule["Discipline"].nunique())
        summary_col3.metric("Packages", schedule["Package"].nunique())
        summary_col4.metric("Locations / WBS Groups", schedule["WBS location"].nunique())
        summary_col5.metric(
            "Critical Path Activities",
            len(schedule[schedule["Critical Path"] == "Yes"])
        )

        # ====================================================
        # 15. FILTER VALIDATED SCHEDULE
        # ====================================================

        st.subheader("Filter Validated Schedule")

        min_start_date = schedule["Start Date"].min().date()
        max_finish_date = schedule["Finish Date"].max().date()

        date_toggle_col1, date_toggle_col2 = st.columns(2)

        with date_toggle_col1:
            use_start_filter = st.checkbox(
                "Filter by Start Date",
                value=False
            )

        with date_toggle_col2:
            use_finish_filter = st.checkbox(
                "Filter by Finish Date",
                value=False
            )

        date_col1, date_col2 = st.columns(2)

        with date_col1:
            start_date_filter = st.date_input(
                "Start Date From",
                value=min_start_date,
                disabled=not use_start_filter
            )

        with date_col2:
            finish_date_filter = st.date_input(
                "Finish Date To",
                value=max_finish_date,
                disabled=not use_finish_filter
            )

        selected_disciplines = st.session_state.get("discipline_filter", [])
        selected_packages = st.session_state.get("package_filter", [])
        selected_locations = st.session_state.get("location_filter", [])
        selected_critical_paths = st.session_state.get("critical_path_filter", [])

        discipline_options = get_dynamic_options(
            schedule,
            "Discipline",
            selected_disciplines,
            selected_packages,
            selected_locations,
            selected_critical_paths,
            use_start_filter,
            start_date_filter,
            use_finish_filter,
            finish_date_filter
        )

        package_options = get_dynamic_options(
            schedule,
            "Package",
            selected_disciplines,
            selected_packages,
            selected_locations,
            selected_critical_paths,
            use_start_filter,
            start_date_filter,
            use_finish_filter,
            finish_date_filter
        )

        location_options = get_dynamic_options(
            schedule,
            "WBS location",
            selected_disciplines,
            selected_packages,
            selected_locations,
            selected_critical_paths,
            use_start_filter,
            start_date_filter,
            use_finish_filter,
            finish_date_filter
        )

        critical_path_options = get_dynamic_options(
            schedule,
            "Critical Path",
            selected_disciplines,
            selected_packages,
            selected_locations,
            selected_critical_paths,
            use_start_filter,
            start_date_filter,
            use_finish_filter,
            finish_date_filter
        )

        selected_disciplines = [
            item for item in selected_disciplines
            if item in discipline_options
        ]

        selected_packages = [
            item for item in selected_packages
            if item in package_options
        ]

        selected_locations = [
            item for item in selected_locations
            if item in location_options
        ]

        selected_critical_paths = [
            item for item in selected_critical_paths
            if item in critical_path_options
        ]

        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            discipline_filter = st.multiselect(
                "Filter by Discipline",
                discipline_options,
                default=selected_disciplines,
                key="discipline_filter"
            )

            location_filter = st.multiselect(
                "Filter by Location / WBS",
                location_options,
                default=selected_locations,
                key="location_filter"
            )

        with filter_col2:
            package_filter = st.multiselect(
                "Filter by Package",
                package_options,
                default=selected_packages,
                key="package_filter"
            )

            critical_path_filter = st.multiselect(
                "Filter by Critical Path",
                critical_path_options,
                default=selected_critical_paths,
                key="critical_path_filter"
            )

        filtered_schedule = schedule.copy()

        filtered_schedule = apply_date_filters(
            filtered_schedule,
            use_start_filter,
            start_date_filter,
            use_finish_filter,
            finish_date_filter
        )

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

        if critical_path_filter:
            filtered_schedule = filtered_schedule[
                filtered_schedule["Critical Path"].astype(str).isin(critical_path_filter)
            ]

        st.write(f"Filtered Activities: {len(filtered_schedule)}")

        # ====================================================
        # 16. DOWNLOAD FILTERED SCHEDULE
        # ====================================================

        filtered_csv = filtered_schedule.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Filtered Schedule",
            data=filtered_csv,
            file_name="filtered_validated_schedule.csv",
            mime="text/csv"
        )

        # ====================================================
        # 17. PROGRESS SUMMARY
        # Version 0.8 uses placeholder actual progress.
        # Version 0.9 will replace placeholders with saved entries.
        # ====================================================

        st.markdown("---")
        st.subheader("Progress Summary")

        progress_summary = filtered_schedule.copy()

        today_date = date.today()

        progress_summary["Planned Progress %"] = progress_summary.apply(
            lambda row: calculate_planned_progress(
                row["Start Date"],
                row["Finish Date"],
                today_date
            ),
            axis=1
        )

        progress_summary["Actual Progress %"] = 0
        progress_summary["Verification Status"] = "Not Verified"

        progress_summary["Current Status"] = progress_summary.apply(
            lambda row: get_current_status(
                row["Actual Progress %"],
                row["Verification Status"]
            ),
            axis=1
        )

        if progress_summary.empty:
            st.warning("No activities available for progress summary. Adjust the filters above.")

        else:
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

            progress_col1, progress_col2, progress_col3, progress_col4 = st.columns(4)

            progress_col1.metric("Total Activities", total_activities)
            progress_col2.metric("Average Planned Progress", f"{average_planned_progress}%")
            progress_col3.metric("Average Actual Progress", f"{average_actual_progress}%")
            progress_col4.metric("Not Started", not_started_count)

            progress_col5, progress_col6, progress_col7 = st.columns(3)

            progress_col5.metric("In Progress", in_progress_count)
            progress_col6.metric("100% Pending Verification", pending_verification_count)
            progress_col7.metric("100% Verified", verified_count)

            # ====================================================
            # 18. ACTIVITY PROGRESS TABLE
            # ====================================================

            activity_progress_table = progress_summary[
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
                    "Current Status"
                ]
            ].copy()

            st.subheader("Activity Progress Table")

            st.dataframe(
                activity_progress_table,
                use_container_width=True
            )

            # ====================================================
            # 19. OPTIONAL ACTIVITY DETAIL VIEW
            # ====================================================

            st.subheader("Activity Detail View")

            activity_progress_table["Activity Selector"] = (
                activity_progress_table["Activity ID"].astype(str)
                + " | "
                + activity_progress_table["Activity Name"].astype(str)
                + " | "
                + activity_progress_table["WBS location"].astype(str)
            )

            selected_activity_label = st.selectbox(
                "Select Activity for Detail View",
                activity_progress_table["Activity Selector"].tolist()
            )

            selected_activity = activity_progress_table[
                activity_progress_table["Activity Selector"] == selected_activity_label
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

    except Exception as e:
        st.error("Could not read schedule file")
        st.write(e)

else:
    st.info("Upload an Excel or CSV schedule file to begin.")
