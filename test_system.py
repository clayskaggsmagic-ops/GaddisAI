"""
Quick test script to verify GaddisAI system is working.
Tests basic functionality without running full deliberation.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from rag.vectorstore import VectorStore
        from rag.ingest import DocumentIngester
        from rag.retriever import ContextRetriever
        from agents.base_agent import NSCAgent
        from agents.advisor_agent import AdvisorAgent
        from agents.president_agent import PresidentAgent
        from orchestrator import NSCOrchestrator
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_environment():
    """Test environment variables and paths."""
    print("\nTesting environment...")

    issues = []

    # Check API key
    if not os.environ.get("OPENAI_API_KEY"):
        issues.append("OPENAI_API_KEY not set")
    else:
        print("✓ OPENAI_API_KEY is set")

    # Check directories
    required_dirs = [
        "./data/dossiers",
        "./data/memo",
        "./data/doctrine",
        "./config"
    ]

    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            issues.append(f"Directory missing: {dir_path}")
        else:
            print(f"✓ {dir_path} exists")

    # Check config files
    required_files = [
        "./config/roles.yaml",
        "./config/retrieval.yaml"
    ]

    for file_path in required_files:
        if not Path(file_path).exists():
            issues.append(f"Config file missing: {file_path}")
        else:
            print(f"✓ {file_path} exists")

    # Check for dossiers
    dossiers = list(Path("./data/dossiers").glob("*.yaml"))
    print(f"✓ Found {len(dossiers)} dossier(s): {[d.stem for d in dossiers]}")

    if issues:
        print("\n✗ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print("✓ Environment OK")
    return True


def test_rag_initialization():
    """Test RAG system initialization."""
    print("\nTesting RAG initialization...")
    try:
        from rag.vectorstore import VectorStore
        from rag.ingest import DocumentIngester

        # Initialize vector store
        vectorstore = VectorStore(
            config_path="./config/retrieval.yaml",
            persist_directory="./data/chroma_test"
        )
        print("✓ VectorStore initialized")

        # Test document ingester
        ingester = DocumentIngester(
            config_path="./config/retrieval.yaml",
            data_dir="./data"
        )
        print("✓ DocumentIngester initialized")

        # Test ingestion (just check it doesn't crash)
        print("  Testing document ingestion...")
        results = ingester.ingest_all()
        for collection, (docs, metas, ids) in results.items():
            print(f"  - {collection}: {len(docs)} documents")

        print("✓ RAG initialization successful")
        return True

    except Exception as e:
        print(f"✗ RAG initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_initialization():
    """Test agent initialization."""
    print("\nTesting agent initialization...")
    try:
        from agents.advisor_agent import AdvisorAgent
        from agents.president_agent import PresidentAgent

        dossiers_dir = Path("./data/dossiers")
        roles_config = "./config/roles.yaml"

        # Test advisor initialization
        if (dossiers_dir / "SecDef.yaml").exists():
            advisor = AdvisorAgent(
                role="SecDef",
                dossier_path=str(dossiers_dir / "SecDef.yaml"),
                roles_config_path=roles_config,
                model="gpt-4"
            )
            print(f"✓ Advisor initialized: {advisor.person} ({advisor.role})")
        else:
            print("⚠ SecDef.yaml not found, skipping advisor test")

        # Test President initialization
        if (dossiers_dir / "President.yaml").exists():
            president = PresidentAgent(
                role="President",
                dossier_path=str(dossiers_dir / "President.yaml"),
                roles_config_path=roles_config,
                model="gpt-4"
            )
            print(f"✓ President initialized: {president.person}")
            print(f"  Advisor relationships: {president.advisor_relationships}")
        else:
            print("⚠ President.yaml not found, skipping President test")

        print("✓ Agent initialization successful")
        return True

    except Exception as e:
        print(f"✗ Agent initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("GaddisAI System Test")
    print("=" * 80)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Environment", test_environment()))
    results.append(("RAG System", test_rag_initialization()))
    results.append(("Agents", test_agent_initialization()))

    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:20s} {status}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n✓ All tests passed! System is ready.")
        print("\nTo run the system:")
        print("  python src/main.py")
    else:
        print("\n✗ Some tests failed. Please fix issues before running.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
