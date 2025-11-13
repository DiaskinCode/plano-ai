# PathAI Backend API Documentation

Complete reference for all PathAI API endpoints.

**Base URL**: `http://192.168.1.6:8000/api` (development)

**Authentication**: Bearer token in `Authorization` header

---

## Table of Contents

1. [Authentication](#authentication)
2. [User & Profile](#user--profile)
3. [Tasks (Todos)](#tasks-todos)
4. [Adaptive Intelligence](#adaptive-intelligence)
5. [Performance & Analytics](#performance--analytics)
6. [Voice Interface](#voice-interface)
7. [Goals & Vision](#goals--vision)
8. [Chat & AI Assistant](#chat--ai-assistant)

---

## Authentication

### Register
```http
POST /api/auth/register/

Request:
{
  "username": "user123",
  "email": "user@example.com",
  "password": "securepass123",
  "password2": "securepass123"
}

Response: 201
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "user123"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJ...",
    "access": "eyJ0eXAiOiJ..."
  }
}
```

### Login
```http
POST /api/auth/login/

Request:
{
  "email": "user@example.com",
  "password": "securepass123"
}

Response: 200
{
  "user": {...},
  "tokens": {...}
}
```

### Refresh Token
```http
POST /api/auth/token/refresh/

Request:
{
  "refresh": "eyJ0eXAiOiJ..."
}

Response: 200
{
  "access": "eyJ0eXAiOiJ..."
}
```

---

## User & Profile

### Get Profile
```http
GET /api/auth/profile/
Authorization: Bearer {token}

Response: 200
{
  "id": 1,
  "name": "John Doe",
  "age": 22,
  "country_of_residence": "Kazakhstan",
  "gpa": 3.8,
  "test_scores": {"IELTS": 7.5},
  "current_role": "Software Engineer",
  "years_of_experience": 3,
  "fitness_level": "intermediate",
  "coach_character": "supportive",
  "energy_peak": "morning",
  "onboarding_completed": true
}
```

### Update Profile
```http
PATCH /api/auth/profile/
Authorization: Bearer {token}

Request:
{
  "name": "John Doe",
  "gpa": 3.8,
  "test_scores": {"IELTS": 7.5, "TOEFL": 105}
}

Response: 200
{...updated profile}
```

---

## Tasks (Todos)

### List Tasks
```http
GET /api/todos/
GET /api/todos/?filter=today
GET /api/todos/?filter=week
GET /api/todos/?filter=overdue
Authorization: Bearer {token}

Response: 200
[
  {
    "id": 123,
    "title": "Write SOP draft",
    "description": "...",
    "priority": 3,
    "status": "ready",
    "task_type": "manual",
    "scheduled_date": "2025-11-08",
    "scheduled_time": "09:00:00",
    "timebox_minutes": 60,
    "cognitive_load": 4,
    "energy_level": "high",
    "is_quick_win": false,
    "task_category": "regular",
    "definition_of_done": [
      {"text": "First draft completed", "weight": 100, "completed": false}
    ],
    "progress_percentage": 0,
    "is_overdue": false,
    "days_overdue": 0
  },
  ...
]
```

### Create Task
```http
POST /api/todos/
Authorization: Bearer {token}

Request:
{
  "title": "Review Cambridge requirements",
  "description": "Check all application requirements",
  "priority": 3,
  "scheduled_date": "2025-11-10",
  "timebox_minutes": 30,
  "task_type": "manual"
}

Response: 201
{...created task}
```

### Update Task
```http
PATCH /api/todos/{id}/
Authorization: Bearer {token}

Request:
{
  "status": "done",
  "progress_percentage": 100
}

Response: 200
{...updated task}
```

### Split Task (AI-powered)
```http
POST /api/todos/{id}/split/
Authorization: Bearer {token}

Response: 200
{
  "parent_task_id": 123,
  "parent_title": "Write SOP",
  "subtasks_created": 3,
  "subtasks": [
    {
      "id": 456,
      "title": "Step 1: Research SOP requirements",
      "scheduled_date": "2025-11-08",
      "timebox_minutes": 30,
      "sequence_order": 1
    },
    ...
  ],
  "message": "Task split into 3 actionable sub-tasks"
}
```

### Get Split Candidates
```http
GET /api/todos/split/candidates/
Authorization: Bearer {token}

Response: 200
{
  "candidates": [
    {
      "task_id": 123,
      "title": "Write SOP",
      "reason": "Overdue by 21 days - needs re-scoping • High cognitive load",
      "days_overdue": 21,
      "timebox_minutes": 180,
      "cognitive_load": 4
    }
  ],
  "count": 3
}
```

---

## Adaptive Intelligence

### Performance Insights
```http
GET /api/auth/performance/
POST /api/auth/performance/  // Trigger fresh analysis
Authorization: Bearer {token}

Response: 200
{
  "completion_rate": 0.65,
  "risk_level": "medium",
  "optimal_schedule": {
    "high_energy_hours": [9, 10, 11],
    "low_energy_hours": [14, 15, 20, 21],
    "best_day": "Monday",
    "worst_day": "Friday",
    "completion_by_hour": {9: 0.85, 10: 0.90, ...},
    "completion_by_day": {"Monday": 0.75, ...}
  },
  "task_type_performance": {
    "auto": {"completed": 5, "total": 8, "rate": 0.625},
    "copilot": {"completed": 3, "total": 10, "rate": 0.3},
    "manual": {"completed": 12, "total": 15, "rate": 0.8}
  },
  "energy_patterns": {
    "high": {"completed": 8, "total": 12, "rate": 0.67},
    "medium": {"completed": 15, "total": 18, "rate": 0.83},
    "low": {"completed": 10, "total": 10, "rate": 1.0}
  },
  "blockers": [
    {
      "task_id": 123,
      "title": "Write SOP",
      "task_type": "manual",
      "days_overdue": 21,
      "status": "ready",
      "pattern": "High cognitive load task • Requires high energy"
    }
  ],
  "strengths": [
    "Excellent overall completion rate (80%)",
    "High success rate with manual tasks (80%)",
    "Peak productivity during 9:00, 10:00, 11:00"
  ],
  "warnings": [
    "Struggling with copilot tasks (30% completion)",
    "Fridays are consistently low-productivity (40%)"
  ],
  "recommended_actions": [
    "Enable proactive AI assistance for co-pilot tasks",
    "Schedule high-priority tasks during peak hours: 9:00, 10:00"
  ],
  "last_analysis": "2025-11-06T10:30:00Z",
  "tasks_analyzed": 45
}
```

### Check for Intervention
```http
GET /api/auth/coach/check-intervention/
Authorization: Bearer {token}

Response: 200
{
  "intervention_needed": true,
  "intervention": {
    "type": "planb_switch",
    "severity": "critical",
    "title": "⚠️ Let's reset your plan",
    "message": "I've noticed your completion rate is at 45%, which suggests the current plan might be too ambitious. Let's adjust to set you up for success.",
    "actions": [
      {
        "action": "extend_deadline",
        "task_id": 123,
        "task_title": "Write SOP",
        "from_date": "2025-11-08",
        "to_date": "2025-11-22",
        "reason": "Give you 2 weeks breathing room"
      },
      ...
    ],
    "alternative_paths": [
      {
        "title": "Extend Cambridge application timeline by 6 months",
        "description": "Instead of rushing, take time to prepare properly (better IELTS, stronger SOP)",
        "confidence": "high",
        "goalspec_id": 5
      }
    ],
    "recommended_next_step": "Accept the timeline extensions and focus on quick wins this week"
  }
}

OR

{
  "intervention_needed": false,
  "message": "You're on track! No intervention needed."
}
```

### Apply Intervention
```http
POST /api/auth/coach/apply-intervention/
Authorization: Bearer {token}

Request:
{
  "intervention": {
    "type": "planb_switch",
    "actions": [...]
  }
}

Response: 200
{
  "success": true,
  "tasks_updated": 5,
  "deadlines_extended": 3,
  "tasks_paused": 2,
  "message": "Successfully applied changes"
}
```

### Dismiss Intervention
```http
POST /api/auth/coach/dismiss-intervention/
Authorization: Bearer {token}

Request:
{
  "intervention_type": "planb_switch",
  "reason": "I want to continue my current plan"
}

Response: 200
{
  "success": true,
  "message": "Intervention dismissed. We'll check again in a few days."
}
```

---

## Performance & Analytics

### Context-Aware Daily Pulse
```http
POST /api/analytics/daily-pulse/contextual/
Authorization: Bearer {token}

Response: 200
{
  "greeting_message": "☀️ Good morning! Your 5-day streak is impressive.",
  "top_priorities": [
    {
      "task_id": 123,
      "title": "Write SOP draft",
      "reason": "High impact for your Cambridge application - deadline in 3 days",
      "timebox_minutes": 60,
      "priority": 3
    },
    ...
  ],
  "workload_assessment": {
    "percentage": 85,
    "status": "manageable",
    "message": "You have 4 hours of work scheduled - achievable!",
    "total_minutes": 240
  },
  "warnings": [
    "⚠️ Task overdue 7 days: Connect with alumni. Let's re-scope?"
  ],
  "smart_suggestions": [
    "💡 Your peak productivity is 9-11am. Schedule SOP draft then.",
    "🎯 You excel at quick wins (90% completion) - knock out 2 this morning."
  ],
  "coaching_note": "Based on last week's patterns, you're strongest in the morning with quick wins. Let's use that to build momentum today.",
  "full_message": "Comprehensive daily briefing...",
  "generated_at": "2025-11-06T08:00:00Z"
}
```

### Streak
```http
GET /api/analytics/streak/
Authorization: Bearer {token}

Response: 200
{
  "current_streak": 5,
  "longest_streak": 12,
  "last_activity_date": "2025-11-06"
}
```

---

## Voice Interface

### Process Voice Command
```http
POST /api/ai/voice/process/
Authorization: Bearer {token}

Request:
{
  "transcript": "Add task review Cambridge application by Friday",
  "timestamp": "2025-11-06T10:30:00Z"
}

Response: 200
{
  "intent": "create_task",
  "action_taken": {
    "task_id": 123,
    "title": "Review Cambridge application",
    "scheduled_date": "2025-11-08",
    "priority": 2
  },
  "response_text": "Got it! I've added 'Review Cambridge application' for Friday.",
  "success": true
}
```

### Voice Query
```http
POST /api/ai/voice/query/
Authorization: Bearer {token}

Request:
{
  "query": "Coach, am I on track?",
  "context": "performance"
}

Response: 200
{
  "answer": "You're doing great! 65% completion rate this month. Your peak productivity is 9-11am. Keep scheduling critical tasks in the morning!",
  "data": {
    "completion_rate": 0.65,
    "peak_hours": [9, 10, 11]
  },
  "intent": "coach_query"
}
```

### Voice Capabilities
```http
GET /api/ai/voice/capabilities/
Authorization: Bearer {token}

Response: 200
{
  "capabilities": [
    {
      "intent": "create_task",
      "examples": [
        "Add task review Cambridge application by Friday",
        "Create task call mentor tomorrow"
      ],
      "description": "Create a new task with optional deadline and priority"
    },
    ...
  ]
}
```

---

## Goals & Vision

### List GoalSpecs
```http
GET /api/auth/goalspecs/
Authorization: Bearer {token}

Response: 200
[
  {
    "id": 5,
    "category": "study",
    "title": "Get into Cambridge for MSc CS",
    "specifications": {
      "degree": "Masters",
      "field": "Computer Science",
      "country": "UK",
      "target_universities": ["Cambridge", "Imperial", "UCL"]
    },
    "status": "active",
    "priority_weight": 1.0,
    "created_at": "2025-11-01T10:00:00Z"
  },
  ...
]
```

### Create GoalSpec
```http
POST /api/auth/goalspecs/
Authorization: Bearer {token}

Request:
{
  "category": "career",
  "title": "Switch to ML Engineer role",
  "specifications": {
    "targetRole": "ML Engineer",
    "targetCompanies": ["Google", "DeepMind"],
    "targetSalary": "$150k+"
  },
  "goal_type": "career",
  "status": "active"
}

Response: 201
{...created goalspec}
```

### Validate Goal Feasibility
```http
POST /api/auth/onboarding/validate-feasibility/
Authorization: Bearer {token}

Request:
{
  "goalspec_id": 5
}

Response: 200
{
  "feasible": true,
  "confidence": "medium",
  "warnings": [
    "Your IELTS score (6.5) is below Cambridge's typical requirement (7.5)"
  ],
  "recommendations": [
    "Retake IELTS (target: 7.5+)",
    "Consider UCL or Edinburgh as backups (require 7.0)"
  ],
  "target_universities": [
    {
      "name": "UCL",
      "tier": "excellent",
      "acceptance_probability": 0.45
    },
    {
      "name": "Warwick",
      "tier": "strong",
      "acceptance_probability": 0.65
    }
  ],
  "estimated_success_rate": 0.55
}
```

---

## Chat & AI Assistant

### Task-Specific Assistant
```http
POST /api/ai/task-assistant/
Authorization: Bearer {token}

Request:
{
  "task_id": 123,
  "question": "How should I structure my SOP?",
  "mode": "clarify"
}

Response: 200
{
  "response": "For Cambridge MSc CS, structure your SOP as: 1. Academic background (focus on relevant projects)...",
  "links": ["https://www.cam.ac.uk/..."],
  "contacts": [],
  "steps": [
    "1. Draft academic background section (200 words)",
    "2. List 3 research interests aligned with Cambridge",
    ...
  ]
}
```

---

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "error": "Field is required",
  "detail": "..."
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to process request: ...",
  "detail": "..."
}
```

---

## Rate Limits

| Tier | Requests/minute | Requests/day |
|------|-----------------|--------------|
| Free | 30 | 500 |
| Pro | 120 | 5,000 |
| Teams | 300 | 20,000 |

---

## Webhooks (Future)

Coming soon: Webhook support for:
- Task completion events
- Intervention triggers
- Milestone achievements
- Daily pulse generation

---

## SDK Support

Official SDKs:
- **JavaScript/TypeScript**: `@pathai/js-sdk` (coming soon)
- **Python**: `pathai-python` (coming soon)
- **React Native**: Built-in with Expo app

---

**Version**: 2.0 (Adaptive Intelligence Release)

**Last Updated**: November 6, 2025
