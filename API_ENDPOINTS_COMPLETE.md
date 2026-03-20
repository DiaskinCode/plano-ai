# API Endpoints - Complete Reference

All new API endpoints for the Atomic Task System have been implemented and wired up.

---

## 🎯 GoalSpec API

**Base URL**: `/api/auth/goalspecs/`

### List Goals
```http
GET /api/auth/goalspecs/
Authorization: Bearer <token>
```

**Response**:
```json
[
  {
    "id": 1,
    "goal_type": "study",
    "title": "Get into top CS MS program",
    "constraints": {
      "country": "USA",
      "degree": "MS in Computer Science",
      "budget": 50000,
      "deadline": "2025-12-31"
    },
    "preferences": {
      "regions": ["West Coast", "East Coast"],
      "focus": "AI/ML"
    },
    "priority_weight": 0.8,
    "daily_time_budget_minutes": 120,
    "cadence_rules": {
      "sequential": ["shortlist", "deadlines", "essays", "lors", "submissions"]
    },
    "is_active": true,
    "completed": false
  }
]
```

### Create Goal
```http
POST /api/auth/goalspecs/
Authorization: Bearer <token>
Content-Type: application/json

{
  "goal_type": "study",
  "title": "Get into top CS MS program",
  "constraints": {
    "country": "USA",
    "degree": "MS in Computer Science"
  },
  "priority_weight": 0.8,
  "daily_time_budget_minutes": 120,
  "cadence_rules": {}
}
```

**Validation**:
- `priority_weight`: Must be between 0.1 and 1.0
- `daily_time_budget_minutes`: Must be positive
- **Study goals**: Require `country` and `degree` in constraints
- **Career goals**: Require `target_role` in constraints
- **Sport goals**: Require `sport_type` in constraints

### Retrieve Goal
```http
GET /api/auth/goalspecs/{id}/
Authorization: Bearer <token>
```

### Update Goal
```http
PATCH /api/auth/goalspecs/{id}/
Authorization: Bearer <token>
Content-Type: application/json

{
  "priority_weight": 0.9,
  "daily_time_budget_minutes": 180
}
```

### Delete Goal
```http
DELETE /api/auth/goalspecs/{id}/
Authorization: Bearer <token>
```

### Custom Actions

#### Complete Goal
```http
POST /api/auth/goalspecs/{id}/complete/
Authorization: Bearer <token>
```

Marks goal as completed and sets `is_active` to `false`.

#### Activate Goal
```http
POST /api/auth/goalspecs/{id}/activate/
Authorization: Bearer <token>
```

#### Deactivate Goal
```http
POST /api/auth/goalspecs/{id}/deactivate/
Authorization: Bearer <token>
```

#### Get Active Goals
```http
GET /api/auth/goalspecs/active/
Authorization: Bearer <token>
```

Returns only active, non-completed goals.

#### Validate Constraints
```http
GET /api/auth/goalspecs/{id}/validate_constraints/
Authorization: Bearer <token>
```

**Response**:
```json
{
  "valid": true,
  "message": "All constraints are valid"
}
```

---

## 📅 Daily Planner API

**Base URL**: `/api/todos/daily-planner/`

### Generate Daily Plan
```http
POST /api/todos/daily-planner/generate/
Authorization: Bearer <token>
Content-Type: application/json

{
  "target_date": "2025-10-15"  // Optional, defaults to today
}
```

**Response**:
```json
{
  "message": "Generated 8 tasks for 2025-10-15",
  "target_date": "2025-10-15",
  "tasks_created": 8,
  "tasks": [
    {
      "id": 123,
      "title": "Research MS programs in USA",
      "task_type": "copilot",
      "timebox_minutes": 45,
      "deliverable_type": "shortlist",
      "definition_of_done": [
        {"text": "Find 10 programs", "weight": 50, "completed": false},
        {"text": "Compare rankings", "weight": 30, "completed": false},
        {"text": "Check deadlines", "weight": 20, "completed": false}
      ],
      "progress_percentage": 0
    }
  ]
}
```

