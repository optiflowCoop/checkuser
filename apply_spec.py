import os
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent

dirs = [
    ROOT / 'config',
    ROOT / 'queries',
    ROOT / 'src',
    ROOT / 'scripts',
    ROOT / 'output' / 'raw',
    ROOT / 'output' / 'parsed',
    ROOT / 'output' / 'consolidated',
    ROOT / 'output' / 'reports',
    ROOT / 'output' / 'logs',
    ROOT / 'tests'
]

for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

rules_identity_json = {
  "version": "1.0",
  "identity": {
    "raw_key_format": "{ENV_DB}|{USERID}",
    "candidate_keys": [
      "LOGINID",
      "PERSONID",
      "USERID"
    ],
    "allow_auto_merge_before_ad": False
  },
  "account_classification": {
    "classes": [
      "HUMAN",
      "TECHNICAL",
      "MOBILE",
      "TEST",
      "GENERIC",
      "INTEGRATION",
      "UNKNOWN"
    ],
    "rules": [
      {
        "class": "TEST",
        "match_any_field_regex": [
          "(?i)test",
          "(?i)teste",
          "(?i)dummy"
        ]
      },
      {
        "class": "MOBILE",
        "match_userid_regex": [
          "(?i)^mobile_"
        ],
        "match_groups_regex": [
          "(?i)MOBILE"
        ]
      },
      {
        "class": "TECHNICAL",
        "match_userid_exact": [
          "MAXADMIN",
          "MAXINST",
          "MAXINSTUSER",
          "MXINTADM",
          "OOGMON"
        ],
        "match_userid_regex": [
          "(?i)prtg",
          "(?i)monitor",
          "(?i)svc",
          "(?i)service"
        ]
      },
      {
        "class": "INTEGRATION",
        "match_userid_regex": [
          "(?i)api",
          "(?i)ws",
          "(?i)int",
          "(?i)integration"
        ]
      },
      {
        "class": "GENERIC",
        "match_userid_exact": [
          "FIELDSUPPORT",
          "OPERATIONMANAGER",
          "ASSETMANAGER"
        ]
      }
    ],
    "default_class": "HUMAN"
  },
  "collision_types": [
    "PERSONID_CONFLICT",
    "LOGINID_CONFLICT",
    "STATUS_CONFLICT",
    "ACCOUNT_CLASS_CONFLICT",
    "ORPHAN_GROUP_MEMBERSHIP",
    "BLANK_IDENTITY_FIELDS",
    "CROSS_ENV_USERID_REUSE",
    "CROSS_ENV_LOGIN_REUSE",
    "AD_CONFLICT",
    "AD_NOT_FOUND",
    "NO_CONFLICT"
  ],
  "hard_rules": [
    {
      "name": "personid_conflict",
      "when": {
        "env_count_gt": 1,
        "distinct_personid_gt": 1
      },
      "set": {
        "collision_type": "PERSONID_CONFLICT",
        "hypothesis": "CONFIRMED_DIFFERENT_PERSON",
        "merge_decision": "DO_NOT_MERGE",
        "review_priority": "HIGH"
      }
    },
    {
      "name": "loginid_conflict",
      "when": {
        "env_count_gt": 1,
        "distinct_loginid_gt": 1
      },
      "set": {
        "collision_type": "LOGINID_CONFLICT",
        "hypothesis": "REQUIRES_REVIEW",
        "merge_decision": "MANUAL_REVIEW_REQUIRED",
        "review_priority": "MEDIUM"
      }
    },
    {
      "name": "status_conflict",
      "when": {
        "env_count_gt": 1,
        "distinct_status_gt": 1
      },
      "set": {
        "collision_type": "STATUS_CONFLICT",
        "hypothesis": "REQUIRES_REVIEW",
        "merge_decision": "MANUAL_REVIEW_REQUIRED",
        "review_priority": "MEDIUM"
      }
    },
    {
      "name": "account_class_conflict",
      "when": {
        "env_count_gt": 1,
        "distinct_account_class_gt": 1
      },
      "set": {
        "collision_type": "ACCOUNT_CLASS_CONFLICT",
        "hypothesis": "REQUIRES_REVIEW",
        "merge_decision": "MANUAL_REVIEW_REQUIRED",
        "review_priority": "MEDIUM"
      }
    },
    {
      "name": "blank_identity_fields",
      "when": {
        "any_blank_in": [
          "PERSONID",
          "LOGINID",
          "STATUS"
        ]
      },
      "set": {
        "collision_type": "BLANK_IDENTITY_FIELDS",
        "hypothesis": "REQUIRES_REVIEW",
        "merge_decision": "MANUAL_REVIEW_REQUIRED",
        "review_priority": "MEDIUM"
      }
    }
  ],
  "match_score": {
    "positive": {
      "same_personid_all_envs": 40,
      "same_loginid_all_envs": 30,
      "same_account_class": 10,
      "same_type": 10,
      "same_defsite_or_coherent_site": 5,
      "high_group_overlap": 5
    },
    "negative": {
      "different_personid": -50,
      "different_loginid": -40,
      "conflicting_status": -20,
      "account_class_conflict": -15
    }
  },
  "score_bands": [
    {
      "min": -999,
      "max": 0,
      "hypothesis": "CONFIRMED_DIFFERENT_PERSON",
      "merge_decision": "DO_NOT_MERGE",
      "review_priority": "HIGH"
    },
    {
      "min": 1,
      "max": 49,
      "hypothesis": "REQUIRES_REVIEW",
      "merge_decision": "MANUAL_REVIEW_REQUIRED",
      "review_priority": "MEDIUM"
    },
    {
      "min": 50,
      "max": 79,
      "hypothesis": "POTENTIAL_SAME_PERSON",
      "merge_decision": "AWAITING_AD_MATCH",
      "review_priority": "LOW"
    },
    {
      "min": 80,
      "max": 999,
      "hypothesis": "POTENTIAL_SAME_PERSON",
      "merge_decision": "MERGE_AFTER_AD_MATCH",
      "review_priority": "LOW"
    }
  ],
  "ad_reconciliation": {
    "statuses": [
      "PENDING",
      "CONFIRMED",
      "CONFLICT",
      "NOT_FOUND"
    ],
    "post_ad_decisions": {
      "CONFIRMED": "READY_FOR_MAS9_MAPPING",
      "CONFLICT": "DO_NOT_MERGE",
      "NOT_FOUND": "MANUAL_REVIEW_REQUIRED",
      "PENDING": "AWAITING_AD_MATCH"
    }
  },
  "reporting": {
    "html_sections": [
      "Executive Summary",
      "Cross-Environment Identity Reuse",
      "Critical Different-Person Cases",
      "Awaiting AD Match",
      "Sanitation Worklist",
      "Access by Raw Identity"
    ],
    "excel_sheets": [
      "ExecutiveSummary",
      "IdentitySummary",
      "CrossEnvUserIDReuse",
      "LoginConflicts",
      "CriticalDifferentPerson",
      "AwaitingADMatch",
      "SanitationWorklist",
      "AccessByRawIdentity",
      "AccessByGroupExpanded",
      "BaselineDivergences",
      "LicenseFootprint"
    ]
  }
}

