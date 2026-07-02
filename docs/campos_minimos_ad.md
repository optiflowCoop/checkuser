# Campos Mínimos Necessários - Relação AD

## Os 6 Campos Obrigatórios

| Campo | Tipo | Descrição | Finalidade |
|-------|------|-----------|------------|
| `sAMAccountName` | String | Login do usuário no AD | **Match direto com USERID do Maximo** |
| `UserPrincipalName` | String | E-mail institucional | **Match direto com EMAIL do Maximo** |
| `DisplayName` | String | Nome completo | **Validação de identidade** |
| `Mail` | String | E-mail principal | **Confirmação de identidade** |
| `Enabled` | Boolean | Conta ativa/inativa | **Filtrar apenas usuários ativos** |
| `MemberOf` | String | Grupos de segurança | **Identificar permissões de acesso** |

---

## Por que esses 6 campos?

### 1. **sAMAccountName** (CRÍTICO)
- **Propósito**: Login único do usuário no AD
- **Uso**: Comparar diretamente com `USERID` do Maximo
- **Exemplo**: `joao.silva` ↔ `joao.silva`

### 2. **UserPrincipalName** (CRÍTICO)
- **Propósito**: Identificador único no formato email
- **Uso**: Match com campo `EMAIL` do Maximo
- **Exemplo**: `joao.silva@foresea.com.br` ↔ `joao.silva@foresea.com.br`

### 3. **DisplayName** (CRÍTICO)
- **Propósito**: Nome completo para validação visual
- **Uso**: Confirmar que é a mesma pessoa (evita homônimos)
- **Exemplo**: `João Carlos Silva`

### 4. **Mail** (CRÍTICO)
- **Propósito**: E-mail de contato principal
- **Uso**: Validação secundária de identidade
- **Exemplo**: `joao.silva@foresea.com.br`

### 5. **Enabled** (CRÍTICO)
- **Propósito**: Status da conta (ativa/inativa)
- **Uso**: Filtrar apenas contas ativas para análise
- **Exemplo**: `TRUE` (apenas contas ativas)

### 6. **MemberOf** (CRÍTICO)
- **Propósito**: Grupos de segurança aos quais o usuário pertence
- **Uso**: Identificar se usuário tem acesso ao Maximo
- **Exemplo**: `GRP_MAXIMO_USERS;GRP_MAXIMO_ADMIN`

---

## Comando PowerShell Mínimo

```powershell
Get-ADUser -Filter {Enabled -eq $true} -Properties sAMAccountName, UserPrincipalName, DisplayName, Mail, MemberOf | 
Select-Object sAMAccountName, UserPrincipalName, DisplayName, Mail, Enabled, MemberOf | 
Export-Csv -Path "relacao_usuarios_ad.csv" -Encoding UTF8 -NoTypeInformation
```

---

## Exemplo de Saída Esperada (CSV)

```csv
sAMAccountName,UserPrincipalName,DisplayName,Mail,Enabled,MemberOf
joao.silva,joao.silva@foresea.com.br,João Carlos Silva,joao.silva@foresea.com.br,TRUE,GRP_MAXIMO_USERS
maria.souza,maria.souza@foresea.com.br,Maria Souza,maria.souza@foresea.com.br,TRUE,GRP_MAXIMO_ADMIN
carlos.lima,carlos.lima@foresea.com.br,Carlos Lima,carlos.lima@foresea.com.br,FALSE,GRP_MAXIMO_USERS
```

---

## O que NÃO precisa (por enquanto):

❌ Dados pessoais detalhados (telefone, endereço, matrícula)  
❌ Datas de criação/modificação  
❌ Informações de hierarquia (gestor, departamento)  
❌ Dados de expiração de conta

**Esses campos podem ser solicitados posteriormente se necessário para análises mais profundas.**

---

## Resumo

**Mínimo viável = 6 campos** que permitem:
1. ✅ Match direto entre Maximo e AD
2. ✅ Identificação de duplicatas
3. ✅ Detecção de órfãos
4. ✅ Validação de identidade
5. ✅ Verificação de permissões de acesso

Com apenas esses 6 campos, já é possível fazer 90% do trabalho de consolidação de identidades.