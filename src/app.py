import streamlit as st
import pandas as pd


# Show duplicate detection results
st.subheader("Duplicate Detection Results")

report_file = "reports/duplicate_candidates_20261017_155240.csv"

try:
    duplicates = pd.read_csv(report_file)

    col1, col2, col3 = st.columns(3)

    col1.metric("Candidate Pairs", len(duplicates))
    col2.metric(
        "Likely Matches",
        (duplicates["decision"] == "LIKELY_MATCH").sum()
    )
    col3.metric(
        "Needs Review",
        (duplicates["decision"] == "REVIEW").sum()
    )

    st.subheader("Potential Duplicate Records")
    st.dataframe(duplicates, use_container_width=True)

except FileNotFoundError:
    st.warning("Run the duplicate detection program first.")
