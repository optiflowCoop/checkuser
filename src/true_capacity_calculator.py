#!/usr/bin/env python3
"""
Fase 4: Cálculo REAL de Capacidade (High-Water Mark)
Modelo único e data-driven.
SEM heurísticas.
"""

import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IN_DIR = ROOT / "output" / "consolidated"
OUT_DIR = ROOT / "output" / "consolidated"

SESSION_MINUTES = 60
LOOKBACK_DAYS = 90


def _load_csv(path):
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _parse_dt(s):
    if not s:
        return None
    text = str(s).strip().rsplit(".", 1)[0]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d-%H.%M.%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            continue
    return None


def _fmt_hour(dt):
    return dt.strftime("%Y-%m-%d %H:00")


def main():
    print("📊 Fase 4: CÁLCULO REAL DE CAPACIDADE (NEM ÚNICO)")

    optimizations_path = IN_DIR / "license_optimization_recommendations.csv"
    logintrack_path = IN_DIR / "consolidated_logintracking.csv"

    optimizations = _load_csv(optimizations_path)
    login_rows = _load_csv(logintrack_path)

    if not optimizations or not login_rows:
        print("❌ Dados insuficientes para cálculo de capacidade.")
        return

    # Golden record
    golden = {}
    for row in optimizations:
        userid = (row.get("USERID") or "").strip().upper()
        if not userid:
            continue

        rec = (row.get("RECOMMENDATION") or "").upper()
        if "DESATIVAR" in rec or "NÃO MIGRAR" in rec:
            continue

        cost = int(row.get("APP_POINTS_COST", 0) or 0)
        lic = (row.get("REQUIRED_LICENSE") or "").strip().upper()

        if userid not in golden or cost > golden[userid]["cost"]:
            golden[userid] = {"cost": cost, "license": lic}

    # Authorized fixo
    authorized_reserved = sum(
        u["cost"] for u in golden.values()
        if "AUTHORIZED" in u["license"]
    )

    # Janela temporal
    max_dt = None
    for rec in login_rows:
        if (rec.get("ATTEMPTRESULT") or "").upper() != "LOGIN":
            continue
        dt = _parse_dt(rec.get("ATTEMPTDATE"))
        if dt and (max_dt is None or dt > max_dt):
            max_dt = dt

    if not max_dt:
        print("⚠ Nenhum login válido encontrado.")
        return

    window_start = max_dt - timedelta(days=LOOKBACK_DAYS)
    session_delta = timedelta(minutes=SESSION_MINUTES)

    concurrent_users_by_hour = defaultdict(set)

    for rec in login_rows:
        if (rec.get("ATTEMPTRESULT") or "").upper() != "LOGIN":
            continue

        userid = (rec.get("USERID") or "").strip().upper()
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

    for bucket, users in concurrent_users_by_hour.items():
        hourly_counts[bucket] = len(users)

        concurrent_cost = 0
        total_cost = 0

        for uid in users:
            record = golden.get(uid)
            if not record:
                continue

            total_cost += record["cost"]
            if "CONCURRENT" in record["license"]:
                concurrent_cost += record["cost"]

        hourly_app_points[bucket] = total_cost
        hourly_concurrent_app_points[bucket] = concurrent_cost
        hourly_app_points_nem[bucket] = authorized_reserved + concurrent_cost

    if not hourly_app_points_nem:
        print("⚠ Nenhum dado de concorrência calculado.")
        return

    peak_hour = max(hourly_app_points_nem.items(), key=lambda x: x[1])
    true_total_app_points = peak_hour[1]

    metrics = {
        "unique_human_users": len(golden),
        "authorized_reserved_points": authorized_reserved,
        "true_total_app_points": true_total_app_points,
        "hourly_counts": {_fmt_hour(h): v for h, v in hourly_counts.items()},
        "hourly_app_points": {_fmt_hour(h): v for h, v in hourly_app_points.items()},
        "hourly_concurrent_app_points": {_fmt_hour(h): v for h, v in hourly_concurrent_app_points.items()},
        "hourly_app_points_nem": {_fmt_hour(h): v for h, v in hourly_app_points_nem.items()},
        "peak_hours": [[_fmt_hour(peak_hour[0]), peak_hour[1]]],
        "peak_hours_users": sorted(
            [[_fmt_hour(h), v] for h, v in hourly_counts.items()],
            key=lambda x: x[1],
            reverse=True
        )[:24],
        "peak_contributors": [],
        "peak_contributors_count": 0,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "true_capacity_metrics.json"
    out_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"✅ JSON atualizado: {out_path}")


if __name__ == "__main__":
    main()