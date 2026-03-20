"""
Essay Templates Data

Contains default essay templates for college applications.
These will be loaded into the database via management command.
"""

ESSAY_TEMPLATES = [
    {
        'name': 'Common App Personal Statement',
        'essay_type': 'personal_statement',
        'prompt': 'Discuss an accomplishment, event, or realization that sparked a period of personal growth and a new understanding of yourself or others.',
        'word_count_min': 250,
        'word_count_max': 650,
        'universities': ['Common App', 'All Common App Members'],
        'structure_outline': {
            'introduction': 'Hook reader with a vivid scene or moment (75-100 words)',
            'body_paragraphs': [
                {
                    'section': 'The Experience',
                    'points': ['Describe the challenge/event in detail', 'Show initial reactions and emotions'],
                    'suggested_words': 150
                },
                {
                    'section': 'The Journey',
                    'points': ['What you did', 'How you approached it', 'Actions you took'],
                    'suggested_words': 200
                },
                {
                    'section': 'The Growth',
                    'points': ['What you learned', 'How you changed', 'New understanding'],
                    'suggested_words': 150
                }
            ],
            'conclusion': 'Connect to who you are today and future goals (75-100 words)',
            'themes': ['Growth', 'Self-awareness', 'Transformation', 'Resilience'],
            'total_words': 650
        },
        'key_themes': [
            'Personal growth and transformation',
            'Self-reflection and awareness',
            'Overcoming challenges',
            'Learning from experience',
            'Impact on others'
        ],
        'tips': '''• Focus on ONE specific story, not your entire life
• Show, don't tell - use vivid details and sensory language
• Be authentic - write in your own voice
• Use "I" statements and be personal
• Start with action/hook, not general introduction
• End by connecting to your future
• Avoid cliché topics unless you have a unique angle
• Be specific - names, places, details matter''',
        'sample_essays': [
            {
                'title': 'The Piano Lesson',
                'theme': 'Learning through failure',
                'hook': 'The wrong note echoed through the auditorium...'
            }
        ],
        'order': 1
    },
    {
        'name': 'Why This College',
        'essay_type': 'why_college',
        'prompt': 'Why do you want to attend this university?',
        'word_count_min': 100,
        'word_count_max': 500,
        'universities': ['Most Universities', 'Supplemental Essays'],
        'structure_outline': {
            'introduction': 'Your academic interests and career goals (50-75 words)',
            'body_paragraphs': [
                {
                    'section': 'Academic Fit',
                    'points': ['Specific programs/majors', 'Professors you want to work with', 'Research opportunities'],
                    'suggested_words': 125
                },
                {
                    'section': 'Campus Culture',
                    'points': ['Clubs/organizations', 'Campus traditions', 'Student community'],
                    'suggested_words': 125
                },
                {
                    'section': 'Your Contribution',
                    'points': ['What you will bring to campus', 'How you will engage', 'Unique perspective'],
                    'suggested_words': 100
                }
            ],
            'conclusion': 'Why you are a perfect match (50-75 words)',
            'themes': ['Academic Fit', 'Campus Community', 'Future Contribution'],
            'total_words': 500
        },
        'key_themes': [
            'Academic alignment',
            'Campus community fit',
            'Future contribution',
            'Specific programs/opportunities',
            'Research and learning goals'
        ],
        'tips': '''• Name SPECIFIC professors, courses, programs
• Show you\'ve done research - mention campus visits, talks with students
• Avoid generic praise ("beautiful campus", "great reputation")
• Connect YOUR goals to THEIR offerings
• Explain why you need THIS college, not just any college
• Show how you will contribute to campus community
• Be specific about what you will do there''',
        'order': 2
    },
    {
        'name': 'Why This Major',
        'essay_type': 'why_major',
        'prompt': 'Describe your intended major and why you are passionate about it.',
        'word_count_min': 150,
        'word_count_max': 500,
        'universities': ['Most Universities', 'Supplemental Essays'],
        'structure_outline': {
            'introduction': 'Spark moment - when you discovered this passion (50-75 words)',
            'body_paragraphs': [
                {
                    'section': 'Exploration',
                    'points': ['How you explored this interest', 'Activities/projects/courses', 'What you learned'],
                    'suggested_words': 150
                },
                {
                    'section': 'Passion',
                    'points': ['Why this field excites you', 'Questions you want to answer', 'Impact you want to make'],
                    'suggested_words': 125
                },
                {
                    'section': 'Future',
                    'points': ['Career goals', 'How this major prepares you', 'Problems you want to solve'],
                    'suggested_words': 100
                }
            ],
            'conclusion': 'Why this university\'s program is perfect for you (50-75 words)',
            'themes': ['Intellectual Curiosity', 'Career Preparation', 'Academic Journey'],
            'total_words': 500
        },
        'key_themes': [
            'Intellectual curiosity',
            'Academic journey',
            'Career aspirations',
            'Passion for field',
            'Future impact'
        ],
        'tips': '''• Show PROGRESSION - how interest developed over time
• Connect past experiences to future goals
• Be specific about what excites you
• Avoid "I\'ve always wanted to..." - show specific moments
• Mention books, projects, experiences that shaped your interest
• Show you understand what the major involves
• Connect to specific university programs''',
        'order': 3
    },
    {
        'name': 'Leadership Experience',
        'essay_type': 'leadership',
        'prompt': 'Describe a leadership experience and how you made a positive impact.',
        'word_count_min': 200,
        'word_count_max': 500,
        'universities': ['Many Universities', 'Supplemental Essays'],
        'structure_outline': {
            'introduction': 'The leadership challenge or opportunity (50-75 words)',
            'body_paragraphs': [
                {
                    'section': 'Actions Taken',
                    'points': ['Specific actions you took', 'How you led others', 'Decisions you made'],
                    'suggested_words': 150
                },
                {
                    'section': 'Challenges',
                    'points': ['Obstacles you faced', 'How you overcame them', 'Problem-solving'],
                    'suggested_words': 125
                },
                {
                    'section': 'Impact',
                    'points': ['Measurable results', 'Impact on others/organization', 'What changed'],
                    'suggested_words': 100
                }
            ],
            'conclusion': 'What you learned about leadership (50-75 words)',
            'themes': ['Initiative', 'Teamwork', 'Problem-Solving', 'Impact'],
            'total_words': 500
        },
        'key_themes': [
            'Taking initiative',
            'Leading by example',
            'Collaboration',
            'Problem-solving',
            'Measurable impact'
        ],
        'tips': '''• Focus on ACTIONS you took, not just your position/title
• Show humility - acknowledge teamwork
• Include specific, measurable results when possible
• Don\'t just say "I\'m a leader" - show it through examples
• Mention challenges and how you overcame them
• Show growth in leadership skills
• Focus on IMPACT you made, not just role you had''',
        'order': 4
    },
    {
        'name': 'Overcoming Challenge',
        'essay_type': 'challenge',
        'prompt': 'Discuss a challenge you\'ve faced and how you overcame it.',
        'word_count_min': 250,
        'word_count_max': 650,
        'universities': ['Common App', 'Many Universities'],
        'structure_outline': {
            'introduction': 'The challenge - set the scene (75-100 words)',
            'body_paragraphs': [
                {
                    'section': 'The Struggle',
                    'points': ['Why it was difficult', 'Initial failures/obstacles', 'Emotions faced'],
                    'suggested_words': 150
                },
                {
                    'section': 'The Response',
                    'points': ['Actions you took', 'Strategies you tried', 'Support you sought'],
                    'suggested_words': 200
                },
                {
                    'section': 'The Outcome',
                    'points': ['How you overcame it', 'What you achieved', 'Growth from experience'],
                    'suggested_words': 125
                }
            ],
            'conclusion': 'How this changed you and what you learned (75-100 words)',
            'themes': ['Resilience', 'Problem-Solving', 'Growth Mindset', 'Perseverance'],
            'total_words': 650
        },
        'key_themes': [
            'Resilience and perseverance',
            'Problem-solving',
            'Growth mindset',
            'Learning from failure',
            'Personal strength'
        ],
        'tips': '''• Don\'t just complain - focus on YOUR agency and actions
• Show growth, not just victory
• Be honest about struggles - vulnerability is powerful
• Focus on what you LEARNED, not just what happened
• Avoid cliché challenges unless you have unique perspective
• Show specific steps you took to overcome
• Connect to who you are today
• It\'s okay to not fully succeed - focus on growth''',
        'order': 5
    },
    {
        'name': 'Extracurricular Activity',
        'essay_type': 'activity',
        'prompt': 'Describe an extracurricular activity that is meaningful to you.',
        'word_count_min': 150,
        'word_count_max': 500,
        'universities': ['Many Universities', 'Supplemental Essays'],
        'structure_outline': {
            'introduction': 'The activity and why it matters to you (50-75 words)',
            'body_paragraphs': [
                {
                    'section': 'Involvement',
                    'points': ['What you do in the activity', 'Time and effort invested', 'Progression over time'],
                    'suggested_words': 125
                },
                {
                    'section': 'Impact',
                    'points': ['What you\'ve accomplished', 'Impact on others/community', 'Skills developed'],
                    'suggested_words': 150
                },
                {
                    'section': 'Meaning',
                    'points': ['Why it matters to you', 'How it shaped you', 'Connection to future'],
                    'suggested_words': 100
                }
            ],
            'conclusion': 'How this activity connects to your goals (50-75 words)',
            'themes': ['Passion', 'Commitment', 'Impact', 'Growth'],
            'total_words': 500
        },
        'key_themes': [
            'Deep commitment',
            'Skill development',
            'Community impact',
            'Personal growth',
            'Passion and interest'
        ],
        'tips': '''• Don\'t just list activities - focus on ONE in depth
• Show progression over time (how you grew in the activity)
• Include specific details and anecdotes
• Focus on IMPACT you made, not just participation
• Explain WHY it matters to you personally
• Connect to your academic/career goals if relevant
• Show, don\'t tell - use specific examples
• Mention leadership roles, awards, recognition''',
        'order': 6
    },
    {
        'name': 'Community Service',
        'essay_type': 'community',
        'prompt': 'Describe your community service experience and its impact on you.',
        'word_count_min': 200,
        'word_count_max': 500,
        'universities': ['Many Universities', 'Scholarship Essays'],
        'structure_outline': {
            'introduction': 'The community need and your involvement (50-75 words)',
            'body_paragraphs': [
                {
                    'section': 'Service Actions',
                    'points': ['What you did', 'Time commitment', 'Specific efforts'],
                    'suggested_words': 150
                },
                {
                    'section': 'Impact',
                    'points': ['Impact on community/others', 'Measurable outcomes', 'Relationships built'],
                    'suggested_words': 125
                },
                {
                    'section': 'Learning',
                    'points': ['What you learned', 'Perspective gained', 'How it changed you'],
                    'suggested_words': 100
                }
            ],
            'conclusion': 'Connection to future service and goals (50-75 words)',
            'themes': ['Service', 'Empathy', 'Social Responsibility', 'Impact'],
            'total_words': 500
        },
        'key_themes': [
            'Social responsibility',
            'Empathy and understanding',
            'Community impact',
            'Personal growth through service',
            'Civic engagement'
        ],
        'tips': '''• Focus on impact you made, not just hours logged
• Show understanding of community needs
• Be specific about what you DID
• Include stories of people you helped (respect their privacy)
• Reflect on what you learned about yourself/others
• Connect to future goals of continued service
• Avoid savior complex - show humility and learning
• Demonstrate genuine commitment, not just resume building''',
        'order': 7
    },
    {
        'name': 'Significant Achievement',
        'essay_type': 'achievement',
        'prompt': 'Discuss an achievement that is meaningful to you.',
        'word_count_min': 200,
        'word_count_max': 500,
        'universities': ['Many Universities', 'Scholarship Essays'],
        'structure_outline': {
            'introduction': 'The achievement and why it matters (50-75 words)',
            'body_paragraphs': [
                {
                    'section': 'The Journey',
                    'points': ['Work and effort required', 'Challenges faced', 'Time and dedication'],
                    'suggested_words': 150
                },
                {
                    'section': 'The Achievement',
                    'points': ['What you accomplished', 'Recognition received', 'Significance of achievement'],
                    'suggested_words': 125
                },
                {
                    'section': 'Growth',
                    'points': ['Skills developed', 'Lessons learned', 'How it shaped you'],
                    'suggested_words': 100
                }
            ],
            'conclusion': 'Connection to future goals (50-75 words)',
            'themes': ['Excellence', 'Dedication', 'Growth', 'Achievement'],
            'total_words': 500
        },
        'key_themes': [
            'Hard work and dedication',
            'Excellence and mastery',
            'Overcoming obstacles',
            'Personal growth',
            'Future goals'
        ],
        'tips': '''• Choose achievement meaningful to YOU, not just impressive to others
• Show the WORK behind the achievement
• Mention obstacles and challenges you overcame
• Be humble but confident
• Explain WHY it matters to you
• Don\'t just list awards - tell the story behind them
• Show growth and learning process
• Connect achievement to your character/future''',
        'order': 8
    },
    {
        'name': 'Creative/Unconventional Essay',
        'essay_type': 'creative',
        'prompt': 'Share a creative expression or unique perspective on yourself.',
        'word_count_min': 250,
        'word_count_max': 650,
        'universities': ['Common App', 'Some Universities'],
        'structure_outline': {
            'note': 'Creative essays can have unique structures',
            'approach_1': 'Start in middle of action, then reveal context',
            'approach_2': 'Use metaphor/analogy throughout',
            'approach_3': 'Write from unique perspective (object, concept, etc.)',
            'themes': ['Creativity', 'Unique Perspective', 'Authentic Voice'],
            'total_words': 650
        },
        'key_themes': [
            'Creativity and originality',
            'Unique perspective',
            'Authentic voice',
            'Risk-taking',
            'Self-expression'
        ],
        'tips': '''• Take risks but remain authentic to your voice
• Creativity should serve purpose, not just be gimmicky
• Still needs to reveal something meaningful about you
• Can use humor, but don\'t force it
• Consider your audience - some colleges more open to creative than others
• Tie creative elements back to your character/growth
• Show, don\'t tell - this applies especially to creative essays
• Get feedback - does creativity work or confuse?''',
        'order': 9
    },
    {
        'name': 'Supplemental Essay - Short Answer',
        'essay_type': 'supplemental',
        'prompt': 'Please briefly elaborate on one of your extracurricular activities or work experiences.',
        'word_count_min': 50,
        'word_count_max': 150,
        'universities': ['Many Universities', 'Short Supplements'],
        'structure_outline': {
            'approach': 'Direct and focused',
            'structure': [
                'What activity/job (1 sentence)',
                'What you did/your role (2-3 sentences)',
                'Impact/what you learned (2-3 sentences)'
            ],
            'themes': ['Focus', 'Impact', 'Brevity'],
            'total_words': 150
        },
        'key_themes': [
            'Concise communication',
            'Specific impact',
            'Meaningful engagement'
        ],
        'tips': '''• Every word must count - be concise
• Focus on ONE activity, not overview of many
• Lead with action, not introduction
        Be specific - details over generalities
        Show impact in limited space
        Cut all fluff and filler
        Use strong verbs
• Don\'t repeat what\'s in activity list - add depth/insight''',
        'order': 10
    },
]
