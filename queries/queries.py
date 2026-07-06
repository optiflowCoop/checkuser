from typing import Dict

STANDARD_QUERIES: Dict[str, str] = {
    "maxuser": (
        "SELECT USERID, PERSONID, STATUS, TYPE, DEFSITE, LOGINID, MAXUSERID "
        "FROM MAXUSER"
    ),
    "person": (
        "SELECT PERSONID, FIRSTNAME, LASTNAME, DISPLAYNAME "
        "FROM PERSON"
    ),
    "email": (
        "SELECT PERSONID, EMAILADDRESS FROM EMAIL WHERE ISPRIMARY = 1"
    ),
    "groupuser": (
        "SELECT GROUPUSERID, USERID, GROUPNAME FROM GROUPUSER"
    ),
    "maxgroup": (
        "SELECT GROUPNAME, DESCRIPTION, INDEPENDENT, AUTHALLSITES, AUTHALLGLS, AUTHALLSTOREROOMS, "
        "AUTHLABORALL, AUTHLABORCREW, AUTHLABORSELF, AUTHLABORSUPER, AUTHPERSONGROUP, DFLTAPP, WORKCENTER FROM MAXGROUP"
    ),
    "persongroup": (
        "SELECT PERSONGROUP, DESCRIPTION, ISCREWWORKGROUP, OOG_DEPARTMENT, OOG_USEINMOC, OOG_ISTOPSIDE "
        "FROM PERSONGROUP"
    ),
    "persongroupteam": (
        "SELECT RESPPARTY, RESPPARTYGROUP, RESPPARTYSEQ, RESPPARTYGROUPSEQ, GROUPDEFAULT, "
        "ORGDEFAULT, SITEDEFAULT, USEFORORG, USEFORSITE, PERSONGROUPTEAMID, PERSONGROUP FROM PERSONGROUPTEAM"
    ),
    "persongroupview": (
        "SELECT personid, status, displayname, firstname, lastname, department, title, employeetype, jobcode, supervisor, birthdate, lastevaldate, nextevaldate, hiredate, terminationdate, location, locationsite, locationorg, shiptoaddress, billtoaddress, droppoint, wfmailelection, transemailelection, delegate, delegatefromdate, delegatetodate, pcardnum, pcardtype, pcardexpdate, pcardverification, addressline1, addressline2, addressline3, city, regiondistrict, county, stateprovince, country, postalcode, vip, statusdate, acceptingwfmail, wopriority, loctoservreq, personuid, langcode, sendersysid, sourcesysid, ownersysid, externalrefid, language, locale, timezone, hasld, rowstamp, resppartygroup, respparty, resppartygroupseq, resppartyseq, usefororg, useforsite, groupdefault, orgdefault, sitedefault, persongroupteamid, persongroup FROM persongroupview"
    ),
    "maxlicusage": "SELECT USERID, LICENSENUM, ISSELFSERVICEUSER, ISUNLICUSER, ISLATEST FROM MAXLICUSAGE",
    "maslicusage": "SELECT USERID, MAXPRODID, LICENSETYPE, ISADMIN FROM MASLICUSAGE",
    "maxlicuserasc": "SELECT USERID, LICENSENUM FROM MAXLICUSERASC",
    "maxlicappaccess": "SELECT APPNAME, MODULE, SELFSERVICE, LIMITEDUSE, AUTHORIZEDUSE FROM MAXLICAPPACCESS",
    "maxlicapps": "SELECT LICENSENUM, APPNAME, ACCESSLEVEL, MODULE, MAXPRODID FROM MAXLICAPPS",
    "maxrelationship": "SELECT NAME, PARENT, CHILD, WHERECLAUSE, CARDINALITY, DBJOINREQUIRED, REMARKS, MAXRELATIONSHIPID FROM MAXRELATIONSHIP",
    
    # Queries para Indicadores Mensais - Placeholders para datas
    "workorder_indicadores": (
        "SELECT SITEID, COUNT(*) as TOTAL, "
        "YEAR(REPORTDATE) as ANO, MONTH(REPORTDATE) as MES "
        "FROM WORKORDER "
        "WHERE HISTORYFLAG = 0 AND ISTASK = 0 "
        "AND STATUS IN ('COMP','CLOSE','INPRG') "
        "AND REPORTDATE BETWEEN "
        "TIMESTAMP('{data_inicio}') AND TIMESTAMP('{data_fim}') "
        "GROUP BY SITEID, YEAR(REPORTDATE), MONTH(REPORTDATE) "
        "ORDER BY SITEID, ANO, MES"
    ),
    "moc_indicadores": (
        "SELECT SITEID, COUNT(*) as TOTAL, "
        "YEAR(REPORTDATE) as ANO, MONTH(REPORTDATE) as MES "
        "FROM WORKORDER "
        "WHERE WOCLASS = 'MOC' AND HISTORYFLAG = 0 "
        "AND STATUS IN ('COMP','CLOSE','INPRG') "
        "AND REPORTDATE BETWEEN "
        "TIMESTAMP('{data_inicio}') AND TIMESTAMP('{data_fim}') "
        "GROUP BY SITEID, YEAR(REPORTDATE), MONTH(REPORTDATE) "
        "ORDER BY SITEID, ANO, MES"
    ),
    "ptw_indicadores": (
        "SELECT SITEID, COUNT(*) as TOTAL, "
        "YEAR(CREATEDATE) as ANO, MONTH(CREATEDATE) as MES "
        "FROM PLUSGPERMITWORK "
        "WHERE HISTORYFLAG = 0 "
        "AND STATUS IN ('ISSUED','CLOSED','ISOLATION COMP','ISOLATION REMOVED') "
        "AND CREATEDATE BETWEEN "
        "TIMESTAMP('{data_inicio}') AND TIMESTAMP('{data_fim}') "
        "GROUP BY SITEID, YEAR(CREATEDATE), MONTH(CREATEDATE) "
        "ORDER BY SITEID, ANO, MES"
    ),
    "loto_indicadores": (
        "SELECT SITEID, COUNT(*) as TOTAL, "
        "YEAR(LCK07) as ANO, MONTH(LCK07) as MES "
        "FROM LOCKOUT "
        "WHERE LCK07 IS NOT NULL "
        "AND LCK07 BETWEEN "
        "TIMESTAMP('{data_inicio}') AND TIMESTAMP('{data_fim}') "
        "GROUP BY SITEID, YEAR(LCK07), MONTH(LCK07) "
        "ORDER BY SITEID, ANO, MES"
    ),
    # Queries específicas para indicadores (usando >= e < para incluir último dia)
    "moc_doc_indicadores": (
        "SELECT COUNT(*) as TOTAL, SITEID "
        "FROM PLUSGMOC w "
        "WHERE REPORTDATE >= TIMESTAMP('{data_inicio}') "
        "AND REPORTDATE < TIMESTAMP('{data_fim}') "
        "AND PARENT IS NULL "
        "AND WONUM LIKE 'MOC-DOC%' "
        "GROUP BY SITEID"
    ),
    "wo_indicadores": (
        "SELECT COUNT(*) as TOTAL, SITEID "
        "FROM WORKORDER w "
        "WHERE REPORTDATE >= TIMESTAMP('{data_inicio}') "
        "AND REPORTDATE < TIMESTAMP('{data_fim}') "
        "AND PARENT IS NULL "
        "AND WONUM NOT LIKE 'MOC-%' "
        "GROUP BY SITEID"
    ),
    "ptw_indicadores_new": (
        "SELECT COUNT(*) as TOTAL, SITEID "
        "FROM PLUSGPERMITWORK p "
        "WHERE CREATEDATE >= TIMESTAMP('{data_inicio}') "
        "AND CREATEDATE < TIMESTAMP('{data_fim}') "
        "GROUP BY SITEID"
    ),
    "loto_indicadores_new": (
        "SELECT COUNT(*) as TOTAL, SITEID "
        "FROM PLUSGISOLATION p "
        "WHERE CREATEDATE >= TIMESTAMP('{data_inicio}') "
        "AND CREATEDATE < TIMESTAMP('{data_fim}') "
        "GROUP BY SITEID"
    ),
    "maxobject": "SELECT SERVICENAME, OBJECTNAME, CLASSNAME, DESCRIPTION, ENTITYNAME, EXTENDSOBJECT, ISVIEW, PERSISTENT, MAINOBJECT, RESOURCETYPE FROM MAXOBJECT",
    "maxattribute": "SELECT OBJECTNAME, ATTRIBUTENAME, ALIAS, AUTOKEYNAME, CANAUTONUM, CLASSNAME, DEFAULTVALUE, DOMAINID, ENTITYNAME, ESIGFILTER, HASLD, ISPOSITIVE, LENGTH, MAXTYPE, MUSTBE, PERSISTENT, PRIMARYKEYCOLSEQ, REQUIRED, SAMEASATTRIBUTE, SAMEASOBJECT, SCALE, SEARCHTYPE, TITLE, MAXATTRIBUTEID FROM MAXATTRIBUTE",
    "maxapps": "SELECT APP, DESCRIPTION, ORIGINALAPP, MAXAPPSID FROM MAXAPPS",
    "sigoption": "SELECT APP, OPTIONNAME, DESCRIPTION, ESIGENABLED, VISIBLE, SIGOPTIONID FROM SIGOPTION",
    "logintracking": (
        "SELECT USERID, APP, ATTEMPTDATE, ATTEMPTRESULT, CLIENTHOST, CLIENTADDR "
        "FROM LOGINTRACKING "
        "WHERE ATTEMPTDATE >= CURRENT_DATE - 90 DAYS AND ATTEMPTRESULT = 'LOGIN'"
    ),
}