with open(ROOT / 'config' / 'rules.identity.json', 'w', encoding='utf-8') as f:
    json.dump(rules_identity_json, f, indent=2)

query_catalog = {
  "queries": [
    { "name": "maxuser", "category": "identity", "output_name": "maxuser", "required": True },
    { "name": "groupuser", "category": "access", "output_name": "groupuser", "required": True },
    { "name": "maxgroup", "category": "access", "output_name": "maxgroup", "required": True },
    { "name": "persongroup", "category": "access", "output_name": "persongroup", "required": False },
    { "name": "persongroupteam", "category": "access", "output_name": "persongroupteam", "required": False },
    { "name": "maxlicusage", "category": "licensing", "output_name": "maxlicusage", "required": False },
    { "name": "maslicusage", "category": "licensing", "output_name": "maslicusage", "required": False },
    { "name": "maxlicuserasc", "category": "licensing", "output_name": "maxlicuserasc", "required": False },
    { "name": "maxlicappaccess", "category": "licensing", "output_name": "maxlicappaccess", "required": False },
    { "name": "maxlicapps", "category": "licensing", "output_name": "maxlicapps", "required": False }
  ]
}
with open(ROOT / 'config' / 'query_catalog.json', 'w', encoding='utf-8') as f:
    json.dump(query_catalog, f, indent=2)

print("Generated configs.")
