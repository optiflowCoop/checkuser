# services/usage_analyzer.py

def analyze_usage(user_profiles):
    """Gera/normaliza OPTIMIZATION_REC e OPTIMIZATION_REASON usando dados já calculados upstream.

    Importante: este módulo não deve simular (random). Ele deve ser determinístico e baseado
    em campos presentes em `profile` gerados pelo pipeline (ex.: app_points.py / true_capacity_calculator.py).
    """

    for profile in user_profiles:
        # Valores já deveriam existir no profile; se não existirem, assume defaults seguros.
        login_count = int(profile.get("LOGIN_COUNT_90D") or 0)
        days_since_last = profile.get("DAYS_SINCE_LAST")
        try:
            days_since_last = int(days_since_last) if days_since_last != "" else 0
        except (TypeError, ValueError):
            days_since_last = 0

        ent = (profile.get("ENTITLEMENT") or "").strip().upper()
        license_model = (profile.get("LICENSE_MODEL") or "").strip().upper()

        # Regras determinísticas (mesmas categorias usadas no dashboard/plano).
        recommendation = "OK"
        reason = ""

        if days_since_last > 90:
            recommendation = "INATIVO (>90d)"
            reason = "Usuário sem atividade recente. Avaliar bloqueio."
        elif ent == "PREMIUM" and not profile.get("USED_PREMIUM", True):
            # USED_PREMIUM deve ser preenchido upstream se existir; se não existir, consideramos True.
            recommendation = "DOWNGRADE_CANDIDATE"
            reason = "Possui permissão Premium, mas não utiliza módulos O&G."
        elif license_model == "AUTHORIZED" and login_count < 30:
            recommendation = "MOVE_TO_CONCURRENT"
            reason = "Custo Authorized, mas com baixa frequência de acesso."
        elif license_model == "AUTHORIZED" and login_count >= 30:
            recommendation = "CONFIRMED_AUTHORIZED"
            reason = "Alto uso confirmado."

        profile["LOGIN_COUNT_90D"] = login_count
        profile["DAYS_SINCE_LAST"] = days_since_last
        profile["OPTIMIZATION_REC"] = recommendation
        profile["OPTIMIZATION_REASON"] = reason

        # Mantém USED_PREMIUM sem inventar aleatoriedade.
        if "USED_PREMIUM" not in profile:
            profile["USED_PREMIUM"] = True

    return user_profiles

