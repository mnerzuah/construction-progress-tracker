# ============================================================
# Developed by Michael N. Erzuah
# CONSTRUCTION PROGRESS TRACKER - STREAMLIT MVP
# Version 0.8
#
# New in Version 0.8:
# 1. Activity selection workflow
# 2. Selected activity details card
# 3. Planned progress calculation
# 4. Basic activity status preview
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
        temp_df = temp_df[
            temp_df["Discipline"].astype(str).isin(selected_disciplines)
        ]

    if target_column != "Package" and selected_packages:
        temp_df = temp_df[
            temp_df["Package"].astype(str).isin(selected_packages)
        ]

    if target_column != "WBS location" and selected_locations:
        temp_df = temp_df[
            temp_df["WBS location"].astype(str).isin(selected_locations)
        ]

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
        return 0

    if today_date > finish_date:
        return 100

    total_duration = (finish_date - start_date).days

    if total_duration <= 0:
        return 100

    elapsed_duration = (today_date - start_date).days

    planned_progress = (elapsed_duration / total_duration) * 100

    return round(planned_progress, 1)


def get_activity_status_preview(planned_progress):
    if planned_progress == 0:
        return "Not Started"

    if planned_progress < 100:
        return "In Progress"

    return "Should Be Complete"


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

        discipline_options = get_dynamic_options(
            schedule,
            "Discipline",
            selected_disciplines,
            selected_packages,
            selected_locations,
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

        discipline_filter = st.multiselect(
            "Filter by Discipline",
            discipline_options,
            default=selected_disciplines,
            key="discipline_filter"
        )

        package_filter = st.multiselect(
            "Filter by Package",
            package_options,
            default=selected_packages,
            key="package_filter"
        )

        location_filter = st.multiselect(
            "Filter by Location / WBS",
            location_options,
            default=selected_locations,
            key="location_filter"
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

        # ====================================================
        # 18. VERSION 0.8 - ACTIVITY SELECTION WORKFLOW
        # User selects one activity from the filtered schedule.
        # ====================================================

        st.markdown("---")
        st.subheader("Activity Selection")

        if filtered_schedule.empty:
            st.warning("No activities available for selection. Adjust the filters above.")

        else:
            activity_selection_table = filtered_schedule.copy()

            activity_selection_table["Activity Selector"] = (
                activity_selection_table["Activity ID"].astype(str)
                + " | "
                + activity_selection_table["Activity Name"].astype(str)
                + " | "
                + activity_selection_table["WBS location"].astype(str)
            )

            selected_activity_label = st.selectbox(
                "Select Activity",
                activity_selection_table["Activity Selector"].tolist()
            )

            selected_activity = activity_selection_table[
                activity_selection_table["Activity Selector"] == selected_activity_label
            ].iloc[0]

            # =================================================
            # 19. SELECTED ACTIVITY DETAILS CARD
            # Shows context before progress is entered.
            # =================================================

            st.subheader("Selected Activity Details")

            detail_col1, detail_col2, detail_col3 = st.columns(3)

            with detail_col1:
                st.write("**Activity ID:**")
                st.write(selected_activity["Activity ID"])

                st.write("**Activity Name:**")
                st.write(selected_activity["Activity Name"])

                st.write("**Critical:**")
                st.write(selected_activity["Critical"])

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

                duration_days = (
                    selected_activity["Finish Date"].date()
                    - selected_activity["Start Date"].date()
                ).days

                st.write("**Duration:**")
                st.write(f"{duration_days} days")

            # =================================================
            # 20. PLANNED PROGRESS PREVIEW
            # Uses today's date against schedule start/finish.
            # =================================================

            today_date = date.today()

            planned_progress = calculate_planned_progress(
                selected_activity["Start Date"],
                selected_activity["Finish Date"],
                today_date
            )

            status_preview = get_activity_status_preview(
                planned_progress
            )

            st.subheader("Planned Progress Preview")

            progress_col1, progress_col2, progress_col3 = st.columns(3)

            progress_col1.metric(
                "Today",
                today_date.strftime("%Y-%m-%d")
            )

            progress_col2.metric(
                "Planned Progress",
                f"{planned_progress}%"
            )

            progress_col3.metric(
                "Schedule Status Preview",
                status_preview
            )

            st.progress(
                int(planned_progress)
            )

    except Exception as e:
        st.error("Could not read schedule file")
        st.write(e)

else:
    st.info("Upload an Excel or CSV schedule file to begin.")
