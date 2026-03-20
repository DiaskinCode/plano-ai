"""
Task Template System

Provides deterministic, template-based task generation with guaranteed personalization.
No LLM hallucinations, works on Day 1, uses existing profile data.

Architecture:
1. TaskTemplate - Base template with variables
2. Template Registry - 40 pre-built templates (20 study, 20 career)
3. Variable extraction - Pull from UserProfile + GoalSpec

Layer 2: Jinja2 conditional blocks for personalization
- {% if has_startup_background %} - Founder-specific content
- {% if gpa_needs_compensation %} - GPA compensation strategies
- {% if test_prep_needed.ielts %} - Smart test prep (only if needed)
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
from jinja2 import Template


class TemplateCategory(str, Enum):
    """Task categories"""
    STUDY = "study"
    CAREER = "career"
    SPORT = "sport"
    LANGUAGE = "language"
    FINANCE = "finance"


class MilestoneType(str, Enum):
    """Milestone types within categories"""
    # Study
    UNIVERSITY_RESEARCH = "university_research"
    EXAM_PREP = "exam_prep"
    SOP_DRAFTING = "sop_drafting"
    RECOMMENDATIONS = "recommendations"
    APPLICATIONS = "applications"
    VISA_PROCESS = "visa_process"
    SCHOLARSHIPS = "scholarships"

    # Career
    RESUME_UPDATE = "resume_update"
    LINKEDIN_OPTIMIZATION = "linkedin_optimization"
    JOB_APPLICATIONS = "job_applications"
    JOB_SEARCH = "job_search"
    NETWORKING = "networking"
    SKILL_BUILDING = "skill_building"
    INTERVIEW_PREP = "interview_prep"

    # Sport
    WORKOUT_PLAN = "workout_plan"
    NUTRITION = "nutrition"
    PROGRESS_TRACKING = "progress_tracking"


class BudgetTier(str, Enum):
    """Budget-based template variants"""
    BUDGET = "budget"  # < $15k
    STANDARD = "standard"  # $15k-30k
    PREMIUM = "premium"  # > $30k


@dataclass
class TaskTemplate:
    """
    Structured task template with variables.

    Variables are filled from UserProfile + GoalSpec to guarantee personalization.
    """
    id: str
    name: str
    category: TemplateCategory
    milestone_type: MilestoneType
    variables: List[str]
    base_template: str
    budget_tier: BudgetTier = BudgetTier.STANDARD
    timebox_minutes: int = 60
    priority: int = 2
    energy_level: str = "medium"

    def render(self, context: Dict[str, any]) -> str:
        """
        Fill template variables with user data using Jinja2.

        Args:
            context: Dictionary with variable values (now includes personalization flags)

        Returns:
            Rendered task string with all variables filled and conditional blocks evaluated

        Raises:
            KeyError: If required variable is missing from context
        """
        # Validate required variables are present (but allow extra flags for conditionals)
        missing = set(self.variables) - set(context.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        # Check if template uses Jinja2 syntax ({% or {{) or old .format() syntax ({)
        has_jinja_blocks = '{%' in self.base_template or '{{' in self.base_template
        has_format_syntax = '{' in self.base_template and '{{' not in self.base_template

        if has_jinja_blocks:
            # Use Jinja2 for rendering (supports {{ var }} and {% if %} blocks)
            template = Template(self.base_template)
            return template.render(**context)
        elif has_format_syntax:
            # Backward compatibility: old templates using {var} format
            return self.base_template.format(**context)
        else:
            # No variables, return as-is
            return self.base_template

    def get_metadata(self) -> Dict:
        """Get task metadata for database storage"""
        return {
            "timebox_minutes": self.timebox_minutes,
            "priority": self.priority,
            "energy_level": self.energy_level,
            "template_id": self.id,
            "template_category": self.category.value,
            "template_milestone_type": self.milestone_type.value,
        }


# ============================================================================
# STUDY DOMAIN TEMPLATES (20 templates)
# ============================================================================

# ----------------------------------------------------------------------------
# University Research Templates (3 variants)
# ----------------------------------------------------------------------------

UNIVERSITY_RESEARCH_BUDGET = TaskTemplate(
    id="university_research_budget",
    name="University Research (Budget-Constrained)",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.UNIVERSITY_RESEARCH,
    variables=["num_schools", "target_regions", "max_tuition", "field", "degree_level"],
    base_template="""Research {num_schools} {degree_level} programs in {target_regions} with tuition < {max_tuition}/year.

Focus on: {field} programs with strong reputation and affordable living costs.

Create spreadsheet with:
- University name, country, city
- Annual tuition (in USD)
- Application deadline
- Minimum GPA/test score requirements
- Cost of living estimate

Target: Find programs where total cost (tuition + living) < {max_tuition} × 1.5""",
    budget_tier=BudgetTier.BUDGET,
    timebox_minutes=90,
    priority=3,
    energy_level="high"
)

UNIVERSITY_RESEARCH_STANDARD = TaskTemplate(
    id="university_research_standard",
    name="University Research (Standard)",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.UNIVERSITY_RESEARCH,
    variables=["num_schools", "target_countries", "max_tuition", "field", "degree_level", "research_interest"],
    base_template="""Research {num_schools} top {degree_level} {field} programs in {target_countries} (tuition < {max_tuition}/year).

Focus on programs with:
- Strong {research_interest} research groups
- Good industry connections
- International student support

Create comparison spreadsheet:
- University, ranking, tuition
- Application requirements (GPA, test scores, documents)
- Deadlines (early vs regular)
- Scholarship opportunities
- Notable professors/labs in {research_interest}""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=120,
    priority=3,
    energy_level="high"
)

UNIVERSITY_RESEARCH_PREMIUM = TaskTemplate(
    id="university_research_premium",
    name="University Research (Top-Tier)",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.UNIVERSITY_RESEARCH,
    variables=["num_schools", "target_universities", "field", "degree_level", "research_interest"],
    base_template="""Research {num_schools} top-tier {degree_level} {field} programs: {target_universities}.

Deep dive for each:
- Admission statistics (acceptance rate, average GPA/scores)
- Research labs in {research_interest} (professors, recent publications)
- Alumni outcomes (placement, salaries)
- Unique program features
- Scholarship opportunities (merit-based, need-based)

Create detailed comparison document with pros/cons for each.""",
    budget_tier=BudgetTier.PREMIUM,
    timebox_minutes=180,
    priority=3,
    energy_level="high"
)

# ----------------------------------------------------------------------------
# IELTS/TOEFL Exam Registration (3 variants)
# ----------------------------------------------------------------------------

IELTS_REGISTRATION_BUDGET = TaskTemplate(
    id="ielts_registration_budget",
    name="IELTS Registration (Budget-Aware)",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.EXAM_PREP,
    variables=["country", "target_score", "exam_month"],
    base_template="""Register for IELTS Academic test in {country} for {exam_month} intake.

Target score: {target_score} (required for university applications)

Steps:
1. Compare test center fees in your area (prices vary $200-280)
2. Check test dates (book 2-3 months ahead for best availability)
3. Register for computer-based IELTS (results in 3-5 days, same price)
4. Keep $30 buffer for potential re-take if needed

Budget: $220-250 (one attempt)""",
    budget_tier=BudgetTier.BUDGET,
    timebox_minutes=30,
    priority=3,
    energy_level="low"
)

IELTS_PREP_WEAKNESS_WRITING = TaskTemplate(
    id="ielts_prep_weakness_writing",
    name="IELTS Writing Preparation (Weakness-Targeted)",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.EXAM_PREP,
    variables=["current_score", "target_score", "exam_date"],
    base_template="""IELTS Writing practice - target your weakest section.

Current: {current_score} → Target: {target_score} (by {exam_date})

Week 1-2 Focus:
- Complete 5 Task 2 essays (250 words, 40 min each)
- Use Cambridge IELTS Book 14-16 (free PDFs online)
- Focus on: Clear thesis, paragraphing, examples
- Self-assess using official band descriptors

Week 3-4:
- Get 3 essays reviewed (use r/IELTS or ieltsliz.com free feedback)
- Practice Task 1 (3 reports per week)
- Time yourself strictly (Task 1: 20min, Task 2: 40min)

Daily: 30-40 minutes writing practice""",
    budget_tier=BudgetTier.BUDGET,
    timebox_minutes=30,
    priority=3,
    energy_level="high"
)

IELTS_PREP_INTENSIVE = TaskTemplate(
    id="ielts_prep_intensive",
    name="IELTS Intensive Preparation (< 30 Days)",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.EXAM_PREP,
    variables=["current_score", "target_score", "days_until_exam", "weakness"],
    base_template="""URGENT: IELTS prep - {days_until_exam} days until exam.

Current: {current_score} → Target: {target_score}
Weakness: {weakness}

Daily schedule (2 hours/day):
- Hour 1: Focus on {weakness} (your weak section)
- Hour 2: Full practice tests (alternate sections daily)

Resources:
- Cambridge IELTS 14-18 (official practice tests)
- IELTS Liz website (free strategies)
- YouTube: IELTS Advantage (focused tips)

Week-by-week:
- Week 1-2: Skill building ({weakness} focus)
- Week 3: Full mock tests (one every 2 days)
- Week 4: Review mistakes, memorize vocabulary

Goal: +0.5 band improvement possible with focused effort.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=120,
    priority=3,
    energy_level="high"
)

# ----------------------------------------------------------------------------
# SOP (Statement of Purpose) Drafting (3 variants)
# ----------------------------------------------------------------------------

SOP_DRAFT_INTRO = TaskTemplate(
    id="sop_draft_intro",
    name="SOP Introduction Draft",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.APPLICATIONS,
    variables=["field", "university_name", "key_project", "research_interest"],
    base_template="""Draft SOP introduction for {university_name} {field} program.

Hook (First 2-3 sentences):
- Start with your {key_project} experience
- Connect it to your interest in {research_interest}
- Make it specific, not generic

Example structure:
"When I [specific achievement from {key_project}], I realized [insight about {research_interest}]. This experience at [your institution] sparked my determination to pursue advanced study in {field}, particularly in the area of {research_interest}."

Length: 150-200 words
Tone: Confident but humble, specific not generic

Goal: Compelling intro that shows WHY you're passionate about {research_interest}.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=60,
    priority=3,
    energy_level="high"
)

