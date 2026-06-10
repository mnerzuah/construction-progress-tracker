import streamlit as st
import pandas as pd

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
    "Start",
    "Finish"
]

OPTIONAL_COLUMNS = ["Critical"]

st.title("Construction Progress Tracker")
st.write("Schedule-based construction progress tracking MVP")

project_name = st.text_input("Project Name")

uploaded_file = st.file_uploader(
    "Upload Schedule File",
    type=["xlsx", "xls", "csv"]
)

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            schedule = pd.read_csv(uploaded_file)
        else:
            schedule = pd.read_excel(uploaded_file)

        st.success("Schedule uploaded successfully")

        st.subheader("Schedule Preview")
        st.dataframe(schedule.head(20), use_container_width=True)

        missing_columns = [
            col for col in REQUIRED_COLUMNS
            if col not in schedule.columns
        ]

        if missing_columns:
            st.error("Schedule is missing required fields:")
            for col in missing_columns:
                st.write(f"- {col}")

        else:
            st.success("All required fields are present")

            if "Critical" not in schedule.columns:
                schedule["Critical"] = ""

            schedule = schedule[REQUIRED_COLUMNS + ["Critical"]].copy()

            schedule["Start"] = pd.to_datetime(
                schedule["Start"],
                errors="coerce"
            )

            schedule["Finish"] = pd.to_datetime(
                schedule["Finish"],
                errors="coerce"
            )

            schedule = schedule.dropna(
                subset=REQUIRED_COLUMNS
            )

            st.subheader("Schedule Summary")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Total Activities", len(schedule))
            col2.metric("Disciplines", schedule["Discipline"].nunique())
            col3.metric("Packages", schedule["Package"].nunique())
            col4.metric("Rooms / Locations", schedule["WBS location"].nunique())

            st.subheader("Validated Schedule")
            st.dataframe(schedule, use_container_width=True)

    except Exception as e:
        st.error("Could not read schedule file")
        st.write(e)

else:
    st.info("Upload an Excel or CSV schedule file to begin.")
