#!/usr/bin/env python3
"""
Script de Validação Pós-Refatoração
Valida que todas as correções críticas foram aplicadas corretamente.

Data: 2026-07-01
Autor: Eduardo Silva (Foresea)
"""

import sys
from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.config import get_app_points_config
from scripts.analysis.entitlement import calculate_app_points, determine_user_entitlement
from scripts.analysis.licensing import assign_license_model
from scripts.analysis.classification import classify_usage_profile
from src.true_capacity_calculator import _normalize_userid

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name, passed, details=""):
    """Pretty print test results."""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"  {status} {name}")
    if details:
        print(f"        {details}")

def print_section(title):
    """Print section header."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE} {title}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")

def validate_apppoints_config():
    """Test 1: Verify BASE/AUTHORIZED = 3"""
    print_section("TEST 1: AppPoints Configuration")
    
    config = get_app_points_config()
    base_auth = config['BASE']['AUTHORIZED']
    
    passed = (base_auth == 3)
    print_test(
        "BASE/AUTHORIZED = 3",
        passed,
        f"Value: {base_auth} (expected: 3)"
    )
    
    # Verify all canonical values
    tests = [
        ('PREMIUM/AUTHORIZED', config['PREMIUM']['AUTHORIZED'], 5),
        ('PREMIUM/CONCURRENT', config['PREMIUM']['CONCURRENT'], 15),
        ('BASE/CONCURRENT', config['BASE']['CONCURRENT'], 10),
    ]
    
    all_passed = passed
    for name, actual, expected in tests:
        test_passed = (actual == expected)
        all_passed = all_passed and test_passed
        print_test(name, test_passed, f"Value: {actual} (expected: {expected})")
    
    return all_passed

def validate_userid_normalization():
    """Test 2: Verify USERID normalization function"""
    print_section("TEST 2: USERID Normalization")
    
    tests = [
        ("Simple uppercase", "JOHN DOE", "JOHNDOE"),
        ("With spaces", "  MARY JANE  ", "MARYJANE"),
        ("Mixed case", "Bob Smith", "BOBSMITH"),
        ("Already normalized", "ALICE", "ALICE"),
        ("Empty string", "", ""),
        ("None input", None, ""),
    ]
    
    all_passed = True
    for name, input_val, expected in tests:
        result = _normalize_userid(input_val)
        passed = (result == expected)
        all_passed = all_passed and passed
        print_test(name, passed, f"'{input_val}' → '{result}' (expected: '{expected}')")
    
    return all_passed

def validate_move_to_concurrent_threshold():
    """Test 3: Verify MOVE_TO_CONCURRENT uses < 30 threshold"""
    print_section("TEST 3: MOVE_TO_CONCURRENT Threshold")
    
    # Import the recommendation function
    from scripts.services.app_points import _recommend
    
    # Mock profile
    profile = {'GROUPS': [], 'USERID': 'TEST'}
    
    tests = [
        ("19 logins → MOVE_TO_CONCURRENT", 19, 'MOVE_TO_CONCURRENT'),
        ("25 logins → MOVE_TO_CONCURRENT", 25, 'MOVE_TO_CONCURRENT'),
        ("29 logins → MOVE_TO_CONCURRENT", 29, 'MOVE_TO_CONCURRENT'),
        ("30 logins → CONFIRMED_AUTHORIZED", 30, 'CONFIRMED_AUTHORIZED'),
        ("50 logins → CONFIRMED_AUTHORIZED", 50, 'CONFIRMED_AUTHORIZED'),
    ]
    
    all_passed = True
    for name, login_count, expected_rec in tests:
        rec, _ = _recommend(profile, 'BASE', 'AUTHORIZED', login_count, 'ONSHORE')
        passed = (rec == expected_rec)
        all_passed = all_passed and passed
        print_test(name, passed, f"Got: {rec} (expected: {expected_rec})")
    
    return all_passed

def validate_canonical_imports():
    """Test 4: Verify canonical functions are importable"""
    print_section("TEST 4: Canonical Function Imports")
    
    tests = [
        ("calculate_app_points", calculate_app_points),
        ("determine_user_entitlement", determine_user_entitlement),
        ("assign_license_model", assign_license_model),
        ("classify_usage_profile", classify_usage_profile),
    ]
    
    all_passed = True
    for name, func in tests:
        passed = callable(func)
        all_passed = all_passed and passed
        print_test(name, passed, f"Module: {func.__module__}")
    
    return all_passed

def validate_calculate_app_points_logic():
    """Test 5: Verify calculate_app_points returns correct values"""
    print_section("TEST 5: AppPoints Calculation Logic")
    
    tests = [
        ('PREMIUM/AUTHORIZED', 'PREMIUM', 'AUTHORIZED', 5),
        ('PREMIUM/CONCURRENT', 'PREMIUM', 'CONCURRENT', 15),
        ('BASE/AUTHORIZED', 'BASE', 'AUTHORIZED', 3),  # Critical fix
        ('BASE/CONCURRENT', 'BASE', 'CONCURRENT', 10),
        ('LIMITED/CONCURRENT', 'LIMITED', 'CONCURRENT', 5),
        ('SELF FREE', 'SELF FREE', 'CONCURRENT', 0),
    ]
    
    all_passed = True
    for name, entitlement, license_model, expected in tests:
        result = calculate_app_points(entitlement, license_model)
        passed = (result == expected)
        all_passed = all_passed and passed
        print_test(name, passed, f"Got: {result} (expected: {expected})")
    
    return all_passed

def validate_output_files():
    """Test 6: Verify output files exist and have valid structure"""
    print_section("TEST 6: Output Files Validation")
    
    consolidated_dir = ROOT / 'output' / 'consolidated'
    
    files_to_check = [
        ('license_decision_plan.csv', ['USERID', 'APP_POINTS', 'OPTIMIZATION_REC']),
        ('true_capacity_metrics.json', None),
        ('license_optimization_recommendations.csv', ['USERID', 'APP_POINTS_COST']),
    ]
    
    all_passed = True
    for filename, required_cols in files_to_check:
        filepath = consolidated_dir / filename
        exists = filepath.exists()
        
        if not exists:
            print_test(f"{filename} exists", False, "File not found")
            all_passed = False
            continue
        
        if filename.endswith('.json'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    has_data = len(data) > 0
                    print_test(f"{filename} valid", has_data, f"Keys: {list(data.keys())[:5]}")
                    all_passed = all_passed and has_data
            except Exception as e:
                print_test(f"{filename} valid", False, f"Error: {str(e)}")
                all_passed = False
        
        elif filename.endswith('.csv'):
            try:
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames
                    row_count = sum(1 for _ in reader)
                    
                    has_required = all(col in headers for col in required_cols)
                    print_test(
                        f"{filename} structure",
                        has_required,
                        f"Rows: {row_count}, Has required columns: {has_required}"
                    )
                    all_passed = all_passed and has_required
            except Exception as e:
                print_test(f"{filename} valid", False, f"Error: {str(e)}")
                all_passed = False
    
    return all_passed

def validate_nem_calculation():
    """Test 7: Verify NEM calculation has improved with normalization"""
    print_section("TEST 7: NEM Calculation Validation")
    
    metrics_file = ROOT / 'output' / 'consolidated' / 'true_capacity_metrics.json'
    
    if not metrics_file.exists():
        print_test("NEM metrics exist", False, "File not found - run true_capacity_calculator.py first")
        return False
    
    try:
        with open(metrics_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        required_keys = [
            'unique_human_users',
            'authorized_reserved_points',
            'true_total_app_points',
            'hourly_app_points_nem',
        ]
        
        all_passed = True
        for key in required_keys:
            exists = key in data
            all_passed = all_passed and exists
            detail = f"Value: {data.get(key, 'N/A')}" if exists else "Missing"
            print_test(f"NEM has '{key}'", exists, detail)
        
        # Check that hourly_app_points_nem has data
        hourly_nem = data.get('hourly_app_points_nem', {})
        has_hourly_data = len(hourly_nem) > 0
        print_test(
            "Hourly NEM data populated",
            has_hourly_data,
            f"Hours tracked: {len(hourly_nem)}"
        )
        all_passed = all_passed and has_hourly_data
        
        return all_passed
        
    except Exception as e:
        print_test("NEM metrics valid", False, f"Error: {str(e)}")
        return False

def main():
    """Run all validation tests."""
    print(f"\n{YELLOW}{'='*80}{RESET}")
    print(f"{YELLOW} CHECKUSER - Validação Pós-Refatoração 2026-07-01{RESET}")
    print(f"{YELLOW}{'='*80}{RESET}")
    
    tests = [
        ("AppPoints Configuration", validate_apppoints_config),
        ("USERID Normalization", validate_userid_normalization),
        ("MOVE_TO_CONCURRENT Threshold", validate_move_to_concurrent_threshold),
        ("Canonical Imports", validate_canonical_imports),
        ("AppPoints Calculation", validate_calculate_app_points_logic),
        ("Output Files", validate_output_files),
        ("NEM Calculation", validate_nem_calculation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"{RED}ERROR in {name}: {str(e)}{RESET}")
            results.append((name, False))
    
    # Summary
    print_section("SUMMARY")
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"
        print(f"  {status} {name}")
    
    print(f"\n{BLUE}Total: {passed_count}/{total_count} tests passed{RESET}")
    
    if passed_count == total_count:
        print(f"\n{GREEN}{'='*80}{RESET}")
        print(f"{GREEN} ✓ ALL VALIDATIONS PASSED{RESET}")
        print(f"{GREEN} Sistema refinado, robusto e confiável!{RESET}")
        print(f"{GREEN}{'='*80}{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{'='*80}{RESET}")
        print(f"{RED} ✗ SOME VALIDATIONS FAILED{RESET}")
        print(f"{RED} Revisar correções antes de deploy{RESET}")
        print(f"{RED}{'='*80}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
