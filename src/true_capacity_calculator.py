#!/usr/bin/env python3
"""src/true_capacity_calculator.py

Fase 4: Cálculo Real de AppPoints (Data Science)

Objetivo (para alimentar a aba Peak do dashboard):
- Ler consolidated_logintracking.csv
- Assumir sessão ativa por janela (SESSION_MINUTES)
- Buckets por hora (últimas 48h)
- Calcular simultâneos por hora (hourly_counts)
- Somar custo de AppPoints por USERID (usage_analysis_phase3.csv -> APP_POINTS_COST)
- Persistir em output/consolidated/true_capacity_metrics.json com schema:
  - hourly_counts: {"YYYY-MM-DD HH:00": int}
  - hourly_app_points: {"YYYY-MM-DD HH:00": int}
  - peak_hours: [["YYYY-MM-DD HH:00", int_points], ...]
"""

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.rules_manager import rules_manager

IN_DIR = ROOT / "output" / "consolidated"
OUT_DIR = ROOT / "output" / "consolidated"


def _load_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _parse_dt(val):
    if not val:
        return None
    s = str(val).strip()
    if not s:
        return None
    try:
        # ISO (ex: 2026-03-27 05:24:26.059000) e variantes
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        pass

    # fallbacks comuns
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d-%H.%M.%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None