### Preview Daily Plan
```http
GET /api/todos/daily-planner/preview/?target_date=2025-10-15
Authorization: Bearer <token>
```

Generates plan without creating tasks (for preview).

**Response**:
```json
{
  "target_date": "2025-10-15",
  "total_tasks": 8,
  "total_minutes": 480,
  "plan": [...]
}
```

### Get Time Allocation
```http
GET /api/todos/daily-planner/allocation/
Authorization: Bearer <token>
```

Shows how time is allocated across active goals.

**Response**:
```json
{
  "total_daily_minutes": 480,
  "allocations": [
    {
      "goal_id": 1,
      "goal_title": "Get into top CS MS program",
      "goal_type": "study",
      "priority_weight": 0.8,
      "allocated_minutes": 240,
      "percentage": 50.0
    },
    {
      "goal_id": 2,
      "goal_title": "Land SWE role at FAANG",
      "goal_type": "career",
      "priority_weight": 0.6,
      "allocated_minutes": 180,
      "percentage": 37.5
    }
  ]
}
```

---

## 📊 Weekly Review API

**Base URL**: `/api/todos/weekly-review/`

### Get Weekly Review
```http
GET /api/todos/weekly-review/?week_start=2025-10-13
Authorization: Bearer <token>
```

If `week_start` is not provided, uses last Monday.

**Response**:
```json
{
  "week_start": "2025-10-13",
  "week_end": "2025-10-19",
  "stats": {
    "total_tasks": 42,
    "completed": 35,
    "completion_rate": 83,
    "total_hours": 24.5,
    "avg_progress": 78
  },
  "wins": [
    {
      "type": "task_completed",
      "title": "Completed: Submit Stanford application",
      "message": "Successfully submitted application",
      "progress": 100
    },
    {
      "type": "high_completion_rate",
      "title": "Great week! 83% completion rate",
      "message": "You completed 35 out of 42 tasks"
    }
  ],
  "blockers": [
    {
      "type": "blocked_task",
      "title": "Task blocked: Request LOR from Prof. Smith",
      "task_id": 456,
      "reason": "Waiting on previous task completion"
    }
  ],
  "streaks": {
    "current_streak": 7,
    "longest_week_streak": 7,
    "daily_completion": [
      {"date": "2025-10-13", "completed": 6, "total": 7, "has_activity": true},
      {"date": "2025-10-14", "completed": 5, "total": 6, "has_activity": true},
      {"date": "2025-10-15", "completed": 5, "total": 5, "has_activity": true},
      {"date": "2025-10-16", "completed": 6, "total": 6, "has_activity": true},
      {"date": "2025-10-17", "completed": 4, "total": 5, "has_activity": true},
      {"date": "2025-10-18", "completed": 5, "total": 7, "has_activity": true},
      {"date": "2025-10-19", "completed": 4, "total": 6, "has_activity": true}
    ]
  },
  "next_week_plan": {
    "total_tasks": 38,
    "total_hours": 22.0,
    "focus_areas": [
      {"goal": "Get into top CS MS program", "task_count": 15},
      {"goal": "Land SWE role at FAANG", "task_count": 12},
      {"goal": "Run 5K in under 25 minutes", "task_count": 11}
    ]
  }
}
```

### Generate Weekly Review
```http
POST /api/todos/weekly-review/generate/
Authorization: Bearer <token>
Content-Type: application/json

{
  "week_start": "2025-10-13"  // Optional
}
```

Same response as GET, but explicitly generates fresh data.

### Get Formatted Review
```http
GET /api/todos/weekly-review/formatted/?week_start=2025-10-13
Authorization: Bearer <token>
```

**Response**:
```json
{
  "week_start": "2025-10-13",
  "markdown": "# Weekly Review\n\n## Stats\n- Completed: 35/42 (83%)\n..."
}
```

### Get Stats Only
```http
GET /api/todos/weekly-review/stats-only/?week_start=2025-10-13
Authorization: Bearer <token>
```

Returns just the statistics without wins/blockers/streaks.

---

## 📎 Task Evidence API

**Base URL**: `/api/todos/evidence/`