SOP_FULL_DRAFT = TaskTemplate(
    id="sop_full_draft",
    name="Complete SOP Draft",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.APPLICATIONS,
    variables=["university_name", "program_name", "field", "key_project_1", "key_project_2", "research_interest", "career_goal"],
    base_template="""Write complete SOP draft for {university_name} - {program_name}.

Structure (800-1000 words):

1. Introduction (150 words)
   - Hook with {key_project_1} experience
   - Why {research_interest}?

2. Academic Background (250 words)
   - Highlight {key_project_1} and {key_project_2}
   - Connect to {field} fundamentals
   - Show progression of interest

3. Why This Program (250 words)
   - Specific professors/labs at {university_name}
   - How program aligns with {research_interest}
   - Unique opportunities at {university_name}

4. Future Goals (200 words)
   - Short-term: Research goals during program
   - Long-term: {career_goal}
   - How degree enables this

5. Conclusion (100 words)
   - Recap fit
   - Enthusiasm for {university_name}

First draft goal: Get ideas on paper, refine later.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=180,
    priority=3,
    energy_level="high"
)

# ----------------------------------------------------------------------------
# Recommendation Letter Requests (2 variants)
# ----------------------------------------------------------------------------

RECOMMENDATION_REQUEST_PROFESSOR = TaskTemplate(
    id="recommendation_request_professor",
    name="Request Recommendation from Professor",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.APPLICATIONS,
    variables=["professor_name", "course_name", "grade_received", "university_name", "program_name", "deadline"],
    base_template="""Email {professor_name} to request recommendation letter.

Context:
- You took their {course_name} course (grade: {grade_received})
- Applying to: {university_name} - {program_name}
- Deadline: {deadline}

Email template:

Subject: Recommendation Letter Request for {university_name} Application

Dear Professor {professor_name},

I hope this email finds you well. I'm reaching out to ask if you would be willing to write a strong letter of recommendation for my application to {university_name}'s {program_name}.

I particularly enjoyed your {course_name} course, where I [mention specific project or achievement]. I believe your perspective on my analytical skills would strengthen my application.

The deadline is {deadline}. I'm happy to provide:
- My CV/transcript
- Program details
- Draft of key points to highlight

Would you be available to discuss this? I understand if your schedule doesn't permit.

Thank you for considering this request.

Best regards"

(Sign with your name)

---

Goal: Send email, follow up in 3 days if no response.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=30,
    priority=3,
    energy_level="medium"
)

# ----------------------------------------------------------------------------
# Application Submission (2 variants)
# ----------------------------------------------------------------------------

APPLICATION_SUBMISSION_EARLY = TaskTemplate(
    id="application_submission_early",
    name="Submit Early Application",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.APPLICATIONS,
    variables=["university_name", "program_name", "early_deadline", "fee", "savings_amount"],
    base_template="""Submit {university_name} {program_name} application BEFORE {early_deadline} (early deadline).

Benefits of early submission:
- Save ${savings_amount} on application fee
- 15-20% higher acceptance rate
- Priority consideration for scholarships
- Earlier admission decision

Checklist before submitting:
□ All transcripts uploaded
□ Test scores sent (IELTS/TOEFL, GRE if required)
□ SOP reviewed (no typos!)
□ Recommendation letters confirmed
□ Application fee ready: ${fee}

Double-check:
- Correct program selected (don't mix up similar programs)
- All sections complete (save as you go)
- Contact info correct (for interview invites)

Goal: Submit 7+ days before deadline to avoid technical issues.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=90,
    priority=3,
    energy_level="medium"
)

# ----------------------------------------------------------------------------
# Visa Preparation (2 variants)
# ----------------------------------------------------------------------------

VISA_PREP_DOCUMENTS = TaskTemplate(
    id="visa_prep_documents",
    name="Visa Documentation Preparation",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.VISA_PROCESS,
    variables=["country", "visa_type", "required_funds", "program_start_date"],
    base_template="""Prepare visa application documents for {country} ({visa_type}).

Required documents checklist:
□ Passport (valid 6+ months beyond {program_start_date})
□ Admission letter from university
□ Financial proof: ${required_funds} (bank statement, 6 months history)
□ Academic transcripts
□ English proficiency certificate (IELTS/TOEFL)
□ Visa application form (online)
□ Passport photos (check {country} requirements: 2x2 or different)

Financial proof tips:
- Bank statement must show consistent ${required_funds} balance
- Can combine: personal savings + sponsor letter + scholarship
- Some countries require explanation for large deposits

Next step: Book visa appointment (usually 1-2 months wait time).""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=120,
    priority=3,
    energy_level="high"
)

# ----------------------------------------------------------------------------
# Scholarship Research (2 variants)
# ----------------------------------------------------------------------------

SCHOLARSHIP_RESEARCH_BUDGET = TaskTemplate(
    id="scholarship_research_budget",
    name="Scholarship Research (Budget-Critical)",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.SCHOLARSHIPS,
    variables=["field", "degree_level", "target_countries", "funding_gap"],
    base_template="""Find scholarships to cover ${funding_gap} funding gap for {degree_level} {field}.

Target: 5 scholarships you're eligible for.

Search strategy:
1. University-specific scholarships (check each university's website)
2. Government scholarships (Chevening, DAAD, Sweden SI, etc.)
3. External scholarships (Field-specific organizations)

For each scholarship, note:
- Amount (full tuition vs partial vs stipend)
- Eligibility (GPA, nationality, field restrictions)
- Deadline
- Application requirements (essays, recommendations, interviews)
- Selection criteria (merit vs need-based)

Priority:
- Automatic consideration (no extra application)
- Need-based (if you qualify)
- Merit-based (if GPA > 3.5)

Goal: Create spreadsheet with 5 viable options.""",
    budget_tier=BudgetTier.BUDGET,
    timebox_minutes=120,
    priority=3,
    energy_level="high"
)

# ============================================================================
# CAREER DOMAIN TEMPLATES (20 templates)
# ============================================================================

# ----------------------------------------------------------------------------
# Resume Update (3 variants)
# ----------------------------------------------------------------------------

RESUME_UPDATE_ENTRY_LEVEL = TaskTemplate(
    id="resume_update_entry_level",
    name="Resume Update (Entry-Level)",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.RESUME_UPDATE,
    variables=["current_role", "target_role", "key_skill_1", "key_skill_2", "top_achievement"],
    base_template="""Update resume for {target_role} applications (from {current_role}).

Structure (1 page max):

1. Header
   - Name, email, phone, LinkedIn, GitHub/portfolio
   - One-line headline: "{current_role} → {target_role} | {key_skill_1}, {key_skill_2}"

2. Experience (reverse chronological)
   - Current role: {current_role}
   - Focus on: {top_achievement} (quantify impact)
   - Use action verbs: Built, Led, Improved, Launched
   - Format: "Achieved X by doing Y, resulting in Z"

3. Skills (relevant to {target_role})
   - Technical: {key_skill_1}, {key_skill_2}
   - Soft skills: (only if you can back them up with examples)

4. Education
   - Degree, GPA (if > 3.5), relevant coursework

Goal: Tailored resume that shows {current_role} → {target_role} progression.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=90,
    priority=3,
    energy_level="high"
)

RESUME_UPDATE_MID_LEVEL = TaskTemplate(
    id="resume_update_mid_level",
    name="Resume Update (Mid-Level, 3-5 years exp)",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.RESUME_UPDATE,
    variables=["years_experience", "current_role", "target_role", "company_1", "company_2", "top_achievement", "target_industry"],
    base_template="""Update resume for {target_role} in {target_industry} ({years_experience} years experience).

Key strategy: Show impact, not just responsibilities.

Experience section (focus here):

{company_2} | {current_role}
• {top_achievement} (THIS is your headline achievement - quantify it)
• Led [specific project] resulting in [measurable outcome]
• Improved [metric] by [percentage]

{company_1} | [Previous role]
• Focus on 2-3 most relevant achievements
• De-emphasize older/less-relevant roles

Skills:
- Only list skills you've used in last 2 years
- Match job description keywords from {target_role} postings

Remove:
- Objective statement (waste of space)
- References available upon request (obvious)
- Skills you learned 5+ years ago but don't use

Goal: 1-page resume (2 pages if 8+ years experience) optimized for ATS.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=120,
    priority=3,
    energy_level="high"
)

# ----------------------------------------------------------------------------
# LinkedIn Optimization (3 variants)
# ----------------------------------------------------------------------------

