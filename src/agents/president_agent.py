"""
President agent implementation with relationship weighting and interest alignment.
The President receives recommendations from advisors, weighs them based on
personal relationships and interest alignment, then makes the final decision.
"""

from typing import Dict, List, Optional
import math
from .base_agent import NSCAgent


class PresidentAgent(NSCAgent):
    """
    President agent that receives advisor recommendations and makes final decisions.
    Weighs advice based on:
    1. Personal relationship/favor with each advisor
    2. Alignment of recommendation with President's own interests/priorities
    """

    def __init__(
        self,
        role: str,
        dossier_path: str,
        roles_config_path: str,
        model: str = "gpt-4"
    ):
        """
        Initialize President agent.

        Args:
            role: Should be "President"
            dossier_path: Path to President's dossier
            roles_config_path: Path to roles.yaml with advisor relationships
            model: OpenAI model to use
        """
        super().__init__(role, dossier_path, roles_config_path, model)

        # Extract advisor relationships (favor/trust scores)
        self.advisor_relationships = self.role_config.get("advisor_relationships", {})

    def calculate_interest_alignment(
        self,
        recommendation: Dict[str, str]
    ) -> float:
        """
        Calculate how well an advisor's recommendation aligns with President's interests.

        Uses simple weight matching: compares advisor's priority weights with President's.
        Higher alignment = advisor prioritizes same things President cares about.

        Args:
            recommendation: Advisor's recommendation dict with 'weights' key

        Returns:
            Alignment score between 0.0 and 1.0
        """
        advisor_weights = recommendation.get("weights", {})

        if not advisor_weights or not self.weights:
            return 0.5  # Neutral if no weights available

        # Calculate dot product of weight vectors (normalized)
        common_priorities = set(self.weights.keys()) & set(advisor_weights.keys())

        if not common_priorities:
            return 0.5  # Neutral if no common priorities

        # Dot product of aligned priorities
        alignment_sum = 0.0
        for priority in common_priorities:
            alignment_sum += self.weights[priority] * advisor_weights[priority]

        # Normalize by max possible alignment
        max_alignment = sum(self.weights[p] * advisor_weights[p]
                          for p in common_priorities)
        max_possible = sum(max(self.weights[p], advisor_weights[p])
                          for p in common_priorities)

        if max_possible == 0:
            return 0.5

        # Scale to 0-1 range
        alignment = alignment_sum / max_possible

        return alignment

    def calculate_advisor_weight(
        self,
        advisor_role: str,
        recommendation: Dict[str, str]
    ) -> Dict[str, float]:
        """
        Calculate final weight to give an advisor's recommendation.

        Combines:
        1. Relationship score (how much President favors this advisor)
        2. Interest alignment (how well recommendation aligns with President's priorities)

        Args:
            advisor_role: Role name (e.g., "SecDef")
            recommendation: Advisor's recommendation dict

        Returns:
            Dict with 'relationship_score', 'alignment_score', 'final_weight', 'explanation'
        """
        # Get relationship score (0.0 to 1.0)
        relationship_score = self.advisor_relationships.get(advisor_role, 0.5)

        # Calculate interest alignment (0.0 to 1.0)
        alignment_score = self.calculate_interest_alignment(recommendation)

        # Combine: 60% relationship, 40% alignment
        # (President favors loyal advisors but also considers alignment)
        final_weight = (0.6 * relationship_score) + (0.4 * alignment_score)

        explanation = (
            f"{advisor_role}: Relationship={relationship_score:.2f}, "
            f"Alignment={alignment_score:.2f}, "
            f"Final Weight={final_weight:.2f}"
        )

        return {
            "relationship_score": relationship_score,
            "alignment_score": alignment_score,
            "final_weight": final_weight,
            "explanation": explanation
        }

    def make_decision(
        self,
        query: str,
        context: str,
        memories: Optional[List[Dict]] = None,
        advisor_recommendations: List[Dict[str, str]] = None,
        temperature: float = 0.7
    ) -> Dict:
        """
        Make final presidential decision based on weighted advisor recommendations.

        Args:
            query: Original policy question
            context: Retrieved background context
            memories: Relevant memories from past deliberations
            advisor_recommendations: List of advisor recommendation dicts
            temperature: LLM temperature

        Returns:
            Dict with 'decision', 'rationale', 'advisor_weights', 'full_deliberation'
        """
        if advisor_recommendations is None:
            advisor_recommendations = []
        # Calculate weights for each advisor
        advisor_weights = {}
        for rec in advisor_recommendations:
            advisor_role = rec.get("role", "Unknown")
            weight_info = self.calculate_advisor_weight(advisor_role, rec)
            advisor_weights[advisor_role] = weight_info

        # Build system prompt
        system_prompt = self._build_system_prompt()
        system_prompt += "\n\n## Your Decision-Making Process\n"
        system_prompt += "You weigh advice from your advisors based on:\n"
        system_prompt += "1. Your personal relationship and trust in each advisor\n"
        system_prompt += "2. How well their recommendations align with your priorities\n"
        system_prompt += "3. Your own judgment and experience\n"

        # Build user prompt with weighted recommendations
        user_prompt_parts = []

        # Add context
        if context:
            user_prompt_parts.append("## Background Information\n")
            user_prompt_parts.append(context)
            user_prompt_parts.append("\n")

        # Add memories from past deliberations
        if memories and len(memories) > 0:
            user_prompt_parts.append("## Your Relevant Memories from Past Deliberations\n")
            user_prompt_parts.append("These are your memories of past interactions, decisions, and reflections:\n\n")
            for memory in memories:
                timestamp = memory.get("timestamp", "Unknown time")
                content = memory.get("content", "")
                memory_type = memory.get("memory_type", "observation")

                # Format timestamp nicely
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%B %d, %Y at %I:%M %p")
                except:
                    time_str = timestamp

                # Different formatting for reflections vs observations
                if memory_type == "reflection":
                    user_prompt_parts.append(f"**[REFLECTION]** ({time_str})")
                    user_prompt_parts.append(f"  {content}\n")
                else:
                    user_prompt_parts.append(f"- [{time_str}] {content}")

            user_prompt_parts.append("\n")

        # Add policy question
        user_prompt_parts.append("## Policy Question\n")
        user_prompt_parts.append(query)
        user_prompt_parts.append("\n")

        # Add advisor recommendations with weights
        user_prompt_parts.append("## Advisor Recommendations\n")
        user_prompt_parts.append("You have received recommendations from your advisors. "
                                "Here is how much weight to give each advisor:\n\n")

        for rec in advisor_recommendations:
            advisor_role = rec.get("role", "Unknown")
            advisor_person = rec.get("person", "Unknown")
            weight_info = advisor_weights.get(advisor_role, {})

            user_prompt_parts.append(f"### {advisor_person} ({advisor_role})")
            user_prompt_parts.append(f"**Weight**: {weight_info.get('final_weight', 0.5):.2f}")
            user_prompt_parts.append(f"**Explanation**: {weight_info.get('explanation', '')}")
            user_prompt_parts.append(f"\n**Recommendation**:\n{rec.get('recommendation', rec.get('full_response', ''))}")
            user_prompt_parts.append("\n")

        # Add decision prompt
        user_prompt_parts.append("""
## Your Task

Make your final decision on this policy question. Your response should include:

1. **Decision**: Your clear, actionable decision
2. **Rationale**: Explain your reasoning, including:
   - Which advisors' recommendations you gave more weight to and why
   - How their advice aligns (or doesn't) with your priorities
   - Your own judgment on the situation
3. **Implementation**: Any specific guidance on how to implement this decision

Remember: You make the final call based on your priorities, your relationships with advisors, and your judgment of what's best for the country.
""")

        user_prompt = "\n".join(user_prompt_parts)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )

        content = response.choices[0].message.content

        # Parse decision
        sections = self._parse_decision(content)

        return {
            "role": self.role,
            "person": self.person,
            "decision": sections.get("decision", content),
            "rationale": sections.get("rationale", ""),
            "implementation": sections.get("implementation", ""),
            "full_response": content,
            "advisor_weights": advisor_weights,
            "query": query
        }

    def _parse_decision(self, content: str) -> Dict[str, str]:
        """
        Parse structured decision from LLM response.

        Args:
            content: Full LLM response

        Returns:
            Dict with parsed sections
        """
        sections = {
            "decision": "",
            "rationale": "",
            "implementation": ""
        }

        current_section = None
        lines = content.split("\n")

        for line in lines:
            line_lower = line.lower().strip()

            if "decision" in line_lower and line.startswith("#"):
                current_section = "decision"
                continue
            elif "rationale" in line_lower and line.startswith("#"):
                current_section = "rationale"
                continue
            elif "implementation" in line_lower and line.startswith("#"):
                current_section = "implementation"
                continue

            if current_section:
                sections[current_section] += line + "\n"

        # If no sections found, put everything in decision
        if not any(sections.values()):
            sections["decision"] = content

        return sections

    def select_problem_and_question(
        self,
        advisor_problems: Dict,
        context: str,
        memories: Optional[List[Dict]] = None,
        previous_meetings: Optional[List[Dict]] = None,
        temperature: float = 0.7
    ) -> Dict:
        """
        Select 1 problem from advisor's 3 presented problems and formulate a follow-up question.

        Args:
            advisor_problems: Dict with 'role', 'person', 'problems' (list of 3 problems)
            context: Retrieved background context from RAG
            memories: Relevant memories from past deliberations
            previous_meetings: Transcripts of previous meetings (for context)
            temperature: LLM temperature

        Returns:
            Dict with 'selected_problem_index', 'selected_problem', 'question', 'token_usage'
        """
        system_prompt = self._build_system_prompt()

        # Build prompt for problem selection
        user_prompt_parts = []

        # Add advisor and their problems
        advisor_person = advisor_problems.get("person", "Unknown")
        advisor_role = advisor_problems.get("role", "Unknown")
        problems = advisor_problems.get("problems", [])

        user_prompt_parts.append(f"## Meeting with {advisor_person} ({advisor_role})\n")
        user_prompt_parts.append(f"{advisor_person} has presented 3 policy problems for your consideration:\n\n")

        for i, problem in enumerate(problems, 1):
            user_prompt_parts.append(f"**PROBLEM {i}**")
            user_prompt_parts.append(f"Title: {problem.get('title', 'Unknown')}")
            user_prompt_parts.append(f"Description: {problem.get('description', '')}")
            user_prompt_parts.append(f"Initial Recommendation: {problem.get('initial_recommendation', '')}")
            user_prompt_parts.append("\n")

        # Add background context
        if context:
            user_prompt_parts.append("## Background Information\n")
            user_prompt_parts.append(context)
            user_prompt_parts.append("\n")

        # Add memories
        if memories and len(memories) > 0:
            user_prompt_parts.append("## Your Relevant Memories from Past Deliberations\n")
            for memory in memories:
                timestamp = memory.get("timestamp", "Unknown time")
                content = memory.get("content", "")
                memory_type = memory.get("memory_type", "observation")

                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%B %d, %Y at %I:%M %p")
                except:
                    time_str = timestamp

                if memory_type == "reflection":
                    user_prompt_parts.append(f"**[REFLECTION]** ({time_str})")
                    user_prompt_parts.append(f"  {content}\n")
                else:
                    user_prompt_parts.append(f"- [{time_str}] {content}")

            user_prompt_parts.append("\n")

        # Add previous meetings for context
        if previous_meetings:
            user_prompt_parts.append("## Previous Meetings Today\n")
            for meeting in previous_meetings:
                prev_advisor = meeting.get("advisor_person", "Unknown")
                user_prompt_parts.append(f"- Met with {prev_advisor}")
                selected = meeting.get("selected_problem", {})
                if selected:
                    user_prompt_parts.append(f"  - Discussed: {selected.get('title', 'Unknown')}")
            user_prompt_parts.append("\n")

        # Add instruction
        user_prompt_parts.append("""
## Your Task

Select the **ONE** problem that is most pressing or interesting to you, then formulate **ONE** follow-up question for the advisor.

Format your response exactly as follows:

**SELECTED PROBLEM**: [Number 1, 2, or 3]

**REASON**: [Brief explanation of why this problem is most important to you - 1-2 sentences]

**QUESTION**: [Your specific follow-up question for the advisor]

Choose based on:
- Your priorities and interests
- Urgency of the situation
- What you need to know to make a decision
- Context from previous meetings (if any)
""")

        user_prompt = "\n".join(user_prompt_parts)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )

        content = response.choices[0].message.content

        # Extract token usage
        usage = response.usage if hasattr(response, 'usage') else None
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        # Parse selected problem and question
        parsed = self._parse_problem_selection(content)
        selected_index = parsed.get("selected_index", 0)
        selected_problem = problems[selected_index] if 0 <= selected_index < len(problems) else problems[0]

        return {
            "role": self.role,
            "person": self.person,
            "selected_problem_index": selected_index,
            "selected_problem": selected_problem,
            "question": parsed.get("question", "Can you provide more details?"),
            "reason": parsed.get("reason", ""),
            "full_response": content,
            "token_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
        }

    def synthesize_policy_document(
        self,
        query: str,
        context: str,
        memories: Optional[List[Dict]] = None,
        all_meetings: List[Dict] = None,
        temperature: float = 0.7
    ) -> Dict:
        """
        Synthesize all meeting discussions into a comprehensive NSC policy document.

        Args:
            query: The original Foreign Affairs article or scenario
            context: Retrieved background context from RAG
            memories: Relevant memories from past deliberations
            all_meetings: List of all meeting transcripts
            temperature: LLM temperature

        Returns:
            Dict with 'policy_document', 'token_usage'
        """
        system_prompt = self._build_system_prompt()
        system_prompt += "\n\n## Your Task\n"
        system_prompt += "You are synthesizing all advisor discussions into a comprehensive National Security Council policy document."

        # Build prompt for synthesis
        user_prompt_parts = []

        # Add the original scenario
        user_prompt_parts.append("## Foreign Affairs Article / Scenario\n")
        user_prompt_parts.append(query)
        user_prompt_parts.append("\n")

        # Add background context
        if context:
            user_prompt_parts.append("## Background Information\n")
            user_prompt_parts.append(context)
            user_prompt_parts.append("\n")

        # Add memories
        if memories and len(memories) > 0:
            user_prompt_parts.append("## Your Relevant Memories from Past Deliberations\n")
            for memory in memories:
                timestamp = memory.get("timestamp", "Unknown time")
                content = memory.get("content", "")
                memory_type = memory.get("memory_type", "observation")

                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%B %d, %Y at %I:%M %p")
                except:
                    time_str = timestamp

                if memory_type == "reflection":
                    user_prompt_parts.append(f"**[REFLECTION]** ({time_str})")
                    user_prompt_parts.append(f"  {content}\n")
                else:
                    user_prompt_parts.append(f"- [{time_str}] {content}")

            user_prompt_parts.append("\n")

        # Add all meeting transcripts
        user_prompt_parts.append("## Advisor Meeting Summaries\n")
        user_prompt_parts.append("You met with your advisors and discussed the following:\n\n")

        if all_meetings:
            for i, meeting in enumerate(all_meetings, 1):
                advisor_person = meeting.get("advisor_person", "Unknown")
                advisor_role = meeting.get("advisor_role", "Unknown")

                user_prompt_parts.append(f"### Meeting {i}: {advisor_person} ({advisor_role})\n")

                # Problems presented
                problems = meeting.get("problems", [])
                user_prompt_parts.append(f"\n**Problems Presented:**")
                for j, problem in enumerate(problems, 1):
                    user_prompt_parts.append(f"\n{j}. {problem.get('title', 'Unknown')}")

                # Selected problem and discussion
                selected = meeting.get("selected_problem", {})
                question = meeting.get("question", "")
                answer = meeting.get("answer", "")

                user_prompt_parts.append(f"\n\n**Discussion Focus:** {selected.get('title', 'Unknown')}")
                user_prompt_parts.append(f"\n**Your Question:** {question}")
                user_prompt_parts.append(f"\n**{advisor_person}'s Answer:** {answer}")
                user_prompt_parts.append("\n")

        # Add instruction for NSC document format
        user_prompt_parts.append("""
## Your Task

Write a comprehensive **National Security Council Policy Document** that synthesizes all the discussions and presents your final policy position.

Use the following structure:

# National Security Council Policy Document

## I. SITUATION ASSESSMENT
[Summarize the current situation based on the Foreign Affairs article and advisor input]

## II. POLICY ANALYSIS
[Analyze the key problems identified by your advisors and your assessment of each]

## III. POLICY DECISION
[Your clear, actionable policy decisions on how the United States will respond]

## IV. IMPLEMENTATION GUIDANCE
[Specific guidance on how to implement these decisions, including:]
- Immediate actions
- Resource allocation
- Interagency coordination
- Timeline and milestones

Be comprehensive but concise. This document represents the official U.S. national security policy position.
""")

        user_prompt = "\n".join(user_prompt_parts)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )

        content = response.choices[0].message.content

        # Extract token usage
        usage = response.usage if hasattr(response, 'usage') else None
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        return {
            "role": self.role,
            "person": self.person,
            "policy_document": content,
            "token_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
        }

    def _parse_problem_selection(self, content: str) -> Dict:
        """
        Parse problem selection and question from LLM response.

        Args:
            content: Full LLM response

        Returns:
            Dict with 'selected_index', 'reason', 'question'
        """
        result = {
            "selected_index": 0,
            "reason": "",
            "question": ""
        }

        lines = content.split("\n")
        current_field = None

        for line in lines:
            line_stripped = line.strip()

            # Check for field markers
            if line_stripped.startswith("**SELECTED PROBLEM"):
                current_field = "selected_index"
                # Extract number from line
                if "1" in line_stripped:
                    result["selected_index"] = 0
                elif "2" in line_stripped:
                    result["selected_index"] = 1
                elif "3" in line_stripped:
                    result["selected_index"] = 2
                continue
            elif line_stripped.startswith("**REASON"):
                current_field = "reason"
                value = line_stripped.replace("**REASON**:", "").replace("**REASON**", "").strip()
                result["reason"] = value
                continue
            elif line_stripped.startswith("**QUESTION"):
                current_field = "question"
                value = line_stripped.replace("**QUESTION**:", "").replace("**QUESTION**", "").strip()
                result["question"] = value
                continue

            # Continue accumulating text for current field
            if current_field in ["reason", "question"] and line_stripped:
                if result[current_field]:
                    result[current_field] += " " + line_stripped
                else:
                    result[current_field] = line_stripped

        return result

    def __repr__(self):
        return f"PresidentAgent(person={self.person}, advisors={list(self.advisor_relationships.keys())})"
