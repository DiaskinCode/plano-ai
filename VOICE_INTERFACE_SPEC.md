# Voice Interface Specification

## Overview

Voice interface for PathAI to enable hands-free task management and coaching interactions.

**Use Cases**:
1. Quick task capture while driving
2. Daily check-ins while getting ready
3. Task completion updates while working out
4. Coach conversations while commuting

---

## Architecture

### Client-Side (Mobile App)
- **Speech-to-Text**: Expo AV or device native
- **Text-to-Speech**: Expo Speech or device native
- **Wake word**: "Hey PathAI" or button press

### Backend (API)
- **Voice endpoint**: Process voice commands
- **Response generation**: Natural language responses
- **Context awareness**: Use full user context

---

## Voice Commands

### Task Management
```
"Add task: Review Cambridge application by Friday"
→ Creates task with deadline

"Mark task done: Write SOP"
→ Completes matching task

"What's next?"
→ Returns top 3 priorities from Daily Pulse

"Show my tasks for today"
→ Lists today's tasks

"Split task: Prepare visa documents"
→ Triggers AI task splitting
```

### Daily Check-In
```
"Start daily check-in"
→ Begins check-in flow

"I completed 3 out of 5 tasks today"
→ Records completion

"I'm feeling overwhelmed"
→ Triggers adaptive coach intervention
```

### Coach Interaction
```
"Coach, am I on track?"
→ Returns performance summary

"Why am I falling behind?"
→ Explains performance insights

"What should I focus on?"
→ Returns adaptive coaching recommendations
```

### Quick Queries
```
"When is my next deadline?"
→ Returns nearest deadline

"What's my streak?"
→ Returns current streak count

"How many tasks this week?"
→ Returns weekly completion stats
```

---

## API Endpoints

### 1. Process Voice Command
```
POST /api/voice/process
Authorization: Bearer <token>

Request:
{
  "transcript": "Add task review Cambridge application by Friday",
  "audio_url": "https://...", // Optional for verification
  "timestamp": "2025-11-06T10:30:00Z"
}

Response:
{
  "intent": "create_task",
  "action_taken": {
    "task_id": 123,
    "title": "Review Cambridge application",
    "scheduled_date": "2025-11-08"
  },
  "response_text": "Got it! I've added 'Review Cambridge application' for Friday.",
  "response_audio_url": "https://..." // Optional TTS
}
```

### 2. Voice-Enabled Daily Check-In
```
POST /api/voice/checkin
Authorization: Bearer <token>

Request:
{
  "transcript": "I completed 3 out of 5 tasks today. I'm feeling a bit overwhelmed.",
  "date": "2025-11-06"
}

Response:
{
  "checkin_recorded": true,
  "completed_tasks": 3,
  "total_tasks": 5,
  "coach_response": "I hear you. Completing 3 out of 5 is solid progress. Let's lighten tomorrow's load - I've adjusted your schedule.",
  "intervention_triggered": true,
  "intervention_type": "workload_reduction"
}
```

### 3. Voice Query
```
POST /api/voice/query
Authorization: Bearer <token>

Request:
{
  "query": "Coach, am I on track?",
  "context": "daily_pulse" // Optional: daily_pulse, performance, tasks
}

Response:
{
  "answer": "You're on a 5-day streak with 65% completion rate. You're doing well, but watch Friday - that's your weakest day.",
  "data": {
    "streak": 5,
    "completion_rate": 0.65,
    "weak_day": "Friday"
  }
}
```

---

## Natural Language Processing

### Intent Classification

Use Claude/GPT to classify voice commands:

```python
def classify_intent(transcript: str) -> Dict:
    """
    Possible intents:
    - create_task
    - complete_task
    - list_tasks
    - daily_checkin
    - coach_query
    - performance_query
    - split_task
    - skip_task
    """
    prompt = f"""
    Classify this user voice command into one of these intents:

    Voice command: "{transcript}"

    Intents:
    - create_task: User wants to add a new task
    - complete_task: User finished a task
    - list_tasks: User wants to see tasks
    - daily_checkin: User doing daily check-in
    - coach_query: User asking coach for advice
    - performance_query: User asking about progress
    - split_task: User wants to break down a task
    - skip_task: User wants to skip/postpone a task

    Also extract:
    - Task title (if applicable)
    - Date/deadline (if mentioned)
    - Sentiment (positive/neutral/negative)

    Return JSON.
    """

    # Call LLM
    response = call_llm(prompt)
    return response
```

---

## Implementation Plan

### Phase 1: Basic Commands (Week 1-2)
- ✅ Add task via voice
- ✅ Mark task complete
- ✅ List today's tasks
- ✅ Simple coach query

### Phase 2: Contextual Responses (Week 3-4)
- ✅ Use Daily Pulse for "What's next?"
- ✅ Use Performance Insights for "Am I on track?"
- ✅ Trigger interventions from voice check-ins

### Phase 3: Conversational Flow (Week 5-6)
- ✅ Multi-turn conversations
- ✅ Follow-up questions
- ✅ Clarifications ("Which task?")

### Phase 4: Voice-First Experience (Week 7-8)
- ✅ Hands-free mode
- ✅ Ambient voice assistant
- ✅ Car mode UI

