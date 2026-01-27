#!/usr/bin/env python
"""
Script to run tests with coverage reporting for code quality assessment
"""
import os
import sys
import subprocess

def run_tests_with_coverage():
    """Run Django tests with coverage"""
    os.chdir(os.path.dirname(__file__))

    # Install coverage if not present
    try:
        import coverage
    except ImportError:
        print("Installing coverage...")
        subprocess.run([sys.executable, "-m", "pip", "install", "coverage"], check=True)

    # Run tests with coverage
    cmd = [
        sys.executable, "-m", "coverage", "run",
        "--source=accounts,assets,audit,brokers,claims,companies,invoices,notifications,policies,reports",
        "manage.py", "test"
    ]

    print("Running tests with coverage...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("Tests passed! Generating coverage report...")
        # Generate coverage report
        subprocess.run([sys.executable, "-m", "coverage", "report"], check=True)
        subprocess.run([sys.executable, "-m", "coverage", "html"], check=True)
        print("Coverage report generated in htmlcov/")
    else:
        print("Tests failed:")
        print(result.stdout)
        print(result.stderr)
        return False

    return True

if __name__ == "__main__":
    success = run_tests_with_coverage()
    sys.exit(0 if success else 1)