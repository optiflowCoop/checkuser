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
    "maxobject": "SELECT SERVICENAME, OBJECTNAME, CLASSNAME, DESCRIPTION, ENTITYNAME, EXTENDSOBJECT, ISVIEW, PERSISTENT, MAINOBJECT, RESOURCETYPE FROM MAXOBJECT",
    "maxattribute": "SELECT OBJECTNAME, ATTRIBUTENAME, ALIAS, AUTOKEYNAME, CANAUTONUM, CLASSNAME, DEFAULTVALUE, DOMAINID, ENTITYNAME, ESIGFILTER, HASLD, ISPOSITIVE, LENGTH, MAXTYPE, MUSTBE, PERSISTENT, PRIMARYKEYCOLSEQ, REQUIRED, SAMEASATTRIBUTE, SAMEASOBJECT, SCALE, SEARCHTYPE, TITLE, MAXATTRIBUTEID FROM MAXATTRIBUTE",
    "maxapps": "SELECT APP, DESCRIPTION, ORIGINALAPP, MAXAPPSID FROM MAXAPPS",
    "sigoption": "SELECT APP, OPTIONNAME, DESCRIPTION, ESIGENABLED, VISIBLE, SIGOPTIONID FROM SIGOPTION",
    "pr_sod_evidence": (
        "SELECT COALESCE(p.SITEID,'') || ',' || COALESCE(p.PRNUM,'') || ',' || "
        "COALESCE(REPLACE(p.DESCRIPTION, ',', ';'), '') || ',' || "
        "COALESCE(REPLACE(CHAR(p.TOTALCOST), ',', '.'), '') || ',' || "
        "COALESCE(p.STATUS,'') || ',' || COALESCE(p.REQUESTEDBY,'') || ',' || "
        "COALESCE(a.PERSONID,'') || ',' || COALESCE(CHAR(a.TRANSDATE),'') || ',' || COALESCE(CHAR(b.TRANSDATE),'') || ',' || "
        "CASE WHEN EXISTS (SELECT 1 FROM WFTRANSACTION w WHERE w.OWNERTABLE='PR' AND w.OWNERID=a.OWNERID "
        "AND w.ACTIONPERFORMED='OOG_PRWENG') THEN 'SIM' ELSE 'NAO' END "
        "AS CSV_ROW "
        "FROM WFTRANSACTION a "
        "JOIN WFTRANSACTION b ON a.OWNERID = b.OWNERID AND a.OWNERTABLE = b.OWNERTABLE AND a.PERSONID = b.PERSONID "
        "JOIN PR p ON p.PRID = a.OWNERID "
        "WHERE a.OWNERTABLE = 'PR' AND a.ACTIONPERFORMED = 'PR WAPPR' AND b.ACTIONPERFORMED = 'PR APPR' "
        "AND a.PERSONID NOT IN ('MAXADMIN') "
        "AND a.TRANSDATE >= CURRENT_DATE - 365 DAYS"
    ),
    "siteauth": "SELECT GROUPNAME, SITEID FROM SITEAUTH",
    "pr_po_same_approver": (
        "SELECT COALESCE(p.SITEID,'') || ',' || COALESCE(p.PRNUM,'') || ',' || "
        "COALESCE(REPLACE(p.DESCRIPTION, ',', ';'), '') || ',' || "
        "COALESCE(REPLACE(CHAR(p.TOTALCOST), ',', '.'), '') || ',' || "
        "COALESCE(p.STATUS,'') || ',' || COALESCE(a.PERSONID,'') || ',' || "
        "COALESCE(CHAR(a.TRANSDATE),'') || ',' || COALESCE(CHAR(b.TRANSDATE),'') || ',' || "
        "COALESCE((SELECT MIN(pl.PONUM) FROM PRLINE pl WHERE pl.PRNUM=p.PRNUM AND pl.SITEID=p.SITEID "
        "AND pl.PONUM IS NOT NULL), '') "
        "AS CSV_ROW "
        "FROM WFTRANSACTION a "
        "JOIN WFTRANSACTION b ON a.OWNERID = b.OWNERID AND a.OWNERTABLE = b.OWNERTABLE AND a.PERSONID = b.PERSONID "
        "JOIN PR p ON p.PRID = a.OWNERID "
        "WHERE a.OWNERTABLE = 'PR' AND a.ACTIONPERFORMED = 'PR APPR' AND b.ACTIONPERFORMED = 'OOG_CREAPOGRP' "
        "AND a.PERSONID NOT IN ('MAXADMIN') "
        "AND a.TRANSDATE >= CURRENT_DATE - 365 DAYS"
    ),
    "pr_self_approval": (
        "SELECT COALESCE(p.SITEID,'') || ',' || COALESCE(p.PRNUM,'') || ',' || "
        "COALESCE(REPLACE(p.DESCRIPTION, ',', ';'), '') || ',' || "
        "COALESCE(REPLACE(CHAR(p.TOTALCOST), ',', '.'), '') || ',' || "
        "COALESCE(p.STATUS,'') || ',' || COALESCE(p.OOG_REQUESTEDBY,'') || ',' || "
        "COALESCE(b.PERSONID,'') || ',' || COALESCE(CHAR(b.TRANSDATE),'') || ',' || "
        "CASE WHEN EXISTS (SELECT 1 FROM WFTRANSACTION w WHERE w.OWNERTABLE='PR' AND w.OWNERID=p.PRID "
        "AND w.ACTIONPERFORMED='OOG_PRWENG') THEN 'SIM' ELSE 'NAO' END "
        "AS CSV_ROW "
        "FROM PR p "
        "JOIN WFTRANSACTION b ON b.OWNERID = p.PRID AND b.OWNERTABLE = 'PR' "
        "WHERE b.ACTIONPERFORMED = 'PR APPR' "
        "AND UPPER(p.OOG_REQUESTEDBY) = b.PERSONID "
        "AND p.OOG_REQUESTEDBY IS NOT NULL "
        "AND b.TRANSDATE >= CURRENT_DATE - 365 DAYS"
    ),
    "applicationauth": (
        "SELECT GROUPNAME, APP, OPTIONNAME FROM APPLICATIONAUTH "
        "WHERE APP IN ('PLUSGPR','PLUSGPO','CREATEDR') "
        "AND OPTIONNAME IN ('INSERT','SAVE','WAPPR','APPR','APPROVE','UNAPPROVE','CANCEL','COMPLETE')"
    ),
    "applicationauth_full": (
        "SELECT GROUPNAME, APP, OPTIONNAME FROM APPLICATIONAUTH"
    ),
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
        return sql
    return name