---

## Voice Response Templates

### Task Created
```
"Got it! I've added '{task_title}' {for date}."
"Done. '{task_title}' is on your list {for date}."
"Perfect. I'll remind you about '{task_title}' on {date}."
```

### Task Completed
```
"Awesome! '{task_title}' is marked done."
"Great work! That's task {count} today."
"Nice! You're on a roll - {streak} days strong."
```

### Coach Query
```
"You're doing great! {completion_rate}% completion this week."
"Here's what I see: {performance_summary}"
"Based on your patterns, {recommendation}"
```

### Intervention
```
"I noticed you're falling behind. Let's simplify your week."
"You have {overdue_count} overdue tasks. Want me to re-scope them?"
"Your Friday performance drops - let's move critical tasks to Monday."
```

---

## Privacy & Security

### Audio Handling
- **Client-side transcription** preferred (Expo Speech Recognition)
- **Server-side fallback**: Use Whisper API if needed
- **No audio storage**: Only store transcripts
- **Encryption**: All voice data encrypted in transit

### Consent
- Require explicit opt-in: "Enable voice commands?"
- Clear privacy policy: "Voice commands are transcribed, not recorded"
- Allow opt-out: "Disable voice in Settings"

---

## Technical Stack

### Frontend (React Native)
```typescript
// expo-av or expo-speech
import { Audio } from 'expo-av';
import * as Speech from 'expo-speech';

// Voice command handler
const handleVoiceCommand = async () => {
  // Start recording
  const { recording } = await Audio.Recording.createAsync(
    Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY
  );

  // Stop after user stops speaking
  await recording.stopAndUnloadAsync();

  // Transcribe (client-side or send to backend)
  const transcript = await transcribe(recording.getURI());

  // Send to backend
  const response = await fetch('/api/voice/process', {
    method: 'POST',
    body: JSON.stringify({ transcript })
  });

  // Speak response
  Speech.speak(response.response_text);
};
```

### Backend (Django)
```python
# voice_views.py
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_voice_command(request):
    """Process voice command and return response."""
    transcript = request.data.get('transcript')

    # Classify intent
    intent = classify_voice_intent(transcript)

    # Execute action
    if intent['type'] == 'create_task':
        task = create_task_from_voice(request.user, intent)
        return Response({
            'response_text': f"Got it! I've added '{task.title}'.",
            'action_taken': {'task_id': task.id}
        })

    elif intent['type'] == 'coach_query':
        response = generate_coach_response(request.user, transcript)
        return Response({
            'response_text': response
        })

    # ... more intents
```

---

## Testing Scenarios

### Scenario 1: Quick Task Capture
```
User: "Hey PathAI, add task research IELTS requirements by tomorrow"
Assistant: "Got it! I've added 'Research IELTS requirements' for tomorrow."
[Task created: Research IELTS requirements, scheduled: 2025-11-07]
```

### Scenario 2: Daily Check-In
```
User: "Start daily check-in"
Assistant: "How did today go? Did you complete your tasks?"
User: "I finished 2 out of 4 tasks. The SOP task is too hard."
Assistant: "I hear you. Let me break down that SOP task into smaller steps. I've split it into 3 manageable pieces for you."
[Triggers task splitting for SOP task]
```

### Scenario 3: Coach Query
```
User: "Coach, am I on track for my Cambridge application?"
Assistant: "You're making progress, but your completion rate is 55% this week. You need to speed up - the deadline is in 6 weeks. Let me suggest: Focus on your IELTS prep this week. Want me to adjust your schedule?"
User: "Yes, adjust it"
Assistant: "Done. I've moved 3 low-priority tasks to next week and added daily IELTS practice slots at 9am - your peak hour."
[Applies adaptive coaching intervention]
```

---

## Metrics to Track

1. **Voice Command Accuracy**
   - Intent classification accuracy: Target 95%+
   - Entity extraction accuracy: Target 90%+

2. **User Engagement**
   - % of users who enable voice: Target 30%
   - Voice commands per active voice user: Target 5+/week

3. **Task Completion via Voice**
   - % of tasks created via voice: Track
   - % of tasks completed via voice: Track

4. **Coach Interaction**
   - Voice coach queries per user: Target 2+/week
   - Intervention acceptance via voice: Target 70%+

---

## Accessibility Benefits

Voice interface makes PathAI accessible to:
- **Visually impaired** users
- **Motor impairment** users
- **Busy professionals** (hands-free)
- **Multitaskers** (while driving, cooking, exercising)

---

## Future Enhancements

### V2: Conversational AI
- Multi-turn conversations
- Context retention across sessions
- Proactive voice check-ins ("How's your day going?")

### V3: Ambient Coach
- Always-listening mode (opt-in)
- Interrupts when detecting stress ("You sound overwhelmed - want to talk?")
- Celebrates wins in real-time ("I heard you finished! Great job!")

### V4: Voice Analytics
- Sentiment analysis from voice tone
- Stress detection (elevated voice, pace)
- Energy level detection (suggests break if fatigued)

---

**Status**: Voice interface specification complete. Ready for implementation with basic command support first.

**Recommended Start**: Implement `/api/voice/process` endpoint with intent classification + task creation.