LINKEDIN_OPTIMIZATION_HEADLINE = TaskTemplate(
    id="linkedin_optimization_headline",
    name="LinkedIn Headline Optimization",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.JOB_SEARCH,
    variables=["current_role", "target_role", "key_skill_1", "key_skill_2", "target_industry"],
    base_template="""Optimize LinkedIn headline for {{ target_role }} in {{ target_industry }}.

{% if has_startup_background %}🚀 YOUR UNIQUE ADVANTAGE:
You're not just a {{ current_role }} - you're a founder with {{ startup_users }} users.

Recommended headline:
"{{ startup_role }} at {{ startup_name }} ({{ startup_users }} users) | {{ key_skill_1 }} & {{ key_skill_2 }} | Seeking {{ target_role }} roles"

This stands out because:
- Entrepreneurial mindset + execution ability (founder)
- Real traction ({{ startup_users }} proves product-market fit)
- Technical depth ({{ key_skill_1 }}, {{ key_skill_2 }})

Alternative format:
"{{ current_role }} & Founder | Built {{ startup_name }} to {{ startup_users }} users | {{ key_skill_1 }} + {{ key_skill_2 }}"
{% else %}
Current format (probably generic): "{{ current_role }} at [Company]"

Optimized format: "{{ current_role }} → {{ target_role }} | {{ key_skill_1 }} & {{ key_skill_2 }} | Open to {{ target_industry }} roles"

Examples:
- BAD: "Software Engineer at Acme Corp"
- GOOD: "Backend Engineer → Tech Lead | Python, AWS, Microservices | Open to fintech startups"

Why this works:
- Shows career direction ({{ current_role }} → {{ target_role }})
- Keywords for recruiters ({{ key_skill_1 }}, {{ key_skill_2 }})
- Signals availability ("Open to {{ target_industry }}")
{% endif %}

Character limit: 220 characters

Also update:
- Profile photo (professional, smiling, plain background)
- Banner (relevant to {{ target_industry }} - use Canva free templates)
- About section (first 2 lines visible - make them count)

Goal: 3x more profile views from recruiters.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=30,
    priority=2,
    energy_level="low"
)

LINKEDIN_ABOUT_SECTION = TaskTemplate(
    id="linkedin_about_section",
    name="LinkedIn About Section Rewrite",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.JOB_SEARCH,
    variables=["current_role", "target_role", "years_experience", "top_achievement", "target_industry", "unique_skill"],
    base_template="""Rewrite LinkedIn About section for {{ target_role }} in {{ target_industry }}.

Structure (300-400 words):

{% if has_startup_background %}HOOK (first 2 lines - visible without "see more"):
"I built {{ startup_name }} to {{ startup_users }} users as {{ startup_role }}. Now leveraging my {{ unique_skill }} and entrepreneurial mindset to drive impact as {{ target_role }} in {{ target_industry }}."

PROOF (Founder Story):
"As a founder, I've:
• Built {{ startup_name }} from 0 → {{ startup_users }} users ({{ startup_description }})
• {{ top_achievement }}
• Led product, engineering, and growth across {{ years_experience }}+ years

This taught me:
- How to ship fast and iterate based on user feedback
- How to build scalable systems under resource constraints
- How to wear multiple hats and solve ambiguous problems"

WHAT I'M LOOKING FOR:
"I'm exploring {{ target_role }} opportunities where my founder experience creates unique value. Ideal for roles requiring:
- 0→1 product building
- Ambiguous problem-solving
- Cross-functional leadership
- Startup mentality in {{ target_industry }}"
{% else %}HOOK (first 2 lines - visible without "see more"):
"I help [companies/teams] [achieve specific outcome] through {{ unique_skill }}. Currently {{ current_role }}, seeking {{ target_role }} roles in {{ target_industry }}."

PROOF:
"Over {{ years_experience }} years, I've:
• {{ top_achievement }} (quantified result)
• [Second achievement]
• [Third achievement]"

WHAT I'M LOOKING FOR:
"I'm exploring {{ target_role }} opportunities where I can [specific value you bring]. Particularly interested in {{ target_industry }} companies that [your values/culture fit]."
{% endif %}

CALL TO ACTION:
"Open to: {{ target_role }} roles, consulting projects, collaborations
Let's connect: [your email]"

Writing tips:
- Use "I" not "He/She" (first person)
- Short paragraphs (mobile-friendly)
- Bullet points for scannability
- Keywords: {{ target_role }}, {{ target_industry }}, {{ unique_skill }}

Goal: Compelling About section that converts profile views → messages.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=60,
    priority=2,
    energy_level="high"
)

# ----------------------------------------------------------------------------
# Job Applications (3 variants)
# ----------------------------------------------------------------------------

JOB_APPLICATION_TARGETED = TaskTemplate(
    id="job_application_targeted",
    name="Targeted Job Application (Referral/Dream Company)",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.JOB_SEARCH,
    variables=["company_name", "role_title", "referral_name", "key_qualification", "why_company"],
    base_template="""Apply to {role_title} at {company_name} (via {referral_name} referral).

Pre-application research (30 min):
- Read job description 3 times, highlight keywords
- Research hiring manager on LinkedIn
- Find company's recent news/product launches
- Identify how you fit their needs

Application steps:

1. Resume (tailored):
   - Match keywords from JD in your experience section
   - Emphasize {key_qualification} (they specifically want this)

2. Cover letter (250 words):
   - Para 1: Why {company_name}? ({why_company})
   - Para 2: Your {key_qualification} + relevant achievement
   - Para 3: Referral mention ("{referral_name} suggested I'd be a great fit")

3. Referral process:
   - Message {referral_name}: "Thanks for offering to refer me. I've applied via [link]. My application ID is [X]. Could you submit the referral?"
   - Follow up in 3 days if no response

4. Follow-up:
   - Connect with hiring manager on LinkedIn (personalized note)
   - Wait 7-10 days, then polite follow-up email

Success rate with referral: 30-40% interview rate (vs 2-5% cold apply).""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=90,
    priority=3,
    energy_level="high"
)

JOB_APPLICATION_VOLUME = TaskTemplate(
    id="job_application_volume",
    name="Volume Job Applications (5-10 applications)",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.JOB_SEARCH,
    variables=["target_role", "target_companies", "applications_target"],
    base_template="""Apply to {applications_target} {target_role} positions at: {target_companies}.

Batch application strategy (optimize for volume + quality):

1. Resume template:
   - One master resume optimized for {target_role}
   - Tweak only headline + top 2 bullets per application (10 min each)

2. Cover letter template:
   - Generic paragraphs 1 and 3
   - Customize only paragraph 2 (company-specific) per application

3. Application tracker:
   - Spreadsheet: Company, Role, Date Applied, Link, Status
   - Set reminders: Follow up after 7 days if no response

4. Daily quota:
   - {applications_target} applications over 3 days
   - Morning session: Research + customize (2 hours)
   - Evening session: Submit applications (1 hour)

Efficiency tips:
- Use job board filters to find exact matches
- Save cover letter templates in Google Docs
- Use LinkedIn Easy Apply for volume (lower success rate but fast)

Goal: {applications_target} quality applications submitted by end of week.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=180,
    priority=2,
    energy_level="medium"
)

# ----------------------------------------------------------------------------
# Networking (3 variants)
# ----------------------------------------------------------------------------

NETWORKING_WARM_INTRO = TaskTemplate(
    id="networking_warm_intro",
    name="Networking via Warm Introduction",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.NETWORKING,
    variables=["contact_name", "contact_company", "mutual_connection", "purpose"],
    base_template="""Reach out to {contact_name} ({contact_company}) via {mutual_connection} intro.

Step 1: Ask {mutual_connection} for introduction
Message template:
"Hey {mutual_connection}, hope you're well! I'm exploring {purpose} and noticed you know {contact_name} at {contact_company}. Would you be comfortable introducing us? I'd love to learn about their experience with [relevant topic]. No pressure if timing isn't right!"

Step 2: After intro, email {contact_name} (within 24 hours):
Subject: Quick intro from {mutual_connection} - {purpose}

"Hi {contact_name},

Thanks to {mutual_connection} for the intro! I'm currently {purpose} and am impressed by {contact_company}'s work on [specific project/product].

Would you have 15-20 minutes for a quick call? I'd love to learn about [specific topic related to your goal].

I'm flexible on timing - happy to work around your schedule.

Best,
(Your name here)"

Step 3: After call, follow up:
- Thank you email within 24 hours
- Connect on LinkedIn
- Share useful resource (article/tool they might like)

Goal: Build relationship, not just extract information.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=45,
    priority=2,
    energy_level="medium"
)

NETWORKING_COLD_OUTREACH = TaskTemplate(
    id="networking_cold_outreach",
    name="Cold LinkedIn Outreach (Alumni/Industry)",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.NETWORKING,
    variables=["target_role", "target_industry", "common_ground", "num_people", "university"],
    base_template="""Cold outreach to {num_people} {target_role} professionals in {target_industry}.

Who to target:
- Alumni from your university in {target_role}
- People who transitioned from similar role as yours
- Professionals at companies you're interested in
- Shared connection: {common_ground}

LinkedIn message template (keep under 300 characters):
"Hi [Name], fellow [university] alum here! I'm exploring {target_role} roles in {target_industry} and really admire your career path. Would you have 15 min to share advice on making this transition? Happy to work around your schedule."

Key elements:
- Common ground first ({common_ground}, {university})
- Specific ask (15 min, advice on transition)
- Make it easy (flexible timing)
- No resume/job ask (just learning)

Response rate: ~20-30% for alumni, ~10-15% for cold outreach

After response:
- Schedule 15-20 min call
- Prepare 3-5 specific questions
- Send thank you + connect on LinkedIn

Goal: {num_people} messages sent, 3-5 responses expected.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=60,
    priority=2,
    energy_level="medium"
)

# ----------------------------------------------------------------------------
# Skill Building (3 variants)
# ----------------------------------------------------------------------------

SKILL_BUILDING_TARGETED_WEAKNESS = TaskTemplate(
    id="skill_building_targeted_weakness",
    name="Skill Building (Targeted Weakness)",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.SKILL_BUILDING,
    variables=["skill_gap", "target_role", "learning_resource", "time_commitment_hours"],
    base_template="""Build {skill_gap} proficiency for {target_role} applications.

Current gap: {target_role} job descriptions frequently require {skill_gap}, which you lack.

Learning plan ({time_commitment_hours} hours over 4 weeks):

Week 1-2: Fundamentals
- Resource: {learning_resource} (free/paid course)
- Goal: Understand core concepts
- Time: {time_commitment_hours}/2 hours/week

Week 3-4: Hands-on practice
- Build small project using {skill_gap}
- Document on GitHub/portfolio
- Goal: Demonstrable proof of skill

Outcome to claim on resume:
"Developed {skill_gap} proficiency through [project name]: [brief description of what you built]"

Success criteria:
- Can discuss {skill_gap} in interview
- Have portfolio piece showing {skill_gap}
- Update LinkedIn skills section

Note: You don't need expert-level, just "working knowledge" for most roles.""",
    budget_tier=BudgetTier.BUDGET,
    timebox_minutes=60,
    priority=2,
    energy_level="high"
)

