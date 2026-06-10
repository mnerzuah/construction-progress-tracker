import streamlit as st

st.set_page_config(
    page_title="Construction Progress Tracker",
    layout="wide"
)

st.title("Construction Progress Tracker")

st.write(
    "Schedule-based construction progress tracking MVP"
)

project_name = st.text_input(
    "Project Name"
)

if project_name:
    st.success(
        f"Project Loaded: {project_name}"
    )

st.markdown("---")

st.subheader("MVP Workflow")

st.write("1. Upload Schedule")
st.write("2. Select Discipline")
st.write("3. Select Package")
st.write("4. Select Room")
st.write("5. Select Activity")
st.write("6. Enter Progress")
st.write("7. Submit for Verification")
