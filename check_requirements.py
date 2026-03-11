#!/usr/bin/env python3
"""
Check if all requirements are installed for the Fabric Conversion App
"""

import sys
import subprocess

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Need 3.10+")
        return False

def check_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name

    try:
        __import__(import_name)
        print(f"✓ {package_name} - Installed")
        return True
    except ImportError:
        print(f"✗ {package_name} - Not installed")
        print(f"   Install with: pip install {package_name}")
        return False

def check_node():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        version = result.stdout.strip()
        print(f"✓ Node.js {version} - Installed")
        return True
    except FileNotFoundError:
        print("✗ Node.js - Not installed")
        print("   Download from: https://nodejs.org/")
        return False

def check_npm():
    """Check if npm is installed"""
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        version = result.stdout.strip()
        print(f"✓ npm {version} - Installed")
        return True
    except FileNotFoundError:
        print("✗ npm - Not installed")
        return False

def check_odbc_driver():
    """Check if ODBC Driver is available"""
    try:
        import pyodbc
        drivers = pyodbc.drivers()
        odbc_18 = any('ODBC Driver 18' in d for d in drivers)
        odbc_17 = any('ODBC Driver 17' in d for d in drivers)

        if odbc_18:
            print("✓ ODBC Driver 18 for SQL Server - Installed")
            return True
        elif odbc_17:
            print("⚠ ODBC Driver 17 for SQL Server - Installed (18 recommended)")
            return True
        else:
            print("✗ ODBC Driver for SQL Server - Not found")
            print("   Download from: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server")
            return False
    except ImportError:
        print("⚠ Cannot check ODBC drivers (pyodbc not installed)")
        return False

def main():
    print("=" * 60)
    print("Fabric Conversion App - Requirements Check")
    print("=" * 60)
    print()

    checks = []

    # System requirements
    print("System Requirements:")
    print("-" * 60)
    checks.append(check_python_version())
    checks.append(check_node())
    checks.append(check_npm())

    print()
    print("Python Packages:")
    print("-" * 60)
    checks.append(check_package('flask', 'flask'))
    checks.append(check_package('flask-cors', 'flask_cors'))
    checks.append(check_package('python-dotenv', 'dotenv'))
    checks.append(check_package('oracledb'))
    checks.append(check_package('pyodbc'))
    checks.append(check_package('anthropic'))

    print()
    print("Database Drivers:")
    print("-" * 60)
    checks.append(check_odbc_driver())

    print()
    print("=" * 60)

    if all(checks):
        print("✓ All requirements satisfied!")
        print("  Ready to run: npm run dev")
    else:
        failed = checks.count(False)
        print(f"✗ {failed} requirement(s) missing")
        print("  Please install missing requirements and run again")

    print("=" * 60)

    return 0 if all(checks) else 1

if __name__ == '__main__':
    sys.exit(main())