# ----------------------------------------------------------------------------
# Interview Prep (3 variants)
# ----------------------------------------------------------------------------

INTERVIEW_PREP_BEHAVIORAL = TaskTemplate(
    id="interview_prep_behavioral",
    name="Behavioral Interview Preparation",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.INTERVIEW_PREP,
    variables=["company_name", "role_title", "top_achievement", "challenge_story"],
    base_template="""Prepare behavioral interview answers for {role_title} at {company_name}.

Use STAR method (Situation, Task, Action, Result):

1. Top achievement story ({top_achievement}):
   - Situation: What was the context?
   - Task: What needed to be done?
   - Action: What did YOU specifically do?
   - Result: Quantified outcome

2. Challenge/conflict story ({challenge_story}):
   - Situation: Describe the challenge
   - Task: Your responsibility
   - Action: How you handled it
   - Result: Resolution + lesson learned

3. Common questions to prepare:
   - "Tell me about yourself" (2-minute pitch)
   - "Why {company_name}?" (research their recent work)
   - "Why this role?" (connect your experience to {role_title})
   - "Where do you see yourself in 5 years?"
   - "Tell me about a time you failed"

Practice:
- Record yourself answering (check for filler words: um, like, you know)
- Time yourself (answers should be 1-3 minutes)
- Practice with friend/mentor

Goal: 5-7 polished stories covering common behavioral themes.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=90,
    priority=3,
    energy_level="high"
)

# ----------------------------------------------------------------------------
# Additional Study Templates (8 templates)
# ----------------------------------------------------------------------------

# SOP Drafting - Additional variant
SOP_DRAFT_WEAKNESS_FOCUSED = TaskTemplate(
    id="sop_draft_weakness_focused",
    name="SOP Draft (Address Weakness)",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.SOP_DRAFTING,
    variables=["field", "degree_level", "target_university", "weakness", "how_improved"],
    base_template="""Draft Statement of Purpose for {{ degree_level }} {{ field }} at {{ target_university }}.

{% if gpa_needs_compensation %}💡 GPA COMPENSATION STRATEGY:
Your GPA ({{ gpa_raw }}) is below average, BUT you have strong compensating factors.

{% if has_startup_background %}🚀 FOUNDER ADVANTAGE:
Lead with your startup achievement in paragraph 1:
"While my GPA of {{ gpa_raw }} reflects the demands of building {{ startup_name }} ({{ startup_users }} users) alongside my studies, this experience gave me practical {{ field }} skills that classroom learning alone cannot provide."

Structure:
1. Opening: Lead with {{ startup_name }} - "As {{ startup_role }} of {{ startup_name }}, I..."
2. Startup Experience:
   - What you built: {{ startup_description }}
   - Scale achieved: {{ startup_users }} users
   - Technical challenges solved (directly relevant to {{ field }})
3. Academic Context:
   - Acknowledge GPA: "Balancing startup with coursework"
   - Highlight strong grades in {{ field }}-specific courses
   - Emphasize practical application over theoretical grades
4. Why Graduate School Now:
   - Startup taught you what you DON'T know
   - Need structured learning in [specific area]
   - {{ target_university }}'s program fills these gaps
5. Future: Combine founder mindset + academic rigor

Key Message: "I chose to build something real over optimizing grades. Now I want both."
{% elif has_notable_achievements %}📊 ACHIEVEMENT-BASED COMPENSATION:
Your notable achievements compensate for GPA:

Structure:
1. Opening: Lead with your strongest achievement
2. Academic Journey: Acknowledge GPA, explain context (work, family, etc.)
3. Evidence of Capability:
   - Professional achievements that demonstrate {{ field }} skills
   - Self-directed learning and certifications
   - Real-world projects beyond classroom
4. Why {{ target_university }}: Their program aligns with your practical experience
5. Future: How you'll excel with focused academic environment
{% endif %}
{% else %}Address academic weakness upfront: {{ weakness }}

Structure:
1. Opening: Your research interest in {{ field }} (1 paragraph)
2. Academic background: Highlight strengths, contextualize {{ weakness }}
3. Address weakness: "{{ how_improved }}" - show growth trajectory
4. Why this program: Connect your goals to {{ target_university }}'s strengths
5. Future goals: How degree advances your career
{% endif %}

Length: 800-1000 words
Tone: Confident but honest about growth areas

Key: Turn weakness into story of resilience and learning.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=120,
    priority=3,
    energy_level="high"
)

# Application Tracking
APPLICATION_TRACKING_SETUP = TaskTemplate(
    id="application_tracking_setup",
    name="Application Tracking Setup",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.APPLICATIONS,
    variables=["num_schools", "deadline_earliest"],
    base_template="""Set up application tracking system for {num_schools} university applications.

Create spreadsheet with columns:
- University name
- Program name
- Application deadline (earliest: {deadline_earliest})
- Status (Not Started / In Progress / Submitted / Decision Received)
- Required documents checklist
- Application fee
- Portal login credentials
- Notes

Add conditional formatting:
- Red: Deadline < 2 weeks
- Yellow: Deadline < 1 month
- Green: Submitted

Set calendar reminders:
- 2 weeks before each deadline
- 1 week before each deadline

Goal: Never miss a deadline, track progress at a glance.""",
    budget_tier=BudgetTier.BUDGET,
    timebox_minutes=45,
    priority=2,
    energy_level="medium"
)

# Portfolio Preparation for Applications
PORTFOLIO_PREPARATION = TaskTemplate(
    id="portfolio_preparation",
    name="Portfolio/CV Preparation for Applications",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.APPLICATIONS,
    variables=["field", "top_projects", "skills"],
    base_template="""Prepare academic portfolio/CV for {field} applications.

Compile:
1. Academic projects: {top_projects}
   - Brief description (2-3 sentences each)
   - Technologies/methods used
   - Results/outcomes (quantified if possible)

2. Technical skills: {skills}
   - Programming languages
   - Tools/frameworks
   - Research methods

3. Publications/presentations (if any)
   - Conference papers
   - Journal articles
   - Posters/presentations

4. Awards/honors
   - Scholarships
   - Competition wins
   - Dean's list

Format:
- PDF, max 2 pages
- Clean, academic template
- Proofread (zero typos)

Goal: Showcase your best work in {field}.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=90,
    priority=2,
    energy_level="high"
)

# Scholarship Essay
SCHOLARSHIP_ESSAY_DRAFT = TaskTemplate(
    id="scholarship_essay_draft",
    name="Scholarship Essay Draft",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.SCHOLARSHIPS,
    variables=["scholarship_name", "essay_topic", "field", "financial_need"],
    base_template="""Draft scholarship essay for {scholarship_name}.

Topic: {essay_topic}

Structure:
1. Hook: Personal story showing passion for {field}
2. Academic journey: Your path to this point
3. Financial context: {financial_need} (be specific but dignified)
4. Future impact: How scholarship enables your goals
5. Contribution: What you'll bring to community

Key points:
- Show, don't tell (use specific examples)
- Connect financial need to opportunity
- Demonstrate you'll make most of scholarship
- Express gratitude and responsibility

Length: Follow exact word limit in prompt
Tone: Genuine, humble, forward-looking

Goal: Stand out through authenticity and clear vision.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=120,
    priority=3,
    energy_level="high"
)

# English Proficiency Test Strategy
TEST_PREP_STRATEGY = TaskTemplate(
    id="test_prep_strategy",
    name="Test Prep Strategy Plan",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.EXAM_PREP,
    variables=["test_name", "current_score", "target_score", "weeks_until_test", "weakness_section"],
    base_template="""Create {test_name} prep strategy to improve from {current_score} to {target_score} in {weeks_until_test} weeks.

Current assessment:
- Overall: {current_score}
- Weakness: {weakness_section}

Study plan:
Week 1-2: Diagnostic
- Take 2 full practice tests
- Identify specific error patterns in {weakness_section}
- Review fundamentals

Week 3-{weeks_until_test}: Targeted practice
- {weakness_section}: 60% of study time
- Other sections: 40% of study time
- Daily: 1-2 hours minimum
- Weekly: 1 full practice test

Resources needed:
- Official {test_name} practice tests
- {weakness_section} focused materials
- Vocabulary flashcards (if applicable)

Target: +0.5 to +1.0 improvement per month with consistent practice.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=60,
    priority=2,
    energy_level="medium"
)

# Visa Document Checklist
VISA_DOCUMENT_CHECKLIST = TaskTemplate(
    id="visa_document_checklist",
    name="Visa Document Checklist",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.VISA_PROCESS,
    variables=["country", "visa_type", "financial_proof_amount"],
    base_template="""Create {visa_type} visa document checklist for {country}.

Required documents (typical):
1. Valid passport (6+ months validity)
2. University acceptance letter
3. Financial proof: {financial_proof_amount}
   - Bank statements (last 6 months)
   - Scholarship letters
   - Sponsor letters (if applicable)
4. Academic transcripts + certificates
5. English proficiency test results
6. Visa application form (completed)
7. Passport photos (check exact specifications)
8. Health insurance proof
9. Accommodation proof
10. Visa fee payment receipt

Next steps:
- Verify exact requirements on official {country} visa website
- Note country-specific variations
- Schedule visa appointment (can take 4-8 weeks)
- Prepare interview questions (if required)

Organize:
- Create folder with all documents
- Make 2 copies of everything
- Digital backup (scan all documents)

Timeline: Start 3 months before departure.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=60,
    priority=3,
    energy_level="medium"
)

