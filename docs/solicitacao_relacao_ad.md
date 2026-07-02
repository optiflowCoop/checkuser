# Solicitação de Relação de Usuários - Active Directory

**Data:** 01/07/2026  
**Solicitante:** Equipe de Governança de Identidades  
**Destinatário:** Time de Tecnologia / Infraestrutura  
**Prioridade:** Alta  
**Prazo Sugerido:** 5 dias úteis

---

## 1. Contexto e Propósito

### 1.1 Cenário Atual
Atualmente, o sistema Maximo opera com múltiplas instâncias (BASE, ODN1, ODN2, N06, N08, N09, HTQ), cada uma com sua própria base de usuários. Isso resulta em:
- **Duplicação de identidades**: Um mesmo usuário pode ter credenciais diferentes em cada ambiente
- **Fragmentação de acesso**: Dificuldade em rastrear atividades cross-ambiente
- **Sobrecarga de licenciamento**: Usuários duplicados consumindo licenças desnecessariamente

### 1.2 Nova Arquitetura
Com a implementação do **SML (Single Sign-On) com MFA**, teremos:
- **Login unificado**: Um único conjunto de credenciais para todos os ambientes Maximo
- **Autenticação centralizada**: Gerenciada pelo Active Directory (AD)
- **Eliminação de duplicatas**: Cada usuário terá exatamente uma identidade no ecossistema

### 1.3 Objetivo da Solicitação
Para garantir a **consolidação correta de identidades** durante a migração, precisamos confrontar:
1. **Usuários existentes no Maximo** (extraídos via queries SQL)
2. **Usuários existentes no AD** (fonte da verdade para autenticação)

Isso permitirá:
- ✅ Identificar duplicatas e consolidar em um único login
- ✅ Mapear qual usuário do Maximo corresponde a qual usuário do AD
- ✅ Detectar usuários órfãos (existem no Maximo mas não no AD)
- ✅ Detectar usuários com acesso indevido (existem no AD mas não no Maximo)
- ✅ Validar atributos críticos (nome, email, departamento, grupo)

---

## 2. Campos Solicitados no Relatório

### 2.1 Campos Obrigatórios (Mínimo Viável)

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `sAMAccountName` | String | Login do usuário no AD | `joao.silva` |
| `UserPrincipalName` | String | UPN completo (email institucional) | `joao.silva@foresea.com.br` |
| `DisplayName` | String | Nome completo do usuário | `João Carlos Silva` |
| `GivenName` | String | Primeiro nome | `João` |
| `Surname` | String | Sobrenome | `Carlos Silva` |
| `Mail` | String | E-mail principal | `joao.silva@foresea.com.br` |
| `Department` | String | Departamento/Setor | `TI - Infraestrutura` |
| `Title` | String | Cargo/Função | `Analista de Sistemas` |
| `MemberOf` | String | Grupos de segurança (separados por `;`) | `GRP_MAXIMO_USERS;GRP_MAXIMO_ADMIN` |
| `Enabled` | Boolean | Conta ativa/inativa | `TRUE` / `FALSE` |
| `WhenCreated` | DateTime | Data de criação da conta | `2020-03-15 10:30:00` |
| `WhenChanged` | DateTime | Última modificação | `2025-06-20 14:22:10` |
| `LastLogonDate` | DateTime | Último login no AD | `2025-06-28 08:15:30` |

### 2.2 Campos Desejáveis (Alta Prioridade)

| Campo | Tipo | Descrição | Finalidade |
|-------|------|-----------|------------|
| `DistinguishedName` | String | DN completo do usuário | Identificação única no AD |
| `ObjectGUID` | GUID | GUID do objeto AD | Chave primária técnica |
| `EmployeeID` | String | Matrícula/RH | Correlação com sistema de RH |
| `TelephoneNumber` | String | Telefone corporativo | Contato alternativo |
| `Office` | String | Localização física | `São Paulo - SP` |
| `Company` | String | Empresa/Subsidiária | `FORESEA` / `PARCEIRO` |
| `Manager` | String | Gestor direto (DN ou UPN) | Hierarquia organizacional |
| `AccountExpirationDate` | DateTime | Data de expiração | Identificar contas temporárias |

### 2.3 Campos Opcionais (Baixa Prioridade)

| Campo | Tipo | Descrição | Finalidade |
|-------|------|-----------|------------|
| `Description` | String | Descrição da conta | Notas adicionais |
| `Info` | String | Campo informativo | Observações técnicas |
| `ScriptPath` | String | Script de logon | Auditoria de autenticação |
| `HomeDirectory` | String | Diretório home | Mapeamento de pastas |
| `ProfilePath` | String | Caminho do perfil | Perfil roaming |

---

## 3. Formato de Entrega

### 3.1 Estrutura do Arquivo
- **Formato:** CSV (UTF-8 com BOM) ou Excel (.xlsx)
- **Delimitador:** `;` (ponto e vírgula) ou `,` (vírgula)
- **Encoding:** UTF-8
- **Nome do arquivo:** `relacao_usuarios_ad_YYYYMMDD.csv` (ex: `relacao_usuarios_ad_20250701.csv`)

