"""
Intelligent Task Splitter

Automatically breaks down large/blocked tasks into smaller sub-tasks.

Use cases:
1. User repeatedly skips a task → Split it into 3 micro-tasks
2. Task has high cognitive load (4-5) → Break down into steps
3. Task is overdue by > 2 weeks → Re-scope into achievable chunks
4. User explicitly requests AI breakdown via "Ask AI" in task

This makes overwhelming tasks actionable.
"""

import os
from anthropic import Anthropic
from typing import Dict, List
from datetime import datetime, timedelta
from django.utils import timezone


class TaskSplitter:
    """
    AI-powered task decomposition service.

    Analyzes a task and breaks it into 2-5 concrete sub-tasks.
    """

    def __init__(self):
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.model = "claude-3-5-sonnet-20241022"

    def should_split_task(self, task) -> tuple[bool, str]:
        """
        Determine if a task should be split.

        Returns:
            (should_split: bool, reason: str)
        """
        reasons = []

        # Check if overdue by > 14 days
        if task.is_overdue and task.days_overdue > 14:
            reasons.append(f"Overdue by {task.days_overdue} days - needs re-scoping")

        # Check if high cognitive load
        if task.cognitive_load and task.cognitive_load >= 4:
            reasons.append(f"High cognitive load ({task.cognitive_load}/5) - needs breakdown")

        # Check if long timebox (> 120 min)
        if task.timebox_minutes and task.timebox_minutes > 120:
            reasons.append(f"Long task ({task.timebox_minutes} min) - easier in chunks")

        # Check if repeatedly skipped (heuristic: status hasn't changed in 7+ days)
        if task.status == 'ready' and task.created_at < timezone.now() - timedelta(days=7):
            reasons.append("Task sitting idle for 7+ days - might be overwhelming")

        if reasons:
            return (True, " • ".join(reasons))
        else:
            return (False, "")

    def split_task_intelligent(self, task, user_context: str = "") -> List[Dict]:
        """
        Use AI to intelligently split a task into sub-tasks.

        Args:
            task: Todo object to split
            user_context: Additional user profile context

        Returns:
            [
                {
                    "title": "Step 1: Research IELTS requirements",
                    "description": "Find minimum scores for target universities",
                    "timebox_minutes": 30,
                    "task_type": "manual",
                    "priority": 3,
                    "sequence_order": 1,
                    "definition_of_done": [
                        {"text": "List of 5 universities with IELTS requirements", "weight": 100, "completed": false}
                    ]
                },
                ...
            ]
        """
        prompt = f"""You are an expert task breakdown specialist. Your job is to decompose a large, overwhelming task into 2-5 concrete, actionable sub-tasks.

ORIGINAL TASK:
Title: {task.title}
Description: {task.description}
Type: {task.task_type}
Timebox: {task.timebox_minutes} minutes
Cognitive Load: {task.cognitive_load}/5
Priority: {task.priority}
Deadline: {task.scheduled_date}

{f"USER CONTEXT:\\n{user_context}" if user_context else ""}

TASK BREAKDOWN REQUIREMENTS:
1. Create 2-5 sub-tasks (prefer 3)
2. Each sub-task should be:
   - Concrete and actionable (clear verb + deliverable)
   - 15-45 minutes max
   - Low cognitive load (1-3)
   - Sequential (step 1 → step 2 → step 3)
3. Sub-tasks should add up to complete the original task
4. Use realistic timeboxes (don't underestimate)
5. Each sub-task needs a clear Definition of Done

RESPONSE FORMAT (JSON array):
[
    {{
        "title": "Step 1: [Verb] [Target]",
        "description": "Detailed description of what to do",
        "timebox_minutes": 30,
        "task_type": "manual" | "copilot" | "auto",
        "priority": {task.priority},
        "sequence_order": 1,
        "cognitive_load": 2,
        "definition_of_done": [
            {{"text": "Concrete outcome", "weight": 100, "completed": false}}
        ]
    }},
    ...
]

IMPORTANT:
- Make sub-tasks feel achievable (not overwhelming)
- First sub-task should be a quick win (< 30 min)
- Use the same task_type as parent unless it makes sense to change
- Keep sequence_order sequential (1, 2, 3, ...)

Generate the sub-tasks now:"""

        try:
            response = self.anthropic.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            import json
            subtasks_json = response.content[0].text

            # Extract JSON if wrapped in markdown
            if "```json" in subtasks_json:
                subtasks_json = subtasks_json.split("```json")[1].split("```")[0].strip()
            elif "```" in subtasks_json:
                subtasks_json = subtasks_json.split("```")[1].split("```")[0].strip()

            subtasks = json.loads(subtasks_json)

            return subtasks

        except Exception as e:
            print(f"Error splitting task with AI: {e}")
            # Fallback: Simple split
            return self._fallback_split(task)

    def _fallback_split(self, task) -> List[Dict]:
        """
        Fallback splitting logic if AI fails.

        Simple heuristic: Split into Research → Plan → Execute
        """
        timebox_per_subtask = max(30, task.timebox_minutes // 3)

        return [
            {
                "title": f"Research: {task.title}",
                "description": f"Gather information needed for: {task.title}",
                "timebox_minutes": timebox_per_subtask,
                "task_type": "manual",
                "priority": task.priority,
                "sequence_order": 1,
                "cognitive_load": 2,
                "definition_of_done": [
                    {"text": "Research notes compiled", "weight": 100, "completed": False}
                ]
            },
            {
                "title": f"Plan: {task.title}",
                "description": f"Create action plan for: {task.title}",
                "timebox_minutes": timebox_per_subtask,
                "task_type": "manual",
                "priority": task.priority,
                "sequence_order": 2,
                "cognitive_load": 2,
                "definition_of_done": [
                    {"text": "Step-by-step plan created", "weight": 100, "completed": False}
                ]
            },
            {
                "title": f"Execute: {task.title}",
                "description": f"Complete: {task.title}",
                "timebox_minutes": timebox_per_subtask,
                "task_type": task.task_type,
                "priority": task.priority,
                "sequence_order": 3,
                "cognitive_load": 3,
                "definition_of_done": [
                    {"text": f"Completed {task.title}", "weight": 100, "completed": False}
                ]
            }
        ]

    def create_subtasks(self, task, subtasks_data: List[Dict]) -> List:
        """
        Create Todo objects for sub-tasks.

        Args:
            task: Parent task
            subtasks_data: List of sub-task dicts from split_task_intelligent()

        Returns:
            List of created Todo objects
        """
        from todos.models import Todo

        created_subtasks = []
        base_date = task.scheduled_date

        for i, subtask_data in enumerate(subtasks_data):
            # Stagger deadlines (each subtask gets +2 days from previous)
            scheduled_date = base_date + timedelta(days=i * 2)

            try:
                subtask = Todo.objects.create(
                    user=task.user,
                    goalspec=task.goalspec,
                    vision=task.vision,
                    milestone=task.milestone,
                    parent_task=task,  # Link to parent
                    title=subtask_data['title'],
                    description=subtask_data.get('description', ''),
                    task_type=subtask_data.get('task_type', 'manual'),
                    priority=subtask_data.get('priority', task.priority),
                    scheduled_date=scheduled_date,
                    timebox_minutes=subtask_data.get('timebox_minutes', 30),
                    cognitive_load=subtask_data.get('cognitive_load', 2),
                    energy_level=task.energy_level,
                    deliverable_type=task.deliverable_type,
                    definition_of_done=subtask_data.get('definition_of_done', []),
                    status='ready',
                    source='ai_generated',
                    notes=f"Auto-generated from parent task: {task.title}",
                    constraints={
                        'parent_task_id': task.id,
                        'sequence_order': subtask_data.get('sequence_order', i + 1),
                    }
                )
                created_subtasks.append(subtask)

            except Exception as e:
                print(f"Error creating subtask: {e}")

        return created_subtasks

    def split_and_create(self, task, user_context: str = "") -> Dict:
        """
        Full flow: Split task and create sub-tasks.

        Returns:
            {
                "parent_task_id": 123,
                "parent_title": "Write SOP",
                "subtasks_created": 3,
                "subtasks": [
                    {"id": 456, "title": "Step 1: Research SOP requirements", "scheduled_date": "2025-11-08"},
                    ...
                ],
                "message": "Task split into 3 actionable sub-tasks"
            }
        """
        # Get AI-powered split
        subtasks_data = self.split_task_intelligent(task, user_context)

        # Create Todo objects
        created_subtasks = self.create_subtasks(task, subtasks_data)

        # Mark parent task as "blocked" (waiting for subtasks to complete)
        task.status = 'blocked'
        task.notes += f"\n\n[Auto-split on {timezone.now().date()}] Task was overwhelming, split into {len(created_subtasks)} sub-tasks."
        task.save(update_fields=['status', 'notes'])

        return {
            "parent_task_id": task.id,
            "parent_title": task.title,
            "subtasks_created": len(created_subtasks),
            "subtasks": [
                {
                    "id": st.id,
                    "title": st.title,
                    "scheduled_date": str(st.scheduled_date),
                    "timebox_minutes": st.timebox_minutes,
                    "sequence_order": st.constraints.get('sequence_order', 0),
                }
                for st in created_subtasks
            ],
            "message": f"Task split into {len(created_subtasks)} actionable sub-tasks"
        }


# Singleton instance
task_splitter = TaskSplitter()
