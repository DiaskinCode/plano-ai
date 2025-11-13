# Opportunities Page Deprecation Plan

## Context

Based on the product critique, the "Opportunities Page" feature (`OpportunityEvent` model in `events/models.py`) should be removed.

**Original Intent**: Track new opportunities that might change the user's vision/goals.

**Why Remove**:
1. **Adds cognitive overhead** - Users already overwhelmed with tasks
2. **Unclear value prop** - Doesn't fit natural workflow
3. **Redundant** - Adaptive coaching now handles course corrections automatically
4. **Distracts from core** - PathAI is about execution, not discovery

---

## Current Implementation

### Backend
- **Model**: `events.models.OpportunityEvent`
- **Fields**: title, description, AI impact assessment, user action
- **Related**: Used in check-in flow (`CheckInEvent.new_opportunities`)

### Frontend (if exists)
- Likely in "Opportunities" tab or section
- Shows list of opportunities with AI recommendations

---

## Deprecation Strategy

### Phase 1: Stop Creating New Opportunities (Immediate)
1. Comment out opportunity creation logic
2. Hide opportunities UI in frontend
3. Keep database model for historical data

### Phase 2: Redirect to Adaptive Coaching (Week 2)
1. When users click "Opportunities", show:
   - "We've replaced Opportunities with Adaptive Coaching"
   - Redirect to `/coach/check-intervention/`
2. Update help docs

### Phase 3: Data Migration (Week 4)
1. Export existing opportunities to user notes
2. Notify users: "Your opportunities have been saved to notes"
3. Archive `OpportunityEvent` table

### Phase 4: Complete Removal (Week 8)
1. Remove `OpportunityEvent` model
2. Remove from check-in flow
3. Remove all related API endpoints
4. Clean up migrations

---

## Alternative: Pivot to "Smart Suggestions"

Instead of removing entirely, pivot to simpler "Smart Suggestions":

### Current (Complex):
```
OpportunityEvent:
  - title: "Stanford AI course"
  - description: "..."
  - ai_impact_assessment: "game_changer"
  - requires_vision_change: True
  - user_action: "pivot" | "integrate" | "ignore"
```

### New (Simple):
```
SmartSuggestion:
  - message: "💡 Based on your Cambridge goal, consider: Stanford's free AI course"
  - action_type: "task" | "resource" | "tip"
  - related_goal_id: 123
  - dismissed: False
```

**Benefits**:
- Simpler mental model
- No "pivot your life" pressure
- Actionable (creates task directly)

---

## Recommended Action

**Option 1: Complete Removal** (Recommended)
- Cleaner product
- Less maintenance
- Adaptive coaching covers this use case

**Option 2: Pivot to Smart Suggestions**
- Keeps some discovery value
- Less overwhelming
- More actionable

**Decision**: Recommend **Option 1** based on critique feedback.

---

## Code Changes Required

### 1. Backend

#### Mark as deprecated in models.py:
```python
# events/models.py

class OpportunityEvent(models.Model):
    """
    DEPRECATED: This model is being phased out.

    Use AdaptiveCoach interventions instead for course corrections.
    Kept for historical data only.
    """
    # ... existing fields

    class Meta:
        ordering = ['-date_occurred']
        # Add deprecation warning
        verbose_name = "Opportunity Event (DEPRECATED)"
```

#### Remove from check-in flow:
```python
# events/models.py

class CheckInEvent(models.Model):
    # ... existing fields

    # DEPRECATED: Remove this field in next major version
    # new_opportunities = models.TextField(blank=True)
```

### 2. Frontend

#### Hide opportunities tab:
```typescript
// navigation.tsx
const tabs = [
  { name: 'Home', icon: '🏠' },
  { name: 'Tasks', icon: '✅' },
  { name: 'Goals', icon: '🎯' },
  // { name: 'Opportunities', icon: '💡' }, // DEPRECATED
  { name: 'Coach', icon: '🤖' }, // NEW: Adaptive coaching
  { name: 'Analytics', icon: '📊' },
]
```

#### Add migration banner (optional):
```typescript
// If user has old opportunities
<Banner type="info">
  We've moved Opportunities to Adaptive Coaching.
  Your AI coach now proactively suggests improvements.
  <Link to="/coach">Check it out →</Link>
</Banner>
```

---

## Migration Communication

### Email to Users (Week 1)
**Subject**: "PathAI just got smarter - Introducing Adaptive Coaching"

```
Hi [Name],

We've been listening to your feedback, and we're making PathAI simpler and smarter.

**What's Changing:**
❌ Opportunities Page → ✅ Adaptive Coaching

Instead of manually reviewing opportunities, your AI coach now:
- Proactively detects when you're falling behind
- Suggests Plan-B course corrections automatically
- Sends smart notifications at the right time

**Action Required:**
None! Your existing opportunities have been saved to your notes.

Try it out: Open PathAI → Coach tab

Questions? Reply to this email.

- PathAI Team
```

### In-App Notification
```
🎉 New: Adaptive Coaching

We've replaced the Opportunities page with something better:
Your AI coach now proactively helps you when you're struggling.

No more manual tracking. Just focus on execution.

[Try Coach Tab] [Dismiss]
```

---

## Timeline

| Week | Action | Owner |
|------|--------|-------|
| Week 1 | Hide UI, stop creating new opportunities | Frontend |
| Week 1 | Mark models as deprecated | Backend |
| Week 2 | Add migration banner | Frontend |
| Week 2 | Send user communication email | Marketing |
| Week 4 | Export data to user notes | Backend |
| Week 4 | Archive table | Backend |
| Week 8 | Remove model & migrations | Backend |

---

## Success Metrics

1. **User Confusion**: < 5% support tickets about missing opportunities
2. **Coach Adoption**: 50%+ users try adaptive coaching within 2 weeks
3. **NPS Change**: No drop (or ideally +5 points)
4. **Retention**: No increase in churn

---

## Rollback Plan

If users revolt:
1. Re-enable opportunities UI
2. Keep both features (Coach + Opportunities)
3. Run A/B test: Opportunities ON vs OFF
4. Measure: Which cohort has better retention?

---

**Status**: Opportunities deprecation plan documented. Ready for implementation after user communication.

**Recommendation**: Proceed with complete removal in favor of Adaptive Coaching (simpler, more proactive, less cognitive overhead).
