# scripts/services/app_points.py
import pandas as pd
import os
from scripts.analysis.classification import classify_usage_profile, assign_license_model
from scripts.analysis.entitlement import determine_user_entitlement, calculate_app_points


def calculate_real_concurrency_factor():
    """
    Motor Analytics: Lê os logs reais de produção da Foresea para determinar
    a taxa exata de concorrência por cargo, abandonando a média de mercado.
    """
    try:
        # Tenta carregar o tracking real do pipeline
        track_df = pd.read_csv('output/consolidated/consolidated_logintracking.csv')
        user_df = pd.read_csv('output/consolidated/consolidated_user_identity.csv')

        # Filtra apenas logins com sucesso
        if 'ATTEMPTRESULT' in track_df.columns:
            track_df = track_df[track_df['ATTEMPTRESULT'].str.upper() == 'LOGIN']

        # Converte a data e arredonda para o Dia (visão de turno offshore 12h/24h)
        track_df['ATTEMPTDATE'] = pd.to_datetime(track_df['ATTEMPTDATE'])
        track_df['LOGIN_DAY'] = track_df['ATTEMPTDATE'].dt.date

        # Junta com os cargos dos usuários
        merged_df = pd.merge(track_df, user_df, on='USERID', how='inner')

        # 1. Calcula o Pico Diário de usuários únicos logados POR CARGO
        daily_active_by_title = merged_df.groupby(['LOGIN_DAY', 'TITLES'])['USERID'].nunique().reset_index()
        peak_by_title = daily_active_by_title.groupby('TITLES')['USERID'].max().reset_index()
        peak_by_title.rename(columns={'USERID': 'PEAK_CONCURRENT_USERS'}, inplace=True)

        # 2. Calcula o Total de pessoas físicas registradas naquele cargo
        total_by_title = user_df.groupby('TITLES')['USERID'].nunique().reset_index()
        total_by_title.rename(columns={'USERID': 'TOTAL_PHYSICAL_USERS'}, inplace=True)

        # 3. Calcula o Fator Exato de Escala
        ratio_df = pd.merge(peak_by_title, total_by_title, on='TITLES')
        ratio_df['REAL_FACTOR'] = ratio_df['PEAK_CONCURRENT_USERS'] / ratio_df['TOTAL_PHYSICAL_USERS']

        # Retorna um dicionário { 'Cargo': Fator Float }
        return dict(zip(ratio_df['TITLES'], ratio_df['REAL_FACTOR']))
    except Exception as e:
        print(f"[Aviso Analytics] Não foi possível processar o logintracking para concorrência real: {e}")
        return {}  # Retorna dicionário vazio, fallback de segurança ativado abaixo


def simulate_app_points(profiles_to_simulate):
    """
    Executa a simulação de AppPoints cruzando a regra de negócio do MAS 9
    com a concorrência real extraída do banco de dados.
    """
    app_points_data = []

    # Aciona o motor de analytics do logintracking
    real_concurrency_map = calculate_real_concurrency_factor()

    for profile in profiles_to_simulate:
        usage = classify_usage_profile(len(profile['GROUPS']))
        entitlement = determine_user_entitlement(profile['GROUPS'])

        # Saneamento crítico de strings
        display_names = [str(n).strip() for n in profile.get('DISPLAYNAME', []) if n and str(n).strip()]
        titles = [str(t).strip() for t in profile.get('TITLES', []) if t and str(t).strip()]
        cargo_principal = titles[0] if titles else "SEM CARGO"

        license_model = assign_license_model(usage, titles)
        points = calculate_app_points(entitlement, license_model)

        # Determinação da recomendação de otimização
        login_count = profile.get('LOGIN_COUNT_90D', 0)
        if login_count == 0:
            rec = "INATIVO (>90d)"
        elif license_model == "AUTHORIZED" and login_count < 15:
            rec = "MOVE_TO_CONCURRENT"
        elif entitlement == "PREMIUM" and "OIL" not in "".join(titles).upper():
            rec = "DOWNGRADE_CANDIDATE"
        else:
            rec = "CONFIRMED_AUTHORIZED"

        # Busca o fator de concorrência real calculado pelo logintracking.
        # Fallback de segurança: Se for cargo desconhecido, adota a média conservadora (0.33)
        real_factor = real_concurrency_map.get(cargo_principal, 0.3333)

        # Limita o fator entre 10% (mínimo irreal) e 100% (todos logados)
        real_factor = max(0.10, min(real_factor, 1.0))

        app_points_data.append({
            'USERID': profile['USERID'],
            'DISPLAYNAME': '; '.join(display_names) if display_names else "N/A",
            'ENTITLEMENT': entitlement,
            'LICENSE_MODEL': license_model,
            'APP_POINTS': points,
            'USAGE_PROFILE': usage,
            'TITLES': '; '.join(titles) if titles else "N/A",
            'OPTIMIZATION_REC': rec,
            'LOGIN_COUNT_90D': login_count,
            'REAL_FACTOR': real_factor  # <- Nova Métrica de Analytics
        })
    return app_points_data