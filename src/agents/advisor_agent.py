"""
Advisor agent implementation for NSC principals (SecDef, SecState, NSA, etc.).
Advisors provide recommendations directly to the President.
"""

from typing import Dict, List, Optional
from .base_agent import NSCAgent


class AdvisorAgent(NSCAgent):
    """
    Advisor agent that provides policy recommendations to the President.
    Examples: SecDef, SecState, NSA, etc.
    """

    def generate_recommendation(
        self,
        query: str,
        context: str,
        memories: Optional[List[Dict]] = None,
        other_recommendations: Optional[List[Dict]] = None,
        temperature: float = 0.7
    ) -> Dict[str, str]:
        """
        Generate advisor's recommendation to the President.

        Args:
            query: Policy question from user
            context: Retrieved background context from RAG
            memories: Relevant memories from past deliberations
            other_recommendations: Optional list of other advisors' recommendations
                                  (advisors can see each other's positions)
            temperature: LLM temperature

        Returns:
            Dict with 'role', 'person', 'recommendation', 'rationale', 'risks', 'alternatives'
        """
        system_prompt = self._build_system_prompt()

        # Build detailed prompt for advisor recommendation
        user_prompt_parts = []

        # Add context
        if context:
            user_prompt_parts.append("## Relevant Background Information\n")
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

        # Add other advisors' recommendations if available
        if other_recommendations:
            user_prompt_parts.append("## Other Advisors' Recommendations\n")
            for rec in other_recommendations:
                speaker = rec.get("person", rec.get("role", "Unknown"))
                content = rec.get("recommendation", rec.get("content", ""))
                user_prompt_parts.append(f"**{speaker} ({rec.get('role', '')})**:\n{content}\n")
            user_prompt_parts.append("\n")

        # Add the policy question
        user_prompt_parts.append("## Policy Question\n")
        user_prompt_parts.append(query)
        user_prompt_parts.append("\n")

        # Add instruction for structured response
        user_prompt_parts.append("""
## Your Task

Provide your recommendation to the President on this policy question. Your response should include:

1. **Recommendation**: Your clear, actionable recommendation
2. **Rationale**: Why you recommend this course of action, based on:
   - Your mandate and priorities
   - Your priority weights (deterrence, alliances, budget, etc.)
   - Relevant background information
3. **Risks**: Key risks and potential downsides of your recommendation
4. **Alternatives**: Brief mention of alternative approaches (if any)

Be direct and specific. The President needs clear guidance rooted in your expertise and responsibilities.
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

        # Parse structured response (basic parsing, could be improved)
        sections = self._parse_recommendation(content)

        return {
            "role": self.role,
            "person": self.person,
            "recommendation": sections.get("recommendation", content),
            "rationale": sections.get("rationale", ""),
            "risks": sections.get("risks", ""),
            "alternatives": sections.get("alternatives", ""),
            "full_response": content,
            "weights": self.weights,
            "red_lines": self.red_lines
        }

    def _parse_recommendation(self, content: str) -> Dict[str, str]:
        """
        Parse structured recommendation from LLM response.

        Args:
            content: Full LLM response

        Returns:
            Dict with parsed sections
        """
        sections = {
            "recommendation": "",
            "rationale": "",
            "risks": "",
            "alternatives": ""
        }

        # Simple section parsing based on headers
        current_section = None
        lines = content.split("\n")

        for line in lines:
            line_lower = line.lower().strip()

            if "recommendation" in line_lower and line.startswith("#"):
                current_section = "recommendation"
                continue
            elif "rationale" in line_lower and line.startswith("#"):
                current_section = "rationale"
                continue
            elif "risk" in line_lower and line.startswith("#"):
                current_section = "risks"
                continue
            elif "alternative" in line_lower and line.startswith("#"):
                current_section = "alternatives"
                continue

            if current_section:
                sections[current_section] += line + "\n"

        # If no sections found, put everything in recommendation
        if not any(sections.values()):
            sections["recommendation"] = content

        return sections

    def present_problems(
        self,
        query: str,
        context: str,
        memories: Optional[List[Dict]] = None,
        previous_meetings: Optional[List[Dict]] = None,
        temperature: float = 0.7
    ) -> Dict:
        """
        Present 3 policy problems based on Foreign Affairs article context.

        Args:
            query: The Foreign Affairs article or scenario context
            context: Retrieved background context from RAG
            memories: Relevant memories from past deliberations
            previous_meetings: Transcripts of previous advisor meetings (for awareness)
            temperature: LLM temperature

        Returns:
            Dict with 'role', 'person', 'problems' (list of 3 problem dicts), 'token_usage'
        """
        system_prompt = self._build_system_prompt()

        # Build prompt for problem presentation
        user_prompt_parts = []

        # Add context from Foreign Affairs article
        if context:
            user_prompt_parts.append("## Foreign Affairs Article Context\n")
            user_prompt_parts.append(context)
            user_prompt_parts.append("\n")

        # Add article/scenario query
        if query:
            user_prompt_parts.append("## Current Scenario\n")
            user_prompt_parts.append(query)
            user_prompt_parts.append("\n")

        # Add memories from past deliberations
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

        # Add previous meetings for awareness
        if previous_meetings:
            user_prompt_parts.append("## Previous Advisor Meetings with President\n")
            user_prompt_parts.append("You are aware of these previous discussions:\n\n")
            for meeting in previous_meetings:
                advisor_name = meeting.get("advisor_person", meeting.get("advisor_role", "Unknown"))
                user_prompt_parts.append(f"**Meeting with {advisor_name}:**\n")

                problems = meeting.get("problems", [])
                user_prompt_parts.append(f"- Presented {len(problems)} problems\n")

                selected_problem = meeting.get("selected_problem", {})
                if selected_problem:
                    user_prompt_parts.append(f"- President focused on: {selected_problem.get('title', 'Unknown')}\n")

                user_prompt_parts.append("\n")

            user_prompt_parts.append("\n")

        # Add instruction for structured response
        user_prompt_parts.append("""
## Your Task

Based on the Foreign Affairs article context and your expertise, identify the **3 most pressing policy problems** in your domain that require presidential attention.

For each problem, provide:

1. **Title**: Brief, clear title (5-10 words)
2. **Description**: What is the problem? Why is it urgent? (2-3 sentences)
3. **Initial Recommendation**: Your preliminary recommendation for addressing it (1-2 sentences)

Format your response exactly as follows:

**PROBLEM 1**
Title: [Your title]
Description: [Your description]
Initial Recommendation: [Your recommendation]

**PROBLEM 2**
Title: [Your title]
Description: [Your description]
Initial Recommendation: [Your recommendation]

**PROBLEM 3**
Title: [Your title]
Description: [Your description]
Initial Recommendation: [Your recommendation]

Focus on problems that align with your mandate and priority weights. Be specific and actionable.
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

        # Parse the 3 problems from response
        problems = self._parse_problems(content)

        return {
            "role": self.role,
            "person": self.person,
            "problems": problems,
            "full_response": content,
            "token_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
        }

    def answer_question(
        self,
        question: str,
        selected_problem: Dict,
        context: str,
        memories: Optional[List[Dict]] = None,
        temperature: float = 0.7
    ) -> Dict:
        """
        Answer the President's follow-up question about a selected problem.

        Args:
            question: The President's question
            selected_problem: The problem the President selected (from present_problems)
            context: Retrieved background context from RAG
            memories: Relevant memories from past deliberations
            temperature: LLM temperature

        Returns:
            Dict with 'role', 'person', 'answer', 'token_usage'
        """
        system_prompt = self._build_system_prompt()

        # Build prompt for answering question
        user_prompt_parts = []

        # Add the selected problem context
        user_prompt_parts.append("## The Problem You Presented\n")
        user_prompt_parts.append(f"**Title**: {selected_problem.get('title', 'Unknown')}\n")
        user_prompt_parts.append(f"**Description**: {selected_problem.get('description', '')}\n")
        user_prompt_parts.append(f"**Your Initial Recommendation**: {selected_problem.get('initial_recommendation', '')}\n")
        user_prompt_parts.append("\n")

        # Add relevant background context
        if context:
            user_prompt_parts.append("## Relevant Background Information\n")
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

        # Add the President's question
        user_prompt_parts.append("## President's Question\n")
        user_prompt_parts.append(question)
        user_prompt_parts.append("\n")

        # Add instruction
        user_prompt_parts.append("""
## Your Task

Answer the President's question directly and thoroughly. Draw on:
- Your expertise and mandate
- The problem context you presented
- Relevant background information
- Your past experiences (memories)

Be specific, actionable, and honest about risks and trade-offs. The President needs clear guidance to make an informed decision.
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
            "answer": content,
            "question": question,
            "token_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
        }

    def _parse_problems(self, content: str) -> List[Dict]:
        """
        Parse 3 problems from LLM response.

        Args:
            content: Full LLM response

        Returns:
            List of 3 problem dicts with 'title', 'description', 'initial_recommendation'
        """
        problems = []
        lines = content.split("\n")

        current_problem = None
        current_field = None

        for line in lines:
            line_stripped = line.strip()

            # Check for problem marker
            if line_stripped.startswith("**PROBLEM"):
                if current_problem:
                    problems.append(current_problem)
                current_problem = {
                    "title": "",
                    "description": "",
                    "initial_recommendation": ""
                }
                continue

            # Check for field markers
            if line_stripped.startswith("Title:"):
                current_field = "title"
                value = line_stripped.replace("Title:", "").strip()
                if current_problem:
                    current_problem["title"] = value
                continue
            elif line_stripped.startswith("Description:"):
                current_field = "description"
                value = line_stripped.replace("Description:", "").strip()
                if current_problem:
                    current_problem["description"] = value
                continue
            elif line_stripped.startswith("Initial Recommendation:"):
                current_field = "initial_recommendation"
                value = line_stripped.replace("Initial Recommendation:", "").strip()
                if current_problem:
                    current_problem["initial_recommendation"] = value
                continue

            # Continue accumulating text for current field
            if current_field and current_problem and line_stripped:
                if current_problem[current_field]:
                    current_problem[current_field] += " " + line_stripped
                else:
                    current_problem[current_field] = line_stripped

        # Add the last problem
        if current_problem:
            problems.append(current_problem)

        # Ensure we have exactly 3 problems (fill with placeholders if needed)
        while len(problems) < 3:
            problems.append({
                "title": "Problem parsing error",
                "description": "Unable to parse this problem from response",
                "initial_recommendation": "N/A"
            })

        return problems[:3]  # Return only first 3

    def __repr__(self):
        return f"AdvisorAgent(role={self.role}, person={self.person})"
