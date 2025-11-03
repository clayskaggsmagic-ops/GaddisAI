"""
LangGraph orchestrator for hub-and-spoke NSC deliberation.
All advisors meet with the President directly (no coordinator synthesis).
"""

from typing import Dict, List, TypedDict, Annotated, Optional
import operator
import random
from pathlib import Path
from langgraph.graph import StateGraph, END
from agents.advisor_agent import AdvisorAgent
from agents.president_agent import PresidentAgent
from rag.retriever import ContextRetriever
from memory.memory_store import MemoryStore


class DeliberationState(TypedDict):
    """State passed through the deliberation workflow."""
    query: str  # Original policy question
    context: str  # Retrieved background context from RAG
    memories: Dict  # Agent-specific memories retrieved for this deliberation
    advisor_recommendations: Annotated[List[Dict], operator.add]  # Recommendations from advisors
    presidential_decision: Dict  # Final decision from President
    reflections: List[Dict]  # Post-deliberation reflections
    audit_trail: Annotated[List[Dict], operator.add]  # Full history for transparency


class SequentialMeetingState(TypedDict):
    """State for sequential meeting workflow."""
    query: str  # Foreign Affairs article or scenario
    context: str  # Retrieved background context from RAG
    memories: Dict  # Agent-specific memories
    advisor_order: List[str]  # Randomized order of advisors
    current_meeting_index: int  # Which meeting we're on
    completed_meetings: Annotated[List[Dict], operator.add]  # All meeting transcripts
    policy_document: Dict  # Final NSC policy document
    audit_trail: Annotated[List[Dict], operator.add]


