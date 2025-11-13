from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ChatConversation, ChatMessage
from .serializers import ChatConversationSerializer, ChatMessageListSerializer


class ConversationListView(APIView):
    """List all conversations and create new ones"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """Get all user's conversations"""
        conversations = ChatConversation.objects.filter(user=request.user)
        serializer = ChatConversationSerializer(conversations, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new conversation"""
        conversation = ChatConversation.objects.create(
            user=request.user,
            title=request.data.get('title', 'New Chat')
        )
        serializer = ChatConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ConversationDetailView(APIView):
    """Get, update, or delete a specific conversation"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, pk):
        """Get conversation details"""
        try:
            conversation = ChatConversation.objects.get(id=pk, user=request.user)
            serializer = ChatConversationSerializer(conversation)
            return Response(serializer.data)
        except ChatConversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        """Update conversation (e.g., rename)"""
        try:
            conversation = ChatConversation.objects.get(id=pk, user=request.user)
            if 'title' in request.data:
                conversation.title = request.data['title']
                conversation.save()
            serializer = ChatConversationSerializer(conversation)
            return Response(serializer.data)
        except ChatConversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        """Delete a conversation"""
        try:
            conversation = ChatConversation.objects.get(id=pk, user=request.user)
            conversation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ChatConversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)


class ConversationMessagesView(APIView):
    """Get all messages in a conversation"""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, conversation_id):
        """Get all messages in a conversation"""
        try:
            conversation = ChatConversation.objects.get(id=conversation_id, user=request.user)
            messages = conversation.messages.all()
            serializer = ChatMessageListSerializer(messages, many=True)
            return Response(serializer.data)
        except ChatConversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)
