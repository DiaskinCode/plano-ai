# Multi-Category Onboarding Fix Summary

## Issues Identified

### 1. **Inconsistent Category State**
**Problem**: Users could complete categories that weren't in their `selected_categories` list, causing:
```python
selected_categories: ['study']
completed_categories: ['study', 'career']  # ❌ More than selected!
```

This broke the completion logic:
```python
all_complete = set(['study', 'career']) == set(['study'])  # Always False!
```

**Fix**: Auto-add categories to `selected_categories` when they're being chatted for (onboarding_views.py:662-666)

### 2. **Duplicate GoalSpec Creation**
**Problem**: When retrying onboarding, the system created duplicate GoalSpecs for the same category.

User 39 had 4 GoalSpecs for the "study" category!

**Fix**: Modified `create_goalspec_from_chat()` to check for existing GoalSpecs and UPDATE instead of creating duplicates (onboarding_views.py:787-798)

### 3. **Failed Task Generation Not Retrying**
**Problem**: If task generation failed, the `tasks_generated` flag was set to `True`, preventing retries even though 0 tasks existed.

**Fix**: Enhanced idempotency check to verify tasks actually exist, allowing retry if `tasks_generated=True` but `tasks_count=0` (onboarding_views.py:699-714)

## Backend Fixes Applied

### Changes Made:

1. **File**: `users/onboarding_views.py`

   **Line 662-666**: Auto-add category to selected_categories
   ```python
   if category not in progress.selected_categories:
       print(f"[OnboardingChat] WARNING: Category '{category}' not in selected_categories, adding it now")
       progress.selected_categories.append(category)
       progress.save()
   ```

2. **Line 699-714**: Improved idempotency with task existence check
   ```python
   existing_tasks_count = Todo.objects.filter(user=user).count()

   if progress.tasks_generated and existing_tasks_count > 0:
       # Tasks exist, skip generation
   elif progress.tasks_generated and existing_tasks_count == 0:
       # Flag set but no tasks - retry generation
   ```

3. **Line 787-798**: Prevent duplicate GoalSpecs
   ```python
   existing = GoalSpec.objects.filter(user=user, category=category, is_active=True).first()

   if existing:
       # Update existing instead of creating duplicate
       existing.title = title
       existing.specifications = specifications
       # ...
   ```

4. **User 39 State Fixed**: Ran cleanup script that:
   - Synced selected_categories with completed_categories
   - Removed 3 duplicate GoalSpecs
   - Reset tasks_generated flag to allow retry

## Current Backend Response Structure

### When More Categories Remain:
```json
{
  "status": "chatting",
  "completed_category": "study",
  "next_category": "career",
  "progress": {
    "completed": 1,
    "total": 2
  }
}
```

### When All Categories Complete:
```json
{
  "status": "complete",
  "tasks_created": 15,
  "goalspecs_created": 2,
  "message": "Onboarding complete! Your personalized plan is ready."
}
```

## Frontend Requirements

### ⚠️ CRITICAL: Frontend Must Check `status` Field

The frontend is currently **ignoring** the `status` field and always navigating to "Your plan is ready" screen, even when more categories need to be chatted.

### Required Frontend Logic:

```typescript
// After calling /api/onboarding/chat/complete/
const response = await api.post('/api/onboarding/chat/complete/', {
  category: 'study',
  extracted_data: {...}
});

if (response.status === 'chatting') {
  // More categories to complete
  // Option 1: Navigate to category selection screen showing progress
  navigation.navigate('CategorySelection', {
    completedCategories: response.progress.completed,
    totalCategories: response.progress.total,
    nextCategory: response.next_category
  });

  // Option 2: Automatically start chat for next category
  navigation.navigate('ChatOnboarding', {
    category: response.next_category
  });

} else if (response.status === 'complete') {
  // All done! Navigate to success screen
  navigation.navigate('OnboardingComplete', {
    tasksCreated: response.tasks_created
  });
}
```

### UI Improvements Needed:

1. **Category Progress Screen**
   - Show all selected categories
   - Mark completed categories with checkmark ✓
   - Show current/next category to chat for
   - Display progress: "2 of 3 categories complete"

2. **Completion Screen**
   - Only show when `status === 'complete'`
   - Display actual tasks created count (not hardcoded 0!)
   - Should not appear until ALL categories are done

## API Endpoints Reference

### `/api/onboarding/status/` (GET)
Check user's current onboarding state:

```json
{
  "needs_onboarding": true,
  "is_complete": false,
  "status": "chatting",
  "selected_categories": ["study", "career"],
  "completed_categories": ["study"],
  "current_category": "career",
  "tasks_generated": false
}
```

**Use this endpoint** when user opens the app to determine:
- Should they see onboarding?
- Which screen to show (category selection, chat, or complete)?
- What their progress is

### `/api/onboarding/chat/complete/` (POST)
Complete chat for a category:

**Request:**
```json
{
  "category": "study",
  "extracted_data": {...},
  "selected_categories": ["study", "career"]  // Optional, only on first call
}
```

**Response:** See "Backend Response Structure" above

## Testing

### Test Script: `test_onboarding_fix.py`

Run this to verify the fix works:
```bash
./venv/bin/python test_onboarding_fix.py
```

Expected output:
```
✅ Everything looks good! Onboarding should complete successfully.

Expected outcome:
  - Tasks will be generated
  - Career data will be merged to profile
  - Career GoalSpec will be created
  - Study GoalSpec will be updated (not duplicated)
  - progress.is_complete will be set to True
  - profile.onboarding_completed will be set to True
```

### Debug Script: `debug_onboarding_state.py`

Check any user's onboarding state:
```bash
./venv/bin/python debug_onboarding_state.py
```

## Summary

### Backend Status: ✅ FIXED
- All 3 issues resolved
- User 39's broken state cleaned up
- Comprehensive test shows it should work

### Frontend Status: ❌ NEEDS FIX
- Must check `response.status` field
- Must implement proper navigation logic
- Must show category progress UI

### Next Steps:
1. Update frontend to check `status` field in response
2. Implement category progress screen
3. Only show "Your plan is ready" when `status === 'complete'`
4. Test end-to-end flow with multiple categories
