import { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  Alert,
  ActivityIndicator,
  Modal,
  ScrollView,
  TextInput,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { colors, spacing, borderRadius } from '@/theme';
import LiquidGlassCard from '@/components/LiquidGlassCard';
import { essaysAPI } from '@/services/api';

// Essay types and their colors
const getEssayTypeColor = (type: string): string => {
  const colors: { [key: string]: string } = {
    'personal_statement': '#3B82F6',  // Blue
    'why_college': '#10B981',         // Green
    'why_major': '#8B5CF6',           // Purple
    'leadership': '#F59E0B',          // Orange
    'challenge': '#EF4444',           // Red
    'activity': '#06B6D4',            // Cyan
    'community': '#EC4899',           // Pink
    'achievement': '#F97316',         // Orange-Red
    'creative': '#A855F7',            // Purple
    'supplemental': '#6B7280',        // Gray
  };
  return colors[type] || '#5B6AFF';
};

const getEssayTypeIcon = (type: string): string => {
  const icons: { [key: string]: string } = {
    'personal_statement': '📝',
    'why_college': '🎓',
    'why_major': '🔬',
    'leadership': '👥',
    'challenge': '💪',
    'activity': '🎯',
    'community': '🤝',
    'achievement': '🏆',
    'creative': '🎨',
    'supplemental': '✍️',
  };
  return icons[type] || '📄';
};

const getStatusColor = (status: string): string => {
  const colors: { [key: string]: string } = {
    'brainstorming': '#6B7280',  // Gray
    'outlining': '#3B82F6',      // Blue
    'drafting': '#F59E0B',       // Orange
    'reviewing': '#8B5CF6',      // Purple
    'polishing': '#10B981',      // Green
    'completed': '#06B6D4',      // Cyan
  };
  return colors[status] || '#6B7280';
};

const getStatusLabel = (status: string): string => {
  const labels: { [key: string]: string } = {
    'brainstorming': 'Brainstorming',
    'outlining': 'Outlining',
    'drafting': 'Drafting',
    'reviewing': 'Reviewing',
    'polishing': 'Polishing',
    'completed': 'Completed',
  };
  return labels[status] || status;
};

// Essay templates data (from backend)
const ESSAY_TEMPLATES = [
  {
    id: 1,
    name: 'Common App Personal Statement',
    essay_type: 'personal_statement',
    word_count_min: 250,
    word_count_max: 650,
    description: 'Your main personal statement for the Common Application'
  },
  {
    id: 2,
    name: 'Why This College',
    essay_type: 'why_college',
    word_count_min: 100,
    word_count_max: 500,
    description: 'Explain why you want to attend a specific university'
  },
  {
    id: 3,
    name: 'Why This Major',
    essay_type: 'why_major',
    word_count_min: 150,
    word_count_max: 500,
    description: 'Describe your intended major and passion'
  },
  {
    id: 4,
    name: 'Leadership Experience',
    essay_type: 'leadership',
    word_count_min: 200,
    word_count_max: 500,
    description: 'Share a leadership experience and impact'
  },
  {
    id: 5,
    name: 'Overcoming Challenge',
    essay_type: 'challenge',
    word_count_min: 250,
    word_count_max: 650,
    description: 'Discuss a challenge you\'ve overcome'
  },
];

export default function EssaysScreen() {
  const router = useRouter();
  const [essays, setEssays] = useState<any[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [showUniversityInput, setShowUniversityInput] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
  const [universityName, setUniversityName] = useState('');

  // Debug: Log when showUniversityInput changes
  useEffect(() => {
    console.log('showUniversityInput changed to:', showUniversityInput);
  }, [showUniversityInput]);

  // Load essays and templates
  const loadData = async () => {
    try {
      // Load templates from backend
      const templatesResponse = await essaysAPI.getTemplates();
      // Backend returns {templates: [...], count: N}
      setTemplates(templatesResponse.data.templates || []);

      // Load essay projects
      const essaysResponse = await essaysAPI.getProjects();
      // Backend returns {projects: [...], count: N} or just [...]
      setEssays(essaysResponse.data.projects || essaysResponse.data || []);
    } catch (error) {
      console.error('Error loading essays:', error);
      Alert.alert('Error', 'Failed to load essays');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const startNewEssay = (template: any) => {
    console.log('Starting new essay:', template.name);
    setSelectedTemplate(template);
    setShowTemplates(false); // Close template modal first
    setTimeout(() => {
      console.log('About to show university input modal');
      setShowUniversityInput(true); // Then show university input
    }, 300);
  };

  const createEssayProject = async () => {
    if (!universityName.trim()) {
      Alert.alert('Required', 'Please enter a university name');
      return;
    }

    try {
      // Call API to create essay project
      const response = await essaysAPI.startEssay({
        template_id: selectedTemplate.id,
        target_university: universityName
      });

      const newEssay = response.data;

      Alert.alert(
        'Success!',
        `Created "${selectedTemplate.name}" for ${universityName}`,
        [
          { text: 'Start Writing', onPress: () => {
            router.push(`/essay/${newEssay.id}`);
          }},
          { text: 'OK' }
        ]
      );

      setShowUniversityInput(false);
      setUniversityName('');
      setSelectedTemplate(null);
      loadData(); // Refresh the list to show the new essay
    } catch (error) {
      console.error('Error creating essay:', error);
      Alert.alert('Error', 'Failed to create essay project');
    }
  };

  const renderEssayCard = ({ item }: { item: any }) => {
    const progress = item.progress_percentage || 0;
    const wordCount = item.word_count || 0;
    const wordCountGoal = item.word_count_goal || 650;

    return (
      <TouchableOpacity
        style={styles.essayCard}
        onPress={() => router.push(`/essay/${item.id}`)}
      >
        <View style={styles.essayCardHeader}>
          <View style={styles.essayTitleContainer}>
            <Text style={styles.essayTypeIcon}>
              {getEssayTypeIcon(item.essay_type)}
            </Text>
            <View style={styles.essayTitleText}>
              <Text style={styles.essayTitle}>{item.title}</Text>
              <Text style={styles.essayUniversity}>{item.target_university || 'General'}</Text>
            </View>
          </View>
          <View style={[styles.statusBadge, { backgroundColor: getStatusColor(item.status) }]}>
            <Text style={styles.statusText}>{getStatusLabel(item.status)}</Text>
          </View>
        </View>

        {/* Progress Bar */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBackground}>
            <View style={[styles.progressFill, { width: `${progress}%` }]} />
          </View>
          <Text style={styles.progressText}>{progress}%</Text>
        </View>

        {/* Word Count */}
        <View style={styles.wordCountContainer}>
          <MaterialCommunityIcons name="text" size={16} color={colors.textSecondary} />
          <Text style={styles.wordCountText}>
            {wordCount} / {wordCountGoal} words
          </Text>
        </View>

        {/* Actions */}
        <View style={styles.essayActions}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push(`/essay/${item.id}`)}
          >
            <MaterialCommunityIcons name="pencil" size={18} color={colors.primary} />
            <Text style={styles.actionText}>Edit</Text>
          </TouchableOpacity>
          {item.status === 'drafting' && (
            <TouchableOpacity style={styles.actionButton}>
              <MaterialCommunityIcons name="chat" size={18} color={colors.primary} />
              <Text style={styles.actionText}>Get Feedback</Text>
            </TouchableOpacity>
          )}
        </View>
      </TouchableOpacity>
    );
  };

  const renderTemplateCard = ({ item }: { item: any }) => (
    <TouchableOpacity
      style={styles.templateCard}
      onPress={() => startNewEssay(item)}
      activeOpacity={0.7}
    >
      <Text style={styles.templateIcon}>{getEssayTypeIcon(item.essay_type)}</Text>
      <Text style={styles.templateName}>{item.name}</Text>
      <Text style={styles.templateWordCount}>
        {item.word_count_min} - {item.word_count_max} words
      </Text>
      <Text style={styles.templateDescription}>{item.description}</Text>
      <View style={styles.templateAction}>
        <MaterialCommunityIcons name="plus" size={20} color={colors.primary} />
        <Text style={styles.templateActionText}>Create Essay</Text>
      </View>
    </TouchableOpacity>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <MaterialCommunityIcons name="file-document-edit" size={80} color={colors.textTertiary} />
      <Text style={styles.emptyTitle}>No Essays Yet</Text>
      <Text style={styles.emptyDescription}>
        Start your college application essays with AI-powered assistance
      </Text>
      <TouchableOpacity
        style={styles.startButton}
        onPress={() => setShowTemplates(true)}
      >
        <MaterialCommunityIcons name="plus" size={24} color="#fff" />
        <Text style={styles.startButtonText}>Start Your First Essay</Text>
      </TouchableOpacity>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Essays</Text>
          <Text style={styles.headerSubtitle}>
            {essays.length} {essays.length === 1 ? 'Essay' : 'Essays'}
          </Text>
        </View>
        <TouchableOpacity
          style={styles.createButton}
          onPress={() => setShowTemplates(true)}
        >
          <MaterialCommunityIcons name="plus" size={20} color="#fff" />
          <Text style={styles.createButtonText}>Create New</Text>
        </TouchableOpacity>
      </View>

      {/* Start New Essay Button */}
      <TouchableOpacity
        style={styles.fab}
        onPress={() => setShowTemplates(true)}
      >
        <MaterialCommunityIcons name="plus" size={24} color="#fff" />
      </TouchableOpacity>

      {/* Essays List or Empty State */}
      {essays.length === 0 ? (
        renderEmptyState()
      ) : (
        <FlatList
          data={essays}
          renderItem={renderEssayCard}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContainer}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        />
      )}

      {/* Template Selection Modal */}
      <Modal
        visible={showTemplates}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowTemplates(false)}>
              <MaterialCommunityIcons name="close" size={28} color={colors.text} />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Choose Essay Type</Text>
            <View style={{ width: 28 }} />
          </View>

          <FlatList
            data={templates}
            renderItem={renderTemplateCard}
            keyExtractor={(item) => item.id.toString()}
            contentContainerStyle={styles.templateList}
            numColumns={2}
            scrollEnabled={true}
          />
        </View>
      </Modal>

      {/* University Input Modal */}
      <Modal
        visible={showUniversityInput}
        animationType="slide"
        transparent={true}
        onRequestClose={() => {
          console.log('Modal onRequestClose called');
          setShowUniversityInput(false);
        }}
      >
        <View style={styles.overlay}>
          <View style={styles.inputModal}>
            <Text style={styles.inputModalTitle}>Target University</Text>
            <Text style={styles.inputModalSubtitle}>
              Which university is this {selectedTemplate?.name?.toLowerCase()} for?
            </Text>

            <TextInput
              style={styles.input}
              placeholder="e.g., MIT, Stanford, Harvard"
              placeholderTextColor={colors.textTertiary}
              value={universityName}
              onChangeText={setUniversityName}
              autoFocus
            />

            <View style={styles.inputActions}>
              <TouchableOpacity
                style={[styles.inputButton, styles.inputButtonCancel]}
                onPress={() => {
                  setShowUniversityInput(false);
                  setUniversityName('');
                  setSelectedTemplate(null);
                }}
              >
                <Text style={styles.inputButtonTextCancel}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.inputButton, styles.inputButtonCreate]}
                onPress={createEssayProject}
              >
                <Text style={styles.inputButtonTextCreate}>Create Essay</Text>
              </TouchableOpacity>
            </View>
          </View>
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.lg,
    paddingTop: spacing.xl * 2,
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  headerSubtitle: {
    fontSize: 16,
    color: colors.textSecondary,
  },
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.lg,
  },
  createButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: spacing.xs,
  },
  listContainer: {
    padding: spacing.md,
  },
  essayCard: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  essayCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  essayTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  essayTypeIcon: {
    fontSize: 24,
    marginRight: spacing.sm,
  },
  essayTitleText: {
    flex: 1,
  },
  essayTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.text,
  },
  essayUniversity: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  statusBadge: {
    paddingHorizontal: spacing.xs,
    paddingVertical: 2,
    borderRadius: borderRadius.sm,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#fff',
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  progressBackground: {
    flex: 1,
    height: 6,
    backgroundColor: colors.background,
    borderRadius: 3,
    overflow: 'hidden',
    marginRight: spacing.xs,
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.primary,
  },
  progressText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.text,
  },
  wordCountContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  wordCountText: {
    fontSize: 12,
    color: colors.textSecondary,
    marginLeft: spacing.xs,
  },
  essayActions: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: spacing.md,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: spacing.lg,
  },
  actionText: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.primary,
    marginLeft: spacing.xs,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
  },
  emptyDescription: {
    fontSize: 16,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.xl,
  },
  startButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.lg,
  },
  startButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginLeft: spacing.sm,
  },
  fab: {
    position: 'absolute',
    bottom: spacing.xl,
    right: spacing.lg,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: colors.background,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.lg,
    paddingTop: spacing.xl * 2,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text,
  },
  templateList: {
    padding: spacing.md,
  },
  templateCard: {
    flex: 1,
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    margin: spacing.xs,
    borderWidth: 1,
    borderColor: colors.border,
    minHeight: 180,
    justifyContent: 'space-between',
  },
  templateIcon: {
    fontSize: 40,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  templateName: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    textAlign: 'center',
    marginBottom: spacing.xs,
  },
  templateWordCount: {
    fontSize: 12,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  templateDescription: {
    fontSize: 11,
    color: colors.textTertiary,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  templateAction: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: spacing.sm,
  },
  templateActionText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.primary,
    marginLeft: spacing.xs,
  },
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  inputModal: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
    width: '100%',
  },
  inputModalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  inputModalSubtitle: {
    fontSize: 14,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },
  input: {
    backgroundColor: colors.background,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    fontSize: 16,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.lg,
  },
  inputActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  inputButton: {
    flex: 1,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
    alignItems: 'center',
  },
  inputButtonCancel: {
    marginRight: spacing.sm,
    backgroundColor: colors.background,
  },
  inputButtonCreate: {
    marginLeft: spacing.sm,
    backgroundColor: colors.primary,
  },
  inputButtonTextCancel: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
  },
  inputButtonTextCreate: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});
