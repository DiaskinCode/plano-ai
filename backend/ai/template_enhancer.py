"""
LLM Template Enhancer (Week 1 Day 3-4: Hybrid Task Generation Enhancement)

Enhancement layer for template-generated tasks using Claude Sonnet.

KEY PRINCIPLES:
1. Templates guarantee zero hallucinations (base content is pre-written)
2. LLM only polishes/refines the already-rendered template
3. No new information added - only style/clarity improvements
4. All factual content comes from templates + profile data

Use cases:
- Add natural language flow to template output
- Adjust tone based on user preferences
- Make instructions more conversational
- Add motivational context (without changing facts)

NOT allowed:
- Adding new facts (dates, prices, specific resources)
- Changing deliverables or DoD items
- Modifying timebox estimates
- Inventing new steps or requirements

Week 1 Day 3-4 Changes:
- Uses Claude Sonnet (not Haiku) for better quality
- Cost tracking via llm_service
- Always ON (not optional)
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass
from decimal import Decimal

# Import llm_service instead of anthropic client directly
from .llm_service import llm_service


@dataclass
class EnhancementConfig:
    """Configuration for LLM enhancement"""
    enhance_title: bool = True
    enhance_description: bool = True
    enhance_dod: bool = False  # Risky - keep DoD items factual
    tone: str = "professional"  # professional, friendly, motivational
    max_tokens: int = 500


class TemplateEnhancer:
    """
    LLM-based enhancement of template-generated tasks using Claude Sonnet.

    Strategy: Template provides facts, LLM provides polish.

    Week 1 Day 3-4: Now uses llm_service with cost tracking.
    """

    def __init__(self):
        """Initialize enhancer (uses llm_service singleton)"""
        # llm_service is a singleton, no initialization needed
        pass

    def enhance_task(
        self,
        task: Dict[str, Any],
        user_profile: Any,
        user: Any = None,  # User object for cost tracking
        config: Optional[EnhancementConfig] = None
    ) -> Dict[str, Any]:
        """
        Enhance a template-generated task with LLM polish.

        Args:
            task: Template-generated task dict
            user_profile: UserProfile for personalization hints
            user: User object for cost tracking (optional)
            config: Enhancement configuration

        Returns:
            Enhanced task dict with cost metadata
        """
        config = config or EnhancementConfig()

        # Create enhanced copy
        enhanced_task = task.copy()
        total_cost = Decimal('0')

        # Enhance title
        if config.enhance_title and 'title' in task:
            enhanced_title, title_cost = self._enhance_title(
                original_title=task['title'],
                tone=config.tone
            )
            if enhanced_title:
                enhanced_task['title'] = enhanced_title
                total_cost += title_cost

        # Enhance description
        if config.enhance_description and 'description' in task:
            enhanced_description, desc_cost = self._enhance_description(
                original_description=task['description'],
                task_type=task.get('task_type', 'copilot'),
                tone=config.tone,
                user_profile=user_profile
            )
            if enhanced_description:
                enhanced_task['description'] = enhanced_description
                total_cost += desc_cost

        # Mark as enhanced
        enhanced_task['enhanced'] = True
        enhanced_task['source'] = 'template_agent_enhanced'
        enhanced_task['enhancement_cost'] = float(total_cost)

        # Track cost if user provided
        if user and total_cost > 0:
            llm_service.track_cost(user, total_cost, operation='task_enhancement')

        return enhanced_task

    def _enhance_title(self, original_title: str, tone: str) -> tuple[Optional[str], Decimal]:
        """
        Polish task title for better readability using Claude Sonnet.

        Rules:
        - Keep all factual content (numbers, names, deadlines)
        - Improve clarity and flow
        - Match desired tone
        - Max 100 characters

        Returns:
            (enhanced_title, cost) or (None, 0) if failed
        """
        try:
            prompt = f"""You are enhancing a task title for a goal-tracking app.

Original title (from template):
{original_title}

Your job:
1. Keep ALL factual information (numbers, names, deadlines, specifics)
2. Improve readability and natural language flow
3. Tone: {tone}
4. Max 100 characters
5. DO NOT add new facts or change meaning

Return ONLY the enhanced title, nothing else."""

            # Use llm_service with Claude Sonnet
            result = llm_service.generate(
                prompt=prompt,
                max_tokens=150,
                temperature=0.3  # Lower temp for factual enhancement
            )

            enhanced = result['text'].strip()
            cost = result['cost']

            # Validation: Enhanced version shouldn't be too different
            if len(enhanced) > 100 or len(enhanced) < len(original_title) // 2:
                print(f"[TemplateEnhancer] Title enhancement rejected (length check)")
                return None, Decimal('0')

            return enhanced, cost

        except Exception as e:
            print(f"[TemplateEnhancer] Title enhancement failed: {e}")
            return None, Decimal('0')

    def _enhance_description(
        self,
        original_description: str,
        task_type: str,
        tone: str,
        user_profile: Any
    ) -> tuple[Optional[str], Decimal]:
        """
        Polish task description for better engagement using Claude Sonnet.

        Rules:
        - Keep ALL factual content from template
        - Add natural language transitions
        - Match user's preferred tone
        - Optionally add motivational context (without inventing facts)

        Returns:
            (enhanced_description, cost) or (None, 0) if failed
        """
        try:
            # Extract user context for tone matching
            user_name = getattr(user_profile, 'name', 'there')
            energy_peak = getattr(user_profile, 'energy_peak', 'morning')

            prompt = f"""You are enhancing a task description for a goal-tracking app.

Original description (from template):
{original_description}

User context:
- Name: {user_name}
- Energy peak: {energy_peak}
- Task type: {task_type}

Your job:
1. Keep ALL factual information from the original (steps, resources, deliverables)
2. Improve natural language flow and transitions
3. Tone: {tone}
4. Add brief motivational context if appropriate (but NO new facts)
5. Keep structure (if template has steps, keep them)

Return ONLY the enhanced description, nothing else."""

            # Use llm_service with Claude Sonnet
            result = llm_service.generate(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3  # Lower temp for factual enhancement
            )

            enhanced = result['text'].strip()
            cost = result['cost']

            # Validation: Enhanced shouldn't be way longer
            if len(enhanced) > len(original_description) * 1.5:
                print(f"[TemplateEnhancer] Description enhancement rejected (too verbose)")
                return None, Decimal('0')

            return enhanced, cost

        except Exception as e:
            print(f"[TemplateEnhancer] Description enhancement failed: {e}")
            return None, Decimal('0')

    def enhance_batch(
        self,
        tasks: list[Dict[str, Any]],
        user_profile: Any,
        user: Any = None,
        config: Optional[EnhancementConfig] = None
    ) -> list[Dict[str, Any]]:
        """
        Enhance multiple tasks in batch.

        Useful for enhancing a week's worth of tasks at once.
        """
        enhanced_tasks = []

        for task in tasks:
            try:
                enhanced = self.enhance_task(task, user_profile, user, config)
                enhanced_tasks.append(enhanced)
            except Exception as e:
                print(f"[TemplateEnhancer] Failed to enhance task, using original: {e}")
                enhanced_tasks.append(task)

        return enhanced_tasks


# Singleton instance
template_enhancer = TemplateEnhancer()


def enhance_if_enabled(
    task: Dict[str, Any],
    user_profile: Any,
    user: Any = None,
    config: Optional[EnhancementConfig] = None
) -> Dict[str, Any]:
    """
    Convenience function: enhance task with Claude Sonnet.
    Week 1 Day 3-4: Always enabled (uses llm_service).
    """
    return template_enhancer.enhance_task(task, user_profile, user, config)
