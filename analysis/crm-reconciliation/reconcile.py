"""Generic two-CRM reconciliation engine.

Takes two lists of raw records plus a field-mapping config and produces a
match/orphan/mismatch report. Contains no Fireclay-specific field names —
all mapping lives in config.yaml. Intended to be adapted to any pair of
CRM exports by changing only the config.
"""
from rapidfuzz import fuzz


def normalize_record(record: dict, field_map: dict, source_system: str) -> dict:
    def get(key):
        spec = field_map.get(key, "")
        if "+" in spec:
            parts = [str(record.get(p.strip(), "")).strip() for p in spec.split("+")]
            return " ".join(p for p in parts if p)
        return str(record.get(spec, "") or "").strip()

    return {
        "email": get("email").lower(),
        "full_name": get("full_name"),
        "company": get("company"),
        "lifecycle_stage": get("lifecycle_stage"),
        "created_date": get("created_date"),
        "source_system": source_system,
        "source_id": record.get("id") or record.get("Id"),
    }


def _canonical_stage(raw_stage: str, source_system: str, stage_map: dict) -> str | None:
    for canonical, systems in stage_map.items():
        if raw_stage in systems.get(source_system, []):
            return canonical
    return None


def reconcile(hubspot_records: list, salesforce_records: list, config: dict) -> dict:
    hs_norm = [normalize_record(r, config["hubspot"], "hubspot") for r in hubspot_records]
    sf_norm = [normalize_record(r, config["salesforce"], "salesforce") for r in salesforce_records]
    threshold = config.get("matching", {}).get("fuzzy_threshold", 85)
    stage_map = config.get("lifecycle_stage_map", {})

    matched, stage_mismatches = [], []
    matched_sf_ids = set()

    # Pass 1: exact email match
    sf_by_email = {r["email"]: r for r in sf_norm if r["email"]}
    for hs in hs_norm:
        if hs["email"] and hs["email"] in sf_by_email:
            sf = sf_by_email[hs["email"]]
            matched.append({
                "hubspot_id": hs["source_id"], "salesforce_id": sf["source_id"],
                "match_method": "email", "confidence": 100.0,
                "field_diffs": _diff(hs, sf),
            })
            matched_sf_ids.add(sf["source_id"])
            _check_stage(hs, sf, stage_map, stage_mismatches)

    matched_hs_ids = {m["hubspot_id"] for m in matched}

    # Pass 2: fuzzy match on name+company for records with no email
    remaining_hs = [r for r in hs_norm if r["source_id"] not in matched_hs_ids]
    remaining_sf = [r for r in sf_norm if r["source_id"] not in matched_sf_ids]
    for hs in remaining_hs:
        if not hs["full_name"]:
            continue
        best, best_score = None, 0
        for sf in remaining_sf:
            if sf["source_id"] in matched_sf_ids or not sf["full_name"]:
                continue
            score = fuzz.token_sort_ratio(
                f"{hs['full_name']} {hs['company']}", f"{sf['full_name']} {sf['company']}"
            )
            if score > best_score:
                best, best_score = sf, score
        if best and best_score >= threshold:
            matched.append({
                "hubspot_id": hs["source_id"], "salesforce_id": best["source_id"],
                "match_method": "fuzzy", "confidence": float(best_score),
                "field_diffs": _diff(hs, best),
            })
            matched_sf_ids.add(best["source_id"])
            _check_stage(hs, best, stage_map, stage_mismatches)

    matched_hs_ids = {m["hubspot_id"] for m in matched}
    hubspot_only = [{"id": r["source_id"], "email": r["email"], "full_name": r["full_name"]}
                    for r in hs_norm if r["source_id"] not in matched_hs_ids]
    salesforce_only = [{"id": r["source_id"], "email": r["email"], "full_name": r["full_name"]}
                       for r in sf_norm if r["source_id"] not in matched_sf_ids]

    return {
        "matched": matched,
        "hubspot_only": hubspot_only,
        "salesforce_only": salesforce_only,
        "stage_mismatches": stage_mismatches,
        "summary": {
            "matched_count": len(matched),
            "hubspot_only_count": len(hubspot_only),
            "salesforce_only_count": len(salesforce_only),
            "stage_mismatch_count": len(stage_mismatches),
        },
    }


def _diff(hs: dict, sf: dict) -> dict:
    diffs = {}
    for field in ("full_name", "company"):
        if hs[field].strip().lower() != sf[field].strip().lower():
            diffs[field] = {"hubspot": hs[field], "salesforce": sf[field]}
    return diffs


def _check_stage(hs: dict, sf: dict, stage_map: dict, out: list):
    hs_canon = _canonical_stage(hs["lifecycle_stage"], "hubspot", stage_map)
    sf_canon = _canonical_stage(sf["lifecycle_stage"], "salesforce", stage_map)
    if hs_canon != sf_canon:
        out.append({
            "hubspot_id": hs["source_id"], "salesforce_id": sf["source_id"],
            "hubspot_raw_stage": hs["lifecycle_stage"], "salesforce_raw_stage": sf["lifecycle_stage"],
            "hubspot_canonical_stage": hs_canon, "salesforce_canonical_stage": sf_canon,
        })
