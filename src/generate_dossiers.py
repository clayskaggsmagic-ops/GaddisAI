#!/usr/bin/env python3
"""
CLI tool to generate YAML dossiers for all NSC roles.

This is a one-time setup script. Run it to create initial dossiers,
then re-run only when you want to refresh the data.

Usage:
    # Generate all dossiers
    python src/generate_dossiers.py

    # Generate just one role
    python src/generate_dossiers.py --role SecDef

    # Generate with specific person
    python src/generate_dossiers.py --role SecDef --person "Lloyd Austin"

    # Overwrite existing files
    python src/generate_dossiers.py --refresh
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from researcher import generate_dossier


# Default role configurations
DEFAULT_ROLES = {
    "President": {
        "role": "President of the United States",
        "person": "Joe Biden"
    },
    "NSA": {
        "role": "National Security Advisor",
        "person": "Jake Sullivan"
    },
    "SecDef": {
        "role": "Secretary of Defense",
        "person": "Lloyd Austin"
    },
    "SecState": {
        "role": "Secretary of State",
        "person": "Antony Blinken"
    }
}


def generate_all_dossiers(output_dir: Path, refresh: bool = False, model: str = "gpt-4o-mini"):
    """Generate dossiers for all default roles."""

    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for short_name, config in DEFAULT_ROLES.items():
        output_file = output_dir / f"{short_name}.yaml"

        # Skip if file exists and not refreshing
        if output_file.exists() and not refresh:
            print(f"⏭️  Skipping {short_name} (file exists, use --refresh to overwrite)")
            continue

        print(f"🔍 Researching {config['role']} ({config['person']})...")

        try:
            dossier = generate_dossier(
                role=config["role"],
                person=config["person"],
                model=model
            )

            # Save to file
            with open(output_file, "w") as f:
                yaml.dump(dossier, f, default_flow_style=False, sort_keys=False)

            print(f"✅ Generated {output_file}")
            results[short_name] = "success"

        except Exception as e:
            print(f"❌ Failed to generate {short_name}: {e}")
            results[short_name] = f"error: {e}"

    return results


def generate_single_dossier(
    short_name: str,
    role: str,
    person: str,
    output_dir: Path,
    refresh: bool = False,
    model: str = "gpt-4o-mini"
):
    """Generate a single dossier."""

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{short_name}.yaml"

    if output_file.exists() and not refresh:
        print(f"⏭️  File {output_file} already exists. Use --refresh to overwrite.")
        return

    print(f"🔍 Researching {role} ({person})...")

    try:
        dossier = generate_dossier(role=role, person=person, model=model)

        with open(output_file, "w") as f:
            yaml.dump(dossier, f, default_flow_style=False, sort_keys=False)

        print(f"✅ Generated {output_file}")

    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate NSC role dossiers using AI research"
    )
    parser.add_argument(
        "--role",
        help="Generate only this role (e.g., SecDef, President)"
    )
    parser.add_argument(
        "--person",
        help="Specific person name (requires --role)"
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Overwrite existing dossier files"
    )
    parser.add_argument(
        "--output-dir",
        default="data/dossiers",
        help="Output directory for dossiers (default: data/dossiers)"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)"
    )

    args = parser.parse_args()

    # Check for API key (warn but allow template mode)
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set - using template mode")
        print("    Templates will need manual editing or re-running with API key\n")

    output_dir = Path(args.output_dir)

    # Generate single role or all roles
    if args.role:
        # Use person from DEFAULT_ROLES if not specified
        if args.role in DEFAULT_ROLES and not args.person:
            config = DEFAULT_ROLES[args.role]
            person = config["person"]
            role = config["role"]
        else:
            person = args.person or "Current officeholder"
            role = args.role

        generate_single_dossier(
            short_name=args.role,
            role=role,
            person=person,
            output_dir=output_dir,
            refresh=args.refresh,
            model=args.model
        )
    else:
        # Generate all
        print("🚀 Generating all NSC dossiers...\n")
        results = generate_all_dossiers(
            output_dir=output_dir,
            refresh=args.refresh,
            model=args.model
        )

        print("\n📊 Summary:")
        for role, status in results.items():
            print(f"  {role}: {status}")


if __name__ == "__main__":
    main()
