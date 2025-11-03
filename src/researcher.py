"""
AI-powered researcher that generates YAML dossiers for NSC roles.

This module uses web search and LLM analysis to create structured
dossiers containing:
- Mandate & priorities
- Positions & recent actions
- Relationships to other principals
- Inferred weights & red lines
- Full provenance (sources with URLs)

Usage:
    from researcher import generate_dossier
    dossier = generate_dossier(role="Secretary of Defense", person="Lloyd Austin")
"""

import os
import json
import yaml
from datetime import datetime
from typing import Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class DossierResearcher:
    """Generates structured dossiers using web research and LLM analysis."""

    def __init__(self, model: str = "gpt-4o-mini", use_api: bool = True):
        """Initialize researcher with OpenAI client."""
        self.use_api = use_api and OPENAI_AVAILABLE
        self.model = model

        if self.use_api:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("⚠️  OPENAI_API_KEY not found, falling back to template mode")
                self.use_api = False
            else:
                self.client = OpenAI(api_key=api_key)

    def research_role(self, role: str, person: Optional[str] = None) -> Dict:
        """
        Research a role and generate structured dossier.

        Args:
            role: Official title (e.g., "Secretary of Defense")
            person: Optional specific person name

        Returns:
            Dict following dossier schema
        """
        # Build search queries
        queries = self._generate_search_queries(role, person)

        # Perform web searches
        search_results = self._web_search(queries)

        # Analyze and structure data
        dossier = self._analyze_and_structure(role, person, search_results)

        return dossier

    def _generate_search_queries(self, role: str, person: Optional[str]) -> List[str]:
        """Generate focused search queries for this role."""
        subject = person if person else role

        return [
            f"{subject} official mandate responsibilities",
            f"{subject} policy positions foreign policy",
            f"{subject} recent actions statements 2024 2025",
            f"{subject} relationships NSC principals",
            f"{subject} priorities goals",
            f"{role} statutory authority legal constraints",
        ]

    def _web_search(self, queries: List[str]) -> List[Dict]:
        """
        Perform web searches for each query.

        In production, this would use actual web search API.
        For MVP, we'll use LLM to simulate research based on training data.
        """
        # TODO: Replace with actual web search API (Brave, Tavily, etc.)
        # For now, we'll use LLM knowledge as a fallback

        results = []
        for query in queries:
            # Simulate search result
            results.append({
                "query": query,
                "note": "Using LLM knowledge (no live web search in MVP)"
            })

        return results

    def _generate_template(self, role: str, person: Optional[str]) -> Dict:
        """Generate a template dossier (fallback when API not available)."""
        return {
            "person": person or "Current officeholder",
            "role": role,
            "updated_at": datetime.now().strftime("%Y-%m-%d"),
            "mandate": [
                f"Execute statutory responsibilities of {role}",
                "Advise President on national security matters within domain"
            ],
            "enduring_priorities": [
                "Maintain organizational readiness",
                "Advance U.S. strategic interests",
                "Coordinate with interagency partners"
            ],
            "positions": [
                {
                    "claim": "Support for rules-based international order",
                    "quote": "[Template - replace with actual quote]",
                    "source": {
                        "title": "Template source",
                        "url": "https://example.com",
                        "date": "2024-01-01"
                    }
                }
            ],
            "recent_actions": [
                {
                    "action": "[Template - add recent action]",
                    "effect": "[Impact/significance]",
                    "source": {
                        "title": "Template source",
                        "url": "https://example.com",
                        "date": "2024-01-01"
                    }
                }
            ],
            "constraints": [
                "Congressional authorization requirements",
                "Budgetary limitations",
                "Statutory authorities"
            ],
            "relationships": {
                "President": "Direct report, policy executor",
                "NSA": "Coordination partner",
                "SecDef": "Peer principal",
                "SecState": "Peer principal"
            },
            "inferences": {
                "interests_weights": {
                    "deterrence": 0.5,
                    "escalation": 0.5,
                    "alliances": 0.5,
                    "readiness": 0.5,
                    "budget": 0.5,
                    "consensus": 0.5
                },
                "red_lines": [
                    "Avoid actions that undermine institutional authority",
                    "Maintain alignment with statutory mandate"
                ],
                "confidence": "low",
                "provenance": [
                    {
                        "title": "Template - requires AI research to populate",
                        "url": "https://example.com",
                        "date": datetime.now().strftime("%Y-%m-%d")
                    }
                ]
            }
        }

    def _analyze_and_structure(
        self,
        role: str,
        person: Optional[str],
        search_results: List[Dict]
    ) -> Dict:
        """Use LLM to analyze search results and generate structured dossier."""

        # Use template if API not available
        if not self.use_api:
            return self._generate_template(role, person)

        subject = f"{person} ({role})" if person else role

        prompt = f"""You are a national security analyst creating a structured dossier for: {subject}

Based on your knowledge (and ideally web search results), create a detailed dossier following this exact YAML schema:

person: "{person or 'Current officeholder'}"
role: "{role}"
updated_at: "{datetime.now().strftime('%Y-%m-%d')}"

mandate:
  - "Official statutory responsibilities"
  - "Key legal authorities"

enduring_priorities:
  - "Long-term priority 1"
  - "Long-term priority 2"
  - "Long-term priority 3"

positions:
  - claim: "Specific policy position"
    quote: "Actual quote if available"
    source:
      title: "Source document/speech"
      url: "https://example.com/source"
      date: "YYYY-MM-DD"

recent_actions:
  - action: "What was done (last 12 months)"
    effect: "Impact/significance"
    source:
      title: "Source"
      url: "https://example.com"
      date: "YYYY-MM-DD"

constraints:
  - "Budgetary constraints"
  - "Congressional oversight requirements"
  - "Treaty obligations"
  - "Bureaucratic limitations"

relationships:
  SecDef: "Brief relationship note"
  SecState: "Brief relationship note"
  NSA: "Brief relationship note"

inferences:
  interests_weights:
    deterrence: 0.0-1.0
    escalation: 0.0-1.0
    alliances: 0.0-1.0
    readiness: 0.0-1.0
    budget: 0.0-1.0
    consensus: 0.0-1.0
  red_lines:
    - "Line that cannot be crossed"
    - "Another critical constraint"
  confidence: "low|medium|high"
  provenance:
    - title: "Analysis based on X"
      url: "https://example.com"
      date: "YYYY-MM-DD"

Instructions:
1. Fill in realistic, factual information
2. Base positions on actual public statements when possible
3. Infer weights based on historical behavior (be explicit about inference)
4. Keep quotes accurate or mark as paraphrased
5. Include plausible sources (real publications/speeches)
6. Mark confidence level honestly
7. Ensure all dates are recent (2023-2025)

Return ONLY valid YAML, no other text."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a national security research analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        yaml_text = response.choices[0].message.content.strip()

        # Remove markdown code fences if present
        if yaml_text.startswith("```"):
            lines = yaml_text.split("\n")
            yaml_text = "\n".join(lines[1:-1])

        # Parse to validate
        dossier = yaml.safe_load(yaml_text)

        return dossier


def generate_dossier(role: str, person: Optional[str] = None, model: str = "gpt-4o-mini") -> Dict:
    """
    Convenience function to generate a dossier.

    Args:
        role: Official title
        person: Optional specific person name
        model: OpenAI model to use

    Returns:
        Dossier dict following schema
    """
    researcher = DossierResearcher(model=model)
    return researcher.research_role(role, person)


if __name__ == "__main__":
    # Quick test
    print("Testing dossier generation...")
    dossier = generate_dossier("Secretary of Defense", "Lloyd Austin")
    print(yaml.dump(dossier, default_flow_style=False, sort_keys=False))
