"""
Master Test Runner for Network Attack Forecast System.
Executes all test functions in tests/ directory.
"""

import sys
from pathlib import Path
import inspect
import importlib

sys.path.insert(0, str(Path(__file__).resolve().parent))

test_files = [
    "tests.test_operation_logger",
    "tests.test_trajectory_xai_and_mitre",
    "tests.test_foundation",
    "tests.test_preprocessing",
    "tests.test_state_and_sequence",
    "tests.test_model_and_rollout",
    "tests.test_mitre_and_xai",
    "tests.test_evaluation"
]

total_passed = 0
total_failed = 0

for mod_name in test_files:
    print(f"\n==========================================")
    print(f"Running: {mod_name}")
    print(f"==========================================")
    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:
        print(f"  [FAIL] Could not import {mod_name}: {e}")
        total_failed += 1
        continue

    for attr_name in dir(mod):
        if attr_name.startswith("test_") and callable(getattr(mod, attr_name)):
            func = getattr(mod, attr_name)
            try:
                func()
                print(f"  [OK] {attr_name}")
                total_passed += 1
            except Exception as e:
                print(f"  [FAIL] {attr_name}: {e}")
                import traceback
                traceback.print_exc()
                total_failed += 1

print(f"\n==========================================")
print(f"Test Summary: {total_passed} passed, {total_failed} failed")
print(f"==========================================")
if total_failed > 0:
    sys.exit(1)