### List Evidence
```http
GET /api/todos/evidence/
Authorization: Bearer <token>
```

Returns all evidence for user's tasks.

### Get Evidence by Task
```http
GET /api/todos/evidence/by-task/?task_id=123
Authorization: Bearer <token>
```

**Response**:
```json
{
  "task_id": 123,
  "task_title": "Research MS programs in USA",
  "evidence_count": 2,
  "evidence": [
    {
      "id": 1,
      "task": 123,
      "evidence_type": "link",
      "url": "https://docs.google.com/spreadsheets/...",
      "uploaded_by": 1,
      "uploaded_at": "2025-10-15T14:30:00Z"
    },
    {
      "id": 2,
      "task": 123,
      "evidence_type": "note",
      "note": "Completed shortlist of 10 programs",
      "uploaded_by": 1,
      "uploaded_at": "2025-10-15T15:45:00Z"
    }
  ]
}
```

### Create Evidence
```http
POST /api/todos/evidence/
Authorization: Bearer <token>
Content-Type: multipart/form-data

{
  "task_id": 123,
  "evidence_type": "photo",
  "file": <image file>
}
```

**Evidence Types**:
- `note`: Text description (use `note` field)
- `link`: URL (use `url` field)
- `photo`: Image from camera/gallery (use `file` field)
- `screenshot`: Screenshot image (use `file` field)
- `file`: Document upload (use `file` field)

**Response**:
```json
{
  "id": 3,
  "task": 123,
  "evidence_type": "photo",
  "file": "/media/evidence/screenshot_123.png",
  "uploaded_by": 1,
  "uploaded_at": "2025-10-15T16:00:00Z"
}
```

**Side Effect**: Automatically recalculates task progress when evidence is uploaded.

### Get Evidence by Type
```http
GET /api/todos/evidence/by-type/?evidence_type=photo
Authorization: Bearer <token>
```

### Update Note Evidence
```http
PATCH /api/todos/evidence/{id}/update-note/
Authorization: Bearer <token>
Content-Type: application/json

{
  "note": "Updated note text"
}
```

Only works for `note`-type evidence.

### Delete Evidence
```http
DELETE /api/todos/evidence/{id}/
Authorization: Bearer <token>
```

**Side Effect**: Automatically recalculates task progress after deletion.

---

## 💬 Task Runs API (Let's Go Sessions)

**Base URL**: `/api/todos/task-runs/`

### List Runs
```http
GET /api/todos/task-runs/
Authorization: Bearer <token>
```

Returns all Let's Go sessions for user's tasks.

### Get Runs by Task
```http
GET /api/todos/task-runs/by-task/?task_id=123
Authorization: Bearer <token>
```

**Response**:
```json
{
  "task_id": 123,
  "task_title": "Research MS programs in USA",
  "total_runs": 3,
  "completed_runs": 2,
  "runs": [
    {
      "id": 1,
      "task": 123,
      "user_inputs": [
        "I want to apply to USA",
        "Computer Science",
        "Yes, AI/ML focus"
      ],
      "ai_responses": [
        "Which country are you targeting?",
        "What degree are you interested in?",
        "Any specific focus areas?"
      ],
      "completed": true,
      "duration_seconds": 450,
      "interactions_count": 3,
      "started_at": "2025-10-15T14:00:00Z"
    }
  ]
}
```

### Create Run
```http
POST /api/todos/task-runs/
Authorization: Bearer <token>
Content-Type: application/json

{
  "task_id": 123,
  "user_inputs": [],
  "ai_responses": []
}
```

**Validation**: Only `copilot` tasks can have runs.

### Update Run
```http
PATCH /api/todos/task-runs/{id}/
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_inputs": ["New user message"],
  "ai_responses": ["New AI message"],
  "completed": false
}
```

**Note**: Messages are appended to existing arrays.

### Add Message
```http
POST /api/todos/task-runs/{id}/add-message/
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_input": "My answer here",
  "ai_response": "AI's response here"
}
```

Convenience endpoint for adding one message exchange.

