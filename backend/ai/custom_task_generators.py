"""
Custom Task Generators (Layer 3)

Generates unique tasks that only specific user backgrounds receive.
- Founders get 40% unique tasks (startup essays, impact quantification)
- Engineers/professionals get 30% unique tasks
- Standard students get 20% unique tasks (baseline)

These tasks are NOT in the template registry - they're dynamically created
based on personalization flags from profile_extractor.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta


class CustomTaskGenerator:
    """
    Generates custom tasks based on user background.

    Each method returns a list of task dictionaries with:
    - title: Task description
    - category: study/career/etc
    - priority: 1-5
    - timebox_minutes: Estimated time
    - energy_level: low/medium/high
    - definition_of_done: Success criteria
    - task_type: Type indicator
    """

    def __init__(self, context: Dict[str, Any]):
        """
        Initialize with full personalization context.

        Args:
            context: Full context from profile_extractor (includes all flags)
        """
        self.context = context

    def generate_founder_tasks(self) -> List[Dict]:
        """
        Generate founder-specific tasks (40% unique content).

        Only called when has_startup_background = True.

        Returns:
            List of 3-5 founder-specific tasks
        """
        if not self.context.get('has_startup_background'):
            return []

        tasks = []
        startup_name = self.context.get('startup_name', 'your startup')
        startup_users = self.context.get('startup_users', '0')
        startup_description = self.context.get('startup_description', 'your startup')
        field = self.context.get('field', 'your field')

        # Task 1: Founder Essay (unique to founders)
        tasks.append({
            'title': f"""Write application essay: "Founder Journey" (connect {startup_name} to {field})

🚀 YOUR UNIQUE STORY:
You built {startup_name} ({startup_users} users) - most applicants don't have this.

Essay prompt: "Describe an entrepreneurial project and what it taught you about {field}."

Structure (500-700 words):
1. The Problem: What gap did {startup_name} address?
2. Building 0→1: Technical challenges you solved ({startup_description})
3. Growth to {startup_users} users: What this taught you about scale, users, systems
4. Limitations Hit: What you realized you DON'T know (why you need graduate school)
5. Bridge to {field}: How {startup_name} exposed you to {field} challenges

Key Insight:
"Building {startup_name} taught me what classrooms can't: real user feedback, production systems, and ambiguous problem-solving. Now I need structured learning in [specific area] to combine founder instincts with academic rigor."

