# Workflow matching the reference slide

1. **Cards data + borrower/co-borrower records** — read CSV input.
2. **Match identities** — standardize name, DOB and address; use exact DOB and fuzzy string similarity.
3. **Link relationships** — retain both relationship IDs and borrower/co-borrower roles in each candidate pair.
4. **Review potential suppression** — label the pair for review; the program never suppresses or merges records automatically.
5. **Deliver reporting** — export detailed CSV and run-summary JSON.
6. **Daily scale** — schedule the script through Windows Task Scheduler or cron.
7. **Business impact** — estimate cost avoidance only when a validated per-case cost and eligible case count are supplied. The reference slide's $112K+ is not an outcome of this sample project.
