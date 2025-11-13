"""
LLM Service Wrapper

Unified interface for LLM calls with:
- Claude 3.5 Sonnet (primary model)
- Token counting and cost tracking
- Generation time logging
- User budget management

Week 1, Day 1-2: Hybrid Task Generation Enhancement
"""

import time
import logging
from decimal import Decimal
from typing import Dict, Optional

import tiktoken
from anthropic import Anthropic
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class LLMService:
    """
    LLM service using Claude 3.5 Sonnet for all task generation.

    Why Sonnet (not Haiku or GPT-4o-mini):
    - Best quality for task generation
    - 200k context window (full user profile)
    - Consistent style across all tasks
    - Fast enough (2-3s response)
    - Cost: ~$0.20/user (acceptable)
    """

    # Model configuration
    # Fallback to Claude 3 Haiku (widely available, faster, cheaper)
    # Original: claude-3-5-sonnet-20240620 (getting 404 - API key may not have access)
    MODEL = "claude-3-haiku-20240307"

    # Pricing (as of Nov 2024)
    PRICE_PER_MILLION_INPUT_TOKENS = Decimal('3.00')   # $3/MTok
    PRICE_PER_MILLION_OUTPUT_TOKENS = Decimal('15.00')  # $15/MTok

    def __init__(self):
        """Initialize Anthropic client and token encoder"""
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        self.client = Anthropic(api_key=api_key)

        # Use GPT-4 encoder as approximation (close enough for Claude)
        try:
            self.encoder = tiktoken.encoding_for_model("gpt-4")
        except Exception as e:
            logger.warning(f"Failed to load tiktoken encoder: {e}, using cl100k_base")
            self.encoder = tiktoken.get_encoding("cl100k_base")

        logger.info(f"[LLMService] Initialized with model: {self.MODEL}")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Dict:
        """
        Generate response with full tracking.

        Args:
            prompt: User prompt
            max_tokens: Maximum output tokens
            temperature: 0-1, higher = more creative
            system_prompt: Optional system prompt

        Returns:
            {
                'text': Generated text,
                'cost': Decimal cost in USD,
                'input_tokens': Count,
                'output_tokens': Count,
                'generation_time': Seconds,
                'model': Model name
            }
        """
        start_time = time.time()

        # Count input tokens
        input_tokens = self._count_tokens(prompt)
        if system_prompt:
            input_tokens += self._count_tokens(system_prompt)

        # Build messages
        messages = [{"role": "user", "content": prompt}]

        try:
            # Call Claude
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt if system_prompt else "",
                messages=messages
            )

            # Extract text
            text = response.content[0].text

            # Count output tokens
            output_tokens = self._count_tokens(text)

            # Calculate cost
            cost = self._calculate_cost(input_tokens, output_tokens)

            # Calculate time
            generation_time = time.time() - start_time

            # Log
            logger.info(
                f"[LLMService] Generated: {input_tokens} in, {output_tokens} out, "
                f"${cost:.4f}, {generation_time:.2f}s"
            )

            return {
                'text': text,
                'cost': cost,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'generation_time': generation_time,
                'model': self.MODEL
            }

        except Exception as e:
            logger.error(f"[LLMService] Generation failed: {e}")
            raise

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        try:
            tokens = self.encoder.encode(text)
            return len(tokens)
        except Exception as e:
            logger.warning(f"Token counting failed: {e}, using character estimate")
            # Fallback: ~4 chars per token
            return len(text) // 4

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> Decimal:
        """Calculate cost based on token counts"""
        input_cost = (Decimal(input_tokens) / Decimal('1000000')) * self.PRICE_PER_MILLION_INPUT_TOKENS
        output_cost = (Decimal(output_tokens) / Decimal('1000000')) * self.PRICE_PER_MILLION_OUTPUT_TOKENS
        total_cost = input_cost + output_cost

        return total_cost.quantize(Decimal('0.0001'))  # Round to 4 decimal places

    def track_cost(self, user, cost: Decimal, operation: str = 'task_generation'):
        """
        Track LLM cost for a user.

        Args:
            user: User object
            cost: Cost in USD
            operation: Operation type (for analytics)
        """
        from users.models import UserProfile

        # Update user's budget
        profile = user.profile
        profile.llm_budget_spent = (profile.llm_budget_spent or Decimal('0')) + cost
        profile.save(update_fields=['llm_budget_spent'])

        # Log to analytics (if model exists)
        try:
            from ai.models import LLMUsageLog
            LLMUsageLog.objects.create(
                user=user,
                operation=operation,
                model=self.MODEL,
                cost=cost
            )
        except Exception as e:
            # LLMUsageLog model might not exist yet, skip for now
            logger.debug(f"LLMUsageLog not available: {e}")

        # Check budget limits
        budget_limit = profile.llm_budget_limit or Decimal('5.00')
        if profile.llm_budget_spent >= budget_limit * Decimal('0.8'):  # 80% threshold
            logger.warning(
                f"[LLMService] User {user.id} approaching budget limit: "
                f"${profile.llm_budget_spent:.2f} / ${budget_limit:.2f}"
            )

            # TODO: Send alert to admin (implement in Week 3)
            # send_admin_alert(f"User {user.id} high LLM usage")

        logger.debug(
            f"[LLMService] Tracked ${cost:.4f} for user {user.id} "
            f"(total: ${profile.llm_budget_spent:.2f})"
        )

    def generate_with_cache(
        self,
        cache_key: str,
        prompt: str,
        ttl: int = 3600,
        **kwargs
    ) -> Dict:
        """
        Generate with caching support.

        Args:
            cache_key: Cache key for this generation
            prompt: User prompt
            ttl: Cache TTL in seconds (default: 1 hour)
            **kwargs: Passed to generate()

        Returns:
            Same as generate(), plus 'from_cache': bool
        """
        # Try cache first
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"[LLMService] Cache HIT: {cache_key}")
            return {
                **cached,
                'from_cache': True
            }

        # Cache miss - generate
        logger.info(f"[LLMService] Cache MISS: {cache_key}")
        result = self.generate(prompt, **kwargs)

        # Cache result
        cache.set(cache_key, result, ttl)

        return {
            **result,
            'from_cache': False
        }


# Singleton instance
llm_service = LLMService()


# Convenience functions
def generate_text(prompt: str, **kwargs) -> str:
    """
    Generate text (convenience wrapper).

    Returns just the text, not full metadata.
    """
    result = llm_service.generate(prompt, **kwargs)
    return result['text']


def generate_with_tracking(user, prompt: str, operation: str = 'task_generation', **kwargs) -> Dict:
    """
    Generate with automatic cost tracking.

    Args:
        user: User object
        prompt: User prompt
        operation: Operation type
        **kwargs: Passed to generate()

    Returns:
        Full generation result with cost tracking
    """
    result = llm_service.generate(prompt, **kwargs)

    # Track cost
    llm_service.track_cost(user, result['cost'], operation)

    return result