# University Email Outreach
PROFESSOR_OUTREACH_RESEARCH = TaskTemplate(
    id="professor_outreach_research",
    name="Professor Outreach for Research Interest",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.UNIVERSITY_RESEARCH,
    variables=["professor_name", "university_name", "research_area", "your_background"],
    base_template="""Draft email to Professor {professor_name} at {university_name} about {research_area}.

Email structure:
Subject: Prospective graduate student - Interest in {research_area} research

Body:
1. Introduction (2 sentences):
   - Your name, background: {your_background}
   - Applying to [program] at {university_name}

2. Specific interest (3-4 sentences):
   - Read their paper: [specific paper title]
   - What interested you about their {research_area} work
   - Your related experience/projects

3. Question (1-2 sentences):
   - Are they accepting graduate students for [year]?
   - Would they be willing to discuss research fit?

4. Closing:
   - Thank you
   - Attach CV

Key rules:
- Keep under 150 words
- Demonstrate you read their work (cite specific paper)
- Don't ask them to review your application
- Professional but not overly formal

Goal: Start conversation, show genuine interest.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=45,
    priority=2,
    energy_level="medium"
)

# Financial Aid Application
FINANCIAL_AID_APPLICATION = TaskTemplate(
    id="financial_aid_application",
    name="Financial Aid Application",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.SCHOLARSHIPS,
    variables=["university_name", "total_cost", "family_contribution", "gap_amount"],
    base_template="""Complete financial aid application for {university_name}.

Financial breakdown:
- Total cost: {total_cost}
- Family contribution: {family_contribution}
- Gap: {gap_amount}

Application components:
1. FAFSA/financial aid form (if required)
2. CSS Profile (for some universities)
3. Tax returns (yours + parents if dependent)
4. Bank statements
5. Financial aid essay explaining need

Essay tips:
- Be specific about {gap_amount}
- Explain what prevents family from covering
- Show you've explored other options (scholarships, part-time work)
- Emphasize commitment to making investment worthwhile

Supporting documents:
- Any special circumstances (medical bills, job loss, siblings in college)
- Letters from employers/sponsors

Submit: Before priority deadline for maximum aid consideration.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=90,
    priority=3,
    energy_level="high"
)

# ----------------------------------------------------------------------------
# Additional Career Templates (10 templates)
# ----------------------------------------------------------------------------

