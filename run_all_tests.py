import os
import sys
import importlib.util

print("==================================================================")
print("  PROJECT SARATHI — ALL MILESTONES (54, 55, 56) MASTER SUITE RUNNER")
print("  Target Release Tag: v2.0.0-master-synthesis                     ")
print("==================================================================
")

# Run all test suites
test_files = [
    "tests/test_milestone_54_vector_rag.py",
    "tests/test_milestone_55_workflow_dag.py",
    "tests/test_milestone_56_v2_platform.py"
]

total_passed = 0
total_failed = 0

sys.path.insert(0, os.getcwd())

for tfile in test_files:
    print(f"
[SUITE] Executing {tfile}...")
    print("------------------------------------------------------------------")
    spec = importlib.util.spec_from_file_location("test_mod", tfile)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    tfuncs = sorted([a for a in dir(mod) if a.startswith("test_")])
    for tf in tfuncs:
        try:
            getattr(mod, tf)()
            print(f"  [PASS] {tf}")
            total_passed += 1
        except Exception as e:
            print(f"  [FAIL] {tf}: {e}")
            total_failed += 1

print("
==================================================================")
print(f"  FINAL SUMMARY: {total_passed} Passed, {total_failed} Failed across all suites.")
print("==================================================================")
