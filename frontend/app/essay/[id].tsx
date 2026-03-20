import { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  TextInput,
  Alert,
  ActivityIndicator,
  Modal,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { colors, spacing, borderRadius } from '@/theme';
import LiquidGlassCard from '@/components/LiquidGlassCard';
import { essaysAPI } from '@/services/api';

type AIAssistantMode = 'brainstorm' | 'outline' | 'review' | 'enhance' | 'chat';

interface EssayProject {
  id: number;
  title: string;
  essay_type: string;
  target_university: string;
  status: string;
  current_draft: string;
  word_count: number;
  word_count_goal: number;
  progress_percentage: number;
  brainstorming_notes: any[];
  selected_topic: any;
  outline_suggestions: any;
}

export default function EssayEditorScreen() {
  const { id } = useLocalSearchParams();
  const router = useRouter();
  const [essay, setEssay] = useState<EssayProject | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState('');
  const [wordCount, setWordCount] = useState(0);
  const [showAIAssistant, setShowAIAssistant] = useState(false);
  const [aiMode, setAiMode] = useState<AIAssistantMode>('brainstorm');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState<any>(null);

  // Load essay data
  const loadEssay = async () => {
    try {
      setLoading(true);
      const response = await essaysAPI.getProject(Number(id));
      const data = response.data;
      setEssay(data);
      setDraft(data.current_draft || '');
      setWordCount(data.word_count || 0);
    } catch (error) {
      console.error('Error loading essay:', error);
      Alert.alert('Error', 'Failed to load essay');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEssay();
  }, [id]);

  // Update word count when draft changes
  useEffect(() => {
    const words = draft.trim().split(/\s+/).filter(w => w.length > 0);
    setWordCount(words.length);
  }, [draft]);

  // Save draft
  const saveDraft = async () => {
    if (!essay) return;

    try {
      setSaving(true);
      await essaysAPI.saveDraft(essay.id, draft);

      // Update word count
      const wordCountValue = draft.trim().split(/\s+/).filter(w => w.length > 0).length;
      setWordCount(wordCountValue);

      // Update essay data without full reload
      setEssay({ ...essay, current_draft: draft, word_count: wordCountValue });
    } catch (error) {
      console.error('Error saving draft:', error);
      Alert.alert('Error', 'Failed to save draft');
    } finally {
      setSaving(false);
    }
  };

  // AI Assistant functions
  const startBrainstorming = async () => {
    if (!essay) return;

    setAiMode('brainstorm');
    setAiLoading(true);
    setShowAIAssistant(true);

    try {
      // TODO: Replace with actual API call
      // const response = await essaysAPI.brainstorm(essay.id);
      // setAiResponse(response.data);

      // Mock response
      setTimeout(() => {
        setAiResponse({
          topics: [
            {
              title: 'The Robot That Changed My Perspective',
              theme: 'Curiosity and Learning',
              compelling: 'Shows growth through engineering project',
              anecdotes: ['Moment when robot first worked', 'Failures and iterations', 'Team collaboration'],
              fit: 'Demonstrates MIT\'s hands-on learning culture'
            },
            {
              title: 'Teaching Myself to Code at 2 AM',
              theme: 'Self-Directed Learning',
              compelling: 'Authentic passion for problem-solving',
              anecdotes: ['First bug that took hours', 'Breakthrough moment', 'Building first app'],
              fit: 'Shows initiative and persistence'
            }
          ]
        });
        setAiLoading(false);
      }, 2000);
    } catch (error) {
      Alert.alert('Error', 'Failed to generate topics');
      setAiLoading(false);
    }
  };

  const generateOutline = async () => {
    if (!essay || !essay.selected_topic) {
      Alert.alert('Topic Required', 'Please select a topic first');
      return;
    }

    setAiMode('outline');
    setAiLoading(true);
    setShowAIAssistant(true);

    try {
      // TODO: Replace with actual API call
      // const response = await essaysAPI.generateOutline(essay.id, {
      //   topic: essay.selected_topic
      // });
      // setAiResponse(response.data);

      // Mock response
      setTimeout(() => {
        setAiResponse({
          outline: {
            introduction: 'Hook: The moment I held my first soldering iron (75 words)',
            body_paragraphs: [
              {
                section: 'The Challenge',
                points: ['Building my first robot', 'Technical obstacles', 'Late nights debugging'],
                suggested_words: 200
              },
              {
                section: 'The Growth',
                points: ['Skills learned', 'Mentorship received', 'Team dynamics'],
                suggested_words: 200
              },
              {
                section: 'The Impact',
                points: ['Robot competition success', 'Teaching others', 'Future projects'],
                suggested_words: 150
              }
            ],
            conclusion: 'Connection to MIT\'s maker culture (75 words)',
            themes: ['Hands-on learning', 'Collaboration', 'Innovation'],
            total_words: 650
          }
        });
        setAiLoading(false);
      }, 2000);
    } catch (error) {
      Alert.alert('Error', 'Failed to generate outline');
      setAiLoading(false);
    }
  };

  const getFeedback = async () => {
    if (wordCount < 50) {
      Alert.alert('Too Short', 'Please write at least 50 words before requesting feedback');
      return;
    }

    setAiMode('review');
    setAiLoading(true);
    setShowAIAssistant(true);

    try {
      // TODO: Replace with actual API call
      // const response = await essaysAPI.getFeedback(essay.id);
      // setAiResponse(response.data);

      // Mock response
      setTimeout(() => {
        setAiResponse({
          feedback: {
            strengths: [
              'Strong opening hook that grabs attention',
              'Authentic voice comes through clearly',
              'Good use of specific details and anecdotes'
            ],
            improvements: [
              'Consider adding more sensory details to bring moments to life',
              'Transition between paragraphs could be smoother',
              'Connect more explicitly to MIT\'s programs and culture'
            ],
            structure_feedback: 'Overall structure is effective. Consider rearranging paragraph 3 to come before paragraph 2 for better flow.',
            content_feedback: 'Content is compelling and specific. The robot building narrative effectively demonstrates your growth.',
            voice_feedback: 'Your authentic voice shines through. Avoid cliché phrases and trust your unique perspective.',
            score: 8
          }
        });
        setAiLoading(false);
      }, 3000);
    } catch (error) {
      Alert.alert('Error', 'Failed to get feedback');
      setAiLoading(false);
    }
  };

  const selectTopic = (topic: any) => {
    if (!essay) return;

    Alert.alert(
      'Select Topic',
      `Use "${topic.title}" for your essay?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Select',
          onPress: async () => {
            try {
              // TODO: Replace with actual API call
              // await essaysAPI.selectTopic(essay.id, { topic });

              setEssay({ ...essay, selected_topic: topic });
              Alert.alert('Topic Selected', 'Now you can generate an outline or start writing!');
              setShowAIAssistant(false);
            } catch (error) {
              Alert.alert('Error', 'Failed to select topic');
            }
          }
        }
      ]
    );
  };

  const renderAIAssistantContent = () => {
    if (aiLoading) {
      return (
        <View style={styles.aiLoadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.aiLoadingText}>
            {aiMode === 'brainstorm' && 'Generating creative topics...'}
            {aiMode === 'outline' && 'Creating detailed outline...'}
            {aiMode === 'review' && 'Analyzing your essay...'}
          </Text>
        </View>
      );
    }

    if (aiMode === 'brainstorm' && aiResponse?.topics) {
      return (
        <View>
          <Text style={styles.aiSectionTitle}>Topic Ideas</Text>
          {aiResponse.topics.map((topic: any, index: number) => (
            <TouchableOpacity
              key={index}
              style={styles.topicCard}
              onPress={() => selectTopic(topic)}
            >
              <Text style={styles.topicTitle}>{topic.title}</Text>
              <Text style={styles.topicTheme}>Theme: {topic.theme}</Text>
              <Text style={styles.topicDescription}>{topic.compelling}</Text>
              <View style={styles.topicActions}>
                <MaterialCommunityIcons name="check-circle" size={20} color={colors.primary} />
                <Text style={styles.topicActionText}>Select This Topic</Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>
      );
    }

    if (aiMode === 'outline' && aiResponse?.outline) {
      const outline = aiResponse.outline;
      return (
        <View>
          <Text style={styles.aiSectionTitle}>Essay Outline</Text>
          <View style={styles.outlineSection}>
            <Text style={styles.outlineLabel}>Introduction</Text>
            <Text style={styles.outlineText}>{outline.introduction}</Text>
          </View>

          {outline.body_paragraphs?.map((paragraph: any, index: number) => (
            <View key={index} style={styles.outlineSection}>
              <Text style={styles.outlineLabel}>{paragraph.section}</Text>
              <Text style={styles.outlineWords}>{paragraph.suggested_words} words</Text>
              {paragraph.points?.map((point: string, i: number) => (
                <Text key={i} style={styles.outlineBullet}>• {point}</Text>
              ))}
            </View>
          ))}

          <View style={styles.outlineSection}>
            <Text style={styles.outlineLabel}>Conclusion</Text>
            <Text style={styles.outlineText}>{outline.conclusion}</Text>
          </View>

          <Text style={styles.outlineTotal}>Total: {outline.total_words} words</Text>
        </View>
      );
    }

    if (aiMode === 'review' && aiResponse?.feedback) {
      const feedback = aiResponse.feedback;
      return (
        <ScrollView style={styles.feedbackContainer}>
          <View style={styles.scoreContainer}>
            <Text style={styles.scoreLabel}>Essay Score</Text>
            <Text style={styles.scoreValue}>{feedback.score}/10</Text>
          </View>

          <View style={styles.feedbackSection}>
            <Text style={styles.feedbackSectionTitle}>✅ Strengths</Text>
            {feedback.strengths?.map((strength: string, index: number) => (
              <Text key={index} style={styles.feedbackItem}>• {strength}</Text>
            ))}
          </View>

          <View style={styles.feedbackSection}>
            <Text style={styles.feedbackSectionTitle}>💡 Improvements</Text>
            {feedback.improvements?.map((improvement: string, index: number) => (
              <Text key={index} style={styles.feedbackItem}>• {improvement}</Text>
            ))}
          </View>

          {feedback.structure_feedback && (
            <View style={styles.feedbackSection}>
              <Text style={styles.feedbackSectionTitle}>📐 Structure</Text>
              <Text style={styles.feedbackText}>{feedback.structure_feedback}</Text>
            </View>
          )}

          {feedback.content_feedback && (
            <View style={styles.feedbackSection}>
              <Text style={styles.feedbackSectionTitle}>📝 Content</Text>
              <Text style={styles.feedbackText}>{feedback.content_feedback}</Text>
            </View>
          )}

          {feedback.voice_feedback && (
            <View style={styles.feedbackSection}>
              <Text style={styles.feedbackSectionTitle}>🗣 Voice</Text>
              <Text style={styles.feedbackText}>{feedback.voice_feedback}</Text>
            </View>
          )}
        </ScrollView>
      );
    }

    return null;
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (!essay) {
    return (
      <View style={styles.errorContainer}>
        <MaterialCommunityIcons name="file-question" size={80} color={colors.textTertiary} />
        <Text style={styles.errorTitle}>Essay Not Found</Text>
        <TouchableOpacity style={styles.errorButton} onPress={() => router.back()}>
          <Text style={styles.errorButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Compact Header */}
      <View style={styles.compactHeader}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <MaterialCommunityIcons name="arrow-left" size={24} color={colors.text} />
        </TouchableOpacity>
        <View style={styles.headerInfo}>
          <Text style={styles.headerTitle} numberOfLines={1}>{essay.title}</Text>
          <Text style={styles.headerMeta}>{essay.target_university} • {wordCount}/{essay.word_count_goal} words</Text>
        </View>
        <TouchableOpacity onPress={saveDraft} disabled={saving} style={styles.saveButton}>
          <MaterialCommunityIcons
            name={saving ? "loading" : "content-save"}
            size={24}
            color={saving ? colors.textTertiary : colors.primary}
          />
        </TouchableOpacity>
      </View>

      {/* AI Action Buttons - Compact */}
      <View style={styles.compactActions}>
        <TouchableOpacity
          style={styles.compactActionButton}
          onPress={startBrainstorming}
        >
          <MaterialCommunityIcons name="lightbulb" size={18} color={colors.primary} />
          <Text style={styles.compactActionText}>Brainstorm</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.compactActionButton}
          onPress={generateOutline}
          disabled={!essay.selected_topic}
        >
          <MaterialCommunityIcons name="format-list-bulleted" size={18} color={colors.primary} />
          <Text style={styles.compactActionText}>Outline</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.compactActionButton}
          onPress={getFeedback}
        >
          <MaterialCommunityIcons name="chat-question" size={18} color={colors.primary} />
          <Text style={styles.compactActionText}>Feedback</Text>
        </TouchableOpacity>
      </View>

      {/* Editor - Main Focus */}
      <TextInput
        style={styles.editor}
        multiline
        placeholder="Start writing your essay here..."
        placeholderTextColor={colors.textTertiary}
        value={draft}
        onChangeText={setDraft}
        textAlignVertical="top"
        autoFocus
      />

      {/* Save Indicator */}
      {saving && (
        <View style={styles.savingIndicator}>
          <Text style={styles.savingText}>Saving...</Text>
        </View>
      )}

      {/* AI Assistant Modal */}
      <Modal
        visible={showAIAssistant}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <View style={styles.aiModalContainer}>
          <View style={styles.aiModalHeader}>
            <TouchableOpacity onPress={() => setShowAIAssistant(false)}>
              <MaterialCommunityIcons name="close" size={28} color={colors.text} />
            </TouchableOpacity>
            <Text style={styles.aiModalTitle}>
              {aiMode === 'brainstorm' && 'Brainstorm Topics'}
              {aiMode === 'outline' && 'Essay Outline'}
              {aiMode === 'review' && 'AI Feedback'}
            </Text>
            <View style={{ width: 28 }} />
          </View>

          <ScrollView style={styles.aiModalContent}>
            {renderAIAssistantContent()}
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
    marginTop: spacing.lg,
  },
  errorButton: {
    marginTop: spacing.lg,
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.lg,
  },
  errorButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  // Compact header styles
  compactHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    paddingTop: spacing.xl * 2,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backButton: {
    padding: spacing.sm,
  },
  headerInfo: {
    flex: 1,
    marginLeft: spacing.sm,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
  },
  headerMeta: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  saveButton: {
    padding: spacing.sm,
  },
  // Compact actions
  compactActions: {
    flexDirection: 'row',
    padding: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    justifyContent: 'space-around',
  },
  compactActionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    backgroundColor: colors.card,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  compactActionText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.primary,
    marginLeft: spacing.xs,
  },
  savingIndicator: {
    position: 'absolute',
    bottom: spacing.xl,
    alignSelf: 'center',
    backgroundColor: colors.card,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
    borderWidth: 1,
    borderColor: colors.border,
  },
  savingText: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  editorContainer: {
    flex: 1,
    padding: spacing.lg,
  },
  editor: {
    flex: 1,
    fontSize: 16,
    lineHeight: 24,
    color: colors.text,
    textAlignVertical: 'top',
  },
  aiModalContainer: {
    flex: 1,
    backgroundColor: colors.background,
  },
  aiModalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.lg,
    paddingTop: spacing.xl * 2,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  aiModalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text,
  },
  aiModalContent: {
    flex: 1,
    padding: spacing.lg,
  },
  aiLoadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  aiLoadingText: {
    fontSize: 16,
    color: colors.textSecondary,
    marginTop: spacing.md,
  },
  aiSectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: spacing.lg,
  },
  topicCard: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  topicTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  topicTheme: {
    fontSize: 14,
    color: colors.primary,
    marginBottom: spacing.sm,
  },
  topicDescription: {
    fontSize: 14,
    color: colors.textSecondary,
    marginBottom: spacing.md,
    lineHeight: 20,
  },
  topicActions: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing.sm,
  },
  topicActionText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.primary,
    marginLeft: spacing.sm,
  },
  outlineSection: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  outlineLabel: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  outlineWords: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  outlineText: {
    fontSize: 14,
    color: colors.textSecondary,
    lineHeight: 20,
  },
  outlineBullet: {
    fontSize: 14,
    color: colors.text,
    marginLeft: spacing.sm,
    marginBottom: spacing.xs,
  },
  outlineTotal: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.primary,
    textAlign: 'center',
    marginTop: spacing.md,
  },
  scoreContainer: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
    alignItems: 'center',
    marginBottom: spacing.lg,
    borderWidth: 2,
    borderColor: colors.primary,
  },
  scoreLabel: {
    fontSize: 16,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  scoreValue: {
    fontSize: 48,
    fontWeight: 'bold',
    color: colors.primary,
  },
  feedbackContainer: {
    flex: 1,
  },
  feedbackSection: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  feedbackSectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: spacing.md,
  },
  feedbackItem: {
    fontSize: 14,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
    lineHeight: 20,
  },
  feedbackText: {
    fontSize: 14,
    color: colors.textSecondary,
    lineHeight: 20,
  },
});
