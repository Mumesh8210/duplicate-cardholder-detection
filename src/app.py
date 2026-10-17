#python
from pathlib import Path

import pandas as pd
import streamlit as st

# ----------------------------------
# 1. Dashboard Configuration
# ----------------------------------
st.set_page_config(
    page_title="Duplicate Cardholder Detection",
    page_icon="📊",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "cardholder_records.csv"
REPORTS_DIR = BASE_DIR / "reports"

# ----------------------------------
# 2. Dashboard Header
# ----------------------------------
st.title("Duplicate Cardholder Detection")
st.write(
    "Identify potential duplicate cardholder records "
    "for review by an authorized analyst."
)

st.divider()

# ----------------------------------
# 3. Load Cardholder Dataset
# ----------------------------------
st.header("Cardholder Dataset")

if DATA_FILE.exists():
    data = pd.read_csv(DATA_FILE)

    col1, col2 = st.columns(2)

    col1.metric("Total Records", f"{len(data):,}")
    col2.metric("Total Columns", len(data.columns))

    with st.expander("View Cardholder Data"):
        st.dataframe(data, use_container_width=True)

else:
    st.error(f"Dataset not found: {DATA_FILE}")

st.divider()

# ----------------------------------
# 4. Load Latest Duplicate Report
# ----------------------------------
st.header("Duplicate Detection Results")

report_files = (
    list(REPORTS_DIR.glob("duplicate_candidates_*.csv"))
    if REPORTS_DIR.exists()
    else []
)

if report_files:

    # Automatically select the newest report
    latest_report = max(
        report_files,
        key=lambda file: file.stat().st_mtime
    )

    try:
        duplicates = pd.read_csv(latest_report)

        st.caption(f"Latest report: {latest_report.name}")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Candidate Pairs",
            f"{len(duplicates):,}"
        )

        if "decision" in duplicates.columns:
            decisions = (
                duplicates["decision"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            col2.metric(
                "Likely Matches",
                f"{(decisions == 'LIKELY_MATCH').sum():,}"
            )

            col3.metric(
                "Needs Review",
                f"{(decisions == 'REVIEW').sum():,}"
            )

        else:
            col2.metric("Likely Matches", "N/A")
            col3.metric("Needs Review", "N/A")

            st.warning(
                "The report does not contain a decision column."
            )

        st.subheader("Potential Duplicate Records")

        if duplicates.empty:
            st.info("No candidate pairs were found.")
        else:
            st.dataframe(
                duplicates,
                use_container_width=True
            )

            st.download_button(
                label="Download Duplicate Report",
                data=duplicates.to_csv(
                    index=False
                ).encode("utf-8"),
                file_name=latest_report.name,
                mime="text/csv"
            )

    except (OSError, pd.errors.ParserError) as error:
        st.error(f"Unable to read the report: {error}")

else:
    st.warning(
        "No duplicate report found. Run the detection program first."
    )

st.divider()

# ----------------------------------
# 5. Business Note
# ----------------------------------
st.subheader("Analyst Review")

st.info(
    "These results are potential matches, not confirmed fraud "
    "or duplicate accounts. An authorized analyst must review "
    "the evidence before any account action is considered."
)