### 3.2 Estrutura de Diretórios Sugerida
```
\\servidor\compartilhamento\governanca_identidades\
├── 2025-07-01\
│   ├── relacao_usuarios_ad_20250701.csv
│   ├── relacao_usuarios_ad_20250701.xlsx
│   └── README.txt
```

### 3.3 Cabeçalho Esperado (CSV)
```csv
sAMAccountName;UserPrincipalName;DisplayName;GivenName;Surname;Mail;Department;Title;MemberOf;Enabled;WhenCreated;WhenChanged;LastLogonDate;DistinguishedName;ObjectGUID;EmployeeID;TelephoneNumber;Office;Company;Manager;AccountExpirationDate
joao.silva;joao.silva@foresea.com.br;João Carlos Silva;João;Carlos Silva;joao.silva@foresea.com.br;TI - Infraestrutura;Analista de Sistemas;GRP_MAXIMO_USERS;TRUE;2020-03-15 10:30:00;2025-06-20 14:22:10;2025-06-28 08:15:30;CN=João Silva,OU=Users,DC=foresea,DC=com,DC=br;{GUID-AQUI};12345;+55-11-99999-9999;São Paulo;FORESEA;CN=Gestor,OU=Users,DC=foresea,DC=com,DC=br;
```

---

## 4. Filtros e Critérios de Extração

### 4.1 Filtros Obrigatórios
- **Apenas contas de usuário** (tipo `user`): Excluir computadores, grupos, OUs
- **Apenas contas habilitadas** (`Enabled = TRUE`): Foco em usuários ativos
- **Excluir contas de serviço**: Filtrar por `Title` ou `Description` contendo "Service", "Sistema", "Automático"
- **Excluir contas de sistema**: `sAMAccountName` começando com `$`, `NT AUTHORITY`, `IUSR`, etc.

### 4.2 Filtros Desejáveis
- **Apenas usuários com login nos últimos 90 dias**: `LastLogonDate >= DATA - 90 dias`
- **Apenas departamentos relevantes**: Filtrar por `Department` contendo termos como "Maximo", "Manutenção", "Operações", "Engenharia"
- **Incluir contas com expiração futura**: `AccountExpirationDate IS NULL OR AccountExpirationDate >= HOJE`

### 4.3 Unidades Organizacionais (OUs) de Interesse
Por favor, incluir **todas as OUs** que contenham usuários com acesso ao Maximo:
- `OU=Users,DC=foresea,DC=com,DC=br`
- `OU=Parceiros,DC=foresea,DC=com,DC=br`
- `OU=Terceiros,DC=foresea,DC=com,DC=br`
- `OU=Integracao,DC=foresea,DC=com,DC=br`

---

## 5. Processo de Validação e Confrontação

### 5.1 Metodologia de Matching
Após receber o relatório do AD, executaremos o seguinte processo:

```
1. NORMALIZAÇÃO
   - Converter todos os logins para UPPERCASE
   - Remover espaços e caracteres especiais
   - Padronizar formato de e-mail

2. MATCHING DIRETO (Alta Confiança)
   - sAMAccountName == USERID_Maximo
   - UserPrincipalName == EMAIL_Maximo
   - EmployeeID == MATRICULA_RH

3. MATCHING FUZZY (Média Confiança)
   - Similaridade de nome > 90%
   - Mesmo domínio de e-mail
   - Mesmo departamento + cargo similar

4. ANÁLISE MANUAL (Baixa Confiança)
   - Usuários sem match direto
   - Possíveis homônimos
   - Casos de divergência
```

### 5.2 Critérios de Consolidação
Um usuário será consolidado (merge) se:
- ✅ Match direto por login ou e-mail
- ✅ Nome similar (>90% de similaridade)
- ✅ Mesmo EmployeeID/Matrícula
- ✅ Mesmo departamento + cargo idêntico

Um usuário será mantido separado se:
- ❌ Nomes diferentes (ex: José Silva vs José Santos)
- ❌ Departamentos diferentes
- ❌ Sem correspondência no AD (órfão)

---

## 6. Exemplo de Uso dos Dados

### 6.1 Cenário 1: Match Direto
**Maximo:** `USERID=joao.silva`, `EMAIL=joao.silva@foresea.com.br`  
**AD:** `sAMAccountName=joao.silva`, `UPN=joao.silva@foresea.com.br`  
**Resultado:** ✅ **Match confirmado** - Consolidar em único login

### 6.2 Cenário 2: Duplicata no Maximo
**Maximo Ambiente 1:** `USERID=joao.silva`, `EMAIL=joao.silva@foresea.com.br`  
**Maximo Ambiente 2:** `USERID=joao.silva2`, `EMAIL=joao.silva@foresea.com.br`  
**AD:** `sAMAccountName=joao.silva`  
**Resultado:** ✅ **Duplicata identificada** - Manter apenas `joao.silva`, desativar `joao.silva2`

