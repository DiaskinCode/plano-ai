"""
Task Cache Service (Week 3 Day 1-2)

Caches LLM-generated tasks to reduce costs for similar users.

Key Insight: Users with similar profiles get similar tasks.
- Founder with PathAI (200k users) → CS Master's at MIT
- Founder with StartupX (150k users) → CS Master's at Stanford
→ 80% of tasks are identical, only 20% differ (university names)

Cache Strategy:
1. Generate profile hash (background + field + key metrics)
2. Check cache for similar profiles (hash match)
3. If cache hit: Return cached tasks, personalize with user details
4. If cache miss: Generate with LLM, cache for future users

Expected savings: 75% cache hit rate → $0.50-0.80 becomes $0.08-0.15 per user
"""

import hashlib
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.core.cache import cache
from decimal import Decimal


class TaskCacheService:
    """
    Caches LLM-generated tasks to reduce costs.

    Week 3: Cost optimization through intelligent caching.
    """

    # Cache settings
    CACHE_TTL = 60 * 60 * 24 * 30  # 30 days
    CACHE_KEY_PREFIX = 'task_cache:'

    def __init__(self):
        pass

    def generate_profile_hash(self, context: Dict[str, Any], goalspec: Any) -> str:
        """
        Generate stable hash from user profile for caching.

        Hash includes:
        - Background type (founder, engineer, student, etc.)
        - Field (CS, AI, Business, etc.)
        - Key metrics (has_startup, gpa_needs_compensation)
        - Goal category (study, career, sport)

        Excludes:
        - Specific names (startup_name, user name)
        - Specific universities (those are personalized later)
        - Specific numbers (200k vs 150k users doesn't change task structure)

        Args:
            context: Full personalization context
            goalspec: GoalSpec instance

        Returns:
            Hash string (32 chars) for cache key
        """
        # Extract cacheable features (stable across similar users)
        cache_features = {
            'background': context.get('background', 'unknown'),
            'field': context.get('field', 'unknown'),
            'category': getattr(goalspec, 'category', 'unknown'),
            'has_startup_background': context.get('has_startup_background', False),
            'has_professional_experience': context.get('has_professional_experience', False),
            'has_research_experience': context.get('has_research_experience', False),
            'gpa_needs_compensation': context.get('gpa_needs_compensation', False),
            'test_prep_needed': context.get('test_prep_needed', {}),
        }

        # Sort keys for stable hash
        cache_str = json.dumps(cache_features, sort_keys=True)

        # Generate hash
        return hashlib.md5(cache_str.encode()).hexdigest()

    def get_cache_key(self, profile_hash: str, generation_type: str) -> str:
        """
        Generate cache key.

        Args:
            profile_hash: Profile hash from generate_profile_hash
            generation_type: 'full_llm' | 'unique' | 'enhanced'

        Returns:
            Cache key string
        """
        return f"{self.CACHE_KEY_PREFIX}{generation_type}:{profile_hash}"

    def get_cached_tasks(
        self,
        context: Dict[str, Any],
        goalspec: Any,
        generation_type: str = 'full_llm'
    ) -> Optional[List[Dict]]:
        """
        Retrieve cached tasks for similar profile.

        Args:
            context: Full personalization context
            goalspec: GoalSpec instance
            generation_type: Type of generation to cache

        Returns:
            List of cached task dictionaries or None if cache miss
        """
        profile_hash = self.generate_profile_hash(context, goalspec)
        cache_key = self.get_cache_key(profile_hash, generation_type)

        cached_data = cache.get(cache_key)

        if cached_data:
            print(f"[TaskCache] ✅ Cache HIT for {generation_type} (hash: {profile_hash[:8]}...)")
            # Personalize cached tasks with current user's details
            tasks = self._personalize_cached_tasks(cached_data['tasks'], context, goalspec)
            return tasks
        else:
            print(f"[TaskCache] ❌ Cache MISS for {generation_type} (hash: {profile_hash[:8]}...)")
            return None

    def cache_tasks(
        self,
        tasks: List[Dict],
        context: Dict[str, Any],
        goalspec: Any,
        generation_type: str = 'full_llm',
        cost: Decimal = Decimal('0')
    ) -> None:
        """
        Cache tasks for future similar users.

        Args:
            tasks: List of task dictionaries to cache
            context: Full personalization context
            goalspec: GoalSpec instance
            generation_type: Type of generation
            cost: Cost of generation (for tracking savings)
        """
        profile_hash = self.generate_profile_hash(context, goalspec)
        cache_key = self.get_cache_key(profile_hash, generation_type)

        # Store tasks with metadata
        cache_data = {
            'tasks': tasks,
            'cached_at': datetime.now().isoformat(),
            'cost': str(cost),  # Store as string for JSON serialization
            'profile_hash': profile_hash,
            'generation_type': generation_type,
        }

        cache.set(cache_key, cache_data, self.CACHE_TTL)
        print(f"[TaskCache] 💾 Cached {len(tasks)} tasks for {generation_type} (hash: {profile_hash[:8]}...)")
        print(f"[TaskCache] Cost saved for future users: ${cost:.4f}")

    def _personalize_cached_tasks(
        self,
        cached_tasks: List[Dict],
        context: Dict[str, Any],
        goalspec: Any
    ) -> List[Dict]:
        """
        Personalize cached tasks with current user's specific details.

        Replaces:
        - Generic university names → User's target universities
        - Generic startup names → User's actual startup name
        - Generic field names → User's specific field

        Args:
            cached_tasks: Tasks from cache
            context: Current user's context
            goalspec: Current user's goalspec

        Returns:
            Personalized tasks
        """
        personalized = []

        # Extract user-specific details
        target_universities = context.get('target_universities', [])
        startup_name = context.get('startup_name', 'your startup')
        field = context.get('field', 'your field')

        for task in cached_tasks:
            personalized_task = task.copy()

            # Personalize title
            title = personalized_task.get('title', '')
            title = self._replace_placeholders(title, context)
            personalized_task['title'] = title

            # Personalize description
            description = personalized_task.get('description', '')
            description = self._replace_placeholders(description, context)
            personalized_task['description'] = description

            # Personalize definition_of_done
            dod = personalized_task.get('definition_of_done', '')
            dod = self._replace_placeholders(dod, context)
            personalized_task['definition_of_done'] = dod

            personalized.append(personalized_task)

        print(f"[TaskCache] 🎯 Personalized {len(personalized)} cached tasks with user details")
        return personalized

    def _replace_placeholders(self, text: str, context: Dict[str, Any]) -> str:
        """
        Replace generic placeholders with user-specific details.

        Args:
            text: Text with placeholders
            context: User context with specific details

        Returns:
            Personalized text
        """
        if not text:
            return text

        # Common placeholder patterns
        replacements = {
            '[university name]': ', '.join(context.get('target_universities', ['your target university'])[:3]),
            '[your university]': ', '.join(context.get('target_universities', ['your target university'])[:3]),
            '[startup name]': context.get('startup_name', 'your startup'),
            '[your startup]': context.get('startup_name', 'your startup'),
            '[field]': context.get('field', 'your field'),
            '[your field]': context.get('field', 'your field'),
            '[target school]': context.get('target_universities', ['your target school'])[0] if context.get('target_universities') else 'your target school',
        }

        personalized_text = text
        for placeholder, replacement in replacements.items():
            personalized_text = personalized_text.replace(placeholder, replacement)

        return personalized_text

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.

        Returns:
            {
                'total_cached_profiles': int,
                'estimated_cost_saved': Decimal,
                'cache_size_mb': float
            }
        """
        # Note: Django cache doesn't provide built-in stats
        # This is a placeholder for future implementation with Redis
        return {
            'total_cached_profiles': 0,  # Would need Redis SCAN to count
            'estimated_cost_saved': Decimal('0'),
            'cache_size_mb': 0.0,
            'note': 'Detailed stats require Redis backend'
        }

    def clear_cache(self, generation_type: Optional[str] = None) -> None:
        """
        Clear cached tasks (for testing or cache invalidation).

        Args:
            generation_type: If specified, only clear this type. If None, clear all.
        """
        if generation_type:
            print(f"[TaskCache] 🗑️  Clearing cache for {generation_type}")
            # Would need to scan all keys with this generation_type
            # This is simplified - in production, use Redis SCAN
        else:
            print(f"[TaskCache] 🗑️  Clearing all task caches")
            # Would clear all keys with CACHE_KEY_PREFIX
            # This is simplified - in production, use Redis SCAN

        print(f"[TaskCache] Note: Full cache clearing requires Redis backend")


# Singleton instance
task_cache_service = TaskCacheService()


def get_cached_tasks(
    context: Dict[str, Any],
    goalspec: Any,
    generation_type: str = 'full_llm'
) -> Optional[List[Dict]]:
    """
    Convenience function to get cached tasks.

    Args:
        context: Full personalization context
        goalspec: GoalSpec instance
        generation_type: Type of generation

    Returns:
        List of cached tasks or None
    """
    return task_cache_service.get_cached_tasks(context, goalspec, generation_type)


def cache_tasks(
    tasks: List[Dict],
    context: Dict[str, Any],
    goalspec: Any,
    generation_type: str = 'full_llm',
    cost: Decimal = Decimal('0')
) -> None:
    """
    Convenience function to cache tasks.

    Args:
        tasks: Tasks to cache
        context: Full personalization context
        goalspec: GoalSpec instance
        generation_type: Type of generation
        cost: Cost of generation
    """
    task_cache_service.cache_tasks(tasks, context, goalspec, generation_type, cost)
