# scripts/services/app_points.py
import pandas as pd
import numpy as np
from scripts.analysis.classification import classify_usage_profile
from scripts.analysis.licensing import assign_license_model
from scripts.analysis.entitlement import determine_user_entitlement, calculate_app_points


def calculate_statistical_concurrency():
    """
    Motor Científico de Dados (High Watermark Analysis):
    Lê os logs de acesso diários e cruza com a contagem total de funcionários por cargo.
    Retorna os percentis P50 (Mediana/Cotidiano), P95 (Pico de Turno) e P100 (Worst Case/Emergência).
    """
    try:
        track_df = pd.read_csv('output/consolidated/consolidated_logintracking.csv')
        user_df = pd.read_csv('output/consolidated/consolidated_user_identity.csv')

        if 'ATTEMPTRESULT' in track_df.columns:
            track_df = track_df[track_df['ATTEMPTRESULT'].str.upper() == 'LOGIN']

        track_df['ATTEMPTDATE'] = pd.to_datetime(track_df['ATTEMPTDATE'])
        track_df['LOGIN_DAY'] = track_df['ATTEMPTDATE'].dt.date

        # FIX: Use 'TITLE' instead of 'TITLES'
        merged_df = pd.merge(track_df, user_df, on='USERID', how='inner')

        # 1. Contagem de logins únicos POR DIA POR CARGO
        daily_active = merged_df.groupby(['LOGIN_DAY', 'TITLE'])['USERID'].nunique().reset_index()
        daily_active.rename(columns={'USERID': 'ACTIVE_USERS'}, inplace=True)

        # 2. Contagem do passivo físico total POR CARGO
        total_users = user_df.groupby('TITLE')['USERID'].nunique().reset_index()
        total_users.rename(columns={'USERID': 'TOTAL_USERS'}, inplace=True)

        # 3. Cruzamento para achar a Taxa de Concorrência Diária
        stats_df = pd.merge(daily_active, total_users, on='TITLE')
        stats_df['DAILY_RATIO'] = stats_df['ACTIVE_USERS'] / stats_df['TOTAL_USERS']

        # 4. Cálculo dos Percentis Estatísticos
        percentiles = stats_df.groupby('TITLE')['DAILY_RATIO'].agg(
            p50=lambda x: np.percentile(x, 50),
            p95=lambda x: np.percentile(x, 95),
            p100='max'
        ).reset_index()

        # Converte para dicionário aninhado: { 'Cargo': {'p50': 0.2, 'p95': 0.4, 'p100': 0.8} }
        return percentiles.set_index('TITLE').to_dict('index')
    except Exception as e:
        print(f"[Aviso Data Science] Fallback ativado. Erro no logintracking: {e}")
        return {}


def simulate_app_points(profiles_to_simulate):
    """
    Simulação avançada aplicando as Regras Críticas O&G e os Fatores Estatísticos.
    """
    app_points_data = []
    stat_map = calculate_statistical_concurrency()

    for profile in profiles_to_simulate:
        usage = classify_usage_profile(len(profile['GROUPS']))
        entitlement = determine_user_entitlement(profile['GROUPS'])

        display_names = [str(n).strip() for n in profile.get('DISPLAYNAME', []) if n and str(n).strip()]
        titles = [str(t).strip() for t in profile.get('TITLES', []) if t and str(t).strip()]
        cargo_principal = titles[0] if titles else "SEM CARGO"

        license_model = assign_license_model(usage, titles)
        points = calculate_app_points(entitlement, license_model)

        login_count = profile.get('LOGIN_COUNT_90D', 0)

        # Otimização Inteligente
        if login_count == 0:
            rec = "INATIVO (>90d)"
        elif license_model == "AUTHORIZED" and login_count < 15:
            rec = "MOVE_TO_CONCURRENT"
        elif entitlement == "PREMIUM" and "OIL" not in "".join(titles).upper():
            rec = "DOWNGRADE_CANDIDATE"
        else:
            rec = "CONFIRMED_AUTHORIZED"

        # Busca os fatores estatísticos reais do cargo. Se não existir, usa médias seguras de O&G.
        cargo_stats = stat_map.get(cargo_principal, {'p50': 0.33, 'p95': 0.50, 'p100': 0.85})

        # Limita os fatores entre 10% (mínimo irreal) e 100% (absoluto)
        f_p50 = max(0.10, min(cargo_stats['p50'], 1.0))
        f_p95 = max(0.15, min(cargo_stats['p95'], 1.0))
        f_p100 = max(0.20, min(cargo_stats['p100'], 1.0))

        app_points_data.append({
            'USERID': profile['USERID'],
            'DISPLAYNAME': '; '.join(display_names) if display_names else "N/A",
            'ENTITLEMENT': entitlement,
            'LICENSE_MODEL': license_model,
            'APP_POINTS': points,
            'TITLES': '; '.join(titles) if titles else "N/A",
            'OPTIMIZATION_REC': rec,
            'LOGIN_COUNT_90D': login_count,
            'FACTOR_P50': f_p50,
            'FACTOR_P95': f_p95,
            'FACTOR_P100': f_p100
        })
    return app_points_data