### 6.3 Cenário 3: Órfão
**Maximo:** `USERID=carlos.silva`, `EMAIL=carlos.silva@foresea.com.br`  
**AD:** *(não encontrado)*  
**Resultado:** ⚠️ **Órfão** - Verificar se é ex-funcionário ou erro de cadastro

### 6.4 Cenário 4: Acesso Indevido
**Maximo:** *(não encontrado)*  
**AD:** `sAMAccountName=maria.souza`, `MemberOf=GRP_MAXIMO_USERS`  
**Resultado:** ⚠️ **Acesso indevido** - Remover do grupo `GRP_MAXIMO_USERS` no AD

---

## 7. Benefícios Esperados

### 7.1 Redução de Custos
- **Economia de licenças**: Eliminação de duplicatas pode reduzir 10-30% do consumo
- **Otimização de NEM**: Cálculo preciso de capacidade real
- **Redução de sobrecarga**: Menos usuários = menos processamento

### 7.2 Governança e Segurança
- **Rastreabilidade**: Um usuário = um login = uma trilha de auditoria
- **Compliance**: Conformidade com políticas de SSO e MFA
- **Controle de acesso**: RBAC (Role-Based Access Control) centralizado
- **Revogação rápida**: Desativar usuário no AD = bloqueio em todos os ambientes

### 7.3 Experiência do Usuário
- **SSO (Single Sign-On)**: Um login para todos os sistemas
- **MFA unificado**: Mesma autenticação em todos os ambientes
- **Redução de senhas**: Apenas um conjunto de credenciais
- **Suporte simplificado**: Help desk resolve em um lugar

---

## 8. Cronograma Sugerido

| Etapa | Responsável | Prazo | Entregável |
|-------|-------------|-------|------------|
| **1. Extração AD** | Time de Tecnologia | 2 dias úteis | Arquivo CSV/Excel com relação de usuários |
| **2. Validação** | Equipe Governança | 1 dia útil | Relatório de validação e estatísticas |
| **3. Matching** | Equipe Governança | 1 dia útil | Matriz de correspondência Maximo ↔ AD |
| **4. Análise de Divergências** | Equipe Governança + TI | 1 dia útil | Lista de casos para resolução manual |
| **5. Plano de Ação** | Equipe Governança | 1 dia útil | Documento com ações corretivas |

**Total:** 5 dias úteis

---

## 9. Requisitos Técnicos

### 9.1 Ferramentas Sugeridas
- **PowerShell** (recomendado):
  ```powershell
  Get-ADUser -Filter {Enabled -eq $true} -Properties *
  ```

- **LDAP Query** (alternativa):
  ```ldap
  (objectClass=user)(objectCategory=person)(userAccountControl=512)
  ```

- **CSVDE** (ferramenta nativa):
  ```cmd
  csvde -f usuarios_ad.csv -r "(objectClass=user)" -l "cn,sAMAccountName,mail,department,title"
  ```

### 9.2 Permissões Necessárias
- Leitura de objetos de usuário no AD
- Acesso aos atributos: `sAMAccountName`, `userPrincipalName`, `mail`, `department`, `title`, `memberOf`, `enabled`, `whenCreated`, `whenChanged`, `lastLogonDate`

### 9.3 Considerações de Segurança
- ⚠️ **Dados sensíveis**: O arquivo conterá informações pessoais (nome, e-mail, departamento)
- 🔒 **Transmissão segura**: Utilizar canal criptografado (SMB, SFTP, ou e-mail criptografado)
- 🗑️ **Descarte seguro**: Excluir arquivos após conclusão da análise
- 📋 **LGPD**: Tratamento conforme Lei Geral de Proteção de Dados

---

## 10. Contatos e Dúvidas

**Dúvidas técnicas sobre a extração:**
- Responsável: [Nome do responsável pelo AD]
- E-mail: [email@foresea.com.br]
- Telefone: [Ramal]

**Dúvidas sobre o propósito ou uso dos dados:**
- Responsável: Equipe de Governança de Identidades
- E-mail: [governanca@foresea.com.br]
- Telefone: [Ramal]

---

## 11. Anexos

### Anexo A: Exemplo de Relatório Esperado
Ver seção 3.3 para exemplo de estrutura CSV.

### Anexo B: Documentação de Referência
- **Maximo Identity Sanity**: Documentação do projeto de governança
- **Active Directory Schema**: Documentação oficial Microsoft
- **LGPD - Lei 13.709/2018**: Diretrizes para tratamento de dados pessoais

### Anexo C: Histórico de Revisões
| Data | Versão | Autor | Alterações |
|------|--------|-------|------------|
| 2025-07-01 | 1.0 | Equipe Governança | Versão inicial |

---

## 12. Aprovações

| Papel | Nome | Assinatura | Data |
|-------|------|------------|------|
| **Solicitante** | [Nome] | ___________ | ___/___/___ |
| **Aprovador Técnico** | [Nome] | ___________ | ___/___/___ |
| **Aprovador Segurança** | [Nome] | ___________ | ___/___/___ |
| **Aprovador LGPD** | [Nome] | ___________ | ___/___/___ |

---

**Fim do Documento**