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
}

DEFAULT_QUERIES = list(STANDARD_QUERIES.keys())


def resolve_query(name: str) -> str:
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
            # Para a view, vamos selecionar todas as colunas e formatar como CSV
            # Precisamos listar todas as colunas da view para garantir a ordem e o COALESCE
            columns = [
                "personid", "status", "displayname", "firstname", "lastname", "department", "title", "employeetype", "jobcode", "supervisor", "birthdate", "lastevaldate", "nextevaldate", "hiredate", "terminationdate", "location", "locationsite", "locationorg", "shiptoaddress", "billtoaddress", "droppoint", "wfmailelection", "transemailelection", "delegate", "delegatefromdate", "delegatetodate", "pcardnum", "pcardtype", "pcardexpdate", "pcardverification", "addressline1", "addressline2", "addressline3", "city", "regiondistrict", "county", "stateprovince", "country", "postalcode", "vip", "statusdate", "acceptingwfmail", "wopriority", "loctoservreq", "personuid", "langcode", "sendersysid", "sourcesysid", "ownersysid", "externalrefid", "language", "locale", "timezone", "hasld", "rowstamp", "resppartygroup", "respparty", "resppartygroupseq", "resppartyseq", "usefororg", "useforsite", "groupdefault", "orgdefault", "sitedefault", "persongroupteamid", "persongroup"
            ]
            csv_columns = [f"COALESCE(REPLACE({col}, ',', ' '), '')" if 'name' in col or 'address' in col or 'title' in col or 'code' in col or 'id' in col or 'type' in col or 'locale' in col or 'timezone' in col else f"COALESCE(CHAR({col}), '')" for col in columns]
            return f"SELECT { ' || \',\' || '.join(csv_columns) } as CSV_ROW FROM PERSONGROUPVIEW"
        return sql
    return name