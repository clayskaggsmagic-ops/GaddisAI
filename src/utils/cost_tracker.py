"""
Simple cost tracking utility for OpenAI API usage.
Provides cost estimates and actual usage tracking.
"""


class CostTracker:
    """Track and estimate OpenAI API costs."""

    # Pricing as of 2024 (per 1M tokens)
    PRICING = {
        "gpt-4o-mini": {
            "input": 0.150,   # $0.15 per 1M input tokens
            "output": 0.600   # $0.60 per 1M output tokens
        },
        "gpt-4-turbo": {
            "input": 10.00,
            "output": 30.00
        },
        "gpt-4": {
            "input": 30.00,
            "output": 60.00
        },
        "text-embedding-3-small": {
            "input": 0.020,
            "output": 0.0
        }
    }

    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize cost tracker.

        Args:
            model: OpenAI model name
        """
        self.model = model
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def estimate_deliberation_cost(self, num_advisors: int = 3, with_memory: bool = True) -> float:
        """
        Estimate cost for a single deliberation.

        Args:
            num_advisors: Number of advisor agents
            with_memory: Whether memory system is enabled

        Returns:
            Estimated cost in dollars
        """
        # Get pricing for model
        pricing = self.PRICING.get(self.model, self.PRICING["gpt-4o-mini"])

        # Estimate tokens per component
        advisor_input = 2500  # Dossier + context + query
        advisor_output = 500  # Recommendation with rationale

        president_input = 4000  # Context + all advisor recommendations
        president_output = 800  # Decision with implementation

        # Base cost (advisors + president)
        base_input_tokens = (num_advisors * advisor_input) + president_input
        base_output_tokens = (num_advisors * advisor_output) + president_output

        # Memory overhead (if enabled)
        if with_memory:
            base_input_tokens += 100  # Memory retrieval
            # Note: Not adding importance scoring since use_llm is now false by default

        # Calculate cost
        input_cost = (base_input_tokens / 1_000_000) * pricing["input"]
        output_cost = (base_output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def add_usage(self, input_tokens: int, output_tokens: int):
        """
        Add actual token usage.

        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
        """
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def get_total_cost(self) -> float:
        """
        Calculate total cost based on actual usage.

        Returns:
            Total cost in dollars
        """
        pricing = self.PRICING.get(self.model, self.PRICING["gpt-4o-mini"])

        input_cost = (self.total_input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.total_output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def format_summary(self) -> str:
        """
        Format a summary of token usage and costs.

        Returns:
            Formatted string with usage statistics
        """
        total_cost = self.get_total_cost()

        summary = [
            "\n" + "=" * 60,
            "API USAGE SUMMARY",
            "=" * 60,
            f"Model: {self.model}",
            f"Input tokens: {self.total_input_tokens:,}",
            f"Output tokens: {self.total_output_tokens:,}",
            f"Total tokens: {self.total_input_tokens + self.total_output_tokens:,}",
            f"Estimated cost: ${total_cost:.4f}",
            "=" * 60
        ]

        return "\n".join(summary)

    @staticmethod
    def format_estimate(cost: float, model: str, num_advisors: int, with_memory: bool) -> str:
        """
        Format a cost estimate message.

        Args:
            cost: Estimated cost
            model: Model name
            num_advisors: Number of advisors
            with_memory: Whether memory is enabled

        Returns:
            Formatted estimate string
        """
        memory_str = "with memory" if with_memory else "without memory"

        return (
            f"\n💰 Cost Estimate: ${cost:.3f} per deliberation "
            f"({num_advisors} advisors, {model}, {memory_str})\n"
        )
