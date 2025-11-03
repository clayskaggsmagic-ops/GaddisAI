"""
Main application entry point for GaddisAI NSC simulator.
Initializes RAG system, agents, and runs deliberations.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict

# Check Python version compatibility
if sys.version_info >= (3, 13):
    print("=" * 80)
    print("WARNING: Python 3.13+ detected")
    print("=" * 80)
    print(f"Current Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print("\nChromaDB does not yet support Python 3.13 due to NumPy compatibility issues.")
    print("This may cause import hangs or runtime errors.")
    print("\nRecommended: Use Python 3.11 or 3.12")
    print("  brew install python@3.12")
    print("  /opt/homebrew/bin/python3.12 -m venv venv")
    print("=" * 80)
    print("\nPress Ctrl+C to exit, or Enter to continue anyway...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(1)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from rag.vectorstore import VectorStore
from rag.ingest import DocumentIngester
from rag.retriever import ContextRetriever
from memory.memory_store import MemoryStore
from orchestrator import NSCOrchestrator
from utils.cost_tracker import CostTracker
from formatters.document_generator import save_sequential_documents


def check_environment():
    """Check that required environment variables are set."""
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)


def initialize_rag(
    config_path: str = "./config/retrieval.yaml",
    data_dir: str = "./data",
    persist_dir: str = "./data/chroma",
    force_reingest: bool = False
):
    """
    Initialize RAG system: vector store and document ingestion.

    Args:
        config_path: Path to retrieval.yaml
        data_dir: Path to data directory
        persist_dir: Path to ChromaDB persistence directory
        force_reingest: If True, clear and re-ingest all documents

    Returns:
        Tuple of (VectorStore, ContextRetriever)
    """
    print("\n=== Initializing RAG System ===\n")

    # Initialize vector store
    vectorstore = VectorStore(config_path=config_path, persist_directory=persist_dir)

    # Check if we need to ingest documents
    collection_counts = vectorstore.list_collections()
    needs_ingestion = any(count == 0 for count in collection_counts.values())

    if force_reingest:
        print("Force re-ingestion requested. Clearing collections...")
        for collection_name in collection_counts.keys():
            if collection_name != "news":  # Don't clear news (not implemented yet)
                vectorstore.clear_collection(collection_name)
        needs_ingestion = True

    if needs_ingestion:
        print("Ingesting documents into vector store...")
        ingester = DocumentIngester(config_path=config_path, data_dir=data_dir)
        all_docs = ingester.ingest_all()

        # Add to vector store
        for collection_name, (documents, metadatas, ids) in all_docs.items():
            if documents:  # Only add if we have documents
                vectorstore.add_documents(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    collection_name=collection_name
                )
    else:
        print("Vector store already populated:")
        for name, count in collection_counts.items():
            print(f"  {name}: {count} documents")

    # Initialize retriever
    retriever = ContextRetriever(vectorstore=vectorstore, config_path=config_path)

    print("\nRAG system initialized.\n")

    return vectorstore, retriever


def initialize_memory(
    config_path: str = "./config/memory.yaml",
    persist_dir: str = "./data/chroma"
):
    """
    Initialize memory system for agent observations and reflections.

    Args:
        config_path: Path to memory.yaml
        persist_dir: Path to ChromaDB persistence directory

    Returns:
        MemoryStore instance
    """
    print("\n=== Initializing Memory System ===\n")

    try:
        memory_store = MemoryStore(config_path=config_path, persist_directory=persist_dir)

        # Report existing memory counts
        memory_count = memory_store.get_memory_count()
        print(f"Memory system initialized with {memory_count} existing memories.\n")

        return memory_store

    except Exception as e:
        print(f"Warning: Could not initialize memory system: {e}")
        print("Continuing without memory support.\n")
        return None


def save_deliberation(result: Dict, output_dir: str = "./output", sequential: bool = False):
    """
    Save deliberation result to JSON file for audit trail.
    For sequential workflows, also generates formatted markdown documents.

    Args:
        result: Deliberation result dict
        output_dir: Directory to save output files
        sequential: If True, generate formatted documents for sequential workflow
    """
    # For sequential workflow, use the document generator
    if sequential and "completed_meetings" in result:
        session_dir = save_sequential_documents(result, output_dir)
        print(f"\n📄 Documents saved to: {session_dir}/")
        print(f"  ✓ {len(result.get('completed_meetings', []))} meeting documents")
        print(f"  ✓ NSC_Policy_Memo.md")
        print(f"  ✓ index.md")
        print(f"  ✓ raw_data.json")
        return session_dir

    # For hub-and-spoke workflow, save JSON only
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    query_slug = result["query"][:50].replace(" ", "_").replace("/", "_")
    filename = f"deliberation_{timestamp}_{query_slug}.json"

    filepath = output_path / filename

    with open(filepath, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\nDeliberation saved to: {filepath}")

    return str(filepath)


def interactive_mode(orchestrator: NSCOrchestrator, cost_tracker: CostTracker, sequential: bool = False):
    """
    Run interactive mode where user can ask multiple questions.

    Args:
        orchestrator: NSCOrchestrator instance
        cost_tracker: CostTracker instance
        sequential: Use sequential workflow instead of hub-and-spoke
    """
    workflow_type = "Sequential Meetings" if sequential else "Hub-and-Spoke"
    print("\n" + "=" * 80)
    print(f"GaddisAI NSC Simulator - Interactive Mode ({workflow_type})")
    print("=" * 80)
    print("\nType your policy questions below. Type 'quit' or 'exit' to end.\n")

    while True:
        try:
            query = input("Policy Question: ").strip()

            if query.lower() in ["quit", "exit", "q"]:
                print("\nExiting...")
                print(cost_tracker.format_summary())
                break

            if not query:
                continue

            # Run deliberation
            if sequential:
                result = orchestrator.deliberate_sequential(query)
                formatted_output = orchestrator.format_sequential_output(result)
            else:
                result = orchestrator.deliberate(query)
                formatted_output = orchestrator.format_deliberation_output(result)

            # Track token usage
            usage = result.get("token_usage", {})
            cost_tracker.add_usage(
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0)
            )

            # Format and display
            print("\n" + formatted_output)

            # Show cost for this deliberation
            this_cost = cost_tracker.PRICING.get(cost_tracker.model, cost_tracker.PRICING["gpt-4o-mini"])
            input_cost = (usage.get("input_tokens", 0) / 1_000_000) * this_cost["input"]
            output_cost = (usage.get("output_tokens", 0) / 1_000_000) * this_cost["output"]
            total_deliberation_cost = input_cost + output_cost

            print(f"\n💰 This deliberation: ${total_deliberation_cost:.4f} "
                  f"({usage.get('total_tokens', 0):,} tokens)")

            # Save to file
            save_deliberation(result, sequential=sequential)

        except KeyboardInterrupt:
            print("\n\nExiting...")
            print(cost_tracker.format_summary())
            break
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()


def single_query_mode(orchestrator: NSCOrchestrator, query: str, cost_tracker: CostTracker, sequential: bool = False):
    """
    Run single query and exit.

    Args:
        orchestrator: NSCOrchestrator instance
        query: Policy question
        cost_tracker: CostTracker instance
        sequential: Use sequential workflow instead of hub-and-spoke
    """
    # Run deliberation
    if sequential:
        result = orchestrator.deliberate_sequential(query)
        formatted_output = orchestrator.format_sequential_output(result)
    else:
        result = orchestrator.deliberate(query)
        formatted_output = orchestrator.format_deliberation_output(result)

    # Track token usage
    usage = result.get("token_usage", {})
    cost_tracker.add_usage(
        usage.get("input_tokens", 0),
        usage.get("output_tokens", 0)
    )

    # Format and display
    print("\n" + formatted_output)

    # Show cost summary
    print(cost_tracker.format_summary())

    # Save to file
    save_deliberation(result, sequential=sequential)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="GaddisAI: NSC Policy Deliberation Simulator"
    )
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        default=None,
        help="Single policy question to deliberate (optional: sequential mode can run autonomously)"
    )
    parser.add_argument(
        "--reingest",
        action="store_true",
        help="Force re-ingestion of all documents into vector store"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4-turbo",
        help="OpenAI model to use (default: gpt-4-turbo)"
    )
    parser.add_argument(
        "--config-dir",
        type=str,
        default="./config",
        help="Path to config directory"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./data",
        help="Path to data directory"
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="Disable memory system (run without agent memories)"
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Use sequential meeting workflow instead of hub-and-spoke"
    )

    args = parser.parse_args()

    # Check environment
    check_environment()

    # Initialize RAG system
    config_path = Path(args.config_dir) / "retrieval.yaml"
    vectorstore, retriever = initialize_rag(
        config_path=str(config_path),
        data_dir=args.data_dir,
        force_reingest=args.reingest
    )

    # Initialize memory system (optional)
    memory_store = None
    if not args.no_memory:
        memory_config_path = Path(args.config_dir) / "memory.yaml"
        memory_store = initialize_memory(
            config_path=str(memory_config_path),
            persist_dir=str(Path(args.data_dir) / "chroma")
        )

    # Initialize orchestrator
    print("=== Initializing NSC Orchestrator ===\n")
    orchestrator = NSCOrchestrator(
        retriever=retriever,
        memory_store=memory_store,
        data_dir=args.data_dir,
        config_dir=args.config_dir,
        model=args.model
    )
    print("\nOrchestrator initialized.\n")

    # Initialize cost tracker
    cost_tracker = CostTracker(model=args.model)

    # Show cost estimate
    num_advisors = len(orchestrator.advisors)
    estimated_cost = cost_tracker.estimate_deliberation_cost(
        num_advisors=num_advisors,
        with_memory=(memory_store is not None)
    )
    print(cost_tracker.format_estimate(
        estimated_cost,
        args.model,
        num_advisors,
        memory_store is not None
    ))

    # Run in appropriate mode
    if args.sequential and not args.query:
        # Autonomous sequential mode - agents analyze Foreign Affairs and generate policy recommendations
        print("\n" + "=" * 80)
        print("AUTONOMOUS MODE: Agents will analyze Foreign Affairs articles")
        print("and generate national security policy recommendations")
        print("=" * 80 + "\n")

        autonomous_query = (
            "Based on recent Foreign Affairs analysis and current global developments, "
            "identify and analyze critical national security policy challenges requiring "
            "presidential attention. Focus on strategic competition, alliance management, "
            "military readiness, and diplomatic priorities."
        )
        single_query_mode(orchestrator, autonomous_query, cost_tracker, sequential=True)
    elif args.query:
        single_query_mode(orchestrator, args.query, cost_tracker, sequential=args.sequential)
    else:
        interactive_mode(orchestrator, cost_tracker, sequential=args.sequential)


if __name__ == "__main__":
    main()
