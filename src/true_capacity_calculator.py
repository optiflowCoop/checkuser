#!/usr/bin/env python3
"""
Fase 4: Cálculo REAL de Capacidade (High-Water Mark)
Modelo único e data-driven.
SEM heurísticas.
"""

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analysis.entitlement import calculate_app_points



IN_DIR = ROOT / "output" / "consolidated"
OUT_DIR = ROOT / "output" / "consolidated"

SESSION_MINUTES = 60
LOOKBACK_DAYS = 90


def _normalize_userid(uid):
    """
    Normalizes USERID for consistent matching across datasets.
    Removes whitespace and converts to uppercase.
    
    Critical for cross-referencing logintracking with user profiles.
    """
    if not uid:
        return ""
    return str(uid).strip().upper().replace(" ", "")


def _load_csv(path):
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _parse_dt(s):
    if not s:
        return None

    text = str(s).strip()

    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d-%H.%M.%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d"
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return None



def _fmt_hour(dt):
    return dt.strftime("%Y-%m-%d %H:00")


def _scope_from_domain_category(domain_category):
    category = str(domain_category or "").strip().upper()
    if category in ("FORESEA", "PARCEIRO"):
        return "foresea"
    if category == "INTEGRACAO":
        return "integracao"
    if category and category != "SEM DOMINIO":
        return "terceiros"
    return None



