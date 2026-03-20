"""
API Views for Essay Writing Assistance

Provides REST API endpoints for:
- Browsing and selecting essay templates
- Creating and managing essay projects
- AI-powered brainstorming, outlining, feedback, and enhancement
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .essay_models import EssayTemplate, EssayProject, EssayFeedback
from .essay_assistant import EssayAssistant
from .essay_serializers import (
    EssayTemplateSerializer,
    EssayTemplateListSerializer,
    EssayProjectSerializer,
    EssayProjectListSerializer,
    EssayProjectDetailSerializer,
    EssayFeedbackSerializer
)


class EssayTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing essay templates

    Endpoints:
    - GET /api/essay-templates/ - List all templates
    - GET /api/essay-templates/{id}/ - Get template details
    - GET /api/essay-templates/by_type/?type=personal_statement - Filter by type
    """
    permission_classes = (permissions.IsAuthenticated,)
    queryset = EssayTemplate.objects.filter(is_active=True)

    def get_serializer_class(self):
        if self.action == 'list':
            return EssayTemplateListSerializer
        return EssayTemplateSerializer

    def list(self, request, *args, **kwargs):
        """List all active essay templates"""
        templates = self.queryset.order_by('order')
        serializer = self.get_serializer(templates, many=True)
        return Response({
            'templates': serializer.data,
            'count': templates.count()
        })

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Filter templates by essay type"""
        essay_type = request.query_params.get('type')
        if not essay_type:
            return Response(
                {'error': 'Please provide essay_type parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        templates = self.queryset.filter(essay_type=essay_type).order_by('order')
        serializer = EssayTemplateListSerializer(templates, many=True)
        return Response({
            'templates': serializer.data,
            'essay_type': essay_type,
            'count': templates.count()
        })

    @action(detail=False, methods=['get'])
    def types(self, request):
        """Get all available essay types"""
        types_dict = dict(EssayTemplate.ESSAY_TYPES)
        return Response({
            'essay_types': [
                {'value': value, 'label': label}
                for value, label in types_dict.items()
            ]
        })


class EssayProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing essay projects

    Endpoints:
    - GET /api/essay-projects/ - List user's essay projects
    - POST /api/essay-projects/ - Create new essay project
    - GET /api/essay-projects/{id}/ - Get project details
    - PUT/PATCH /api/essay-projects/{id}/ - Update project
    - DELETE /api/essay-projects/{id}/ - Delete project
    - POST /api/essay-projects/start/ - Start new essay from template
    - POST /api/essay-projects/{id}/brainstorm/ - AI brainstorming
    - POST /api/essay-projects/{id}/generate_outline/ - AI outline generation
    - POST /api/essay-projects/{id}/save_draft/ - Save essay draft
    - POST /api/essay-projects/{id}/get_feedback/ - Get AI feedback
    - POST /api/essay-projects/{id}/enhance_paragraph/ - Enhance paragraph
    - POST /api/essay-projects/{id}/complete/ - Mark essay as completed
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Return only user's own essay projects"""
        return EssayProject.objects.filter(user=self.request.user).select_related('template')

    def get_serializer_class(self):
        if self.action == 'list':
            return EssayProjectListSerializer
        elif self.action == 'retrieve':
            return EssayProjectDetailSerializer
        return EssayProjectSerializer

    def list(self, request, *args, **kwargs):
        """List user's essay projects with optional filtering"""
        queryset = self.get_queryset()

        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by essay type
        essay_type = request.query_params.get('essay_type')
        if essay_type:
            queryset = queryset.filter(essay_type=essay_type)

        # Filter by university
        university = request.query_params.get('university')
        if university:
            queryset = queryset.filter(target_university__icontains=university)

        queryset = queryset.order_by('-created_at')
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'projects': serializer.data,
            'count': queryset.count()
        })

    @action(detail=False, methods=['post'])
    def start_essay(self, request):
        """
        Start a new essay project from a template

        Request body:
        {
            "template_id": 1,
            "target_university": "MIT" (optional)
        }
        """
        template_id = request.data.get('template_id')
        target_university = request.data.get('target_university', '')

        if not template_id:
            return Response(
                {'error': 'template_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            template = EssayTemplate.objects.get(id=template_id, is_active=True)
        except EssayTemplate.DoesNotExist:
            return Response(
                {'error': 'Template not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Create essay project
        project = EssayProject.objects.create(
            user=request.user,
            template=template,
            title=f"{template.name} - {target_university or 'General'}",
            essay_type=template.essay_type,
            target_university=target_university,
            target_prompt=template.prompt,
            word_count_goal=template.word_count_max,
            status='brainstorming'
        )

        # Update progress
        project.update_progress()

        serializer = EssayProjectDetailSerializer(project)
        return Response({
            'message': 'Essay project created successfully',
            'project': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def brainstorm(self, request, pk=None):
        """
        AI-powered topic brainstorming

        Returns 10 personalized topic ideas based on user's profile
        """
        project = self.get_object()

        # Check if already brainstormed
        if project.brainstorming_notes and len(project.brainstorming_notes) > 0:
            return Response({
                'message': 'Brainstorming already completed',
                'topics': project.brainstorming_notes
            })

        try:
            assistant = EssayAssistant(request.user)

            topics = assistant.brainstorm_topics(
                project.essay_type,
                project.target_university
            )

            # Save to project
            project.brainstorming_notes = topics
            project.save(update_fields=['brainstorming_notes'])

            return Response({
                'message': f'Generated {len(topics)} topic ideas',
                'topics': topics
            })

        except Exception as e:
            return Response(
                {'error': f'Failed to generate topics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def select_topic(self, request, pk=None):
        """
        Select a topic from brainstorming

        Request body:
        {
            "topic": {topic_object}
        }
        """
        project = self.get_object()
        selected_topic = request.data.get('topic')

        if not selected_topic:
            return Response(
                {'error': 'topic is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        project.selected_topic = selected_topic
        project.status = 'outlining'
        project.save(update_fields=['selected_topic', 'status'])
        project.update_progress()

        return Response({
            'message': 'Topic selected successfully',
            'selected_topic': selected_topic
        })

    @action(detail=True, methods=['post'])
    def generate_outline(self, request, pk=None):
        """
        Generate AI outline for selected topic

        Request body:
        {
            "topic": {topic_object} (optional, uses selected_topic if not provided)
        }
        """
        project = self.get_object()

        # Use selected topic or provided topic
        topic = request.data.get('topic') or project.selected_topic

        if not topic:
            return Response(
                {'error': 'No topic selected. Please select a topic first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            assistant = EssayAssistant(request.user)

            outline = assistant.generate_outline(
                topic,
                project.essay_type,
                project.target_university
            )

            # Save outline
            project.outline_suggestions = outline
            project.save(update_fields=['outline_suggestions'])

            return Response({
                'message': 'Outline generated successfully',
                'outline': outline
            })

        except Exception as e:
            return Response(
                {'error': f'Failed to generate outline: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def save_draft(self, request, pk=None):
        """
        Save essay draft

        Request body:
        {
            "content": "essay text here"
        }
        """
        project = self.get_object()
        content = request.data.get('content', '')

        project.current_draft = content
        project.word_count = len(content.split())
        project.status = 'drafting'
        project.revision_count += 1
        project.save(update_fields=['current_draft', 'word_count', 'status', 'revision_count'])
        project.update_progress()

        serializer = EssayProjectDetailSerializer(project)
        return Response({
            'message': 'Draft saved successfully',
            'project': serializer.data
        })

    @action(detail=True, methods=['post'])
    def get_feedback(self, request, pk=None):
        """
        Get AI feedback on draft

        Analyzes strengths, improvements, and provides score (1-10)
        """
        project = self.get_object()

        if not project.current_draft or len(project.current_draft.strip()) < 50:
            return Response(
                {'error': 'Please write at least 50 words before requesting feedback'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            assistant = EssayAssistant(request.user)

            feedback = assistant.review_draft(
                project.current_draft,
                project.essay_type,
                project.target_university
            )

            # Save feedback
            feedback_obj = EssayFeedback.objects.create(
                essay_project=project,
                draft_content=project.current_draft,
                draft_word_count=project.word_count,
                ai_strengths=feedback.get('strengths', []),
                ai_improvements=feedback.get('improvements', []),
                ai_structure_feedback=feedback.get('structure_feedback', ''),
                ai_content_feedback=feedback.get('content_feedback', ''),
                ai_voice_feedback=feedback.get('voice_feedback', ''),
                ai_grammar_feedback=feedback.get('grammar_style', ''),
                ai_score=feedback.get('score', 7),
                ai_detailed_feedback=feedback.get('ai_detailed_feedback', ''),
                feedback_type='ai'
            )

            # Update project status
            project.status = 'reviewing'
            project.feedback_history.append({
                'feedback_id': feedback_obj.id,
                'score': feedback_obj.ai_score,
                'timestamp': feedback_obj.created_at.isoformat()
            })
            project.save(update_fields=['status', 'feedback_history'])
            project.update_progress()

            return Response({
                'message': 'Feedback generated successfully',
                'feedback': {
                    'id': feedback_obj.id,
                    'strengths': feedback_obj.ai_strengths,
                    'improvements': feedback_obj.ai_improvements,
                    'structure_feedback': feedback_obj.ai_structure_feedback,
                    'content_feedback': feedback_obj.ai_content_feedback,
                    'voice_feedback': feedback_obj.ai_voice_feedback,
                    'grammar_style': feedback_obj.ai_grammar_feedback,
                    'score': feedback_obj.ai_score,
                    'created_at': feedback_obj.created_at
                }
            })

        except Exception as e:
            return Response(
                {'error': f'Failed to generate feedback: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def enhance_paragraph(self, request, pk=None):
        """
        Get suggestions to improve specific paragraph

        Request body:
        {
            "paragraph": "paragraph text here",
            "goal": "make more vivid" (optional)
        }
        """
        project = self.get_object()

        paragraph = request.data.get('paragraph', '')
        goal = request.data.get('goal', 'make more vivid')

        if not paragraph or len(paragraph.strip()) < 10:
            return Response(
                {'error': 'Paragraph must be at least 10 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            assistant = EssayAssistant(request.user)

            variations = assistant.enhance_paragraph(paragraph, goal)

            return Response({
                'message': f'Generated {len(variations)} variations',
                'variations': variations
            })

        except Exception as e:
            return Response(
                {'error': f'Failed to enhance paragraph: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark essay as completed"""
        project = self.get_object()

        project.status = 'completed'
        project.save(update_fields=['status'])
        project.update_progress()

        return Response({
            'message': 'Essay marked as completed!',
            'project': EssayProjectDetailSerializer(project).data
        })

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistics for essay project"""
        project = self.get_object()

        # Calculate stats
        feedback_count = project.feedback_sessions.count()
        avg_score = 0
        if feedback_count > 0:
            scores = [f.ai_score for f in project.feedback_sessions.all() if f.ai_score]
            if scores:
                avg_score = sum(scores) / len(scores)

        return Response({
            'project_id': project.id,
            'word_count': project.word_count,
            'word_count_goal': project.word_count_goal,
            'revision_count': project.revision_count,
            'feedback_count': feedback_count,
            'average_score': round(avg_score, 1),
            'days_since_created': (timezone.now() - project.created_at).days,
            'status': project.status
        })
