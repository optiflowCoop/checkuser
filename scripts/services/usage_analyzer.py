# services/usage_analyzer.py
import random
from datetime import datetime, timedelta

def analyze_usage(user_profiles):
    """
    Simula a análise da tabela LOGINTRACKING para gerar insights de uso real.
    """
    for profile in user_profiles:
        # --- Simulação de Dados de LOGINTRACKING ---
        # Na versão final, isso virá do CSV ou do banco.
        
        # 1. Total de Logins (0 a 100)
        login_count = random.randint(0, 100)
        
        # 2. Dias desde o último login
        days_since_last = random.randint(1, 150)
        
        # 3. Uso de Módulos Premium (Simulação baseada no Entitlement)
        # Se tem Premium, 30% de chance de NÃO ter usado (Downgrade Candidate)
        used_premium = False
        if profile.get('ENTITLEMENT') == 'PREMIUM':
             used_premium = random.choice([True, True, True, False])

        # --- Lógica de Recomendação (Inteligência) ---
        recommendation = "OK"
        reason = ""

        if days_since_last > 90:
             recommendation = "INATIVO (>90d)"
             reason = "Usuário sem atividade recente. Avaliar bloqueio."
        elif profile.get('ENTITLEMENT') == 'PREMIUM' and not used_premium:
             recommendation = "DOWNGRADE_CANDIDATE"
             reason = "Possui permissão Premium, mas não utiliza módulos O&G."
        elif profile.get('LICENSE_MODEL') == 'AUTHORIZED' and login_count < 20:
             recommendation = "MOVE_TO_CONCURRENT"
             reason = "Custo Authorized, mas com baixa frequência de acesso."
        elif profile.get('LICENSE_MODEL') == 'AUTHORIZED' and login_count >= 20:
             recommendation = "CONFIRMED_AUTHORIZED"
             reason = "Alto uso confirmado."

        # Adicionar os insights ao perfil
        profile['LOGIN_COUNT_90D'] = login_count
        profile['DAYS_SINCE_LAST'] = days_since_last
        profile['USED_PREMIUM'] = used_premium
        profile['OPTIMIZATION_REC'] = recommendation
        profile['OPTIMIZATION_REASON'] = reason

    return user_profiles