class NSCOrchestrator:
    """
    Orchestrates hub-and-spoke deliberation between advisors and President.
    """

    def __init__(
        self,
        retriever: ContextRetriever,
        memory_store: Optional[MemoryStore] = None,
        data_dir: str = "./data",
        config_dir: str = "./config",
        model: str = "gpt-4"
    ):
        """
        Initialize NSC orchestrator.

        Args:
            retriever: ContextRetriever instance
            memory_store: MemoryStore instance (optional)
            data_dir: Path to data directory with dossiers
            config_dir: Path to config directory with roles.yaml
            model: OpenAI model to use
        """
        self.retriever = retriever
        self.memory_store = memory_store
        self.data_dir = Path(data_dir)
        self.config_dir = Path(config_dir)
        self.model = model

        # Initialize agents
        self.advisors = {}
        self.president = None

        self._initialize_agents()

        # Build workflow graph
        self.graph = self._build_graph()

    def _initialize_agents(self):
        """Initialize all advisor and President agents from dossiers."""
        dossiers_dir = self.data_dir / "dossiers"
        roles_config = self.config_dir / "roles.yaml"

        # Check for nested structure (trump_admin/) vs flat structure
        trump_admin_dir = dossiers_dir / "trump_admin"
        if trump_admin_dir.exists():
            dossiers_dir = trump_admin_dir

        # Initialize President
        president_dossier = dossiers_dir / "President.yaml"
        if not president_dossier.exists():
            # Try nested profile.yaml structure
            president_profile = dossiers_dir / "President" / "profile.yaml"
            if president_profile.exists():
                president_dossier = president_profile

        if president_dossier.exists():
            self.president = PresidentAgent(
                role="President",
                dossier_path=str(president_dossier),
                roles_config_path=str(roles_config),
                model=self.model
            )
            print(f"Initialized President: {self.president.person}")

        # Initialize advisors (look for both flat and nested structures)
        # First try flat structure
        for dossier_path in dossiers_dir.glob("*.yaml"):
            if dossier_path.stem == "President":
                continue

            role = dossier_path.stem  # e.g., "SecDef", "SecState"
            advisor = AdvisorAgent(
                role=role,
                dossier_path=str(dossier_path),
                roles_config_path=str(roles_config),
                model=self.model
            )
            self.advisors[role] = advisor
            print(f"Initialized {role}: {advisor.person}")

        # Then try nested structure (directories with profile.yaml)
        for role_dir in dossiers_dir.iterdir():
            if not role_dir.is_dir() or role_dir.name == "President":
                continue

            profile_path = role_dir / "profile.yaml"
            if profile_path.exists() and role_dir.name not in self.advisors:
                role = role_dir.name
                advisor = AdvisorAgent(
                    role=role,
                    dossier_path=str(profile_path),
                    roles_config_path=str(roles_config),
                    model=self.model
                )
                self.advisors[role] = advisor
                print(f"Initialized {role}: {advisor.person}")

    def _retrieve_context_node(self, state: DeliberationState) -> DeliberationState:
        """Node: Retrieve relevant context from RAG system and agent memories."""
        query = state["query"]

        # Retrieve context from all sources
        retrieved_docs = self.retriever.retrieve_for_query(
            query=query,
            include_types=["memo", "doctrine", "dossiers"]
        )

        # Format context for prompts
        context = self.retriever.format_context_for_prompt(retrieved_docs)

        # Display retrieved documents for visibility
        print("  Retrieved documents:")
        for doc_type, docs in retrieved_docs.items():
            if docs:
                print(f"    {doc_type.upper()}:")
                for doc in docs:
                    source = doc["metadata"].get("source", "unknown")
                    similarity = 1 - doc.get("distance", 0)

                    # Show section info for dossiers
                    if doc_type == "dossiers" and "section" in doc["metadata"]:
                        section = doc["metadata"]["section"]
                        person = doc["metadata"].get("person", "unknown")
                        print(f"      - {person} ({section}, similarity: {similarity:.3f})")
                    # Show chunk info for memos and doctrine
                    elif "chunk_index" in doc["metadata"]:
                        chunk_idx = doc["metadata"]["chunk_index"]
                        total = doc["metadata"].get("total_chunks", "?")
                        print(f"      - {source} (chunk {chunk_idx+1}/{total}, similarity: {similarity:.3f})")
                    else:
                        print(f"      - {source} (similarity: {similarity:.3f})")

        # Retrieve memories for all agents (if memory store enabled)
        memories = {}
        if self.memory_store:
            print("  Retrieving agent memories...")

            # Retrieve memories for each advisor
            for role in self.advisors.keys():
                agent_memories = self.memory_store.retrieve_memories(
                    agent_role=role,
                    query=query,
                    top_k=5
                )
                memories[role] = agent_memories

            # Retrieve President's memories
            president_memories = self.memory_store.retrieve_memories(
                agent_role="President",
                query=query,
                top_k=5
            )
            memories["President"] = president_memories

        state["context"] = context
        state["memories"] = memories
        state["audit_trail"] = [{
            "step": "context_retrieval",
            "query": query,
            "retrieved_doc_counts": {k: len(v) for k, v in retrieved_docs.items()},
            "retrieved_sources": {
                k: [{"source": doc["metadata"].get("source", "unknown"),
                     "similarity": 1 - doc.get("distance", 0),
                     "chunk": doc["metadata"].get("chunk_index") if "chunk_index" in doc["metadata"] else None}
                    for doc in v]
                for k, v in retrieved_docs.items()
            },
            "memory_counts": {role: len(mems) for role, mems in memories.items()} if memories else {}
        }]

        return state

    def _advisors_consult_node(self, state: DeliberationState) -> DeliberationState:
        """
        Node: All advisors generate recommendations in parallel.
        Advisors can see each other's recommendations (passed in second round if needed).
        """
        query = state["query"]
        context = state["context"]
        memories = state.get("memories", {})
        existing_recommendations = state.get("advisor_recommendations", [])

        recommendations = []

        # Each advisor generates their recommendation
        # They can see other recommendations if they exist
        for role, advisor in self.advisors.items():
            print(f"  {role} ({advisor.person}) is drafting recommendation...")

            # Get memories for this advisor
            agent_memories = memories.get(role, [])

            recommendation = advisor.generate_recommendation(
                query=query,
                context=context,
                memories=agent_memories,
                other_recommendations=existing_recommendations,
                temperature=0.7
            )

            recommendations.append(recommendation)

            # Add to audit trail
            state["audit_trail"] = [{
                "step": f"advisor_recommendation",
                "advisor": role,
                "person": advisor.person,
                "recommendation": recommendation,
                "memories_used": len(agent_memories)
            }]

        state["advisor_recommendations"] = recommendations

        return state

    def _president_decides_node(self, state: DeliberationState) -> DeliberationState:
        """Node: President weighs all advice and makes final decision."""
        query = state["query"]
        context = state["context"]
        memories = state.get("memories", {})
        advisor_recommendations = state["advisor_recommendations"]

        print(f"  President ({self.president.person}) is making decision...")

        # Get President's memories
        president_memories = memories.get("President", [])

        decision = self.president.make_decision(
            query=query,
            context=context,
            memories=president_memories,
            advisor_recommendations=advisor_recommendations,
            temperature=0.7
        )

        state["presidential_decision"] = decision

        # Add to audit trail
        state["audit_trail"] = [{
            "step": "presidential_decision",
            "person": self.president.person,
            "decision": decision,
            "memories_used": len(president_memories)
        }]

        return state

    def _reflect_and_store_node(self, state: DeliberationState) -> DeliberationState:
        """Node: Store observations and generate reflections."""
        if not self.memory_store:
            return state

        query = state["query"]
        advisor_recommendations = state["advisor_recommendations"]
        decision = state["presidential_decision"]

        reflections = []

        # Store advisor observations
        for rec in advisor_recommendations:
            observation = (
                f"I recommended: {rec.get('recommendation', rec.get('full_response', ''))[:200]}... "
                f"on the question: '{query}'"
            )

            self.memory_store.add_observation(
                agent_role=rec["role"],
                content=observation,
                importance=0.7,
                metadata={"type": "recommendation", "query": query}
            )

            # Check if reflection should be generated
            if self.memory_store.should_reflect(rec["role"]):
                reflection = self.memory_store.generate_reflection(rec["role"])
                if reflection:
                    self.memory_store.add_observation(
                        agent_role=rec["role"],
                        content=reflection,
                        importance=0.95,
                        metadata={"type": "reflection"}
                    )
                    reflections.append({"agent": rec["role"], "reflection": reflection})

        # Store President's observation
        top_advisor = max(
            decision.get("advisor_weights", {}).items(),
            key=lambda x: x[1].get("final_weight", 0),
            default=("unknown", {})
        )[0]

        observation = (
            f"I decided: {decision.get('decision', decision.get('full_response', ''))[:200]}... "
            f"on the question: '{query}'. "
            f"I gave most weight to {top_advisor}."
        )

        self.memory_store.add_observation(
            agent_role="President",
            content=observation,
            importance=0.9,
            metadata={"type": "decision", "query": query}
        )

        # Check if President should reflect
        if self.memory_store.should_reflect("President"):
            reflection = self.memory_store.generate_reflection("President")
            if reflection:
                self.memory_store.add_observation(
                    agent_role="President",
                    content=reflection,
                    importance=0.95,
                    metadata={"type": "reflection"}
                )
                reflections.append({"agent": "President", "reflection": reflection})

        state["reflections"] = reflections

        # Add to audit trail
        state["audit_trail"] = [{
            "step": "reflection_and_storage",
            "observations_stored": len(advisor_recommendations) + 1,
            "reflections_generated": len(reflections)
        }]

        return state

    def _conduct_meeting_node(self, state: SequentialMeetingState) -> SequentialMeetingState:
        """
        Node: Conduct one advisor-president meeting.
        Advisor presents 3 problems → President selects 1 + asks question → Advisor answers.
        """
        query = state["query"]
        context = state["context"]
        memories = state.get("memories", {})
        advisor_order = state["advisor_order"]
        current_index = state["current_meeting_index"]
        previous_meetings = state.get("completed_meetings", [])

        # Get current advisor
        advisor_role = advisor_order[current_index]
        advisor = self.advisors[advisor_role]

        print(f"\n  Meeting {current_index + 1}/{len(advisor_order)}: {advisor.person} ({advisor_role})")

        # Step 1: Advisor presents 3 problems
        print(f"    {advisor.person} presenting problems...")
        advisor_memories = memories.get(advisor_role, [])
        problems_result = advisor.present_problems(
            query=query,
            context=context,
            memories=advisor_memories,
            previous_meetings=previous_meetings,
            temperature=0.7
        )

        # Step 2: President selects 1 problem and asks question
        print(f"    President selecting problem...")
        president_memories = memories.get("President", [])
        selection_result = self.president.select_problem_and_question(
            advisor_problems=problems_result,
            context=context,
            memories=president_memories,
            previous_meetings=previous_meetings,
            temperature=0.7
        )

        # Step 3: Advisor answers question
        print(f"    {advisor.person} answering question...")
        answer_result = advisor.answer_question(
            question=selection_result["question"],
            selected_problem=selection_result["selected_problem"],
            context=context,
            memories=advisor_memories,
            temperature=0.7
        )

        # Create meeting transcript
        meeting = {
            "advisor_role": advisor_role,
            "advisor_person": advisor.person,
            "problems": problems_result["problems"],
            "selected_problem": selection_result["selected_problem"],
            "question": selection_result["question"],
            "reason": selection_result.get("reason", ""),  # Why President selected this problem
            "answer": answer_result["answer"],
            "token_usage": {
                "problems": problems_result.get("token_usage", {}),
                "selection": selection_result.get("token_usage", {}),
                "answer": answer_result.get("token_usage", {})
            }
        }

        # Store memories if enabled
        if self.memory_store:
            # Advisor memory: presented problems
            self.memory_store.add_observation(
                agent_role=advisor_role,
                content=f"I presented 3 problems to President on '{query[:100]}...' and discussed: {selection_result['selected_problem'].get('title', '')}",
                importance=0.7
            )

            # President memory: this meeting
            self.memory_store.add_observation(
                agent_role="President",
                content=f"Met with {advisor.person}. Discussed: {selection_result['selected_problem'].get('title', '')}. Asked: {selection_result['question'][:100]}",
                importance=0.8
            )

        state["completed_meetings"] = [meeting]
        state["current_meeting_index"] = current_index + 1

        state["audit_trail"] = [{
            "step": "meeting",
            "meeting_number": current_index + 1,
            "advisor": advisor_role,
            "selected_problem": selection_result["selected_problem"].get("title", "")
        }]

        return state

    def _should_continue_meetings(self, state: SequentialMeetingState) -> str:
        """Conditional: Check if more meetings needed."""
        current_index = state["current_meeting_index"]
        total_advisors = len(state["advisor_order"])

        if current_index < total_advisors:
            return "continue"
        else:
            return "synthesize"

    def _president_synthesizes_node(self, state: SequentialMeetingState) -> SequentialMeetingState:
        """Node: President synthesizes all meetings into NSC policy document."""
        query = state["query"]
        context = state["context"]
        memories = state.get("memories", {})
        all_meetings = state["completed_meetings"]

        print(f"\n  President synthesizing policy document...")

        president_memories = memories.get("President", [])
        policy_result = self.president.synthesize_policy_document(
            query=query,
            context=context,
            memories=president_memories,
            all_meetings=all_meetings,
            temperature=0.7
        )

        # Store memory
        if self.memory_store:
            self.memory_store.add_observation(
                agent_role="President",
                content=f"I synthesized NSC policy document on '{query[:100]}...' after meeting with {len(all_meetings)} advisors",
                importance=0.95
            )

        state["policy_document"] = policy_result

        state["audit_trail"] = [{
            "step": "synthesis",
            "meetings_synthesized": len(all_meetings)
        }]

        return state

    def _build_sequential_graph(self) -> StateGraph:
        """Build LangGraph workflow for sequential meetings."""
        workflow = StateGraph(SequentialMeetingState)

        # Add nodes
        workflow.add_node("retrieve_context", self._retrieve_context_node)
        workflow.add_node("conduct_meeting", self._conduct_meeting_node)
        workflow.add_node("synthesize", self._president_synthesizes_node)

        # Define flow
        workflow.set_entry_point("retrieve_context")
        workflow.add_edge("retrieve_context", "conduct_meeting")

        # Conditional: continue meetings or synthesize
        workflow.add_conditional_edges(
            "conduct_meeting",
            self._should_continue_meetings,
            {
                "continue": "conduct_meeting",  # Loop back
                "synthesize": "synthesize"      # Move to synthesis
            }
        )

        workflow.add_edge("synthesize", END)

        return workflow.compile()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow for hub-and-spoke deliberation."""
        workflow = StateGraph(DeliberationState)

        # Add nodes
        workflow.add_node("retrieve_context", self._retrieve_context_node)
        workflow.add_node("advisors_consult", self._advisors_consult_node)
        workflow.add_node("president_decides", self._president_decides_node)
        workflow.add_node("reflect_and_store", self._reflect_and_store_node)

        # Define edges (linear flow with memory storage at end)
        workflow.set_entry_point("retrieve_context")
        workflow.add_edge("retrieve_context", "advisors_consult")
        workflow.add_edge("advisors_consult", "president_decides")
        workflow.add_edge("president_decides", "reflect_and_store")
        workflow.add_edge("reflect_and_store", END)

        return workflow.compile()

    def deliberate(self, query: str) -> Dict:
        """
        Run full deliberation process on a policy question.

        Args:
            query: Policy question to deliberate

        Returns:
            Dict with full deliberation results including:
            - query
            - context
            - advisor_recommendations
            - presidential_decision
            - audit_trail (full transparency log)
        """
        print(f"\n=== NSC Deliberation ===")
        print(f"Query: {query}\n")

        # Initialize state
        initial_state = {
            "query": query,
            "context": "",
            "memories": {},
            "advisor_recommendations": [],
            "presidential_decision": {},
            "reflections": [],
            "audit_trail": []
        }

        # Run workflow
        print("Retrieving context...")
        final_state = self.graph.invoke(initial_state)

        print("\nDeliberation complete.\n")

        # Calculate total token usage
        total_input = 0
        total_output = 0

        for rec in final_state["advisor_recommendations"]:
            usage = rec.get("token_usage", {})
            total_input += usage.get("input_tokens", 0)
            total_output += usage.get("output_tokens", 0)

        decision_usage = final_state["presidential_decision"].get("token_usage", {})
        total_input += decision_usage.get("input_tokens", 0)
        total_output += decision_usage.get("output_tokens", 0)

        return {
            "query": final_state["query"],
            "context": final_state["context"],
            "advisor_recommendations": final_state["advisor_recommendations"],
            "presidential_decision": final_state["presidential_decision"],
            "audit_trail": final_state["audit_trail"],
            "token_usage": {
                "input_tokens": total_input,
                "output_tokens": total_output,
                "total_tokens": total_input + total_output
            }
        }

    def format_deliberation_output(self, result: Dict) -> str:
        """
        Format deliberation result for human-readable display.

        Args:
            result: Result dict from deliberate()

        Returns:
            Formatted string showing full deliberation
        """
        output_parts = []

        output_parts.append("=" * 80)
        output_parts.append("NSC DELIBERATION SUMMARY")
        output_parts.append("=" * 80)
        output_parts.append(f"\nQUERY: {result['query']}\n")

        # Show advisor recommendations
        output_parts.append("\n" + "=" * 80)
        output_parts.append("ADVISOR RECOMMENDATIONS")
        output_parts.append("=" * 80)

        for rec in result["advisor_recommendations"]:
            output_parts.append(f"\n### {rec['person']} ({rec['role']})")
            output_parts.append(f"\nPriority Weights: {rec.get('weights', {})}")
            output_parts.append(f"Red Lines: {rec.get('red_lines', [])}")
            output_parts.append(f"\n{rec.get('full_response', rec.get('recommendation', ''))}")
            output_parts.append("\n" + "-" * 80)

        # Show presidential decision with weighting
        output_parts.append("\n" + "=" * 80)
        output_parts.append("PRESIDENTIAL DECISION")
        output_parts.append("=" * 80)

        decision = result["presidential_decision"]
        output_parts.append(f"\n### {decision['person']}\n")

        # Show advisor weights
        output_parts.append("**Advisor Influence Weights:**")
        for advisor_role, weight_info in decision.get("advisor_weights", {}).items():
            output_parts.append(f"  - {advisor_role}:")
            output_parts.append(f"    * Relationship Score: {weight_info['relationship_score']:.2f}")
            output_parts.append(f"    * Interest Alignment: {weight_info['alignment_score']:.2f}")
            output_parts.append(f"    * Final Weight: {weight_info['final_weight']:.2f}")

        output_parts.append(f"\n{decision.get('full_response', '')}")

        output_parts.append("\n" + "=" * 80 + "\n")

        return "\n".join(output_parts)

    def deliberate_sequential(self, query: str) -> Dict:
        """
        Run sequential meeting workflow.
        Each advisor meets individually with President in random order.

        Args:
            query: Foreign Affairs article or scenario

        Returns:
            Dict with:
            - query
            - context
            - completed_meetings (list of meeting transcripts)
            - policy_document
            - token_usage
        """
        print(f"\n=== NSC Sequential Meetings ===")
        print(f"Scenario: {query[:100]}...\n")

        # Randomize advisor order
        advisor_order = list(self.advisors.keys())
        random.shuffle(advisor_order)
        print(f"Meeting order: {', '.join(advisor_order)}\n")

        # Initialize state
        initial_state = {
            "query": query,
            "context": "",
            "memories": {},
            "advisor_order": advisor_order,
            "current_meeting_index": 0,
            "completed_meetings": [],
            "policy_document": {},
            "audit_trail": []
        }

        # Build and run sequential graph
        print("Retrieving context...")
        sequential_graph = self._build_sequential_graph()
        final_state = sequential_graph.invoke(initial_state)

        print("\nSequential meetings complete.\n")

        # Calculate total token usage
        total_input = 0
        total_output = 0

        for meeting in final_state["completed_meetings"]:
            usage = meeting.get("token_usage", {})
            for key in ["problems", "selection", "answer"]:
                tokens = usage.get(key, {})
                total_input += tokens.get("input_tokens", 0)
                total_output += tokens.get("output_tokens", 0)

        policy_usage = final_state["policy_document"].get("token_usage", {})
        total_input += policy_usage.get("input_tokens", 0)
        total_output += policy_usage.get("output_tokens", 0)

        return {
            "query": final_state["query"],
            "context": final_state["context"],
            "completed_meetings": final_state["completed_meetings"],
            "policy_document": final_state["policy_document"],
            "audit_trail": final_state["audit_trail"],
            "token_usage": {
                "input_tokens": total_input,
                "output_tokens": total_output,
                "total_tokens": total_input + total_output
            }
        }

    def format_sequential_output(self, result: Dict) -> str:
        """
        Format sequential meeting result for display.

        Args:
            result: Result dict from deliberate_sequential()

        Returns:
            Formatted string
        """
        output_parts = []

        output_parts.append("=" * 80)
        output_parts.append("NSC SEQUENTIAL MEETINGS SUMMARY")
        output_parts.append("=" * 80)
        output_parts.append(f"\nSCENARIO: {result['query'][:200]}...\n")

        # Show each meeting
        output_parts.append("\n" + "=" * 80)
        output_parts.append("ADVISOR MEETINGS")
        output_parts.append("=" * 80)

        for i, meeting in enumerate(result["completed_meetings"], 1):
            advisor = meeting["advisor_person"]
            role = meeting["advisor_role"]

            output_parts.append(f"\n### MEETING {i}: {advisor} ({role})")
            output_parts.append("\n**Problems Presented:**")

            for j, problem in enumerate(meeting["problems"], 1):
                output_parts.append(f"\n{j}. {problem.get('title', 'Unknown')}")
                output_parts.append(f"   {problem.get('description', '')[:150]}...")

            output_parts.append(f"\n\n**President's Focus:** {meeting['selected_problem'].get('title', '')}")
            output_parts.append(f"\n**President's Question:** {meeting['question']}")
            output_parts.append(f"\n**{advisor}'s Answer:**")
            output_parts.append(meeting["answer"])
            output_parts.append("\n" + "-" * 80)

        # Show policy document
        output_parts.append("\n" + "=" * 80)
        output_parts.append("NSC POLICY DOCUMENT")
        output_parts.append("=" * 80)

        policy_doc = result["policy_document"].get("policy_document", "")
        output_parts.append(f"\n{policy_doc}")

        output_parts.append("\n" + "=" * 80 + "\n")

        return "\n".join(output_parts)
