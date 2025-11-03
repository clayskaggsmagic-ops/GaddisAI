"""
Document generator for NSC sequential meetings.
Creates human-readable markdown documents from meeting transcripts.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List


def generate_meeting_document(meeting: Dict, meeting_number: int, scenario: str) -> str:
    """
    Generate a formatted markdown document for a single advisor-president meeting.

    Args:
        meeting: Meeting transcript dict
        meeting_number: Meeting sequence number (1, 2, 3, etc.)
        scenario: The scenario/query for this deliberation

    Returns:
        Formatted markdown string
    """
    advisor_person = meeting.get("advisor_person", "Unknown")
    advisor_role = meeting.get("advisor_role", "Unknown")
    problems = meeting.get("problems", [])
    selected_problem = meeting.get("selected_problem", {})
    question = meeting.get("question", "")
    answer = meeting.get("answer", "")
    reason = meeting.get("reason", "")  # Why President selected this problem

    # Get token usage
    token_usage = meeting.get("token_usage", {})
    total_tokens = 0
    for phase in ["problems", "selection", "answer"]:
        phase_usage = token_usage.get(phase, {})
        total_tokens += phase_usage.get("total_tokens", 0)

    # Build document
    lines = []

    # Header
    lines.append(f"# NSC Meeting #{meeting_number}: {advisor_role} {advisor_person}")
    lines.append(f"**Date:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    lines.append(f"**Scenario:** {scenario[:200]}{'...' if len(scenario) > 200 else ''}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Problems presented
    lines.append("## Problems Presented by " + advisor_role)
    lines.append("")

    for i, problem in enumerate(problems, 1):
        title = problem.get("title", "Untitled Problem")
        description = problem.get("description", "")
        initial_rec = problem.get("initial_recommendation", "")

        lines.append(f"### Problem {i}: {title}")
        lines.append("")
        lines.append(f"**Description:** {description}")
        lines.append("")
        lines.append(f"**Why This Matters:** {initial_rec}")
        lines.append("")

    # President's focus
    lines.append("---")
    lines.append("")
    lines.append("## President's Focus")
    lines.append("")

    selected_title = selected_problem.get("title", "Unknown")
    lines.append(f"**Selected Problem:** {selected_title}")
    lines.append("")

    if reason:
        lines.append(f"**Why This Problem:** {reason}")
        lines.append("")

    lines.append(f"**President's Question:**")
    lines.append(f"> {question}")
    lines.append("")

    # Advisor's response
    lines.append("---")
    lines.append("")
    lines.append(f"## {advisor_person}'s Response")
    lines.append("")
    lines.append(answer)
    lines.append("")

    # Extract key reasoning (if answer has structured sections)
    if "based on" in answer.lower() or "because" in answer.lower() or "reason" in answer.lower():
        lines.append("---")
        lines.append("")
        lines.append("### Key Reasoning")
        lines.append("")
        lines.append("*The response above includes the advisor's reasoning for their recommendations*")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(f"**Meeting Statistics:**")
    lines.append(f"- Total tokens used: {total_tokens:,}")
    lines.append(f"- Meeting concluded at {datetime.now().strftime('%I:%M %p')}")
    lines.append("")

    return "\n".join(lines)


def generate_final_memo_document(policy_doc: Dict, meetings: List[Dict], scenario: str) -> str:
    """
    Generate a formatted markdown document for the final NSC policy memo.

    Args:
        policy_doc: Policy document dict from President
        meetings: List of all meeting transcripts
        scenario: The scenario/query for this deliberation

    Returns:
        Formatted markdown string
    """
    president_person = policy_doc.get("person", "Unknown")
    policy_content = policy_doc.get("policy_document", "")
    token_usage = policy_doc.get("token_usage", {})
    total_tokens = token_usage.get("total_tokens", 0)

    # Build document
    lines = []

    # Header
    lines.append("# National Security Council Policy Memorandum")
    lines.append("")
    lines.append(f"**Date:** {datetime.now().strftime('%B %d, %Y')}")
    lines.append(f"**From:** {president_person}")
    lines.append(f"**Subject:** National Security Policy Recommendations")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Scenario context
    lines.append("## Context")
    lines.append("")
    lines.append(f"This policy memorandum addresses: *{scenario[:300]}{'...' if len(scenario) > 300 else ''}*")
    lines.append("")
    lines.append("This assessment is based on individual consultations with:")
    for meeting in meetings:
        advisor_person = meeting.get("advisor_person", "Unknown")
        advisor_role = meeting.get("advisor_role", "Unknown")
        lines.append(f"- {advisor_role} {advisor_person}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Policy content
    lines.append(policy_content)
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("## Document Metadata")
    lines.append("")
    lines.append(f"- **Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    lines.append(f"- **Based on:** {len(meetings)} individual advisor consultations")
    lines.append(f"- **Analysis tokens:** {total_tokens:,}")
    lines.append("")

    return "\n".join(lines)


def generate_index_document(meetings: List[Dict], scenario: str, session_dir: str) -> str:
    """
    Generate an index document with links to all meeting and policy documents.

    Args:
        meetings: List of all meeting transcripts
        scenario: The scenario/query for this deliberation
        session_dir: Name of the session directory

    Returns:
        Formatted markdown string
    """
    lines = []

    # Header
    lines.append("# NSC Sequential Meetings - Session Index")
    lines.append("")
    lines.append(f"**Date:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    lines.append(f"**Session:** {session_dir}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Scenario
    lines.append("## Scenario")
    lines.append("")
    lines.append(f"{scenario}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Meeting documents
    lines.append("## Individual Meeting Documents")
    lines.append("")

    for i, meeting in enumerate(meetings, 1):
        advisor_person = meeting.get("advisor_person", "Unknown")
        advisor_role = meeting.get("advisor_role", "Unknown")
        selected_problem = meeting.get("selected_problem", {})
        problem_title = selected_problem.get("title", "Unknown")

        # Create safe filename
        filename = f"meeting_{i:02d}_{advisor_role}_{advisor_person.replace(' ', '_')}.md"

        lines.append(f"### Meeting {i}: {advisor_role} {advisor_person}")
        lines.append(f"- **Focus:** {problem_title}")
        lines.append(f"- **Document:** [{filename}](./{filename})")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Final memo
    lines.append("## Final Policy Memorandum")
    lines.append("")
    lines.append("- **Document:** [NSC_Policy_Memo.md](./NSC_Policy_Memo.md)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Raw data
    lines.append("## Additional Files")
    lines.append("")
    lines.append("- **Raw Data (JSON):** [raw_data.json](./raw_data.json)")
    lines.append("  - Complete JSON dump of all meeting data for audit/analysis")
    lines.append("")

    return "\n".join(lines)


def save_sequential_documents(result: Dict, output_dir: str = "./output") -> str:
    """
    Save all sequential meeting documents to a timestamped directory.

    Args:
        result: Result dict from deliberate_sequential()
        output_dir: Base output directory

    Returns:
        Path to the created session directory
    """
    import json

    # Create timestamped session directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create safe query slug for directory name
    query = result.get("query", "deliberation")
    query_slug = "".join(c if c.isalnum() else "_" for c in query[:50])

    session_name = f"sequential_{timestamp}_{query_slug}"
    session_dir = Path(output_dir) / session_name
    session_dir.mkdir(parents=True, exist_ok=True)

    # Extract data
    completed_meetings = result.get("completed_meetings", [])
    policy_document = result.get("policy_document", {})
    scenario = result.get("query", "")

    # 1. Save individual meeting documents
    for i, meeting in enumerate(completed_meetings, 1):
        advisor_person = meeting.get("advisor_person", "Unknown")
        advisor_role = meeting.get("advisor_role", "Unknown")

        # Create safe filename
        filename = f"meeting_{i:02d}_{advisor_role}_{advisor_person.replace(' ', '_')}.md"
        filepath = session_dir / filename

        # Generate and save document
        doc_content = generate_meeting_document(meeting, i, scenario)
        with open(filepath, 'w') as f:
            f.write(doc_content)

    # 2. Save final NSC policy memo
    memo_filepath = session_dir / "NSC_Policy_Memo.md"
    memo_content = generate_final_memo_document(policy_document, completed_meetings, scenario)
    with open(memo_filepath, 'w') as f:
        f.write(memo_content)

    # 3. Save index document
    index_filepath = session_dir / "index.md"
    index_content = generate_index_document(completed_meetings, scenario, session_name)
    with open(index_filepath, 'w') as f:
        f.write(index_content)

    # 4. Save raw JSON for audit trail
    json_filepath = session_dir / "raw_data.json"
    with open(json_filepath, 'w') as f:
        json.dump(result, f, indent=2)

    return str(session_dir)