This essay is ONLY possible because you're a founder. Use it.""",
            'category': self.context.get('category', 'study'),
            'priority': 5,  # Highest priority - unique differentiator
            'timebox_minutes': 180,
            'energy_level': 'high',
            'definition_of_done': f"""✅ Draft complete (500-700 words)
✅ Connects {startup_name} technical challenges to {field}
✅ Quantifies impact ({startup_users} users mentioned)
✅ Shows what you DON'T know (humility + motivation)
✅ Proofread (no typos)""",
            'task_type': 'essay'
        })

        # Task 2: Quantify Startup Impact (for resume/CV)
        tasks.append({
            'title': f"""Quantify {startup_name} impact for CV/resume (with metrics)

You have {startup_users} users - SHOW THE NUMBERS:

Metrics to calculate:
□ User growth rate: "Grew from 0 → {startup_users} users in [X months]"
□ Technical scale: "[Y] requests/day, [Z]% uptime, [A]ms latency"
□ Code ownership: "Built [B]% of codebase ([C] lines of code)"
□ Technologies used: "[List tech stack: Python, React, AWS, etc.]"

Example bullets for resume:
• "Built {startup_name} ({startup_description}) from 0 → {startup_users} users"
• "Architected [system component] handling [X] requests/day with [Y]% uptime"
• "Led full-stack development ([tech stack]) as solo founder/technical co-founder"

Why this matters:
Most students have coursework. You built something REAL with REAL users.""",
            'category': self.context.get('category', 'career'),
            'priority': 4,
            'timebox_minutes': 90,
            'energy_level': 'medium',
            'definition_of_done': f"""✅ 3-5 quantified bullet points
✅ Metrics calculated (user growth, scale, performance)
✅ Tech stack listed
✅ Resume/CV updated
✅ Numbers verified (no exaggeration)""",
            'task_type': 'documentation'
        })

        # Task 3: Get recommendation from startup advisor/investor
        if self.context.get('startup_funding', '$0') != '$0':
            tasks.append({
                'title': f"""Request recommendation letter from {startup_name} advisor/investor

🎯 FOUNDER ADVANTAGE:
Recommendation from someone who funded/advised {startup_name} > generic professor letter.

Email template:

"Hi [Investor/Advisor Name],

I'm applying to {field} programs and would greatly appreciate a recommendation letter highlighting my work on {startup_name}.

Specifically, it would be helpful if you could speak to:
• Technical execution: How we built to {startup_users} users
• Problem-solving under constraints
• Growth mindset and learning agility
• Why I'm ready for graduate-level {field} study

Deadline: [application deadline - 2 weeks]
Programs: [list 3-5 universities]

I've attached:
- My draft SOP (for context)
- {startup_name} metrics summary
- Recommendation form link

Thank you for believing in {startup_name}. This recommendation would mean a lot.

Best regards"

(Sign with your name)

Follow-up plan:
- Send initial request: Today
- Check in after 5 days if no response
- Provide easy template/talking points if needed
- Send thank you note after submission""",
                'category': self.context.get('category', 'study'),
                'priority': 4,
                'timebox_minutes': 60,
                'energy_level': 'medium',
                'definition_of_done': """✅ Advisor/investor identified
✅ Email drafted and personalized
✅ Attachments prepared (SOP, metrics, form link)
✅ Email sent
✅ Calendar reminder set for follow-up""",
                'task_type': 'email'
            })

        # Task 4: LinkedIn founder headline
        tasks.append({
            'title': f"""Update LinkedIn: Highlight {startup_name} founder status

Current headline probably: "Student at [University]"
Better headline: "{self.context.get('startup_role', 'Founder')} @ {startup_name} ({startup_users} users) | {self.context.get('key_skill_1', 'Skills')} | Seeking {self.context.get('target_role', 'opportunities')}"

Why this works:
- Shows execution (built something)
- Shows traction ({startup_users} users)
- Shows technical depth (skills)

About section opener:
"I built {startup_name} to {startup_users} users, tackling {startup_description}. Now seeking to deepen my {field} expertise through [graduate school / industry roles] while bringing my founder mindset to ambiguous, 0→1 challenges."

This positions you as:
✅ Builder (not just learner)
✅ Impact-driven ({startup_users} users)
✅ Hungry to grow (seeking new opportunities)""",
            'category': 'career',
            'priority': 3,
            'timebox_minutes': 45,
            'energy_level': 'low',
            'definition_of_done': f"""✅ LinkedIn headline updated with {startup_name}
✅ About section rewritten (founder story)
✅ Experience section: {startup_name} listed with metrics
✅ Profile photo updated (professional)
✅ URL customized (linkedin.com/in/yourname)""",
            'task_type': 'profile_update'
        })

        return tasks

    def generate_gpa_compensation_tasks(self) -> List[Dict]:
        """
        Generate GPA compensation tasks.

        Only called when gpa_needs_compensation = True (GPA < 3.5 AND strong background).

        Returns:
            List of 2-3 compensation tasks
        """
        if not self.context.get('gpa_needs_compensation'):
            return []

        tasks = []
        gpa = self.context.get('gpa_raw', 3.0)
        field = self.context.get('field', 'your field')

        # Task 1: Address GPA in optional essay
        tasks.append({
            'title': f"""Write optional essay: "Academic Context" (address {gpa} GPA)

Your GPA ({gpa}) is below average, but you have compensating factors.

Optional essay prompt: "Is there anything else you'd like us to know?"

Structure (250-400 words):

1. Acknowledge Reality (1 sentence):
"My GPA of {gpa} doesn't fully reflect my capabilities in {field}."

2. Provide Context (1 paragraph):
- {self.context.get('startup_name', 'Side project')} demanded 20+ hours/week
- Worked part-time to fund education
- Family responsibilities
- Health challenges
(Pick what's true for you - don't make excuses, provide context)

3. Show Growth (1 paragraph):
- {field}-specific courses: [List courses where you got A/A-]
- Recent semester GPA: [If trending up]
- Self-directed learning: [Certifications, projects, online courses]

4. Evidence of Capability (1 paragraph):
- Built {self.context.get('startup_name', 'project')} with {self.context.get('startup_users', 'real users')} users
- Professional achievements
- Research contributions

5. Forward-Looking (1 sentence):
"With full focus on {field} in graduate school, I'm confident I'll excel academically while bringing practical problem-solving skills from my entrepreneurial experience."

Tone: Honest, not defensive. Own it, contextualize it, move forward.""",
            'category': 'study',
            'priority': 4,
            'timebox_minutes': 120,
            'energy_level': 'high',
            'definition_of_done': f"""✅ Draft complete (250-400 words)
✅ GPA ({gpa}) acknowledged honestly
✅ Context provided (not excuses)
✅ Evidence of capability shown
✅ Forward-looking and confident tone
✅ Proofread""",
            'task_type': 'essay'
        })

        # Task 2: Get strong recommendation emphasizing non-GPA strengths
        tasks.append({
            'title': f"""Brief recommender: Emphasize practical skills (compensate for {gpa} GPA)

Your GPA is {gpa}, so recommendations should highlight NON-academic strengths.

Email to recommender:

"Hi [Professor/Manager Name],

Thank you for agreeing to write my recommendation letter for {field} programs.

Given my GPA ({gpa}), it would be especially helpful if your letter could emphasize:

✅ Practical problem-solving skills: [Example from class/work]
✅ Technical depth: [Specific project you excelled at]
✅ Work ethic and growth mindset: [How you overcame challenges]
✅ Real-world impact: [Professional achievements, {self.context.get('startup_name', 'projects')}]

What I DON'T need:
❌ Generic "good student" language
❌ Focus on GPA or academic performance

What WOULD help:
✅ "While their GPA doesn't reflect it, they demonstrated exceptional problem-solving skills when..."
✅ "They may not have the highest GPA, but their practical execution skills..."

Attached:
- My SOP (for context on my goals)
- Resume (highlighting {self.context.get('startup_name', 'achievements')})

Thank you for understanding. Strong recommendations highlighting my practical strengths will help balance my academic record.

Best regards"

(Sign with your name)

This gives recommender permission to address GPA while emphasizing your strengths.""",
            'category': 'study',
            'priority': 4,
            'timebox_minutes': 60,
            'energy_level': 'medium',
            'definition_of_done': """✅ Recommender identified (professor/manager who knows your strengths)
✅ Email drafted
✅ Talking points provided
✅ Resume and SOP attached
✅ Email sent""",
            'task_type': 'email'
        })

        return tasks

    def generate_smart_test_prep_tasks(self) -> List[Dict]:
        """
        Generate test prep tasks ONLY if needed.

        Uses test_prep_needed flags to skip unnecessary prep.
        Example: If IELTS current=7.0, target=7.0 → NO prep task generated.

        Returns:
            List of 0-2 test prep tasks (only for tests that need improvement)
        """
        tasks = []
        test_prep_needed = self.context.get('test_prep_needed', {})

        # Only generate tasks for tests that actually need prep
        if test_prep_needed.get('ielts'):
            current_ielts = self.context.get('ielts_score', 0)
            target_ielts = self.context.get('target_score', 7.0)

            tasks.append({
                'title': f"""IELTS prep: {current_ielts} → {target_ielts} (smart focus)

Current: {current_ielts}
Target: {target_ielts}
Gap: {float(target_ielts) - float(current_ielts)} points

Smart strategy (don't waste time):
1. Diagnose: Take practice test, identify weakest section
2. Focus: Spend 80% time on weakest section
3. Benchmark: Take full practice test every week
4. Stop: When you hit {target_ielts} consistently (don't over-prepare)

Resources:
- IELTS Liz (free): writing and speaking tips
- Cambridge practice tests (paid but worth it)
- HelloTalk app: free speaking practice with natives

Time investment:
- Week 1: Diagnostic (4 hours)
- Weeks 2-4: Focused prep (8 hours/week on weak section)
- Week 5: Final practice test

Total: ~30 hours (vs 100+ hours of unfocused prep)""",
                'category': 'study',
                'priority': 3,
                'timebox_minutes': 240,  # Total for week 1 diagnostic
                'energy_level': 'high',
                'definition_of_done': f"""✅ Diagnostic test completed
✅ Weakest section identified
✅ Study plan created (focused on weak section)
✅ Practice materials acquired
✅ Weekly practice test scheduled""",
                'task_type': 'test_prep'
            })

        if test_prep_needed.get('gre'):
            current_gre = self.context.get('gre_score', 0)
            target_gre = self.context.get('target_gre', 320)

            tasks.append({
                'title': f"""GRE prep: {current_gre} → {target_gre} (quant + verbal balance)

Current: {current_gre}
Target: {target_gre}
Gap: {target_gre - current_gre} points

Smart strategy:
1. Quant (easier to improve): Target 165+ with focused practice
2. Verbal (harder to improve): Target 155+ with vocabulary work
3. AWA: 4.0+ is fine (schools don't care much)

Resources:
- Manhattan Prep 5lb book (best for quant)
- Magoosh Vocabulary app (for verbal)
- ETS Official Guide (real questions)

Time investment:
- Weeks 1-4: Quant mastery (10 hours/week)
- Weeks 5-8: Verbal + vocabulary (10 hours/week)
- Weeks 9-10: Full practice tests (6 hours/week)

Stop when: You consistently hit {target_gre} on practice tests""",
                'category': 'study',
                'priority': 3,
                'timebox_minutes': 600,  # 10 hours first week
                'energy_level': 'high',
                'definition_of_done': f"""✅ Study materials acquired
✅ Baseline test completed
✅ Study schedule created (quant first, then verbal)
✅ Vocabulary app installed
✅ First week quant practice done""",
                'task_type': 'test_prep'
            })

        # If TOEFL needed (less common, only if ielts not sufficient)
        if test_prep_needed.get('toefl'):
            tasks.append({
                'title': f"""TOEFL prep: {self.context.get('toefl_score', 0)} → {self.context.get('target_toefl', 100)}

Same smart strategy as IELTS:
1. Diagnostic test
2. Focus on weakest section
3. Weekly benchmarks
4. Stop when target reached

TOEFL is easier than IELTS for most non-native speakers (more predictable format).""",
                'category': 'study',
                'priority': 3,
                'timebox_minutes': 240,
                'energy_level': 'high',
                'definition_of_done': """✅ Diagnostic completed
✅ Weak section identified
✅ Study plan created
✅ Practice materials ready""",
                'task_type': 'test_prep'
            })

        return tasks

    def generate_all_custom_tasks(self) -> List[Dict]:
        """
        Generate ALL custom tasks based on context.

        Returns:
            Combined list of all custom tasks (founder + GPA + test prep)
        """
        all_tasks = []

        # Founder tasks (40% unique)
        if self.context.get('has_startup_background'):
            founder_tasks = self.generate_founder_tasks()
            all_tasks.extend(founder_tasks)
            print(f"[CustomTaskGenerator] Generated {len(founder_tasks)} founder-specific tasks")

        # GPA compensation tasks
        if self.context.get('gpa_needs_compensation'):
            gpa_tasks = self.generate_gpa_compensation_tasks()
            all_tasks.extend(gpa_tasks)
            print(f"[CustomTaskGenerator] Generated {len(gpa_tasks)} GPA compensation tasks")

        # Smart test prep (only if needed)
        test_tasks = self.generate_smart_test_prep_tasks()
        if test_tasks:
            all_tasks.extend(test_tasks)
            print(f"[CustomTaskGenerator] Generated {len(test_tasks)} test prep tasks (skipped unnecessary tests)")
        else:
            print(f"[CustomTaskGenerator] Skipped test prep - all scores meet targets")

        return all_tasks


# Singleton instance
def create_custom_task_generator(context: Dict[str, Any]) -> CustomTaskGenerator:
    """
    Factory function to create CustomTaskGenerator with context.

    Args:
        context: Full personalization context from profile_extractor

    Returns:
        CustomTaskGenerator instance
    """
    return CustomTaskGenerator(context)
