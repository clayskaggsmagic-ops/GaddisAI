#!/usr/bin/env python3
"""
Simple test script to verify all data files can be loaded.

Tests:
1. All expected data directories exist
2. Files are present in each directory
3. Files are readable
4. Basic content validation (non-empty, reasonable length)
"""

import os
from pathlib import Path


def test_data_loading():
    """Test that all data files load correctly."""

    base_dir = Path("data")
    results = {"success": [], "missing": [], "errors": []}

    # Define expected structure
    expected_files = {
        "memo": ["regional_strategy.txt"],
        "doctrine": ["national_defense_strategy.txt", "treaty_commitments.txt"],
        "dossiers": ["President.yaml", "NSA.yaml", "SecDef.yaml", "SecState.yaml"],
        "news": ["regional_developments.txt", "defense_updates.txt", "diplomatic_developments.txt"]
    }

    print("=" * 60)
    print("DATA LOADING TEST")
    print("=" * 60)

    # Check each directory and file
    for dir_name, file_list in expected_files.items():
        dir_path = base_dir / dir_name

        print(f"\n📁 {dir_name}/")

        if not dir_path.exists():
            print(f"  ❌ Directory not found: {dir_path}")
            results["missing"].append(str(dir_path))
            continue

        for file_name in file_list:
            file_path = dir_path / file_name

            if not file_path.exists():
                print(f"  ❌ Missing: {file_name}")
                results["missing"].append(str(file_path))
                continue

            try:
                # Try to read the file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Validate content
                if len(content) == 0:
                    print(f"  ⚠️  Empty: {file_name}")
                    results["errors"].append(f"{file_path} is empty")
                elif len(content) < 100:
                    print(f"  ⚠️  Too short: {file_name} ({len(content)} chars)")
                    results["errors"].append(f"{file_path} suspiciously short")
                else:
                    word_count = len(content.split())
                    print(f"  ✅ {file_name} ({word_count} words, {len(content)} chars)")
                    results["success"].append(str(file_path))

            except Exception as e:
                print(f"  ❌ Error reading {file_name}: {e}")
                results["errors"].append(f"{file_path}: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully loaded: {len(results['success'])} files")
    print(f"❌ Missing: {len(results['missing'])} files")
    print(f"⚠️  Errors: {len(results['errors'])} files")

    if results["missing"]:
        print("\nMissing files:")
        for item in results["missing"]:
            print(f"  - {item}")

    if results["errors"]:
        print("\nErrors:")
        for item in results["errors"]:
            print(f"  - {item}")

    # Total word count
    total_words = 0
    for file_path_str in results["success"]:
        with open(file_path_str, 'r', encoding='utf-8') as f:
            total_words += len(f.read().split())

    print(f"\n📊 Total corpus: ~{total_words} words across {len(results['success'])} documents")

    # Return status
    if len(results["missing"]) > 0 or len(results["errors"]) > 0:
        print("\n❌ TEST FAILED - Some files missing or have errors")
        return False
    else:
        print("\n✅ TEST PASSED - All data files loaded successfully")
        return True


if __name__ == "__main__":
    success = test_data_loading()
    exit(0 if success else 1)
