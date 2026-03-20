import { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
  Linking,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';
import { aiAPI, todosAPI } from '@/services/api';
import TaskSplitButton from '@/components/TaskSplitButton';

const COLORS = {
  bg: '#131313',
  surface: '#2A2A2A',
  border: '#3E3E3E',
  text: '#ECECEC',
  textSecondary: '#8E8E8E',
  primary: '#5B6AFF',
  userBubble: '#3B82F6',
  aiBubble: '#1A1A1A',
};

interface Message {
  role: 'user' | 'assistant';
  content: string;
  links?: any[];
  contacts?: any[];
  steps?: string[];
}

// Helper function to extract URLs from text
const extractUrls = (text: string): string[] => {
  const urlPattern = /(https?:\/\/[^\s]+)/g;
  const matches = text.match(urlPattern);
  return matches || [];
};

export default function TaskDetailScreen() {
  const { id } = useLocalSearchParams();
  const router = useRouter();
  const { t } = useTranslation();
  const [task, setTask] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showChat, setShowChat] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [sending, setSending] = useState(false);
  const [creatingSubtasks, setCreatingSubtasks] = useState(false);
  const [lastQuestion, setLastQuestion] = useState<string>('');
  const [conversationId, setConversationId] = useState<number | null>(null);
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    loadTask();
    loadConversationHistory();
  }, [id]);

  // Clear messages when task changes
  useEffect(() => {
    setMessages([]);
    setShowChat(true);
    setInputText('');
    setConversationId(null);
  }, [id]);

  const loadTask = async () => {
    try {
      setLoading(true);
      // Get task details
      const response = await todosAPI.getTodos();
      const allTasks = response.data.results || response.data;
      const taskData = allTasks.find((t: any) => t.id === Number(id));

      if (taskData) {
        setTask(taskData);

        // Generate description if it doesn't exist
        if (!taskData.description) {
          try {
            const descResponse = await aiAPI.generateTaskDescription(Number(id));
            setTask(descResponse.data.task);
          } catch (error) {
            console.error('Failed to generate description:', error);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load task:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadConversationHistory = async () => {
    try {
      console.log('[FRONTEND] Loading conversation history for task:', id);
      const response = await aiAPI.getTaskConversation(Number(id));

      if (response.data.conversation_id && response.data.messages.length > 0) {
        console.log('[FRONTEND] Found existing conversation:', response.data.conversation_id);
        console.log('[FRONTEND] Messages count:', response.data.messages.length);

        setConversationId(response.data.conversation_id);

        // Convert backend messages to frontend Message format
        const loadedMessages: Message[] = response.data.messages.map((msg: any) => ({
          role: msg.role,
          content: msg.content,
          links: msg.links || [],
          contacts: msg.contacts || [],
          steps: msg.steps || [],
        }));

        setMessages(loadedMessages);
        console.log('[FRONTEND] Loaded conversation history successfully');
      } else {
        console.log('[FRONTEND] No existing conversation found');
      }
    } catch (error) {
      console.error('[FRONTEND] Failed to load conversation history:', error);
      // Don't show error to user, just start fresh conversation
    }
  };

  const handleAskAI = async (question: string) => {
    if (!question.trim() || sending) return;

    console.log('\n' + '='.repeat(80));
    console.log('[FRONTEND] handleAskAI called');
    console.log('[FRONTEND] Task ID:', id);
    console.log('[FRONTEND] Question:', question.trim());
    console.log('[FRONTEND] Current messages count:', messages.length);
    console.log('[FRONTEND] Conversation ID:', conversationId);
    console.log('='.repeat(80) + '\n');

    const userMessage: Message = {
      role: 'user',
      content: question.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setSending(true);

    try {
      console.log('[FRONTEND] Sending request to backend...');
      console.log('[FRONTEND] Conversation ID:', conversationId || 'New conversation');

      const response = await aiAPI.askTaskAI(Number(id), question.trim(), conversationId || undefined, 'clarify');

      console.log('[FRONTEND] Response received from backend:');
      console.log('[FRONTEND] Response length:', response.data.response?.length || 0);
      console.log('[FRONTEND] Links count:', response.data.links?.length || 0);
      console.log('[FRONTEND] Contacts count:', response.data.contacts?.length || 0);
      console.log('[FRONTEND] Steps count:', response.data.steps?.length || 0);
      console.log('[FRONTEND] Conversation ID:', response.data.conversation_id);
      console.log('[FRONTEND] First 200 chars of response:', response.data.response?.substring(0, 200));

      // Save conversation ID for future requests
      if (response.data.conversation_id && !conversationId) {
        setConversationId(response.data.conversation_id);
        console.log('[FRONTEND] Saved new conversation ID:', response.data.conversation_id);
      }

      const aiMessage: Message = {
        role: 'assistant',
        content: response.data.response,
        links: response.data.links || [],
        contacts: response.data.contacts || [],
        steps: response.data.steps || [],
      };

      setMessages((prev) => [...prev, aiMessage]);

      // Scroll to bottom
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
    } catch (error) {
      console.error('[FRONTEND] ERROR: Failed to get AI response:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setSending(false);
    }
  };

  const handleCreateSubtasks = async (steps: string[]) => {
    if (!steps || steps.length === 0) return;

    try {
      setCreatingSubtasks(true);
      console.log('[FRONTEND] Creating subtasks from steps:', steps);

      await aiAPI.createSubtasksFromAI(Number(id), steps);

      Alert.alert(
        'Success',
        `Created ${steps.length} subtasks! You can see them in your task list.`,
        [{ text: 'OK' }]
      );
    } catch (error) {
      console.error('[FRONTEND] Error creating subtasks:', error);
      Alert.alert('Error', 'Failed to create subtasks. Please try again.');
    } finally {
      setCreatingSubtasks(false);
    }
  };

  const handleOpenUrl = async (url: string) => {
    try {
      const canOpen = await Linking.canOpenURL(url);
      if (canOpen) {
        await Linking.openURL(url);
      } else {
        Alert.alert('Error', 'Cannot open this URL');
      }
    } catch (error) {
      console.error('Error opening URL:', error);
      Alert.alert('Error', 'Failed to open URL');
    }
  };

  const renderMessage = (message: Message, index: number) => {
    const isUser = message.role === 'user';

    return (
      <View
        key={index}
        style={[
          styles.messageContainer,
          isUser ? styles.userMessageContainer : styles.aiMessageContainer,
        ]}
      >
        <View
          style={[
            styles.messageBubble,
            {
              backgroundColor: isUser ? COLORS.userBubble : COLORS.aiBubble,
              borderColor: isUser ? 'transparent' : COLORS.border,
            },
          ]}
        >
          {!isUser && (
            <View style={styles.aiIconContainer}>
              <MaterialCommunityIcons name="sparkles" as any size={16} color={COLORS.primary} />
            </View>
          )}

          <Text style={styles.messageText}>{message.content}</Text>

          {/* Links */}
          {message.links && message.links.length > 0 && (
            <View style={styles.linksContainer}>
              <Text style={styles.sectionTitle}>{t('taskDetails.sections.links')}</Text>
              {message.links.map((link, idx) => (
                <TouchableOpacity key={idx} style={styles.linkItem}>
                  <MaterialCommunityIcons name="open-in-new" size={14} color={COLORS.primary} />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.linkTitle}>{link.title}</Text>
                    <Text style={styles.linkUrl} numberOfLines={1}>{link.url}</Text>
                    {link.description && (
                      <Text style={styles.linkDescription}>{link.description}</Text>
                    )}
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          )}

          {/* Contacts */}
          {message.contacts && message.contacts.length > 0 && (
            <View style={styles.contactsContainer}>
              <Text style={styles.sectionTitle}>{t('taskDetails.sections.contacts')}</Text>
              {message.contacts.map((contact, idx) => (
                <View key={idx} style={styles.contactItem}>
                  <MaterialCommunityIcons
                    name={contact.type === 'email' ? 'email' : 'phone'}
                    size={14}
                    color={COLORS.primary}
                  />
                  <Text style={styles.contactText}>
                    <Text style={styles.contactLabel}>{contact.label}: </Text>
                    {contact.value}
                  </Text>
                </View>
              ))}
            </View>
          )}

          {/* Steps */}
          {message.steps && message.steps.length > 0 && (
            <View style={styles.stepsContainer}>
              <Text style={styles.sectionTitle}>{t('taskDetails.sections.steps')}</Text>
              {message.steps.map((step, idx) => {
                const urls = extractUrls(step);
                return (
                  <View key={idx} style={styles.stepWithLinkContainer}>
                    <View style={styles.stepItem}>
                      <Text style={styles.stepNumber}>{idx + 1}</Text>
                      <Text style={styles.stepText}>{step}</Text>
                    </View>
                    {urls.length > 0 && (
                      <TouchableOpacity
                        style={styles.stepLinkButton}
                        onPress={() => handleOpenUrl(urls[0])}
                      >
                        <MaterialCommunityIcons name="open-in-new" size={14} color={COLORS.primary} />
                        <Text style={styles.stepLinkButtonText}>Open Link</Text>
                      </TouchableOpacity>
                    )}
                  </View>
                );
              })}

              {/* Add to Tasks Button */}
              <TouchableOpacity
                style={styles.addToTasksButton}
                onPress={() => handleCreateSubtasks(message.steps!)}
                disabled={creatingSubtasks}
              >
                <MaterialCommunityIcons
                  name="plus-circle"
                  size={18}
                  color={COLORS.primary}
                />
                <Text style={styles.addToTasksText}>
                  {creatingSubtasks ? t('taskDetails.creating') : t('taskDetails.addToTasks')}
                </Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  if (!task) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <MaterialCommunityIcons name="arrow-left" size={24} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>{t('taskDetails.taskNotFound')}</Text>
        </View>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={0}
    >
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <MaterialCommunityIcons name="arrow-left" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('taskDetails.title')}</Text>
      </View>
      <ScrollView
        ref={scrollViewRef}
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Task Info */}
        <View style={styles.taskCard}>
          <Text style={styles.taskTitle}>{task.title}</Text>

          {task.description && (
            <Text style={styles.taskDescription}>{task.description}</Text>
          )}

          {/* Meta Info */}
          <View style={styles.metaRow}>
            <View style={styles.metaBadge}>
              <MaterialCommunityIcons name="clock-outline" size={14} color={COLORS.textSecondary} />
              <Text style={styles.metaText}>{task.timebox_minutes}{t('taskDetails.minutesSuffix')}</Text>
            </View>
            <View style={styles.metaBadge}>
              <MaterialCommunityIcons name="flag" size={14} color={COLORS.textSecondary} />
              <Text style={styles.metaText}>{t('taskDetails.priority')} {task.priority}</Text>
            </View>
            {task.progress_percentage !== undefined && (
              <View style={styles.metaBadge}>
                <MaterialCommunityIcons name="chart-line" size={14} color={COLORS.textSecondary} />
                <Text style={styles.metaText}>{task.progress_percentage}%</Text>
              </View>
            )}
          </View>

          {/* ✅ AI-Generated Steps & Tips */}
          {task.notes && (
            <View style={styles.aiNotesContainer}>
              {/* University Context */}
              {task.notes.university_context && (
                <View style={styles.noteSection}>
                  <View style={styles.noteHeader}>
                    <MaterialCommunityIcons name="information" size={16} color={COLORS.primary} />
                    <Text style={styles.noteTitle}>University Info</Text>
                  </View>
                  <Text style={styles.noteText}>{task.notes.university_context}</Text>
                </View>
              )}

              {/* Steps */}
              {task.notes.steps && task.notes.steps.length > 0 && (
                <View style={styles.noteSection}>
                  <View style={styles.noteHeader}>
                    <MaterialCommunityIcons name="format-list-numbered" size={16} color={COLORS.primary} />
                    <Text style={styles.noteTitle}>Step-by-Step Instructions ({task.notes.steps.length})</Text>
                  </View>
                  {task.notes.steps.map((step: string, idx: number) => {
                    const urls = extractUrls(step);
                    return (
                      <View key={idx} style={styles.stepWithLinkContainer}>
                        <View style={styles.stepItem}>
                          <Text style={styles.stepNumber}>{idx + 1}</Text>
                          <Text style={styles.stepText}>{step}</Text>
                        </View>
                        {urls.length > 0 && (
                          <TouchableOpacity
                            style={styles.stepLinkButton}
                            onPress={() => handleOpenUrl(urls[0])}
                          >
                            <MaterialCommunityIcons name="open-in-new" size={14} color={COLORS.primary} />
                            <Text style={styles.stepLinkButtonText}>Open Link</Text>
                          </TouchableOpacity>
                        )}
                      </View>
                    );
                  })}
                </View>
              )}

              {/* Tips */}
              {task.notes.tips && task.notes.tips.length > 0 && (
                <View style={styles.noteSection}>
                  <View style={styles.noteHeader}>
                    <MaterialCommunityIcons name="lightbulb-on" size={16} color={COLORS.primary} />
                    <Text style={styles.noteTitle}>Tips & Advice</Text>
                  </View>
                  {task.notes.tips.map((tip: string, idx: number) => (
                    <View key={idx} style={styles.tipItem}>
                      <MaterialCommunityIcons name="check-circle" size={12} color={COLORS.primary} />
                      <Text style={styles.tipText}>{tip}</Text>
                    </View>
                  ))}
                </View>
              )}

              {/* Estimated Cost */}
              {task.notes.estimated_cost && (
                <View style={styles.noteSection}>
                  <View style={styles.noteHeader}>
                    <MaterialCommunityIcons name="cash" size={16} color={COLORS.primary} />
                    <Text style={styles.noteTitle}>Estimated Cost</Text>
                  </View>
                  <Text style={styles.noteText}>{task.notes.estimated_cost}</Text>
                </View>
              )}
            </View>
          )}

          {/* Split Task Button */}
          <View style={styles.actionButtonsRow}>
            <TaskSplitButton
              taskId={Number(id)}
              taskTitle={task.title}
              onSplitComplete={loadTask}
            />
          </View>
        </View>

        {/* AI Chat Interface */}
        {showChat && (
          <View style={styles.chatContainer}>
            <View style={styles.chatHeader}>
              <MaterialCommunityIcons name="lightbulb-on" size={24} color={COLORS.primary} />
              <Text style={styles.chatHeaderText}>{t('taskDetails.aiAssistant')}</Text>
            </View>

            {messages.length === 0 && (
              <View style={styles.emptyChat}>
                <Text style={styles.emptyChatText}>
                  {t('taskDetails.emptyChat')}
                </Text>
                <Text style={styles.emptyChatSubtext}>
                  {t('taskDetails.examples')}
                </Text>
              </View>
            )}

            {messages.map((message, index) => renderMessage(message, index))}

            {sending && (
              <View style={styles.typingIndicator}>
                <ActivityIndicator size="small" color={COLORS.primary} />
                <Text style={styles.typingText}>{t('taskDetails.aiThinking')}</Text>
              </View>
            )}
          </View>
        )}
      </ScrollView>

      {/* Chat Input */}
      {showChat && (
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder={t('taskDetails.placeholder')}
            placeholderTextColor={COLORS.textSecondary}
            value={inputText}
            onChangeText={setInputText}
            onSubmitEditing={() => handleAskAI(inputText)}
            editable={!sending}
          />
          <TouchableOpacity
            style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
            onPress={() => handleAskAI(inputText)}
            disabled={!inputText.trim() || sending}
          >
            <MaterialCommunityIcons
              name="send"
              size={20}
              color={inputText.trim() ? COLORS.primary : COLORS.textSecondary}
            />
          </TouchableOpacity>
        </View>
      )}
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.bg,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 60,
    paddingBottom: 16,
    backgroundColor: COLORS.bg,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backButton: {
    marginRight: 12,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
  },
  taskCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: 16,
  },
  taskTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 12,
    lineHeight: 28,
  },
  taskDescription: {
    fontSize: 15,
    color: COLORS.textSecondary,
    lineHeight: 22,
    marginBottom: 16,
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  metaBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: COLORS.bg,
  },
  metaText: {
    fontSize: 12,
    fontWeight: '500',
    color: COLORS.textSecondary,
  },
  actionButtonsRow: {
    marginTop: 12,
    gap: 8,
  },
  askAIMainButtonContainer: {
    flex: 1,
  },
  askAIMainButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    paddingVertical: 14,
    borderRadius: 12,
  },
  askAIMainButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#fff',
    letterSpacing: 0.5,
  },
  chatContainer: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: 16,
  },
  chatHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  chatHeaderText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  emptyChat: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  emptyChatText: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 8,
  },
  emptyChatSubtext: {
    fontSize: 13,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
  },
  messageContainer: {
    marginBottom: 12,
  },
  userMessageContainer: {
    alignItems: 'flex-end',
  },
  aiMessageContainer: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '90%',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
  },
  aiIconContainer: {
    marginBottom: 4,
  },
  messageText: {
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 20,
  },
  linksContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textSecondary,
    marginBottom: 8,
    textTransform: 'uppercase',
  },
  linkItem: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
    padding: 8,
    backgroundColor: COLORS.bg,
    borderRadius: 8,
  },
  linkTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: 2,
  },
  linkUrl: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginBottom: 2,
  },
  linkDescription: {
    fontSize: 12,
    color: COLORS.text,
  },
  contactsContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  contactItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  },
  contactText: {
    fontSize: 13,
    color: COLORS.text,
  },
  contactLabel: {
    fontWeight: '600',
    color: COLORS.primary,
  },
  stepsContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  stepItem: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  stepNumber: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.primary,
    width: 20,
  },
  stepText: {
    flex: 1,
    fontSize: 13,
    color: COLORS.text,
    lineHeight: 18,
  },
  addToTasksButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 12,
    paddingVertical: 10,
    paddingHorizontal: 16,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
  },
  addToTasksText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
  typingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 8,
  },
  typingText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    fontStyle: 'italic',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 16,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  input: {
    flex: 1,
    backgroundColor: COLORS.bg,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 14,
    color: COLORS.text,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.bg,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
  // ✅ AI-Generated Notes Styles
  aiNotesContainer: {
    marginTop: 16,
    gap: 16,
  },
  noteSection: {
    backgroundColor: COLORS.bg,
    borderRadius: 12,
    padding: 12,
    gap: 8,
  },
  noteHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  noteTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  noteText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    lineHeight: 18,
  },
  stepItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginBottom: 8,
  },
  tipItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginBottom: 6,
  },
  tipText: {
    flex: 1,
    fontSize: 13,
    color: COLORS.textSecondary,
    lineHeight: 18,
  },
  stepWithLinkContainer: {
    marginBottom: 12,
  },
  stepLinkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: COLORS.primary + '20',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  stepLinkButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
  },
});
