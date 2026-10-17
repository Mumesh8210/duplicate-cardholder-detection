import argparse
import json
import re
from datetime import datetime
from itertools import combinations
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

REQUIRED = [
    "record_id", "customer_id", "full_name", "dob", "address",
    "relationship_id", "role", "card_id"
]

def normalize_text(value):
    """Make text comparisons more consistent."""
    if pd.isna(value):
        return ""
    value = str(value).lower().strip()
    value = re.sub(r"[^a-z0-9 ]", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def normalize_date(value):
    """Convert a date to YYYY-MM-DD; return empty text if invalid."""
    if pd.isna(value) or str(value).strip() == "":
        return ""
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return ""
    return parsed.strftime("%Y-%m-%d")

def similarity(text1, text2):
    """Return fuzzy similarity from 0 to 100."""
    if not text1 or not text2:
        return 0
    return fuzz.token_sort_ratio(text1, text2)

def get_candidate_pairs(data):
    """Compare records that share a DOB or name prefix plus birth year."""
    groups = {}
    for idx, row in data.iterrows():
        if row["_dob"]:
            groups.setdefault(("DOB", row["_dob"]), set()).add(idx)
        year = row["_dob"][:4] if row["_dob"] else ""
        prefix = row["_name"][:3]
        if year and len(prefix) == 3:
            groups.setdefault(("NAME_YEAR", prefix, year), set()).add(idx)

    pairs = set()
    for group in groups.values():
        for first, second in combinations(sorted(group), 2):
            # Compare different customer IDs; same-customer multi-relationship
            # records are still visible in the source but not called duplicates here.
            if data.at[first, "customer_id"] != data.at[second, "customer_id"]:
                pairs.add((first, second))
    return sorted(pairs)

def compare_records(first, second):
    name_score = similarity(first["_name"], second["_name"])
    address_score = similarity(first["_address"], second["_address"])
    dob_match = bool(first["_dob"] and second["_dob"] and first["_dob"] == second["_dob"])

    # Explainable weighted score: name 45%, DOB 30%, address 25%.
    score = (0.45 * name_score) + (30 if dob_match else 0) + (0.25 * address_score)

    # Optional identifier is only a synthetic/tokenized identifier in this demo.
    id_match = False
    if "id_token" in first.index and "id_token" in second.index:
        token1 = str(first.get("id_token", "")).strip()
        token2 = str(second.get("id_token", "")).strip()
        id_match = bool(token1 and token2 and token1 == token2)
        if id_match:
            score = max(score, 95)

    if score >= 85:
        decision = "LIKELY_MATCH"
    elif score >= 65:
        decision = "REVIEW"
    else:
        decision = "LOW_CONFIDENCE"

    reasons = []
    if id_match:
        reasons.append("same optional ID token")
    if name_score >= 80:
        reasons.append(f"name similarity {name_score:.0f}%")
    if dob_match:
        reasons.append("exact date of birth")
    if address_score >= 80:
        reasons.append(f"address similarity {address_score:.0f}%")
    if not reasons:
        reasons.append("partial attribute similarity")

    return {
        "match_score": round(score, 1),
        "decision": decision,
        "name_similarity_pct": round(name_score, 1),
        "dob_exact_match": dob_match,
        "address_similarity_pct": round(address_score, 1),
        "id_token_exact_match": id_match,
        "match_reasons": "; ".join(reasons),
    }

def run(input_path, output_dir):
    data = pd.read_csv(input_path, dtype=str).fillna("")
    missing = [column for column in REQUIRED if column not in data.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    if data["record_id"].duplicated().any():
        raise ValueError("Each record_id must be unique.")

    data["_name"] = data["full_name"].map(normalize_text)
    data["_dob"] = data["dob"].map(normalize_date)
    data["_address"] = data["address"].map(normalize_text)

    pairs = get_candidate_pairs(data)
    results = []

    for first_idx, second_idx in pairs:
        first = data.loc[first_idx]
        second = data.loc[second_idx]
        score_info = compare_records(first, second)
        if score_info["decision"] == "LOW_CONFIDENCE":
            continue

        results.append({
            "record_id_1": first["record_id"],
            "customer_id_1": first["customer_id"],
            "name_1": first["full_name"],
            "relationship_id_1": first["relationship_id"],
            "role_1": first["role"],
            "card_id_1": first["card_id"],
            "record_id_2": second["record_id"],
            "customer_id_2": second["customer_id"],
            "name_2": second["full_name"],
            "relationship_id_2": second["relationship_id"],
            "role_2": second["role"],
            "card_id_2": second["card_id"],
            **score_info,
            "review_status": "PENDING",
            "recommended_action": "Human review required; do not auto-merge or suppress",
        })

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"duplicate_candidates_{timestamp}.csv"
    summary_path = output_dir / f"run_summary_{timestamp}.json"

    columns = [
        "record_id_1", "customer_id_1", "name_1", "relationship_id_1",
        "role_1", "card_id_1", "record_id_2", "customer_id_2", "name_2",
        "relationship_id_2", "role_2", "card_id_2", "match_score", "decision",
        "name_similarity_pct", "dob_exact_match", "address_similarity_pct",
        "id_token_exact_match", "match_reasons", "review_status", "recommended_action"
    ]
    report = pd.DataFrame(results, columns=columns)
    report.to_csv(report_path, index=False)

    summary = {
        "run_timestamp": datetime.now().isoformat(timespec="seconds"),
        "input_file": str(input_path),
        "input_records": int(len(data)),
        "candidate_pairs_compared": int(len(pairs)),
        "reported_candidate_pairs": int(len(report)),
        "likely_matches": int((report["decision"] == "LIKELY_MATCH").sum()) if len(report) else 0,
        "needs_review": int((report["decision"] == "REVIEW").sum()) if len(report) else 0,
        "output_report": str(report_path),
        "cost_avoidance": "not_calculated: requires validated cost and eligible case assumptions",
        "thresholds": {"likely_match": 85, "review": 65},
        "note": "Prototype only. All candidates require human review; thresholds are not validated."
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Duplicate Cardholder Detection completed.")
    print(f"Input records: {len(data)}")
    print(f"Candidate pairs compared: {len(pairs)}")
    print(f"Candidate pairs reported: {len(report)}")
    print(f"Likely matches: {summary['likely_matches']}")
    print(f"Needs review: {summary['needs_review']}")
    print(f"CSV report: {report_path}")
    print(f"Run summary: {summary_path}")

def main():
    parser = argparse.ArgumentParser(description="Flag potential duplicate cardholder records.")
    parser.add_argument("--input", default="data/cardholder_records.csv")
    parser.add_argument("--output-dir", default="reports")
    args = parser.parse_args()
    run(args.input, args.output_dir)

if __name__ == "__main__":
    main()