def main():
    print("📊 Fase 4: CÁLCULO DE CAPACIDADE REAL (Golden Record & High-Water Mark)")

    optimizations_path = IN_DIR / "license_optimization_recommendations.csv"
    optimizations = _load_csv(optimizations_path)
    if not optimizations:
        print("❌ ERRO: license_optimization_recommendations.csv não encontrado.")
        return

    # 1) Deduplicação por email (Golden Record)
    golden_records = {}
    for row in optimizations:
        email = (row.get("EMAIL") or "").strip().lower()
        if not email or email == "none":
            email = (row.get("USERID") or "UNKNOWN").strip().upper()

        try:
            cost = int(row.get("APP_POINTS_COST", 0) or 0)
        except Exception:
            cost = 0

        rec_type = row.get("RECOMMENDATION", "") or ""
        req_lic = row.get("REQUIRED_LICENSE", "") or ""

        if "DESATIVAR" in rec_type or "NÃO MIGRAR" in rec_type:
            continue

        if email not in golden_records:
            golden_records[email] = {
                "email": email,
                "max_cost": cost,
                "license_type": req_lic,
            }
        else:
            if cost > golden_records[email]["max_cost"]:
                golden_records[email]["max_cost"] = cost
                golden_records[email]["license_type"] = req_lic

    print(f"✓ Deduplicação: De {len(optimizations)} acessos para {len(golden_records)} pessoas reais.")

    # 2) Authorized vs Concurrent (estimativa baseada no tipo)
    authorized_cost = 0
    concurrent_pool = []

    for _, data in golden_records.items():
        lic_type = data.get("license_type", "") or ""
        cost = int(data.get("max_cost", 0) or 0)

        if "AUTHORIZED" in lic_type:
            authorized_cost += cost
        elif "CONCURRENT" in lic_type:
            concurrent_pool.append(cost)

    raw_concurrent_cost = sum(concurrent_pool)

    # Heurística pico: 35%
    CONCURRENCY_FACTOR = 0.35
    peak_concurrent_cost = int(raw_concurrent_cost * CONCURRENCY_FACTOR)

    true_total_app_points = authorized_cost + peak_concurrent_cost
    contracted = rules_manager.capacity.get("contracted_app_points", 1200)

    print("\n=======================================================")
    print("💰 RESUMO FINANCEIRO E DE LICENCIAMENTO (REALIDADE)")
    print("=======================================================")
    print(f"🔹 Custo Fixo (Authorized Dedicado):     {authorized_cost} AppPoints")
    print(
        f"🔹 Custo Variável (Pico de Concurrent):  {peak_concurrent_cost} AppPoints (calculado via fator {CONCURRENCY_FACTOR * 100}%)"
    )
    print("-------------------------------------------------------")
    print(f"📈 TOTAL ESTIMADO DE APP POINTS:         {true_total_app_points} AppPoints")
    print(f"📦 CAPACIDADE CONTRATADA MAS:            {contracted} AppPoints")
    print("=======================================================\n")

    if true_total_app_points > contracted:
        print(f"🚨 ALERTA: Estamos em DEFICIT de {true_total_app_points - contracted} AppPoints.")
    else:
        print(f"✅ SAUDÁVEL: Temos uma folga de {contracted - true_total_app_points} AppPoints.")

    # 3) Simultaneidade e custo por hora (últimas 48h)
    SESSION_MINUTES = 60
    session_delta = timedelta(minutes=SESSION_MINUTES)

    logintrack_path = IN_DIR / "consolidated_logintracking.csv"

    # USERID -> APP_POINTS_COST (para custo por bucket)
    usage_path = IN_DIR / "usage_analysis_phase3.csv"
    user_cost = {}
    if usage_path.exists():
        usage_rows = _load_csv(usage_path)
        for ur in usage_rows:
            uid = (ur.get("USERID") or "").strip().upper()
            if not uid:
                continue
            try:
                user_cost[uid] = float(ur.get("APP_POINTS_COST", 0) or 0)
            except Exception:
                user_cost[uid] = 0.0

    hourly_counts = defaultdict(int)  # bucket -> num users ativos
    concurrent_users_by_hour = defaultdict(set)  # bucket -> set users ativos
    hourly_app_points = defaultdict(float)  # bucket -> soma custo

    # Janela baseada no tempo máximo real presente nos dados.
    max_dt = None
    for rec in _load_csv(logintrack_path):
        userid = (rec.get("USERID") or "").strip().upper()
        attempt_raw = rec.get("ATTEMPTDATE") or rec.get("ATTEMPT_DATE") or rec.get("DATE") or ""
        dt = _parse_dt(attempt_raw)
        if userid and dt and (max_dt is None or dt > max_dt):
            max_dt = dt
    if max_dt is None:
        max_dt = datetime.now()
    window_start = max_dt - timedelta(hours=48)

    if not logintrack_path.exists():
        print(f"[Aviso] LOGINTRACKING não encontrado: {logintrack_path}")
    else:
        login_rows = _load_csv(logintrack_path)
        # Deduplicar por evento id? Aqui mantemos simples; o set por bucket previne double-count do mesmo user.
        for rec in login_rows:
            userid = (rec.get("USERID") or "").strip().upper()
            attempt_raw = rec.get("ATTEMPTDATE") or rec.get("ATTEMPT_DATE") or rec.get("DATE") or ""
            dt = _parse_dt(attempt_raw)
            if not userid or not dt:
                continue

            # ignora eventos muito antigos
            if dt < (window_start - session_delta):
                continue


            active_until = dt + session_delta

            bucket = dt.replace(minute=0, second=0, microsecond=0)
            while bucket <= active_until:
                if bucket < window_start:
                    bucket = bucket + timedelta(hours=1)
                    continue
                concurrent_users_by_hour[bucket].add(userid)
                hourly_counts[bucket] += 0  # garante chave
                bucket = bucket + timedelta(hours=1)

        for bucket, users in concurrent_users_by_hour.items():
            hourly_counts[bucket] = len(users)
            total_pts = 0.0
            for uid in users:
                total_pts += float(user_cost.get(uid, 0) or 0)
            hourly_app_points[bucket] = total_pts

    # 4) peak_hours (top 24 buckets por app points)
    sorted_hours_pts = sorted(hourly_app_points.items(), key=lambda x: x[1], reverse=True)
    top_buckets = sorted_hours_pts[:24]

    # 4b) peak_hours_users (top 24 buckets por usuários simultâneos)
    sorted_hours_users = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)
    top_buckets_users = sorted_hours_users[:24]

    def _fmt_hour(dt):
        return dt.strftime("%Y-%m-%d %H:00")

    # AppPoints peak buckets (consumo)
    peak_hours = [[_fmt_hour(h), int(round(pts))] for h, pts in top_buckets]

    # Usuários simultâneos peak buckets (capacidade)
    peak_hours_users = [[_fmt_hour(h), int(v)] for h, v in top_buckets_users]

    # 5) Persistir JSON (consumido pelo HTML)
    metrics = {
        "unique_human_users": len(golden_records),
        "authorized_reserved_points": authorized_cost,
        "concurrent_pool_raw_points": raw_concurrent_cost,
        "concurrent_peak_estimated_points": peak_concurrent_cost,
        "true_total_app_points": true_total_app_points,
        "contracted_app_points": contracted,
        "hourly_counts": {_fmt_hour(h): int(v) for h, v in sorted(hourly_counts.items())},
        "hourly_app_points": {_fmt_hour(h): int(round(v)) for h, v in sorted(hourly_app_points.items())},
        "peak_hours": peak_hours,  # AppPoints
        "peak_hours_users": peak_hours_users,  # Usuários simultâneos
        "peak_contributors": [],
        "peak_contributors_count": 0,
    }


    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "true_capacity_metrics.json"
    out_path.write_text(json.dumps(metrics, indent=4), encoding="utf-8")

    print(f"✅ Arquivo gerado: {out_path}")


if __name__ == "__main__":
    main()