DEFAULT_QUERIES = list(STANDARD_QUERIES.keys())


def resolve_query(name: str, data_inicio: str = "2026-01-01 00:00:00", data_fim: str = "2026-12-31 23:59:59") -> str:
    """Resolve query name to SQL, substituindo placeholders de data"""
    lowered = name.strip().lower()
    
    if lowered in STANDARD_QUERIES:
        sql = STANDARD_QUERIES[lowered]
        if lowered == 'person':
            return "SELECT COALESCE(PERSONID, '') || ',' || COALESCE(REPLACE(FIRSTNAME, ',', ' '), '') || ',' || COALESCE(REPLACE(LASTNAME, ',', ' '), '') || ',' || COALESCE(REPLACE(DISPLAYNAME, ',', ' '), '') as CSV_ROW FROM PERSON"
        elif lowered == 'email':
            return "SELECT COALESCE(PERSONID, '') || ',' || COALESCE(REPLACE(EMAILADDRESS, ',', ' '), '') as CSV_ROW FROM EMAIL WHERE ISPRIMARY = 1"
        elif lowered == 'maxuser':
            return "SELECT COALESCE(USERID, '') || ',' || COALESCE(PERSONID, '') || ',' || COALESCE(STATUS, '') || ',' || COALESCE(TYPE, '') || ',' || COALESCE(DEFSITE, '') || ',' || COALESCE(LOGINID, '') || ',' || COALESCE(CHAR(MAXUSERID), '') as CSV_ROW FROM MAXUSER"
        elif lowered == 'groupuser':
            return "SELECT COALESCE(CHAR(GROUPUSERID), '') || ',' || COALESCE(USERID, '') || ',' || COALESCE(GROUPNAME, '') as CSV_ROW FROM GROUPUSER"
        elif lowered == 'persongroupview':
            columns = [
                "personid", "status", "displayname", "firstname", "lastname", "department", "title", "employeetype", "jobcode", "supervisor", "birthdate", "lastevaldate", "nextevaldate", "hiredate", "terminationdate", "location", "locationsite", "locationorg", "shiptoaddress", "billtoaddress", "droppoint", "wfmailelection", "transemailelection", "delegate", "delegatefromdate", "delegatetodate", "pcardnum", "pcardtype", "pcardexpdate", "pcardverification", "addressline1", "addressline2", "addressline3", "city", "regiondistrict", "county", "stateprovince", "country", "postalcode", "vip", "statusdate", "acceptingwfmail", "wopriority", "loctoservreq", "personuid", "langcode", "sendersysid", "sourcesysid", "ownersysid", "externalrefid", "language", "locale", "timezone", "hasld", "rowstamp", "resppartygroup", "respparty", "resppartygroupseq", "resppartyseq", "usefororg", "useforsite", "groupdefault", "orgdefault", "sitedefault", "persongroupteamid", "persongroup"
            ]
            csv_columns = [f"COALESCE(REPLACE({col}, ',', ' '), '')" if 'name' in col or 'address' in col or 'title' in col or 'code' in col or 'id' in col or 'type' in col or 'locale' in col or 'timezone' in col else f"COALESCE(CHAR({col}), '')" for col in columns]
            return f"SELECT { ' || \',\' || '.join(csv_columns) } as CSV_ROW FROM PERSONGROUPVIEW"
        elif lowered in ['workorder_indicadores', 'moc_indicadores', 'ptw_indicadores', 'loto_indicadores',
                        'moc_doc_indicadores', 'wo_indicadores', 'ptw_indicadores_new', 'loto_indicadores_new']:
            # Substitui placeholders de data
            sql = sql.replace('{data_inicio}', data_inicio).replace('{data_fim}', data_fim)
            return sql
        return sql
    return name
