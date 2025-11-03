"""
Base agent class for GaddisAI NSC simulation.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from openai import OpenAI


class NSCAgent:
    """Base class for NSC principals (advisors and President)."""

    def __init__(
        self,
        role: str,
        dossier_path: str,
        roles_config_path: str,
        model: str = "gpt-4"
    ):
        """
        Initialize an NSC agent.

        Args:
            role: Role name (e.g., "SecDef", "SecState", "President")
            dossier_path: Path to agent's dossier YAML file
            roles_config_path: Path to roles.yaml configuration
            model: OpenAI model to use
        """
        self.role = role
        self.model = model
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        # Load dossier
        with open(dossier_path, 'r') as f:
            self.dossier = yaml.safe_load(f)

        # Load role configuration
        with open(roles_config_path, 'r') as f:
            roles_config = yaml.safe_load(f)
            self.role_config = roles_config.get(role, {})

        # Extract key attributes
        self.person = self.dossier.get("person", "Unknown")
        self.title = self.dossier.get("role", role)
        self.weights = self.role_config.get("weights", {})
        self.red_lines = self.role_config.get("red_lines", [])

    def _build_system_prompt(self) -> str:
        """
        Build system prompt from dossier and role configuration.

        Returns:
            System prompt string
        """
        prompt_parts = [
            f"You are {self.person}, {self.title}.",
            f"\n## Your Mandate\n{self.dossier.get('mandate', '')}",
            f"\n## Your Enduring Priorities\n{self.dossier.get('enduring_priorities', '')}",
            "\n## Your Priority Weights"
        ]

        # Add weights
        for priority, weight in self.weights.items():
            prompt_parts.append(f"- {priority}: {weight}")

        # Add red lines
        if self.red_lines:
            prompt_parts.append("\n## Your Red Lines (Non-negotiable Constraints)")
            for red_line in self.red_lines:
                prompt_parts.append(f"- {red_line}")

        # Add positions if available
        if self.dossier.get("positions"):
            prompt_parts.append("\n## Your Known Positions")
            positions = self.dossier.get("positions", {})
            for topic, details in positions.items():
                prompt_parts.append(f"\n### {topic}")
                if isinstance(details, dict):
                    stance = details.get("stance", "")
                    sources = details.get("sources", [])
                    prompt_parts.append(f"{stance}")
                    if sources:
                        prompt_parts.append(f"Sources: {', '.join(sources)}")
                else:
                    prompt_parts.append(str(details))

        # Add recent actions
        if self.dossier.get("recent_actions"):
            prompt_parts.append(f"\n## Your Recent Actions\n{self.dossier.get('recent_actions', '')}")

        # Add constraints
        if self.dossier.get("constraints"):
            prompt_parts.append(f"\n## Current Constraints\n{self.dossier.get('constraints', '')}")

        return "\n".join(prompt_parts)

    def __repr__(self):
        return f"NSCAgent(role={self.role}, person={self.person})"