### Complete Run
```http
POST /api/todos/task-runs/{id}/complete/
Authorization: Bearer <token>
Content-Type: application/json

{
  "duration_seconds": 450,
  "artifact_id": 789  // Optional
}
```

Marks session as completed and optionally links the generated artifact.

### Get Recent Runs
```http
GET /api/todos/task-runs/recent/?limit=10
Authorization: Bearer <token>
```

Returns recent Let's Go sessions across all tasks.

### Get Transcript
```http
GET /api/todos/task-runs/{id}/transcript/
Authorization: Bearer <token>
```

**Response**:
```json
{
  "task_run_id": 1,
  "task_title": "Research MS programs in USA",
  "started_at": "2025-10-15T14:00:00Z",
  "completed": true,
  "duration_seconds": 450,
  "interactions_count": 3,
  "transcript": [
    {"role": "ai", "message": "Which country are you targeting?", "index": 0},
    {"role": "user", "message": "I want to apply to USA", "index": 0},
    {"role": "ai", "message": "What degree are you interested in?", "index": 1},
    {"role": "user", "message": "Computer Science", "index": 1},
    {"role": "ai", "message": "Any specific focus areas?", "index": 2},
    {"role": "user", "message": "Yes, AI/ML focus", "index": 2}
  ]
}
```

---

## 📋 Existing Todo API (Enhanced)

**Base URL**: `/api/todos/`

All existing Todo endpoints remain functional and now support the new atomic task fields:

### List Tasks
```http
GET /api/todos/
Authorization: Bearer <token>
```

### Create Task
```http
POST /api/todos/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Research MS programs in USA",
  "task_type": "copilot",
  "timebox_minutes": 45,
  "deliverable_type": "shortlist",
  "definition_of_done": [
    {"text": "Find 10 programs", "weight": 50, "completed": false},
    {"text": "Compare rankings", "weight": 30, "completed": false},
    {"text": "Check deadlines", "weight": 20, "completed": false}
  ],
  "constraints": {
    "country": "USA",
    "degree": "MS CS"
  },
  "lets_go_inputs": [
    {"question": "Which country?", "type": "text"},
    {"question": "Which degree?", "type": "text"}
  ]
}
```

### Update Task (including DoD)
```http
PATCH /api/todos/{id}/
Authorization: Bearer <token>
Content-Type: application/json

{
  "definition_of_done": [
    {"text": "Find 10 programs", "weight": 50, "completed": true},
    {"text": "Compare rankings", "weight": 30, "completed": true},
    {"text": "Check deadlines", "weight": 20, "completed": false}
  ]
}
```

**Side Effect**: Automatically recalculates `progress_percentage` when DoD is updated.

---

## 🔗 URL Mapping Summary

| Endpoint Pattern | App | Description |
|-----------------|-----|-------------|
| `/api/auth/goalspecs/` | users | GoalSpec CRUD |
| `/api/todos/` | todos | Todo CRUD |
| `/api/todos/daily-planner/` | todos | Daily plan generation |
| `/api/todos/weekly-review/` | todos | Weekly review analytics |
| `/api/todos/evidence/` | todos | Task evidence upload |
| `/api/todos/task-runs/` | todos | Let's Go sessions |

---

## 🎯 Integration Checklist

All backend API endpoints are complete and ready for frontend integration:

- ✅ GoalSpec CRUD endpoints
- ✅ Daily Planner generation endpoint
- ✅ Weekly Review endpoint
- ✅ Evidence upload endpoint
- ✅ Task Runs (Let's Go sessions) endpoint
- ✅ All endpoints wired to URL patterns
- ✅ Authentication required on all endpoints
- ✅ User filtering in querysets

---

## 🚀 Next Steps

1. Test all endpoints using Postman or curl
2. Update frontend API calls to use new endpoints
3. Test end-to-end flows:
   - Onboarding → GoalSpec creation
   - Daily planner generation
   - Let's Go session with artifact creation
   - Evidence upload with progress calculation
   - Weekly review generation
4. Add error handling in frontend for API failures
5. Implement loading states during async operations

---

**Status**: All API endpoints implemented and ready for testing! 🎉
