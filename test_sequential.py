#!/usr/bin/env python3
"""
Simple test script to verify sequential workflow implementation.
Tests structure and method signatures without calling OpenAI API.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from agents.advisor_agent import AdvisorAgent
        from agents.president_agent import PresidentAgent
        from orchestrator import NSCOrchestrator, SequentialMeetingState
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import error: {e}")
        return False


def test_agent_methods():
    """Test that new agent methods exist."""
    print("\nTesting agent methods...")

    try:
        from agents.advisor_agent import AdvisorAgent
        from agents.president_agent import PresidentAgent

        # Check AdvisorAgent methods
        assert hasattr(AdvisorAgent, 'present_problems'), "Missing present_problems method"
        assert hasattr(AdvisorAgent, 'answer_question'), "Missing answer_question method"
        print("  ✓ AdvisorAgent has new methods")

        # Check PresidentAgent methods
        assert hasattr(PresidentAgent, 'select_problem_and_question'), "Missing select_problem_and_question method"
        assert hasattr(PresidentAgent, 'synthesize_policy_document'), "Missing synthesize_policy_document method"
        print("  ✓ PresidentAgent has new methods")

        return True
    except Exception as e:
        print(f"  ✗ Method check error: {e}")
        return False


def test_orchestrator_methods():
    """Test that orchestrator has sequential methods."""
    print("\nTesting orchestrator methods...")

    try:
        from orchestrator import NSCOrchestrator

        assert hasattr(NSCOrchestrator, '_conduct_meeting_node'), "Missing _conduct_meeting_node"
        assert hasattr(NSCOrchestrator, '_should_continue_meetings'), "Missing _should_continue_meetings"
        assert hasattr(NSCOrchestrator, '_president_synthesizes_node'), "Missing _president_synthesizes_node"
        assert hasattr(NSCOrchestrator, '_build_sequential_graph'), "Missing _build_sequential_graph"
        assert hasattr(NSCOrchestrator, 'deliberate_sequential'), "Missing deliberate_sequential"
        assert hasattr(NSCOrchestrator, 'format_sequential_output'), "Missing format_sequential_output"
        print("  ✓ NSCOrchestrator has all sequential methods")

        return True
    except Exception as e:
        print(f"  ✗ Orchestrator check error: {e}")
        return False


def test_state_definition():
    """Test that SequentialMeetingState is defined."""
    print("\nTesting state definition...")

    try:
        from orchestrator import SequentialMeetingState

        # Check required fields exist in type hints
        annotations = SequentialMeetingState.__annotations__
        required_fields = ['query', 'context', 'memories', 'advisor_order',
                          'current_meeting_index', 'completed_meetings',
                          'policy_document', 'audit_trail']

        for field in required_fields:
            assert field in annotations, f"Missing field: {field}"

        print("  ✓ SequentialMeetingState has all required fields")
        return True
    except Exception as e:
        print(f"  ✗ State definition error: {e}")
        return False


def test_method_signatures():
    """Test method signatures match expected parameters."""
    print("\nTesting method signatures...")

    try:
        from agents.advisor_agent import AdvisorAgent
        from agents.president_agent import PresidentAgent
        import inspect

        # Test present_problems signature
        sig = inspect.signature(AdvisorAgent.present_problems)
        params = list(sig.parameters.keys())
        assert 'query' in params and 'context' in params and 'memories' in params, \
            "present_problems missing required parameters"
        print("  ✓ present_problems signature correct")

        # Test answer_question signature
        sig = inspect.signature(AdvisorAgent.answer_question)
        params = list(sig.parameters.keys())
        assert 'question' in params and 'selected_problem' in params, \
            "answer_question missing required parameters"
        print("  ✓ answer_question signature correct")

        # Test select_problem_and_question signature
        sig = inspect.signature(PresidentAgent.select_problem_and_question)
        params = list(sig.parameters.keys())
        assert 'advisor_problems' in params, \
            "select_problem_and_question missing advisor_problems parameter"
        print("  ✓ select_problem_and_question signature correct")

        # Test synthesize_policy_document signature
        sig = inspect.signature(PresidentAgent.synthesize_policy_document)
        params = list(sig.parameters.keys())
        assert 'all_meetings' in params, \
            "synthesize_policy_document missing all_meetings parameter"
        print("  ✓ synthesize_policy_document signature correct")

        return True
    except Exception as e:
        print(f"  ✗ Signature check error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Sequential Workflow Implementation Tests")
    print("=" * 60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Agent Methods", test_agent_methods()))
    results.append(("Orchestrator Methods", test_orchestrator_methods()))
    results.append(("State Definition", test_state_definition()))
    results.append(("Method Signatures", test_method_signatures()))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:.<30} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! Sequential workflow is ready to use.")
        print("\nTo run with your API key:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print("  python src/main.py --sequential --query 'Your question here'")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
