# Duplicate Cardholder Detection Solution

A beginner-friendly Python project based on the workflow in the reference slide.

## Business problem
One person may appear in multiple card, borrower, and co-borrower relationships. Differences in names or addresses can make possible duplicates difficult to identify consistently. This tool flags candidate records for human review and creates reports.

## Workflow
1. Read cardholder / borrower / co-borrower records.
2. Standardize names, dates of birth, addresses, and optional synthetic ID tokens.
3. Generate candidate pairs using DOB or name-prefix blocking.
4. Compare name, DOB, address, and optional ID token using explainable rules.
5. Link matching records to show related relationships.
6. Mark potential records for review; do not automatically suppress or merge records.
7. Generate a detailed CSV report and JSON run summary.
8. Schedule the script to run daily with Windows Task Scheduler or cron.

## Requirements
- Python 3.10+
- pandas
- rapidfuzz

## Run on Windows / VS Code
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py src\detect_duplicates.py --input data\cardholder_records.csv --output-dir reports
```

## Output
- `reports/duplicate_candidates_YYYYMMDD_HHMMSS.csv`: record pairs, score, match reasons, relationship IDs, review status.
- `reports/run_summary_YYYYMMDD_HHMMSS.json`: run metrics and estimated cost avoidance (disabled unless you supply a validated business assumption).

## Input columns
Required: `record_id, customer_id, full_name, dob, address, relationship_id, role, card_id`
Optional: `id_token` (synthetic or tokenized identifier only; never store real SSN or full card numbers).

## Matching approach
- Exact optional ID token match: strong signal when present (but must be governed and validated).
- Exact DOB: supporting signal.
- Name similarity and address similarity: fuzzy signals.
- Scores classify candidates into `LIKELY_MATCH`, `REVIEW`, or `LOW_CONFIDENCE`.
- These starter thresholds are examples only and must be calibrated using reviewed labelled examples.
- Candidate blocking improves speed but may miss pairs when the blocking attributes are incomplete.

## Cost avoidance
The image reference mentions `$112K+` minimum estimated cost avoidance. This code does **not** claim that amount as an achieved result. The run summary only calculates cost avoidance if you explicitly provide a validated cost-per-case and approved eligible case count; otherwise it reports `not_calculated`.

## Daily scheduling
Windows Task Scheduler:
- Program: full path to `.venv\Scripts\python.exe`
- Arguments: `src\detect_duplicates.py --input data\cardholder_records.csv --output-dir reports`
- Start in: project folder
- Trigger: daily at your chosen time

Linux/macOS cron example:
```cron
0 6 * * * cd /path/to/duplicate_cardholder_full_project && /path/to/.venv/bin/python src/detect_duplicates.py --input data/cardholder_records.csv --output-dir reports >> reports/job.log 2>&1
```

## Safety and production notes
This is a portfolio prototype using fictional data. It is not a production decision engine. Do not automatically suppress, merge, or change customer records. Human review, data governance, access controls, audit logging, model validation, and approved data sources are required before operational use.
