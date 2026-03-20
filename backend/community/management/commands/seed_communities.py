"""
Management Command: Seed Communities

Creates:
- Region-based communities (USA, UK, China, Canada, Australia, Europe)
- Topic-based communities (SAT Prep, IELTS Prep, Essays, Portfolios, etc.)
- Demo posts from demo users to show how the system works
- All demo posts are clearly marked as examples

Usage:
    python manage.py seed_communities
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

from community.models import Community, CommunityMember, Post, Comment, PostVote

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed communities and demo posts'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🌱 Starting community seeding...'))

        # Check if communities already exist
        if Community.objects.exists():
            self.stdout.write(self.style.WARNING('⚠️  Communities already exist. Skipping seed.'))
            return

        # Create demo users (marked clearly as demo)
        demo_users = self.create_demo_users()

        # Create region communities
        region_communities = self.create_region_communities()

        # Create topic communities
        topic_communities = self.create_topic_communities()

        # Create demo posts for each community
        all_communities = region_communities + topic_communities
        self.create_demo_posts(all_communities, demo_users)

        self.stdout.write(self.style.SUCCESS(f'✅ Successfully seeded {len(all_communities)} communities!'))
        self.stdout.write(self.style.SUCCESS('📝 Demo posts added from demo users'))
        self.stdout.write(self.style.SUCCESS('🎯 Ready for real user activity!'))

    def create_demo_users(self):
        """Create demo users clearly marked as examples"""
        self.stdout.write('👥 Creating demo users...')

        demo_user_data = [
            {
                'email': 'demo_sarah@pathai.example.com',
                'username': 'demo_sarah',
                'full_name': 'Demo Sarah (USA Applicant)',
                'bio': '🎓 Demo user showing how the community works\nApplying to Ivy League schools\n• This is a demo account',
            },
            {
                'email': 'demo_wei@pathai.example.com',
                'username': 'demo_wei',
                'full_name': 'Demo Wei (China Applicant)',
                'bio': '🎓 Demo user showing how the community works\nTargeting top US universities\n• This is a demo account',
            },
            {
                'email': 'demo_emma@pathai.example.com',
                'username': 'demo_emma',
                'full_name': 'Demo Emma (UK Applicant)',
                'bio': '🎓 Demo user showing how the community works\nOxford and Cambridge hopeful\n• This is a demo account',
            },
        ]

        demo_users = []
        for data in demo_user_data:
            try:
                # Check if user exists
                user = User.objects.get(email=data['email'])
            except User.DoesNotExist:
                # Create new user
                user = User.objects.create_user(
                    email=data['email'],
                    password='demo123456',  # Demo password
                    username=data['username'],
                )
                # Update profile
                if hasattr(user, 'profile'):
                    user.profile.name = data['full_name']
                    user.profile.current_situation = data['bio']  # Use existing field for bio
                    user.profile.save()

            demo_users.append(user)

        self.stdout.write(self.style.SUCCESS(f'   ✅ Created {len(demo_users)} demo users'))
        return demo_users

    def create_region_communities(self):
        """Create region-based communities"""
        self.stdout.write('🌍 Creating region communities...')

        communities_data = [
            {
                'name': 'USA Applicants',
                'slug': 'usa-applicants',
                'description': 'Community for students applying to universities in the United States. Share experiences, ask questions, and support each other through the application process.',
                'community_type': 'region',
                'icon': '🇺🇸',
                'banner_color': '#3B82F6',
                'rules': [
                    'Be respectful to all applicants',
                    'No sharing of confidential admissions info',
                    'Support each other through the process',
                ],
                'member_count': 12500,
                'online_count': 342,
                'is_official': True,
                'tags': ['usa', 'american-universities', 'common-app', 'ivy-league'],
            },
            {
                'name': 'UK Applicants',
                'slug': 'uk-applicants',
                'description': 'For students applying to UK universities (Oxford, Cambridge, Imperial, UCL, etc.). Discuss UCAS, personal statements, and interviews.',
                'community_type': 'region',
                'icon': '🇬🇧',
                'banner_color': '#EF4444',
                'rules': [
                    'Respect the UCAS process',
                    'No sharing of interview questions',
                    'Help others with personal statements',
                ],
                'member_count': 8200,
                'online_count': 187,
                'is_official': True,
                'tags': ['uk', 'ucas', 'oxbridge', 'personal-statement'],
            },
            {
                'name': 'China Applicants',
                'slug': 'china-applicants',
                'description': '中国学生申请社区. Share tips for Chinese applicants to US/UK universities.',
                'community_type': 'region',
                'icon': '🇨🇳',
                'banner_color': '#DC2626',
                'rules': [
                    'Use English or Chinese',
                    '支持其他申请者',
                    'Share honest experiences',
                ],
                'member_count': 5100,
                'online_count': 123,
                'is_official': True,
                'tags': ['china', 'chinese-applicants', 'study-abroad'],
            },
            {
                'name': 'Canada Applicants',
                'slug': 'canada-applicants',
                'description': 'Community for students applying to Canadian universities (Toronto, UBC, McGill, Waterloo, etc.).',
                'community_type': 'region',
                'icon': '🇨🇦',
                'banner_color': '#F59E0B',
                'rules': [
                    'Discuss OUAC process',
                    'Share scholarship info',
                    'Support fellow applicants',
                ],
                'member_count': 3800,
                'online_count': 89,
                'is_official': True,
                'tags': ['canada', 'ouac', 'toronto', 'ubc', 'mcgill'],
            },
            {
                'name': 'Australia Applicants',
                'slug': 'australia-applicants',
                'description': 'Applying to Australian universities? Join this community to discuss the application process, scholarships, and student life.',
                'community_type': 'region',
                'icon': '🇦🇺',
                'banner_color': '#10B981',
                'rules': [
                    'Share scholarship opportunities',
                    'Discuss visa process',
                    'Help with course selection',
                ],
                'member_count': 2100,
                'online_count': 56,
                'is_official': True,
                'tags': ['australia', 'group-of-eight', 'scholarships'],
            },
            {
                'name': 'Europe Applicants',
                'slug': 'europe-applicants',
                'description': 'Community for students applying to European universities. Discuss programs in Germany, Netherlands, France, Spain, and more.',
                'community_type': 'region',
                'icon': '🇪🇺',
                'banner_color': '#6366F1',
                'rules': [
                    'Share country-specific info',
                    'Discuss English-taught programs',
                    'Help with visa applications',
                ],
                'member_count': 4500,
                'online_count': 98,
                'is_official': True,
                'tags': ['europe', 'erasmus', 'tuition-free', 'english-programs'],
            },
        ]

        communities = []
        for data in communities_data:
            community = Community.objects.create(**data)
            communities.append(community)

        self.stdout.write(self.style.SUCCESS(f'   ✅ Created {len(communities)} region communities'))
        return communities

    def create_topic_communities(self):
        """Create topic-based communities"""
        self.stdout.write('📚 Creating topic communities...')

        communities_data = [
            {
                'name': 'SAT Prep',
                'slug': 'sat-prep',
                'description': 'Everything SAT preparation! Share study tips, practice test scores, strategies for Math and Reading/Writing sections.',
                'community_type': 'topic',
                'icon': '📊',
                'banner_color': '#3B82F6',
                'rules': [
                    'Share honest score improvements',
                    'No cheating or score discussion',
                    'Help others with resources',
                ],
                'member_count': 15600,
                'online_count': 412,
                'is_official': True,
                'tags': ['sat', 'sat-prep', 'college-board', 'digital-sat', 'test-prep'],
            },
            {
                'name': 'IELTS Prep',
                'slug': 'ielts-prep',
                'description': 'IELTS preparation community. Share speaking topics, writing task strategies, reading tips, and listening practice resources.',
                'community_type': 'topic',
                'icon': '🗣',
                'banner_color': '#F59E0B',
                'rules': [
                    'Do not share exact test questions',
                    'Share preparation strategies',
                    'Support test takers',
                ],
                'member_count': 9800,
                'online_count': 234,
                'is_official': True,
                'tags': ['ielts', 'english-test', 'study-abroad', 'toefl'],
            },
            {
                'name': 'Essays & Personal Statements',
                'slug': 'essays-personal-statements',
                'description': 'Get feedback on your college essays and personal statements. Share successful essay examples and writing tips.',
                'community_type': 'topic',
                'icon': '📝',
                'banner_color': '#8B5CF6',
                'rules': [
                    'Do not plagiarize essays',
                    'Give constructive feedback',
                    'Respect privacy (remove personal info)',
                ],
                'member_count': 12300,
                'online_count': 387,
                'is_official': True,
                'tags': ['essays', 'personal-statement', 'common-app', 'writing', 'feedback'],
            },
            {
                'name': 'Portfolios & Creative Work',
                'slug': 'portfolios-creative-work',
                'description': 'For art, design, architecture, and creative applicants. Share portfolio tips, get feedback on your work.',
                'community_type': 'topic',
                'icon': '🎨',
                'banner_color': '#EC4899',
                'rules': [
                    'Respect intellectual property',
                    'Give helpful feedback',
                    'Share portfolio requirements',
                ],
                'member_count': 5400,
                'online_count': 143,
                'is_official': True,
                'tags': ['portfolio', 'art', 'design', 'creative', 'architecture'],
            },
            {
                'name': 'Interviews Preparation',
                'slug': 'interviews-prep',
                'description': 'Prepare for college interviews (alumni, admissions officer, Oxbridge). Share strategies and practice questions.',
                'community_type': 'topic',
                'icon': '🎤',
                'banner_color': '#10B981',
                'rules': [
                    'Do not share exact interview questions',
                    'Share general strategies',
                    'Practice with others respectfully',
                ],
                'member_count': 6700,
                'online_count': 176,
                'is_official': True,
                'tags': ['interview', 'alumni-interview', 'oxbridge', 'preparation'],
            },
            {
                'name': 'Financial Aid & Scholarships',
                'slug': 'financial-aid-scholarships',
                'description': 'Discuss CSS Profile, FAFSA, scholarships, grants, and financial aid packages. Share opportunities and tips.',
                'community_type': 'topic',
                'icon': '💰',
                'banner_color': '#22C55E',
                'rules': [
                    'Share legitimate opportunities',
                    'No spam or scams',
                    'Discuss honestly about costs',
                ],
                'member_count': 8900,
                'online_count': 201,
                'is_official': True,
                'tags': ['financial-aid', 'scholarships', 'fafsa', 'css-profile', 'grants'],
            },
            {
                'name': 'Extracurriculars',
                'slug': 'extracurriculars',
                'description': 'Discuss extracurricular activities, leadership roles, community service, competitions, and building a strong profile.',
                'community_type': 'topic',
                'icon': '🎯',
                'banner_color': '#6366F1',
                'rules': [
                    'Share honest experiences',
                    'No boasting or shaming',
                    'Help others find opportunities',
                ],
                'member_count': 7600,
                'online_count': 192,
                'is_official': True,
                'tags': ['extracurriculars', 'leadership', 'activities', 'profile-building'],
            },
            {
                'name': 'Success Stories',
                'slug': 'success-stories',
                'description': 'Share your acceptance stories! What worked? What didn\'t? Inspire others with your journey to college acceptance.',
                'community_type': 'topic',
                'icon': '🎉',
                'banner_color': '#F59E0B',
                'rules': [
                    'Celebrate humbly',
                    'Share honest reflections',
                    'Encourage others',
                    'No bragging',
                ],
                'member_count': 18200,
                'online_count': 521,
                'is_official': True,
                'tags': ['success', 'acceptance', 'admitted', 'celebration', 'inspiration'],
            },
        ]

        communities = []
        for data in communities_data:
            community = Community.objects.create(**data)
            communities.append(community)

        self.stdout.write(self.style.SUCCESS(f'   ✅ Created {len(communities)} topic communities'))
        return communities

    def create_demo_posts(self, communities, demo_users):
        """Create demo posts for each community"""
        self.stdout.write('📝 Creating demo posts...')

        # Demo post templates by community type
        post_templates = {
            'usa-applicants': [
                {
                    'title': 'Just submitted my Common App! 🎉',
                    'content': 'After weeks of editing my essay and checking every detail, I finally hit submit! Applying to: Harvard, Yale, Princeton, Stanford, MIT. Fingers crossed! 🤞\n\nGPA: 3.95 UW\nSAT: 1560\nRank: Top 5%\n\nGood luck to everyone else applying!',
                    'flair': 'success',
                    'author': demo_users[0],  # demo_sarah
                },
                {
                    'title': 'Question about Early Decision',
                    'content': 'If I apply ED to a school and get deferred, can I still apply ED2 elsewhere? Or do I have to wait for Regular Decision? Confused about the rules.',
                    'flair': 'question',
                    'author': demo_users[0],
                },
                {
                    'title': 'How I improved my SAT from 1350 to 1520',
                    'content': 'Started with a 1350 in March, got 1520 in October. Here\'s what worked for me:\n\n1. Khan Academy every day (30 mins)\n2. Took 8 practice tests\n3. Focused on weak areas (Geometry for me)\n4. Learned time management strategies\n\nYou can do it! 💪',
                    'flair': 'advice',
                    'author': demo_users[0],
                },
            ],
            'sat-prep': [
                {
                    'title': 'Official October SAT scores are out!',
                    'content': 'Got my scores: 780 Math, 760 RW = 1540 total! Super happy with this improvement from my 1420 diagnostic test. The Digital SAT format actually helped me focus better.',
                    'flair': 'success',
                    'author': demo_users[0],
                },
                {
                    'title': 'Best resources for Desmos calculator practice?',
                    'content': 'I\'m struggling with the built-in Desmos calculator on the Digital SAT. What resources helped you learn how to use it effectively? Looking specifically for advanced graphing techniques.',
                    'flair': 'question',
                    'author': demo_users[0],
                },
                {
                    'title': 'Warning: Don\'t underestimate the Reading section',
                    'content': 'I focused mostly on Math and thought Reading would be easy. Big mistake! The time pressure on the new Digital SAT Reading is real. Make sure to practice timed passages.',
                    'flair': 'advice',
                    'author': demo_users[0],
                },
            ],
            'essays-personal-statements': [
                {
                    'title': 'My Common App essay: "The Grocery Store Aisle"',
                    'content': 'Wrote about working at my parents\' grocery store and how it taught me about community, diversity, and responsibility. 650 words exactly.\n\nWould anyone be willing to read it and give feedback? I\'ll send a Google Doc link.\n\nTheme: Finding meaning in ordinary work',
                    'flair': 'essay',
                    'author': demo_users[0],
                },
                {
                    'title': 'Supplemental essays are killing me 😅',
                    'content': 'Why does every school need "Why Us?" essays? I\'ve written 12 different versions so far. Applying to 10 schools = 30+ essays total.\n\nHow are you all managing the workload?',
                    'flair': 'discussion',
                    'author': demo_users[0],
                },
                {
                    'title': 'Essay topic idea: Is "sports injury" too cliché?',
                    'content': 'I was a varsity athlete until I got injured junior year. It changed my perspective and led me to discover academic interests.\n\nBut I feel like this is a really common topic. Should I avoid it? Or focus on a unique angle?',
                    'flair': 'question',
                    'author': demo_users[0],
                },
            ],
            'china-applicants': [
                {
                    'title': 'RD轮结果汇总',
                    'content': '为了方便大家，我建了一个表格汇总RD结果。请填入你的录取信息：\n\n[Google Forms链接]\n\nGood luck to everyone! 加油! 🍀',
                    'flair': 'resource',
                    'author': demo_users[1],  # demo_wei
                },
                {
                    'title': 'UC系统 vs 私立大学',
                    'content': '想听听大家的意见：UC Berkeley/UCLA vs 私立大学如USC, NYU？\n\n考虑因素：\n- 学费\n- 地理位置\n- 就业前景\n- 校园文化',
                    'flair': 'discussion',
                    'author': demo_users[1],
                },
                {
                    'title': '从1350到1510的SAT备考经验',
                    'content': '分享我的提分经历：\n\n1. 语法专项训练（Khan Academy）\n2. 数学错题整理\n3. 每周一套真题\n4. 考前一个月每天模考\n\n最重要的：坚持！💪',
                    'flair': 'advice',
                    'author': demo_users[1],
                },
            ],
            'uk-applicants': [
                {
                    'title': 'Just received my Cambridge offer! 🎉',
                    'content': 'Offer from Trinity College, Cambridge for Natural Sciences! Conditions: A*A*A in A-Levels.\n\nStill can\'t believe it. The interview was terrifying but worth it.\n\nHappy to answer questions about the process!',
                    'flair': 'success',
                    'author': demo_users[2],  # demo_emma
                },
                {
                    'title': 'Personal statement feedback needed',
                    'content': 'Drafted my personal statement for Physics at Oxford. It\'s about 4000 characters (the limit).\n\nWould love feedback on:\n1. Is my opening paragraph strong enough?\n2. Do I show enough super-curricular engagement?\n3. Is the tone appropriate for Oxbridge?\n\nPM if you can help!',
                    'flair': 'essay',
                    'author': demo_users[2],
                },
                {
                    'title': 'Oxford interview prep resources',
                    'content': 'Compiled a list of resources that helped me prepare:\n\n- Physics Olympiad past papers\n- "Thinking Physics" by Epstein\n- Khan Academy for basics\n- Practice explaining concepts out loud\n\nThe key is thinking aloud, not getting the right answer immediately.',
                    'flair': 'resource',
                    'author': demo_users[2],
                },
            ],
            'ielts-prep': [
                {
                    'title': 'Got 8.0 overall! Here\'s my breakdown:',
                    'content': 'Just received my IELTS results:\n\nListening: 8.5\nReading: 8.5\nWriting: 7.5\nSpeaking: 7.5\nOverall: 8.0\n\nPrep time: 6 weeks\nWhat worked for me:\n- BBC Learning English for Speaking\n- Past papers for L/R\n- Essay structures for Writing',
                    'flair': 'success',
                    'author': demo_users[1],
                },
                {
                    'title': 'Speaking Part 2: How to handle 2 minutes?',
                    'content': 'I keep running out of things to say in Part 2. The examiner always has to prompt me to continue.\n\nAny tips for extending my answers naturally?',
                    'flair': 'question',
                    'author': demo_users[1],
                },
            ],
            'success-stories': [
                {
                    'title': 'From community college to Ivy League transfer',
                    'content': 'Started at a community college with a 2.8 GPA in high school. Just got accepted as a transfer student to Cornell!\n\nWhat I did right:\n- 4.0 GPA at CC (2 years)\n- Strong professor recommendations\n- Clear "why transfer" essay\n- Extracurricular leadership\n\nDon\'t give up on your dreams! 🌟',
                    'flair': 'success',
                    'author': demo_users[0],
                },
                {
                    'title': 'Full ride to a top 20 school!',
                    'content': 'Got into Duke with a full ride! Posse scholarship + financial aid.\n\nStats:\n- GPA: 3.85\n- SAT: 1480\n- First-generation college student\n- Significant extracurricular leadership\n\nUnderrepresented students: apply to Posse Foundation!',
                    'flair': 'success',
                    'author': demo_users[0],
                },
            ],
            'financial-aid-scholarships': [
                {
                    'title': 'List of full-ride scholarships for international students',
                    'content': 'Compiled a list of full-ride opportunities:\n\n1. Yale (needs-blind for internationals)\n2. Harvard (needs-blind)\n3. MIT (needs-blind)\n4. Stanford (needs-blind)\n5. QuestBridge (US citizens)\n6. Posse Foundation (US cities)\n\nI\'ll add more as I find them. Please comment if you know others!',
                    'flair': 'resource',
                    'author': demo_users[1],
                },
                {
                    'title': 'CSS Profile question about divorced parents',
                    'content': 'My parents are divorced and my father is not in contact. Do I still need to list his information on CSS Profile?\n\nThis is stressing me out because he won\'t contribute but his income might hurt my aid.',
                    'flair': 'question',
                    'author': demo_users[1],
                },
            ],
        }

        total_posts = 0

        for community in communities:
            templates = post_templates.get(community.slug, None)

            if not templates:
                # Generate generic posts for communities without templates
                templates = self.generate_generic_posts(community, demo_users)

            # Create posts from templates
            for i, template in enumerate(templates):
                # Vary dates (posts from last 30 days)
                days_ago = random.randint(1, 30)
                created_at = timezone.now() - timedelta(days=days_ago)

                post = Post.objects.create(
                    community=community,
                    user=template['author'],
                    title=template['title'],
                    content=template['content'],
                    flair=template.get('flair', ''),
                    created_at=created_at,
                    updated_at=created_at,
                )

                # Add some votes to posts
                self.add_demo_votes_to_post(post, demo_users)

                # Add comments to some posts
                if i % 2 == 0:  # Comment on every other post
                    self.add_demo_comments_to_post(post, demo_users)

                total_posts += 1

                # Update community post count
                community.post_count = community.post_count + 1
                community.save()

        self.stdout.write(self.style.SUCCESS(f'   ✅ Created {total_posts} demo posts'))

    def generate_generic_posts(self, community, demo_users):
        """Generate generic posts for communities without specific templates"""
        generic_templates = [
            {
                'title': f'Welcome to {community.name}! 👋',
                'content': f'Excited to join this community! Looking forward to learning from everyone here.\n\nA bit about me:\n- Applying for Fall 2025\n- Interested in [major]\n- From [location]\n\nHappy to connect!',
                'flair': 'discussion',
                'author': random.choice(demo_users),
            },
            {
                'title': f'Resources for {community.name}',
                'content': f'I\'ve been collecting helpful resources for {community.name.lower()}. Will share them here as I find more.\n\nFeel free to add your own!',
                'flair': 'resource',
                'author': random.choice(demo_users),
            },
        ]
        return generic_templates

    def add_demo_votes_to_post(self, post, demo_users):
        """Add random votes to post to make it look realistic"""
        # Add 5-15 random upvotes
        num_votes = random.randint(5, 15)
        post.upvotes = num_votes

        # Maybe add some downvotes (rare)
        if random.random() < 0.2:  # 20% chance
            post.downvotes = random.randint(1, 3)

        post.save()

        # Create actual vote objects from demo users
        for user in random.sample(demo_users, min(len(demo_users), num_votes)):
            if random.random() < 0.7:  # 70% chance of upvote
                PostVote.objects.create(
                    user=user,
                    post=post,
                    vote_type='upvote'
                )

    def add_demo_comments_to_post(self, post, demo_users):
        """Add demo comments to post"""
        num_comments = random.randint(1, 5)

        comment_templates = [
            'This is so helpful! Thanks for sharing.',
            'Congrats! 🎉 Well deserved!',
            'Can you elaborate more on this?',
            'I\'m in the same boat. Good luck to us both!',
            'Great question - I\'m wondering this too.',
        ]

        for i in range(num_comments):
            commenter = random.choice(demo_users)
            content = random.choice(comment_templates)

            # Make comment slightly after post
            days_ago = random.randint(1, 29)

            Comment.objects.create(
                post=post,
                user=commenter,
                content=content,
                created_at=timezone.now() - timedelta(days=days_ago),
            )

        # Update post comment count
        post.comment_count = num_comments
        post.save()