# Cover Letter Template
COVER_LETTER_TARGETED = TaskTemplate(
    id="cover_letter_targeted",
    name="Targeted Cover Letter",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.JOB_APPLICATIONS,
    variables=["company_name", "role_title", "key_requirement", "relevant_achievement"],
    base_template="""Write targeted cover letter for {role_title} at {company_name}.

Structure (max 3 paragraphs):

Paragraph 1 - Hook:
"I'm applying for {role_title} at {company_name}. Your recent [specific company achievement/news] aligns with my passion for [relevant area]."

Paragraph 2 - Fit:
"You're looking for {key_requirement}. In my current role, {relevant_achievement} demonstrates this exact skill. [Add 1-2 more specific examples matching other job requirements]."

Paragraph 3 - Closing:
"I'm excited to bring this experience to {company_name}. I'd welcome the opportunity to discuss how I can contribute to [specific team/project]."

Rules:
- Keep to 250 words max
- No generic statements
- Every sentence references specific job requirement or company detail
- Show enthusiasm for company, not just any job

Goal: Prove you read the job description and researched company.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=45,
    priority=2,
    energy_level="medium"
)

# LinkedIn Content Creation
LINKEDIN_CONTENT_STRATEGY = TaskTemplate(
    id="linkedin_content_strategy",
    name="LinkedIn Content Strategy",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.LINKEDIN_OPTIMIZATION,
    variables=["target_role", "expertise_area", "current_role"],
    base_template="""Create LinkedIn content strategy to build visibility for {target_role} roles.

Content themes (post 2-3x per week):
1. Industry insights about {expertise_area}
2. Lessons learned in {current_role}
3. Career tips for aspiring {target_role}s
4. Commentary on industry news

Post formats:
- Text posts (fastest engagement)
- Carousels (educational content)
- Document posts (guides/templates)
- Polls (spark conversation)

Engagement tactics:
- Comment on 5-10 posts daily in your feed
- Tag relevant people (don't spam)
- Reply to all comments on your posts

Content calendar (4 weeks):
Week 1: Introduction post - "My journey to {current_role}"
Week 2: Educational post - "3 things I learned about {expertise_area}"
Week 3: Industry commentary on recent news
Week 4: Career advice post

Goal: Become known for {expertise_area} expertise in your network.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=90,
    priority=2,
    energy_level="high"
)

# Job Search Automation Setup
JOB_SEARCH_AUTOMATION = TaskTemplate(
    id="job_search_automation",
    name="Job Search Automation Setup",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.JOB_SEARCH,
    variables=["target_role", "target_companies", "location"],
    base_template="""Set up job search automation for {target_role} roles.

Job alerts (set up on each platform):
1. LinkedIn:
   - Search: "{target_role}" + "{location}"
   - Companies: {target_companies}
   - Posted: Last 24 hours
   - Alert: Daily email

2. Indeed/Glassdoor/Google Jobs:
   - Same search criteria
   - Daily alerts

3. Company career pages:
   - {target_companies} - check weekly
   - Subscribe to job alerts on each

Tracking spreadsheet columns:
- Company, role, link
- Date posted, date applied
- Status (Saved / Applied / Interview / Offer / Rejected)
- Notes

Daily routine (15-20 minutes):
- Check alerts
- Apply to 2-3 roles
- Update tracking sheet

Goal: Never miss relevant job posting, apply quickly (within 48 hours).""",
    budget_tier=BudgetTier.BUDGET,
    timebox_minutes=60,
    priority=2,
    energy_level="medium"
)

# Networking Event Preparation
NETWORKING_EVENT_PREP = TaskTemplate(
    id="networking_event_prep",
    name="Networking Event Preparation",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.NETWORKING,
    variables=["event_name", "target_companies", "elevator_pitch"],
    base_template="""Prepare for {event_name} networking event.

Pre-event research:
1. Review attendee list (if available)
2. Identify people from {target_companies}
3. Look up their LinkedIn profiles
4. Find conversation starters (recent posts, shared interests)

Elevator pitch (practice this):
"{elevator_pitch}"
- Keep to 30 seconds
- Include: role, expertise, what you're looking for
- End with question to start conversation

Questions to ask:
- "What are you working on right now?"
- "What's the biggest challenge in [their role]?"
- "How did you get into [their industry]?"
- "Any advice for someone looking to transition to [target role]?"

Materials:
- Business cards (or digital equivalent)
- LinkedIn app ready (for quick connections)
- Notebook for jotting down notes

Follow-up plan:
- Connect on LinkedIn within 24 hours
- Personalized message: "Great chatting about [specific topic]"
- Suggest coffee chat if strong connection

Goal: 5-10 meaningful conversations, 3-5 LinkedIn connections.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=60,
    priority=2,
    energy_level="medium"
)

# Portfolio Website Setup
PORTFOLIO_WEBSITE_SETUP = TaskTemplate(
    id="portfolio_website_setup",
    name="Portfolio Website Setup",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.SKILL_BUILDING,
    variables=["role_type", "top_projects", "domain_name"],
    base_template="""Create portfolio website for {role_type} applications: {domain_name}

Platform options (pick based on budget):
- Budget: GitHub Pages (free) + Jekyll template
- Standard: Wix/Squarespace ($10-15/month)
- Custom: Buy domain + host ($50-100/year)

Website structure:
1. Home: Brief intro + photo
   - "I'm a {role_type} specializing in [expertise]"
   - Professional headshot

2. Projects: {top_projects}
   - Title, description, technologies
   - Screenshots/demos
   - GitHub links (if applicable)
   - Impact/results

3. About: Your story
   - Background
   - Skills
   - What you're looking for

4. Contact: Email + LinkedIn

Design tips:
- Keep it simple (less is more)
- Mobile-friendly
- Fast loading
- No spelling/grammar errors

Add to:
- Resume header
- LinkedIn about section
- Email signature

Goal: Professional online presence showcasing your best work.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=120,
    priority=2,
    energy_level="high"
)

# Informational Interview Request
INFORMATIONAL_INTERVIEW_REQUEST = TaskTemplate(
    id="informational_interview_request",
    name="Informational Interview Request",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.NETWORKING,
    variables=["contact_name", "company_name", "role_title", "connection_point"],
    base_template="""Draft informational interview request to {contact_name} at {company_name}.

Email structure:
Subject: Quick question about {role_title} at {company_name}

Hi {contact_name},

[Connection point]: {connection_point}
(e.g., "I found you through the Stanford alumni network" or "I saw your post about [topic]")

I'm exploring opportunities in [industry/role type], and your experience as {role_title} at {company_name} caught my attention.

Would you be open to a 15-20 minute call? I'd love to learn about:
- Your path to {role_title}
- What you wish you knew when starting
- Advice for someone looking to transition to [target role]

I know you're busy - happy to work around your schedule or do this over email if that's easier.

Thank you for considering!
(Your name here)

Follow-up (if no response in 1 week):
- Brief bump: "Following up on my email below - still interested if you have time!"

During call:
- Be on time, prepared with questions
- Take notes
- Ask: "Is there anyone else you'd recommend I speak with?"
- Thank them, ask to stay in touch

Goal: Learn insider perspective, build relationship.""",
    budget_tier=BudgetTier.BUDGET,
    timebox_minutes=30,
    priority=2,
    energy_level="low"
)

# Salary Negotiation Preparation
SALARY_NEGOTIATION_PREP = TaskTemplate(
    id="salary_negotiation_prep",
    name="Salary Negotiation Preparation",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.INTERVIEW_PREP,
    variables=["role_title", "market_rate", "your_target", "unique_value"],
    base_template="""Prepare salary negotiation for {role_title} offer.

Market research:
- Industry average: {market_rate}
- Your target: {your_target}
- Justification: {unique_value}

Compensation components to negotiate:
1. Base salary (most important)
2. Signing bonus
3. Stock options/equity
4. Annual bonus
5. Benefits (health, 401k match, PTO)
6. Remote work flexibility
7. Professional development budget
8. Start date (can buy time)

Negotiation script:
"Thank you for the offer! I'm excited about the role. Based on my research and [unique value proposition], I was hoping for a base salary of {your_target}. Is there flexibility here?"

If they say no:
"I understand. Are there other components we can adjust? For example, [signing bonus/additional PTO/remote days]?"

Don't:
- Accept first offer immediately (shows you didn't do research)
- Lie about competing offers
- Be aggressive or demanding

Do:
- Express enthusiasm for role
- Use market data, not personal needs
- Be willing to compromise on non-salary items

Goal: 10-20% increase from first offer is realistic.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=60,
    priority=3,
    energy_level="high"
)

# Skills Gap Analysis
SKILLS_GAP_ANALYSIS = TaskTemplate(
    id="skills_gap_analysis",
    name="Skills Gap Analysis for Target Role",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.SKILL_BUILDING,
    variables=["current_role", "target_role", "current_skills"],
    base_template="""Analyze skills gap between {current_role} and {target_role}.

Step 1: Research target role requirements
- Review 10 job postings for {target_role}
- List all required skills mentioned
- Note which skills appear most frequently (80%+ of postings)

Step 2: Self-assessment of {current_skills}
Rate yourself on each required skill (1-5):
- 1: No experience
- 2: Basic understanding
- 3: Can do with guidance
- 4: Can do independently
- 5: Can teach others

Step 3: Identify gaps
- Critical gaps: Skills rated 1-2 that appear in 80%+ of postings
- Nice-to-have gaps: Skills rated 1-2 in <50% of postings

Step 4: Learning plan (focus on top 3 critical gaps)
For each gap:
- Resource (course/book/project)
- Timeline (2-4 weeks per skill)
- Proof of learning (project/certification)

Step 5: Update resume/LinkedIn
- Add "Currently learning: [skills]"
- Shows initiative, addresses gap

Goal: Bridge critical gaps within 3 months.""",
    budget_tier=BudgetTier.BUDGET,
    timebox_minutes=90,
    priority=2,
    energy_level="high"
)

# Personal Brand Audit
PERSONAL_BRAND_AUDIT = TaskTemplate(
    id="personal_brand_audit",
    name="Personal Brand Audit",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.LINKEDIN_OPTIMIZATION,
    variables=["target_role", "current_online_presence"],
    base_template="""Audit online presence for {target_role} job search.

Google yourself:
- Search: (Your name here) + [City/Company]
- What shows up in first page?
- Any red flags to address?

LinkedIn audit:
- Profile photo: Professional? Recent?
- Headline: Does it mention {target_role} or target skills?
- About: Tells your story? Includes keywords?
- Experience: Quantified achievements?
- Recommendations: Have 3-5 recent ones?

Resume audit:
- Tailored to {target_role}?
- ATS-friendly (keywords from job descriptions)?
- Quantified results? (numbers, %, $)
- Max 2 pages?

Social media cleanup:
- Twitter/X: Professional tone?
- Instagram: Set to private if personal
- Facebook: Privacy settings locked down
- Remove any controversial posts

Online portfolio/GitHub:
- {current_online_presence}
- Up to date?
- Showcases best work?

Action items (prioritize top 3):
1. [Issue with highest impact]
2. [Quick win]
3. [Long-term improvement]

Goal: Control narrative, remove red flags, highlight strengths.""",
    budget_tier=BudgetTier.BUDGET,
    timebox_minutes=75,
    priority=2,
    energy_level="medium"
)

# Technical Interview Practice
TECHNICAL_INTERVIEW_PRACTICE = TaskTemplate(
    id="technical_interview_practice",
    name="Technical Interview Practice Plan",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.INTERVIEW_PREP,
    variables=["role_title", "key_technical_skill", "company_name"],
    base_template="""Prepare for technical interview at {company_name} for {role_title}.

Interview format research:
- Check Glassdoor for {company_name} interview questions
- Ask recruiter about interview format
- Common types: coding, system design, case study, take-home

{key_technical_skill} practice plan:
Week 1-2: Fundamentals review
- Core concepts in {key_technical_skill}
- Common patterns/algorithms
- Refresh on best practices

Week 3-4: Practice problems
- LeetCode/HackerRank (if coding)
- Case studies (if consulting/PM)
- System design questions (if senior role)
- Practice 1-2 problems daily

Practice structure:
1. Explain approach out loud (before coding)
2. Write solution
3. Test with edge cases
4. Optimize time/space complexity
5. Explain trade-offs

Mock interviews:
- Schedule 2-3 with friends/mentors
- Use Pramp/interviewing.io
- Record yourself (check clarity)

Day before:
- Review your solutions
- Get good sleep
- Prepare questions for interviewer

Day of:
- Test tech setup (if virtual)
- Have paper/pen ready
- Arrive/login 5 minutes early

Goal: Confidence in explaining thought process.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=120,
    priority=3,
    energy_level="high"
)

# ----------------------------------------------------------------------------
# Context-Aware Template Variants (10 templates)
# ----------------------------------------------------------------------------

# Professor Outreach with Research Interest
PROFESSOR_OUTREACH_RESEARCH_FOCUSED = TaskTemplate(
    id="professor_outreach_research_focused",
    name="Professor Outreach (Research-Focused)",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.UNIVERSITY_RESEARCH,
    variables=["professor_name", "university_name", "research_interest", "top_projects", "current_university"],
    base_template="""Draft email to Professor {professor_name} at {university_name} about {research_interest}.

Email structure:
Subject: Prospective PhD student - Interest in {research_interest} research

Dear Professor {professor_name},

I'm currently completing my degree at {current_university} and am applying to the PhD program at {university_name}.

I've been following your work on {research_interest}, particularly [cite specific recent paper]. Your approach resonates with my research on {top_projects}.

During my undergraduate work, I developed {top_projects}, which gave me hands-on experience in {research_interest}. I'm excited about the possibility of contributing to your lab's work.

Would you be accepting PhD students for [Fall 2026]? I'd welcome the opportunity to discuss potential research fit.

I've attached my CV and would be happy to share my research portfolio.

Best regards,
(Your name here)

Key: Demonstrate genuine research interest with specific examples.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=60,
    priority=3,
    energy_level="high"
)

# Networking with Warm Introduction
NETWORKING_WARM_INTRO_LEVERAGED = TaskTemplate(
    id="networking_warm_intro_leveraged",
    name="Networking via Warm Introduction",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.NETWORKING,
    variables=["warm_intros", "target_role", "target_companies", "connection_point"],
    base_template="""Reach out to warm introduction for {target_role} opportunities.

Warm intro available: {warm_intros}

Message structure:

"Hi [Contact Name],

{connection_point} - I hope this message finds you well.

I'm currently exploring {target_role} opportunities at {target_companies}, and I noticed you have experience in this space.

Would you be open to a brief 15-minute call? I'd love to learn about:
- Your transition to {target_role}
- What you wish you knew when starting
- Any advice for someone making a similar move

I understand you're busy - happy to work around your schedule or keep this to email if that's easier.

Thank you for considering!
(Your name here)"

Follow-up:
- Send within 24 hours of getting intro
- Mention mutual connection explicitly
- Keep ask small and specific
- Offer flexibility on format

Goal: Convert warm intro to informational interview.""",
    budget_tier=BudgetTier.BUDGET,
    timebox_minutes=30,
    priority=2,
    energy_level="low"
)

# Resume Update with Company-Specific Focus
RESUME_UPDATE_COMPANY_TARGETED = TaskTemplate(
    id="resume_update_company_targeted",
    name="Resume Update (Company-Targeted)",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.RESUME_UPDATE,
    variables=["target_role", "target_companies", "top_achievement", "companies_worked", "top_skills"],
    base_template="""Tailor resume for {target_role} applications at {target_companies}.

Your background: {companies_worked}
Key strength: {top_achievement}

Target company research:
1. Visit {target_companies} careers page
2. Find 3-5 {target_role} job postings
3. Extract common keywords (skills, responsibilities, qualifications)
4. Note company values/culture from job descriptions

Resume updates:
1. Professional Summary:
   - Lead with: "{top_achievement}"
   - Include keywords from target company postings
   - Mention {top_skills} explicitly

2. Work Experience:
   - Rewrite bullets to mirror target company language
   - Quantify impact (%, $, time saved)
   - Highlight experience at {companies_worked}

3. Skills Section:
   - Match exact wording from job descriptions
   - List {top_skills} prominently
   - Remove outdated/irrelevant skills

4. Projects/Achievements:
   - Feature work similar to target company challenges
   - Use company-specific terminology

ATS Optimization:
- Match 70%+ of keywords from job description
- Use standard section headers
- Avoid tables, columns, graphics

Goal: Pass ATS and show you understand company needs.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=90,
    priority=3,
    energy_level="high"
)

# Interview Prep with Company Research
INTERVIEW_PREP_COMPANY_RESEARCH = TaskTemplate(
    id="interview_prep_company_research",
    name="Interview Prep (Company-Specific)",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.INTERVIEW_PREP,
    variables=["company_name", "target_role", "top_achievement", "challenge_story", "expertise_area"],
    base_template="""Prepare for {target_role} interview at {company_name}.

Company research (2 hours):
1. Recent news (last 3 months):
   - Product launches, acquisitions, funding
   - Leadership changes
   - Industry challenges

2. Company culture:
   - Values (from website/Glassdoor)
   - Interview format (from Glassdoor)
   - Team structure

3. Interviewer research:
   - LinkedIn background
   - Recent posts/articles
   - Shared connections/interests

Behavioral stories (STAR method):
1. Top achievement: {top_achievement}
   - Situation: [Context]
   - Task: [What needed to be done]
   - Action: [Your specific actions using {expertise_area}]
   - Result: [Quantified outcome]

2. Challenge: {challenge_story}
   - Situation: [The challenge]
   - Task: [Your responsibility]
   - Action: [How you resolved it]
   - Result: [Lesson learned + outcome]

3. "Tell me about yourself" (2-minute pitch):
   - Background in {expertise_area}
   - Why {target_role} at {company_name}
   - What you'll bring to role

Questions for interviewer:
- About company: [Tie to recent news]
- About role: [Show research on team/challenges]
- About growth: [Career progression]

Practice:
- Record yourself answering (check for filler words)
- Time responses (1-3 minutes each)
- Mock interview with friend

Day before:
- Review company news
- Prepare questions based on interviewer's background
- Test tech setup (if virtual)

Goal: Show genuine interest and preparation.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=150,
    priority=3,
    energy_level="high"
)

# Scholarship Essay with Financial Context
SCHOLARSHIP_ESSAY_DETAILED = TaskTemplate(
    id="scholarship_essay_detailed",
    name="Scholarship Essay (Detailed Financial Context)",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.SCHOLARSHIPS,
    variables=["scholarship_name", "essay_topic", "field", "financial_need", "current_university", "target_universities"],
    base_template="""Draft scholarship essay for {scholarship_name}: {essay_topic}

Essay structure (1000 words):

Introduction (150 words):
- Hook: Personal story showing passion for {field}
- Thesis: Why you deserve this scholarship

Academic Journey (300 words):
- Background at {current_university}
- Challenges overcome
- Academic achievements in {field}
- Research interests and projects

Financial Context (250 words):
- Current situation: {financial_need}
- Specific barriers this creates
- How you've managed so far (part-time work, loans, family support)
- Impact on your education/research

Future Goals (200 words):
- Why {target_universities}
- Career objectives in {field}
- How scholarship enables these goals
- Long-term impact you want to make

Giving Back (100 words):
- How you'll contribute to field/community
- Mentorship, research, social impact
- Commitment to paying it forward

Writing tips:
- Show, don't tell (use specific examples)
- Be honest but dignified about financial need
- Connect scholarship to concrete goals
- Express gratitude without being obsequious
- Strong opening and closing

Editing checklist:
- Follows exact word limit
- No grammatical errors
- Authentic voice (not overly formal)
- Specific to this scholarship (not generic)
- Answers all prompt questions

Goal: Stand out through authenticity and clear vision.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=180,
    priority=3,
    energy_level="high"
)

# Job Application with Referral
JOB_APPLICATION_WITH_REFERRAL = TaskTemplate(
    id="job_application_with_referral",
    name="Job Application (With Employee Referral)",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.JOB_APPLICATIONS,
    variables=["company_name", "target_role", "warm_intros", "top_achievement", "unique_value"],
    base_template="""Apply to {target_role} at {company_name} using employee referral.

Referral contact: {warm_intros}

Step 1: Referral outreach (BEFORE applying)
Message to referral:
"Hi [Contact Name],

I noticed {company_name} is hiring for {target_role}. Given my background ({unique_value}), I think I'd be a strong fit.

Would you be comfortable providing a referral? I understand this is a professional recommendation, so I want to make sure you're confident in referring me.

I've attached my resume and can provide any additional info you need.

Thank you for considering!"

Step 2: Wait for referral confirmation (24-48 hours)

Step 3: Complete application
- Use referral code/link
- Mention referral in application notes
- Upload tailored resume highlighting {top_achievement}
- Write cover letter referencing company insider perspective

Step 4: Follow up
- Send thank you note to referrer after applying
- Update them when you hear back
- Keep them posted through process

Cover letter structure:
Paragraph 1: "[Referrer name] suggested I apply for {target_role}. My {unique_value} aligns perfectly with your needs."

Paragraph 2: "{top_achievement} demonstrates my ability to deliver results in similar context."

Paragraph 3: "I'm excited about {company_name}'s [specific initiative]. I'd welcome the opportunity to contribute."

Goal: Leverage referral for 5-10x better chance of interview.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=75,
    priority=3,
    energy_level="high"
)

# LinkedIn Optimization with Industry Focus
LINKEDIN_INDUSTRY_OPTIMIZED = TaskTemplate(
    id="linkedin_industry_optimized",
    name="LinkedIn Optimization (Industry-Specific)",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.LINKEDIN_OPTIMIZATION,
    variables=["target_role", "target_industry", "expertise_area", "top_skills", "companies_worked"],
    base_template="""Optimize LinkedIn profile for {target_role} in {target_industry}.

Headline (max 120 characters):
"{target_role} | {expertise_area} | Ex-{companies_worked} | [Key achievement in 3-5 words]"

About section (2000 characters):

Opening hook (50 words):
"I help [target audience] achieve [specific outcome] through {expertise_area}.

[One-sentence summary of {top_achievement}]"

Experience (150 words):
"My career has focused on {expertise_area} in {target_industry}:

- At {companies_worked}: [Key achievement with metrics]
- Core skills: {top_skills}
- Passionate about: [Specific problem you solve]

What drives me: [Your unique perspective on {target_industry}]"

What I'm looking for (50 words):
"Currently exploring {target_role} opportunities where I can leverage my {expertise_area} expertise to [specific impact].

Open to: {target_industry} companies, [specific role types]
Interested in: [Specific problems/technologies]"

Experience section:
- For each role at {companies_worked}:
  * Start with achievement, not job description
  * Quantify impact (%, $, scale)
  * Use industry-specific keywords
  * Include {top_skills} naturally

Skills section:
- Add all {top_skills}
- Arrange by endorsement count
- Request endorsements from colleagues
- Take skill assessments for top 3 skills

Featured section:
- Add portfolio pieces
- Link to articles/publications
- Showcase {top_achievement}

Settings optimization:
- Set "Open to Work" (recruiters only)
- List {target_role} in preferences
- Add {target_industry} companies to follow

Activity strategy:
- Post 2-3x per week about {expertise_area}
- Comment on industry leaders' posts
- Share insights on {target_industry} trends

Goal: Appear in searches for "{target_role} {target_industry}".""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=120,
    priority=2,
    energy_level="high"
)

# Visa Application with University Specifics
VISA_APPLICATION_DETAILED = TaskTemplate(
    id="visa_application_detailed",
    name="Visa Application (University-Specific)",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.VISA_PROCESS,
    variables=["country", "visa_type", "target_universities", "financial_proof_amount", "field"],
    base_template="""Prepare {visa_type} application for {country} - {target_universities}.

Document checklist:
1. Acceptance letter from {target_universities}
2. Financial proof: {financial_proof_amount}
   - Bank statements (last 6 months)
   - Scholarship letters (if any)
   - Sponsor affidavits with bank statements
3. Academic documents:
   - Transcripts (all degrees)
   - Degree certificates
   - English proficiency test (IELTS/TOEFL)
4. Passport (6+ months validity)
5. Passport photos (2-4, check {country} specifications)
6. Visa application form (completed online)
7. Visa fee payment receipt
8. Health insurance confirmation
9. Accommodation proof (university housing/lease)
10. Statement of Purpose for visa (different from university SOP)

University-specific requirements:
- Check {target_universities} visa guidance page
- Download CAS/I-20 document (required for application)
- Note university-provided support services

Visa interview prep (if required):
Common questions:
1. Why {field} at {target_universities}?
   Answer: [Specific program features, professors, research]

2. Why {country}?
   Answer: [Academic reputation, career opportunities in {field}]

3. How will you fund your studies?
   Answer: [Be specific about {financial_proof_amount} source]

4. What are your plans after graduation?
   Answer: [Return home OR work in {country} if allowed]

5. Why this university?
   Answer: [Specific to {target_universities} strengths in {field}]

Interview tips:
- Be honest and confident
- Have all documents organized
- Dress professionally
- Arrive 15 minutes early
- Bring extra copies of everything

Timeline:
- Apply 3 months before program start
- Typical processing: 4-8 weeks
- Book appointment early (slots fill fast)

Goal: Prepare complete, organized application.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=120,
    priority=3,
    energy_level="high"
)

# Career Pivot Strategy
CAREER_PIVOT_STRATEGY = TaskTemplate(
    id="career_pivot_strategy",
    name="Career Pivot Strategy Plan",
    category=TemplateCategory.CAREER,
    milestone_type=MilestoneType.SKILL_BUILDING,
    variables=["current_role", "target_role", "skill_gap", "years_experience", "expertise_area"],
    base_template="""Create strategic plan for pivot from {current_role} to {target_role}.

Current state:
- Role: {current_role}
- Experience: {years_experience} years
- Strengths: {expertise_area}
- Gap: {skill_gap}

Pivot strategy (3-6 months):

Month 1-2: Build credibility
- Complete online course in {skill_gap}
- Build 1-2 projects demonstrating {target_role} skills
- Update LinkedIn headline to "{current_role} → {target_role}"
- Join {target_role} communities (Slack/Discord)

Month 3-4: Network + visibility
- Attend 2-3 {target_role} meetups/events
- Reach out to 10 people in {target_role} for informational interviews
- Write 3-5 LinkedIn posts about your {target_role} learning journey
- Contribute to open-source projects related to {skill_gap}

Month 5-6: Apply strategically
- Target "hybrid" roles that leverage both {current_role} and {target_role}
- Apply to startups/scale-ups (more open to pivots than big tech)
- Use your {years_experience} years as advantage (maturity, soft skills)
- Emphasize transferable skills from {expertise_area}

Resume strategy:
- Lead with "Transitioning from {current_role} to {target_role}"
- Create "Relevant Projects" section showcasing {skill_gap} work
- Reframe {current_role} experience using {target_role} language
- Highlight transferable skills

Cover letter angle:
"While I've spent {years_experience} years in {current_role}, I've developed strong {skill_gap} skills through [projects]. My background in {expertise_area} gives me a unique perspective that most {target_role}s don't have."

Target companies:
- Startups (more flexible on background)
- Companies hiring for "{current_role} with {target_role} skills"
- Internal transfers (if currently employed)

Realistic expectations:
- May need to take slight pay cut initially
- Start at mid-level in new field despite {years_experience} years
- 3-6 month timeline is aggressive but achievable
- Network referrals are 5x more important for pivots

Success metrics:
- 5 informational interviews completed
- 2 projects built and on portfolio
- 10 applications sent to hybrid roles
- 1 course/certification completed in {skill_gap}

Goal: Position yourself as "{current_role} bringing {expertise_area} to {target_role}".""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=90,
    priority=3,
    energy_level="high"
)

# Application Review with Professor Contacts
APPLICATION_REVIEW_PROFESSOR_NETWORK = TaskTemplate(
    id="application_review_professor_network",
    name="Application Review (Professor Network)",
    category=TemplateCategory.STUDY,
    milestone_type=MilestoneType.APPLICATIONS,
    variables=["target_universities", "professor_contacts", "field", "top_projects"],
    base_template="""Get application materials reviewed by professor network before submitting to {target_universities}.

Reviewers available: {professor_contacts}

Materials to review:
1. Statement of Purpose (SOP)
2. Research proposal (if required)
3. CV/Resume
4. Writing sample

Outreach strategy:

Step 1: Select reviewer
- Choose professor in {field}
- Ideally someone who knows you/your work
- Has connection to {target_universities} if possible

Step 2: Request review (email)
Subject: Request for feedback on {target_universities} application materials

"Dear Professor [Name],

I'm applying to [specific program] at {target_universities} and would greatly value your feedback on my application materials.

Given your expertise in {field} and your familiarity with my work on {top_projects}, I believe your insights would be particularly helpful.

Would you have time for a brief review of my SOP and CV (attached)? I'm specifically looking for feedback on:
1. How clearly I articulate my research interests
2. Whether my past work adequately demonstrates readiness
3. Any red flags or areas that need strengthening

Deadline: [2 weeks before application deadline]

I understand you're busy - even brief comments would be incredibly helpful.

Thank you for considering!
(Your name here)"

Materials to attach:
- Latest draft of SOP (track changes enabled)
- CV (PDF)
- Draft research proposal (if applicable)

Follow-up:
- Send gentle reminder if no response in 5 days
- Thank reviewer promptly when feedback received
- Update them on application outcome
- Offer to help them in future (teaching assistant, research help)

Incorporating feedback:
- Prioritize comments about content over style
- Get second opinion if major revisions suggested
- Track all versions (SOP_v1, SOP_v2, etc.)
- Final proofread after incorporating feedback

Alternative if no professor contacts:
- University writing center review
- Grad student mentors in {field}
- Online communities (r/gradadmissions)
- Professional editing service (last resort, budget $200-500)

Timeline:
- Request review: 4 weeks before deadline
- Receive feedback: 3 weeks before
- Revise: 2 weeks before
- Final review: 1 week before
- Submit: On deadline day

Goal: Get expert feedback to strengthen application before submission.""",
    budget_tier=BudgetTier.STANDARD,
    timebox_minutes=60,
    priority=3,
    energy_level="medium"
)

# ============================================================================
# TEMPLATE REGISTRY
# ============================================================================

# Master registry of all templates
TEMPLATE_REGISTRY: Dict[str, TaskTemplate] = {
    # Study - University Research
    "university_research_budget": UNIVERSITY_RESEARCH_BUDGET,
    "university_research_standard": UNIVERSITY_RESEARCH_STANDARD,
    "university_research_premium": UNIVERSITY_RESEARCH_PREMIUM,

    # Study - IELTS/Exam Prep
    "ielts_registration_budget": IELTS_REGISTRATION_BUDGET,
    "ielts_prep_weakness_writing": IELTS_PREP_WEAKNESS_WRITING,
    "ielts_prep_intensive": IELTS_PREP_INTENSIVE,

    # Study - SOP
    "sop_draft_intro": SOP_DRAFT_INTRO,
    "sop_full_draft": SOP_FULL_DRAFT,

    # Study - Recommendations
    "recommendation_request_professor": RECOMMENDATION_REQUEST_PROFESSOR,

    # Study - Applications
    "application_submission_early": APPLICATION_SUBMISSION_EARLY,

    # Study - Visa
    "visa_prep_documents": VISA_PREP_DOCUMENTS,

    # Study - Scholarships
    "scholarship_research_budget": SCHOLARSHIP_RESEARCH_BUDGET,

    # Career - Resume
    "resume_update_entry_level": RESUME_UPDATE_ENTRY_LEVEL,
    "resume_update_mid_level": RESUME_UPDATE_MID_LEVEL,

    # Career - LinkedIn
    "linkedin_optimization_headline": LINKEDIN_OPTIMIZATION_HEADLINE,
    "linkedin_about_section": LINKEDIN_ABOUT_SECTION,

    # Career - Job Applications
    "job_application_targeted": JOB_APPLICATION_TARGETED,
    "job_application_volume": JOB_APPLICATION_VOLUME,

    # Career - Networking
    "networking_warm_intro": NETWORKING_WARM_INTRO,
    "networking_cold_outreach": NETWORKING_COLD_OUTREACH,

    # Career - Skill Building
    "skill_building_targeted_weakness": SKILL_BUILDING_TARGETED_WEAKNESS,

    # Career - Interview Prep
    "interview_prep_behavioral": INTERVIEW_PREP_BEHAVIORAL,

    # Additional Study Templates (8 templates)
    "sop_draft_weakness_focused": SOP_DRAFT_WEAKNESS_FOCUSED,
    "application_tracking_setup": APPLICATION_TRACKING_SETUP,
    "portfolio_preparation": PORTFOLIO_PREPARATION,
    "scholarship_essay_draft": SCHOLARSHIP_ESSAY_DRAFT,
    "test_prep_strategy": TEST_PREP_STRATEGY,
    "visa_document_checklist": VISA_DOCUMENT_CHECKLIST,
    "professor_outreach_research": PROFESSOR_OUTREACH_RESEARCH,
    "financial_aid_application": FINANCIAL_AID_APPLICATION,

    # Additional Career Templates (10 templates)
    "cover_letter_targeted": COVER_LETTER_TARGETED,
    "linkedin_content_strategy": LINKEDIN_CONTENT_STRATEGY,
    "job_search_automation": JOB_SEARCH_AUTOMATION,
    "networking_event_prep": NETWORKING_EVENT_PREP,
    "portfolio_website_setup": PORTFOLIO_WEBSITE_SETUP,
    "informational_interview_request": INFORMATIONAL_INTERVIEW_REQUEST,
    "salary_negotiation_prep": SALARY_NEGOTIATION_PREP,
    "skills_gap_analysis": SKILLS_GAP_ANALYSIS,
    "personal_brand_audit": PERSONAL_BRAND_AUDIT,
    "technical_interview_practice": TECHNICAL_INTERVIEW_PRACTICE,

    # Context-Aware Variants (10 templates) - Week 2 Day 8-9
    "professor_outreach_research_focused": PROFESSOR_OUTREACH_RESEARCH_FOCUSED,
    "networking_warm_intro_leveraged": NETWORKING_WARM_INTRO_LEVERAGED,
    "resume_update_company_targeted": RESUME_UPDATE_COMPANY_TARGETED,
    "interview_prep_company_research": INTERVIEW_PREP_COMPANY_RESEARCH,
    "scholarship_essay_detailed": SCHOLARSHIP_ESSAY_DETAILED,
    "job_application_with_referral": JOB_APPLICATION_WITH_REFERRAL,
    "linkedin_industry_optimized": LINKEDIN_INDUSTRY_OPTIMIZED,
    "visa_application_detailed": VISA_APPLICATION_DETAILED,
    "career_pivot_strategy": CAREER_PIVOT_STRATEGY,
    "application_review_professor_network": APPLICATION_REVIEW_PROFESSOR_NETWORK,
}


def get_template(template_id: str) -> Optional[TaskTemplate]:
    """Get template by ID"""
    return TEMPLATE_REGISTRY.get(template_id)


def get_templates_by_category(category: TemplateCategory) -> List[TaskTemplate]:
    """Get all templates for a category"""
    return [t for t in TEMPLATE_REGISTRY.values() if t.category == category]


def get_templates_by_milestone_type(milestone_type: MilestoneType) -> List[TaskTemplate]:
    """Get all templates for a milestone type"""
    return [t for t in TEMPLATE_REGISTRY.values() if t.milestone_type == milestone_type]


def get_templates_by_budget_tier(budget_tier: BudgetTier) -> List[TaskTemplate]:
    """Get all templates for a budget tier"""
    return [t for t in TEMPLATE_REGISTRY.values() if t.budget_tier == budget_tier]


# Total templates count
print(f"[TaskTemplates] Loaded {len(TEMPLATE_REGISTRY)} templates")
print(f"  - Study: {len(get_templates_by_category(TemplateCategory.STUDY))}")
print(f"  - Career: {len(get_templates_by_category(TemplateCategory.CAREER))}")