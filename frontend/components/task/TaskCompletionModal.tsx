/**
 * Task Completion Modal
 *
 * Enhanced modal for logging task completion with:
 * - Difficulty rating (1-5 stars)
 * - Completion status (fully/partially/not completed)
 * - Result logging (category-specific)
 * - Quality rating
 * - Time taken
 * - Notes
 * - File attachments
 * - Celebration animation
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  TextInput,
  ActivityIndicator,
  Animated,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { BlurView } from 'expo-blur';
import * as Haptics from 'expo-haptics';
import { todosAPI } from '@/services/api';
import { type TaskCategory } from '@/services/taskCategoriesApi';

const { width, height } = Dimensions.get('window');

interface TaskCompletionModalProps {
  visible: boolean;
  taskId: number;
  taskTitle: string;
  taskCategory?: TaskCategory;
  onClose: () => void;
  onComplete?: (completionData: any) => void;
  estimatedDuration?: number; // in minutes
}

type CompletionStatus = 'fully_completed' | 'partially_completed' | 'not_completed';
type ResultType =
  | 'general'
  | 'essay_word_count'
  | 'test_score'
  | 'portfolio_upload'
  | 'document_submission'
  | 'application_submit'
  | 'practice_test'
  | 'meeting_complete'
  | 'research_complete';

export function TaskCompletionModal({
  visible,
  taskId,
  taskTitle,
  taskCategory,
  onClose,
  onComplete,
  estimatedDuration,
}: TaskCompletionModalProps) {
  const [step, setStep] = useState<'logging' | 'celebrating'>('logging');
  const [loading, setLoading] = useState(false);

  // Form state
  const [difficultyRating, setDifficultyRating] = useState<number>(0);
  const [completionStatus, setCompletionStatus] = useState<CompletionStatus>('fully_completed');
  const [resultType, setResultType] = useState<ResultType>('general');
  const [resultData, setResultData] = useState<Record<string, any>>({});
  const [qualityRating, setQualityRating] = useState<number>(0);
  const [timeTaken, setTimeTaken] = useState<string>('');
  const [notes, setNotes] = useState<string>('');

  // Animation state
  const scaleAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const confettiAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      // Reset form
      setDifficultyRating(0);
      setCompletionStatus('fully_completed');
      setResultType('general');
      setResultData({});
      setQualityRating(0);
      setTimeTaken(estimatedDuration ? estimatedDuration.toString() : '');
      setNotes('');
      setStep('logging');

      // Trigger haptic
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    }
  }, [visible, estimatedDuration]);

  const handleSubmit = async () => {
    if (difficultyRating === 0) {
      alert('Please select a difficulty rating');
      return;
    }

    setLoading(true);

    try {
      // Build result data based on result type
      let finalResultData = { ...resultData };

      // Parse result data based on type
      if (resultType === 'essay_word_count') {
        if (!resultData.word_count) {
          alert('Please enter word count');
          setLoading(false);
          return;
        }
      } else if (resultType === 'test_score' || resultType === 'practice_test') {
        if (!resultData.score) {
          alert('Please enter test score');
          setLoading(false);
          return;
        }
      }

      // Calculate time taken
      const timeTakenMinutes = timeTaken ? parseInt(timeTaken, 10) : null;

      // Submit completion to API
      const response = await todosAPI.completeTask(taskId, {
        actual_duration_minutes: timeTakenMinutes,
        difficulty_rating: difficultyRating,
        completion_status: completionStatus,
        result_type: resultType,
        result_data: finalResultData,
        quality_rating: qualityRating || null,
        notes: notes,
      });

      // Trigger celebration
      await triggerCelebration();

      // Call completion callback
      onComplete?.(response);

      // Close modal after celebration
      setTimeout(() => {
        onClose();
      }, 3000);
    } catch (error) {
      console.error('Failed to complete task:', error);
      alert('Failed to save completion. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const triggerCelebration = async () => {
    setStep('celebrating');
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);

    // Animate confetti
    Animated.parallel([
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 400,
        delay: 200,
        useNativeDriver: true,
      }),
    ]).start();

    // Confetti animation
    Animated.sequence([
      Animated.timing(confettiAnim, {
        toValue: 1,
        duration: 1500,
        useNativeDriver: true,
      }),
      Animated.timing(confettiAnim, {
        toValue: 0,
        duration: 1500,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const renderLoggingStep = () => (
    <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerIcon}>
          <Ionicons name="checkmark-circle" size={48} color="#10B981" />
        </View>
        <Text style={styles.headerTitle}>Complete Task</Text>
        <Text style={styles.headerSubtitle}>{taskTitle}</Text>
        {taskCategory && (
          <View style={[styles.categoryBadge, { backgroundColor: taskCategory.color + '20' }]}>
            <Text style={styles.categoryEmoji}>{taskCategory.icon}</Text>
            <Text style={[styles.categoryName, { color: taskCategory.color }]}>
              {taskCategory.name}
            </Text>
          </View>
        )}
      </View>

      {/* Completion Status */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Completion Status</Text>
        <View style={styles.statusOptions}>
          {[
            { value: 'fully_completed', label: 'Fully Completed', icon: 'checkmark-circle' },
            { value: 'partially_completed', label: 'Partially', icon: 'remove-circle' },
            { value: 'not_completed', label: 'Not Completed', icon: 'close-circle' },
          ].map((option) => (
            <TouchableOpacity
              key={option.value}
              style={[
                styles.statusOption,
                completionStatus === option.value && styles.statusOptionSelected,
              ]}
              onPress={() => setCompletionStatus(option.value as CompletionStatus)}
            >
              <Ionicons
                name={option.icon as any}
                size={24}
                color={completionStatus === option.value ? '#10B981' : '#8E8E8E'}
              />
              <Text
                style={[
                  styles.statusOptionLabel,
                  completionStatus === option.value && styles.statusOptionLabelSelected,
                ]}
              >
                {option.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Difficulty Rating */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>How difficult was this task?</Text>
        <View style={styles.ratingContainer}>
          {[1, 2, 3, 4, 5].map((rating) => (
            <TouchableOpacity
              key={rating}
              onPress={() => {
                setDifficultyRating(rating);
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              }}
              activeOpacity={0.7}
            >
              <Ionicons
                name={difficultyRating >= rating ? 'star' : 'star-outline'}
                size={40}
                color={difficultyRating >= rating ? '#F59E0B' : '#3E3E3E'}
              />
            </TouchableOpacity>
          ))}
        </View>
        <Text style={styles.ratingHint}>
          {difficultyRating === 1 && 'Very Easy'}
          {difficultyRating === 2 && 'Easy'}
          {difficultyRating === 3 && 'Medium'}
          {difficultyRating === 4 && 'Hard'}
          {difficultyRating === 5 && 'Very Hard'}
        </Text>
      </View>

      {/* Quality Rating */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quality of Work (Optional)</Text>
        <View style={styles.ratingContainer}>
          {[1, 2, 3, 4, 5].map((rating) => (
            <TouchableOpacity
              key={rating}
              onPress={() => {
                setQualityRating(rating);
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              }}
              activeOpacity={0.7}
            >
              <Ionicons
                name={qualityRating >= rating ? 'heart' : 'heart-outline'}
                size={32}
                color={qualityRating >= rating ? '#EF4444' : '#3E3E3E'}
              />
            </TouchableOpacity>
          ))}
        </View>
        <Text style={styles.ratingHint}>
          {qualityRating === 1 && 'Poor'}
          {qualityRating === 2 && 'Fair'}
          {qualityRating === 3 && 'Good'}
          {qualityRating === 4 && 'Great'}
          {qualityRating === 5 && 'Excellent'}
        </Text>
      </View>

      {/* Time Taken */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>How long did it take?</Text>
        <View style={styles.inputContainer}>
          <Ionicons name="time-outline" size={20} color="#8E8E8E" />
          <TextInput
            style={styles.input}
            placeholder="Minutes"
            placeholderTextColor="#6B7280"
            value={timeTaken}
            onChangeText={setTimeTaken}
            keyboardType="numeric"
          />
        </View>
      </View>

      {/* Category-Specific Results */}
      {shouldShowResultFields() && renderResultFields()}

      {/* Notes */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Notes (Optional)</Text>
        <TextInput
          style={styles.textArea}
          placeholder="Any additional notes about this task..."
          placeholderTextColor="#6B7280"
          value={notes}
          onChangeText={setNotes}
          multiline
          numberOfLines={4}
          textAlignVertical="top"
        />
      </View>

      {/* Submit Button */}
      <TouchableOpacity
        style={[styles.submitButton, loading && styles.submitButtonDisabled]}
        onPress={handleSubmit}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#FFFFFF" />
        ) : (
          <>
            <Ionicons name="checkmark-circle" size={20} color="#FFFFFF" />
            <Text style={styles.submitButtonText}>Complete Task</Text>
          </>
        )}
      </TouchableOpacity>
    </ScrollView>
  );

  const shouldShowResultFields = (): boolean => {
    if (!taskCategory) return false;

    const resultTypeMap: Record<string, ResultType> = {
      'Documents': 'document_submission',
      'Essays': 'essay_word_count',
      'Portfolio': 'portfolio_upload',
      'SAT Prep': 'practice_test',
      'IELTS Prep': 'practice_test',
      'Applications': 'application_submit',
    };

    const mappedType = resultTypeMap[taskCategory.name];
    if (mappedType) {
      setResultType(mappedType);
      return true;
    }

    return false;
  };

  const renderResultFields = () => {
    if (resultType === 'essay_word_count') {
      return (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Essay Details</Text>
          <View style={styles.inputContainer}>
            <Ionicons name="document-text-outline" size={20} color="#8E8E8E" />
            <TextInput
              style={styles.input}
              placeholder="Word count"
              placeholderTextColor="#6B7280"
              value={resultData.word_count || ''}
              onChangeText={(text) => setResultData({ ...resultData, word_count: text })}
              keyboardType="numeric"
            />
          </View>
          <View style={styles.inputContainer}>
            <Ionicons name="create-outline" size={20} color="#8E8E8E" />
            <TextInput
              style={styles.input}
              placeholder="Prompt type (e.g., Personal Statement)"
              placeholderTextColor="#6B7280"
              value={resultData.prompt_type || ''}
              onChangeText={(text) => setResultData({ ...resultData, prompt_type: text })}
            />
          </View>
        </View>
      );
    }

    if (resultType === 'test_score' || resultType === 'practice_test') {
      return (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Test Score</Text>
          <View style={styles.inputContainer}>
            <Ionicons name="trophy-outline" size={20} color="#8E8E8E" />
            <TextInput
              style={styles.input}
              placeholder="Total score"
              placeholderTextColor="#6B7280"
              value={resultData.score || ''}
              onChangeText={(text) => setResultData({ ...resultData, score: text })}
              keyboardType="numeric"
            />
          </View>
          <View style={styles.inputContainer}>
            <Ionicons name="analytics-outline" size={20} color="#8E8E8E" />
            <TextInput
              style={styles.input}
              placeholder="Section scores (optional)"
              placeholderTextColor="#6B7280"
              value={resultData.section_scores || ''}
              onChangeText={(text) =>
                setResultData({ ...resultData, section_scores: text })
              }
            />
          </View>
        </View>
      );
    }

    return null;
  };

  const renderCelebrationStep = () => (
    <View style={styles.celebrationContent}>
      <Animated.View
        style={[
          styles.celebrationIcon,
          {
            transform: [{ scale: scaleAnim }],
            opacity: fadeAnim,
          },
        ]}
      >
        <Ionicons name="checkmark-circle" size={120} color="#10B981" />
      </Animated.View>

      <Animated.Text
        style={[
          styles.celebrationTitle,
          { opacity: fadeAnim },
        ]}
      >
        Task Completed!
      </Animated.Text>

      <Animated.Text
        style={[
          styles.celebrationSubtitle,
          { opacity: fadeAnim },
        ]}
      >
        Great job staying on track!
      </Animated.Text>

      {/* Progress Stats (Example) */}
      <Animated.View
        style={[
          styles.statsContainer,
          { opacity: fadeAnim },
        ]}
      >
        <View style={styles.stat}>
          <Text style={styles.statValue}>{difficultyRating}/5</Text>
          <Text style={styles.statLabel}>Difficulty</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.stat}>
          <Text style={styles.statValue}>{timeTaken}m</Text>
          <Text style={styles.statLabel}>Time</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.stat}>
          <Text style={styles.statValue}>
            {completionStatus === 'fully_completed' ? '100%' : 'Partial'}
          </Text>
          <Text style={styles.statLabel}>Complete</Text>
        </View>
      </Animated.View>

      {/* Streak Message */}
      <Animated.View
        style={[
          styles.streakBadge,
          { opacity: fadeAnim },
        ]}
      >
        <Ionicons name="flame" size={20} color="#F59E0B" />
        <Text style={styles.streakText}>You're on fire! Keep it up!</Text>
      </Animated.View>
    </View>
  );

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <BlurView intensity={20} style={styles.container}>
        {/* Header */}
        <View style={styles.modalHeader}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color="#8E8E8E" />
          </TouchableOpacity>
          <Text style={styles.modalTitle}>
            {step === 'logging' ? 'Complete Task' : 'Congratulations!'}
          </Text>
          <View style={styles.headerSpacer} />
        </View>

        {/* Content */}
        {step === 'logging' ? renderLoggingStep() : renderCelebrationStep()}
      </BlurView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'rgba(26, 26, 26, 0.95)',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#3E3E3E',
  },
  closeButton: {
    padding: 8,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ECECEC',
  },
  headerSpacer: {
    width: 40,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  header: {
    alignItems: 'center',
    paddingVertical: 24,
    gap: 12,
  },
  headerIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#10B98120',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#ECECEC',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#8E8E8E',
    textAlign: 'center',
  },
  categoryBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    gap: 6,
  },
  categoryEmoji: {
    fontSize: 16,
  },
  categoryName: {
    fontSize: 14,
    fontWeight: '600',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ECECEC',
    marginBottom: 12,
  },
  statusOptions: {
    flexDirection: 'row',
    gap: 8,
  },
  statusOption: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#3E3E3E',
    backgroundColor: '#2A2A2A',
    gap: 6,
  },
  statusOptionSelected: {
    backgroundColor: '#10B98120',
    borderColor: '#10B981',
  },
  statusOptionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#8E8E8E',
  },
  statusOptionLabelSelected: {
    color: '#10B981',
  },
  ratingContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 12,
  },
  ratingHint: {
    fontSize: 14,
    color: '#8E8E8E',
    textAlign: 'center',
    marginTop: 8,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#3E3E3E',
    backgroundColor: '#2A2A2A',
    gap: 12,
    marginBottom: 12,
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: '#ECECEC',
  },
  textArea: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#3E3E3E',
    backgroundColor: '#2A2A2A',
    fontSize: 16,
    color: '#ECECEC',
    minHeight: 100,
  },
  submitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#10B981',
    gap: 8,
    marginTop: 8,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  celebrationContent: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
    gap: 24,
  },
  celebrationIcon: {
    shadowColor: '#10B981',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  celebrationTitle: {
    fontSize: 32,
    fontWeight: '700',
    color: '#ECECEC',
  },
  celebrationSubtitle: {
    fontSize: 18,
    color: '#8E8E8E',
  },
  statsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 16,
    borderRadius: 16,
    backgroundColor: '#2A2A2A',
    gap: 24,
  },
  stat: {
    alignItems: 'center',
    gap: 4,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#ECECEC',
  },
  statLabel: {
    fontSize: 12,
    color: '#8E8E8E',
  },
  statDivider: {
    width: 1,
    height: 40,
    backgroundColor: '#3E3E3E',
  },
  streakBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 20,
    backgroundColor: '#F59E0B20',
    gap: 8,
  },
  streakText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#F59E0B',
  },
});