def main():
    print("📊 Fase 4: CÁLCULO REAL DE CAPACIDADE (NEM ÚNICO)")

    license_plan_path = IN_DIR / "license_decision_plan.csv"
    logintrack_path = IN_DIR / "consolidated_logintracking_from_sources.csv"

    optimizations = _load_csv(license_plan_path)
    login_rows = _load_csv(logintrack_path)

    if not optimizations or not login_rows:
        print("❌ Dados insuficientes para cálculo de capacidade.")
        return

    golden = {}
    skipped_rows = 0
    for row in optimizations:
        userid = _normalize_userid(row.get("USERID"))
        if not userid:
            skipped_rows += 1
            continue

        rec = (row.get("OPTIMIZATION_REC") or "").strip().upper()
        if rec.startswith("INATIVO"):
            continue

        raw_entitlement = (row.get("ENTITLEMENT") or "").strip().upper()
        entitlement = "PREMIUM" if raw_entitlement == "PREMIUM" else "BASE"
        license_model = (row.get("LICENSE_MODEL") or "").strip().upper()
        if license_model not in ("AUTHORIZED", "CONCURRENT"):
            skipped_rows += 1
            continue

        domain_category = (row.get("DOMAIN_CATEGORY") or "").strip().upper()
        scope = _scope_from_domain_category(domain_category)
        if not scope:
            skipped_rows += 1
            continue

        final_entitlement = "BASE" if rec == "DOWNGRADE_CANDIDATE" and entitlement == "PREMIUM" else entitlement
        final_license = "CONCURRENT" if rec == "MOVE_TO_CONCURRENT" else license_model

        raw_points = row.get("APP_POINTS")
        try:
            cost = int(float(raw_points)) if raw_points not in (None, "") else 0
        except (TypeError, ValueError):
            cost = 0

        if cost <= 0:
            cost = int(calculate_app_points(final_entitlement, final_license) or 0)

        if cost <= 0:
            skipped_rows += 1
            continue

        if userid not in golden or cost > golden[userid]["cost"]:
            golden[userid] = {
                "cost": cost,
                "license": final_license,
                "scope": scope,
                "entitlement": final_entitlement,
            }

    print(f"✓ Loaded {len(golden)} active users from license decision plan")
    print(f"✓ Skipped rows: {skipped_rows}")


    authorized_reserved = sum(
        u["cost"] for u in golden.values()
        if "AUTHORIZED" in u["license"]
    )
    authorized_reserved_by_scope = {
        "foresea": sum(u["cost"] for u in golden.values() if u["scope"] == "foresea" and "AUTHORIZED" in u["license"]),
        "terceiros": sum(u["cost"] for u in golden.values() if u["scope"] == "terceiros" and "AUTHORIZED" in u["license"]),
        "integracao": sum(u["cost"] for u in golden.values() if u["scope"] == "integracao" and "AUTHORIZED" in u["license"]),
    }
    authorized_reserved_by_scope["todos"] = sum(authorized_reserved_by_scope.values())

    max_dt = None
    for rec in login_rows:
        result = (rec.get("ATTEMPTRESULT") or "").strip().upper()
        if result != "LOGIN":
            continue
        dt = _parse_dt(rec.get("ATTEMPTDATE"))
        if dt and (max_dt is None or dt > max_dt):
            max_dt = dt

    if not max_dt:
        print("⚠ Nenhum login válido encontrado.")
        print(f"✓ Login rows lidas: {len(login_rows)}")
        sample_dates = [str(r.get('ATTEMPTDATE', '')).strip() for r in login_rows[:5]]
        print(f"✓ Amostra ATTEMPTDATE: {sample_dates}")
        return


    window_start = max_dt - timedelta(days=LOOKBACK_DAYS)
    session_delta = timedelta(minutes=SESSION_MINUTES)

    concurrent_users_by_hour = defaultdict(set)
    for rec in login_rows:
        result = (rec.get("ATTEMPTRESULT") or "").strip().upper()
        if result != "LOGIN":
            continue

        userid = _normalize_userid(rec.get("USERID"))
        dt = _parse_dt(rec.get("ATTEMPTDATE"))
        if not userid or not dt or dt < window_start:
            continue

        active_until = dt + session_delta
        bucket = dt.replace(minute=0, second=0, microsecond=0)
        while bucket <= active_until:
            if bucket >= window_start:
                concurrent_users_by_hour[bucket].add(userid)
            bucket += timedelta(hours=1)

    hourly_counts = {}
    hourly_app_points = {}
    hourly_concurrent_app_points = {}
    hourly_app_points_nem = {}
    hourly_app_points_nem_by_scope = {
        "foresea": {},
        "terceiros": {},
        "integracao": {},
        "todos": {},
    }

    for bucket, users in concurrent_users_by_hour.items():
        hourly_counts[bucket] = len(users)

        concurrent_cost = 0
        total_cost = 0
        concurrent_cost_by_scope = {"foresea": 0, "terceiros": 0, "integracao": 0}

        for uid in users:
            record = golden.get(uid)
            if not record:
                continue

            total_cost += record["cost"]
            if "CONCURRENT" in record["license"]:
                concurrent_cost += record["cost"]
                concurrent_cost_by_scope[record["scope"]] += record["cost"]

        hourly_app_points[bucket] = total_cost
        hourly_concurrent_app_points[bucket] = concurrent_cost
        hourly_app_points_nem[bucket] = authorized_reserved + concurrent_cost
        for scope_key in ("foresea", "terceiros", "integracao"):
            hourly_app_points_nem_by_scope[scope_key][bucket] = authorized_reserved_by_scope[scope_key] + concurrent_cost_by_scope[scope_key]
        hourly_app_points_nem_by_scope["todos"][bucket] = hourly_app_points_nem[bucket]

    if not hourly_app_points_nem:
        print("⚠ Nenhum dado de concorrência calculado.")
        return

    peak_hour = max(hourly_app_points_nem.items(), key=lambda x: x[1])
    true_total_app_points = peak_hour[1]

    peak_hour_dt = peak_hour[0]
    peak_contributors_list = []
    if peak_hour_dt in concurrent_users_by_hour:
        peak_users = concurrent_users_by_hour[peak_hour_dt]
        for uid in peak_users:
            record = golden.get(uid)
            if not record:
                continue
            peak_contributors_list.append({
                "userid": uid,
                "app_points": record["cost"],
                "license_type": record["license"],
                "scope": record["scope"]
            })

    peak_contributors_list.sort(key=lambda x: x["app_points"], reverse=True)
    peak_contributors = peak_contributors_list[:50]

    metrics = {
        "unique_human_users": len(golden),
        "authorized_reserved_points": authorized_reserved,
        "authorized_reserved_points_by_scope": authorized_reserved_by_scope,
        "true_total_app_points": true_total_app_points,
        "hourly_counts": {_fmt_hour(h): v for h, v in hourly_counts.items()},
        "hourly_app_points": {_fmt_hour(h): v for h, v in hourly_app_points.items()},
        "hourly_concurrent_app_points": {_fmt_hour(h): v for h, v in hourly_concurrent_app_points.items()},
        "hourly_app_points_nem": {_fmt_hour(h): v for h, v in hourly_app_points_nem.items()},
        "hourly_app_points_nem_by_scope": {
            scope_key: {_fmt_hour(h): v for h, v in scope_values.items()}
            for scope_key, scope_values in hourly_app_points_nem_by_scope.items()
        },
        "peak_hours": [[_fmt_hour(peak_hour[0]), peak_hour[1]]],
        "peak_hours_users": sorted(
            [[_fmt_hour(h), v] for h, v in hourly_counts.items()],
            key=lambda x: x[1],
            reverse=True
        )[:24],
        "peak_contributors": peak_contributors,
        "peak_contributors_count": len(peak_contributors),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "true_capacity_metrics.json"
    out_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Campos gravados: {', '.join(sorted(metrics.keys()))}")

    print(f"✅ JSON atualizado: {out_path}")



if __name__ == "__main__":
    main()
