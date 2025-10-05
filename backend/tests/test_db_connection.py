"""
Test database connection and asyncpg driver configuration.

Run this test to verify:
1. DATABASE_URL is properly normalized to use asyncpg driver
2. The async engine connects successfully
3. No psycopg2 dependencies are required
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


async def test_database_url_normalization():
    """Test that DATABASE_URL is properly normalized."""
    print("\n" + "=" * 70)
    print("TEST 1: DATABASE_URL Normalization")
    print("=" * 70)

    from app.core.settings import normalize_database_url

    test_cases = [
        ("postgres://user:pass@host:5432/db", "postgresql+asyncpg://user:pass@host:5432/db?ssl=require"),
        ("postgresql://user:pass@host:5432/db", "postgresql+asyncpg://user:pass@host:5432/db?ssl=require"),
        (
            "postgresql+asyncpg://user:pass@host:5432/db?sslmode=require",
            "postgresql+asyncpg://user:pass@host:5432/db?ssl=require",
        ),
        (
            "postgresql+asyncpg://user:pass@host:5432/db?ssl=require",
            "postgresql+asyncpg://user:pass@host:5432/db?ssl=require",
        ),
    ]

    all_passed = True
    for input_url, expected_output in test_cases:
        result = normalize_database_url(input_url)
        passed = result == expected_output

        print(f"\nInput:    {input_url}")
        print(f"Expected: {expected_output}")
        print(f"Result:   {result}")
        print(f"Status:   {'✓ PASS' if passed else '✗ FAIL'}")

        if not passed:
            all_passed = False

    return all_passed


async def test_settings_database_url():
    """Test that settings.DATABASE_URL uses asyncpg driver."""
    print("\n" + "=" * 70)
    print("TEST 2: Settings DATABASE_URL Configuration")
    print("=" * 70)

    from app.core.config import settings

    print(f"\nRaw DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT SET')}")
    print(f"Settings DATABASE_URL: {settings.DATABASE_URL}")

    # Check that it contains asyncpg
    has_asyncpg = "+asyncpg" in settings.DATABASE_URL
    has_ssl = "ssl=" in settings.DATABASE_URL
    no_sslmode = "sslmode=" not in settings.DATABASE_URL

    print(f"\nContains +asyncpg: {'✓ YES' if has_asyncpg else '✗ NO'}")
    print(f"Contains ssl=:     {'✓ YES' if has_ssl else '✗ NO'}")
    print(f"No sslmode=:       {'✓ YES' if no_sslmode else '✗ NO (should use ssl= for asyncpg)'}")

    return has_asyncpg and has_ssl and no_sslmode


async def test_engine_driver():
    """Test that the async engine uses the correct driver."""
    print("\n" + "=" * 70)
    print("TEST 3: SQLAlchemy Engine Driver")
    print("=" * 70)

    from app.core.database import engine

    print(f"\nEngine URL: {engine.url}")
    print(f"Dialect: {engine.dialect.name}")
    print(f"Driver: {engine.driver}")

    is_asyncpg = engine.driver == "asyncpg"
    print(f"\nDriver is asyncpg: {'✓ YES' if is_asyncpg else '✗ NO'}")

    return is_asyncpg


async def test_database_connection():
    """Test actual database connectivity."""
    print("\n" + "=" * 70)
    print("TEST 4: Database Connection")
    print("=" * 70)

    from sqlalchemy import text

    from app.core.database import engine

    try:
        print("\nAttempting to connect to database...")

        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()

            print(f"✓ Connection successful!")
            print(f"PostgreSQL version: {version}")

        return True

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print(f"\nError type: {type(e).__name__}")

        # Check if it's a psycopg2 import error
        if "psycopg2" in str(e):
            print("\n⚠ ERROR: The error mentions psycopg2!")
            print("This means the DATABASE_URL is not using the asyncpg driver.")
            print("Please verify DATABASE_URL contains '+asyncpg'")

        return False


async def test_no_psycopg2_requirement():
    """Verify that psycopg2 is not required by checking imports."""
    print("\n" + "=" * 70)
    print("TEST 5: No psycopg2 Package Required")
    print("=" * 70)

    # Check if psycopg2 can be imported (it shouldn't be installed)
    try:
        import psycopg2

        print("✗ FAIL: psycopg2 package is installed")
        print(f"  Version: {psycopg2.__version__}")
        print("  This package should not be required for asyncpg driver")
        return False
    except ImportError:
        print("✓ PASS: psycopg2 package not installed (as expected)")
        print("  The asyncpg driver is being used correctly")
        return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("DATABASE CONNECTIVITY TEST SUITE")
    print("=" * 70)

    from dotenv import load_dotenv

    # Load environment variables
    env_file = backend_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"\nLoaded environment from: {env_file}")
    else:
        print(f"\n⚠ Warning: No .env file found at {env_file}")

    # Run all tests
    results = {}

    results["URL Normalization"] = await test_database_url_normalization()
    results["Settings Configuration"] = await test_settings_database_url()
    results["Engine Driver"] = await test_engine_driver()
    results["No psycopg2 Required"] = await test_no_psycopg2_requirement()
    results["Database Connection"] = await test_database_connection()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:.<50} {status}")
        if not passed:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n✓ ALL TESTS PASSED!")
        print("\nThe database is configured correctly to use asyncpg driver.")
        print("No psycopg2 dependencies are required.")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        print("\nPlease review the failed tests above and fix the configuration.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
