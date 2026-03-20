import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { useOnboarding } from '@/components/onboarding/OnboardingContext';

const CATEGORIES = [
  'Leadership', 'Academic', 'Sports', 'Arts', 'Community Service',
  'Technology', 'Music', 'Debate', 'Research', 'Other'
];

interface Activity {
  category: string;
  title: string;
  organization: string;
  role: string;
  startDate: string;
  endDate: string;
  isOngoing: boolean;
  hoursPerWeek: string;
  description: string;
}

export default function ExtracurricularsScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const { onboardingData, updateOnboardingData } = useOnboarding();

  const [activities, setActivities] = useState<Activity[]>(onboardingData.extracurriculars || []);
  const [currentActivity, setCurrentActivity] = useState<Partial<Activity>>({
    category: '',
    title: '',
    organization: '',
    role: '',
    startDate: '',
    endDate: '',
    isOngoing: false,
    hoursPerWeek: '',
    description: '',
  });
  const [showCategoryPicker, setShowCategoryPicker] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const resetCurrentActivity = () => {
    setCurrentActivity({
      category: '',
      title: '',
      organization: '',
      role: '',
      startDate: '',
      endDate: '',
      isOngoing: false,
      hoursPerWeek: '',
      description: '',
    });
    setEditingIndex(null);
  };

  const validateAndAddActivity = () => {
    // Debug logging
    console.log('=== VALIDATING ACTIVITY ===');
    console.log('Category:', currentActivity.category);
    console.log('Title:', currentActivity.title, `(${currentActivity.title?.trim().length || 0} chars)`);
    console.log('Role:', currentActivity.role, `(${currentActivity.role?.trim().length || 0} chars)`);
    console.log('Start Date:', currentActivity.startDate);
    console.log('End Date:', currentActivity.endDate, 'Ongoing:', currentActivity.isOngoing);
    console.log('Hours Per Week:', currentActivity.hoursPerWeek);
    console.log('Description:', currentActivity.description, `(${currentActivity.description?.trim().length || 0} chars)`);

    // Collect missing fields
    const missingFields = [];

    if (!currentActivity.category) {
      missingFields.push('Category');
    }

    if (!currentActivity.title || currentActivity.title.trim().length < 3) {
      missingFields.push('Title (min. 3 characters)');
    }

    if (!currentActivity.role || currentActivity.role.trim().length < 2) {
      missingFields.push('Role (min. 2 characters)');
    }

    if (!currentActivity.startDate || currentActivity.startDate.trim().length === 0) {
      missingFields.push('Start Date');
    }

    if (!currentActivity.isOngoing && (!currentActivity.endDate || currentActivity.endDate.trim().length === 0)) {
      missingFields.push('End Date (or mark as ongoing)');
    }

    if (!currentActivity.hoursPerWeek || currentActivity.hoursPerWeek.trim().length === 0) {
      missingFields.push('Hours Per Week');
    }

    if (!currentActivity.description || currentActivity.description.trim().length < 10) {
      missingFields.push('Description (min. 10 characters)');
    }

    // Show all missing fields at once
    if (missingFields.length > 0) {
      Alert.alert(
        'Please Complete Required Fields',
        `Missing or incomplete:\n• ${missingFields.join('\n• ')}`,
        [{ text: 'OK', style: 'default' }]
      );
      return;
    }

    const wordCount = currentActivity.description!.trim().split(/\s+/).length;
    if (wordCount > 150) {
      Alert.alert('Description Too Long', `Your description has ${wordCount} words. Please keep it under 150 words.`);
      return;
    }

    const newActivity: Activity = {
      category: currentActivity.category!,
      title: currentActivity.title!.trim(),
      organization: currentActivity.organization?.trim() || '',
      role: currentActivity.role!.trim(),
      startDate: currentActivity.startDate!.trim(),
      endDate: currentActivity.isOngoing ? '' : (currentActivity.endDate || ''),
      isOngoing: currentActivity.isOngoing!,
      hoursPerWeek: currentActivity.hoursPerWeek!.trim(),
      description: currentActivity.description!.trim(),
    };

    let updatedActivities: Activity[];
    if (editingIndex !== null) {
      updatedActivities = [...activities];
      updatedActivities[editingIndex] = newActivity;
    } else {
      if (activities.length >= 5) {
        Alert.alert('Maximum Reached', 'You can add up to 5 activities');
        return;
      }
      updatedActivities = [...activities, newActivity];
    }

    setActivities(updatedActivities);
    resetCurrentActivity();
  };

  const handleEdit = (index: number) => {
    setCurrentActivity(activities[index]);
    setEditingIndex(index);
  };

  const handleDelete = (index: number) => {
    Alert.alert(
      'Delete Activity',
      'Are you sure you want to delete this activity?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            const updated = activities.filter((_, i) => i !== index);
            setActivities(updated);
            if (editingIndex === index) {
              resetCurrentActivity();
            }
          },
        },
      ]
    );
  };

  const handleNext = async () => {
    try {
      setLoading(true);

      // Save onboarding data
      updateOnboardingData({ extracurriculars: activities });

      router.push('/(onboarding)/plan-selection');
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to save activities');
    } finally {
      setLoading(false);
    }
  };

  const wordCount = currentActivity.description?.trim().split(/\s+/).length || 0;

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Progress */}
          <View style={styles.progressContainer}>
            <View style={styles.progressBar}>
              <View style={[styles.progressFill, { width: '50%' }]} />
            </View>
            <Text style={styles.progressText}>Step 7 of 14</Text>
          </View>

          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Extracurricular Activities</Text>
            <Text style={styles.subtitle}>
              Add up to 5 activities (1-5 recommended)
            </Text>
          </View>

          {/* Activity List */}
          {activities.length > 0 && (
            <View style={styles.activityList}>
              <Text style={styles.listTitle}>Added Activities ({activities.length}/5)</Text>
              {activities.map((activity, index) => (
                <View key={index} style={styles.activityCard}>
                  <View style={styles.activityCardHeader}>
                    <Text style={styles.activityTitle}>{activity.title}</Text>
                    <View style={styles.activityActions}>
                      <TouchableOpacity onPress={() => handleEdit(index)}>
                        <Text style={styles.editButton}>Edit</Text>
                      </TouchableOpacity>
                      <TouchableOpacity onPress={() => handleDelete(index)}>
                        <Text style={styles.deleteButton}>Delete</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                  <Text style={styles.activityDetail}>{activity.category} • {activity.role}</Text>
                  <Text style={styles.activityDetail}>
                    {activity.startDate} - {activity.isOngoing ? 'Present' : activity.endDate}
                  </Text>
                  <Text style={styles.activityDetail}>
                    {activity.hoursPerWeek} hrs/week
                  </Text>
                </View>
              ))}
            </View>
          )}

          {/* Add/Edit Form */}
          <View style={styles.form}>
            <Text style={styles.formTitle}>
              {editingIndex !== null ? 'Edit Activity' : 'Add New Activity'}
            </Text>

            {/* Category */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Category *</Text>
              <TouchableOpacity
                style={styles.picker}
                onPress={() => setShowCategoryPicker(true)}
              >
                <Text style={currentActivity.category ? styles.pickerText : styles.pickerPlaceholder}>
                  {currentActivity.category || 'Select category'}
                </Text>
                <Text style={styles.pickerArrow}>▼</Text>
              </TouchableOpacity>
            </View>

            {/* Title */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Activity Title *</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., Debate Club President"
                value={currentActivity.title}
                onChangeText={(text) => setCurrentActivity({ ...currentActivity, title: text })}
                autoCapitalize="words"
              />
            </View>

            {/* Organization (Optional) */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Organization/School (Optional)</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., Lincoln High School"
                value={currentActivity.organization}
                onChangeText={(text) => setCurrentActivity({ ...currentActivity, organization: text })}
                autoCapitalize="words"
              />
            </View>

            {/* Role */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Your Role *</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., President, Member, Captain"
                value={currentActivity.role}
                onChangeText={(text) => setCurrentActivity({ ...currentActivity, role: text })}
                autoCapitalize="words"
              />
            </View>

            {/* Dates */}
            <View style={styles.row}>
              <View style={[styles.inputGroup, styles.half]}>
                <Text style={styles.label}>Start Date *</Text>
                <TextInput
                  style={styles.input}
                  placeholder="YYYY-MM"
                  value={currentActivity.startDate}
                  onChangeText={(text) => {
                    // Auto-format to YYYY-MM-DD by adding -01 if not specified
                    let formatted = text;
                    if (text.match(/^\d{4}-\d{2}$/)) {
                      formatted = text + '-01';
                    }
                    setCurrentActivity({ ...currentActivity, startDate: formatted })
                  }}
                  keyboardType="numbers-and-punctuation"
                  maxLength={10}
                />
              </View>
              <View style={[styles.inputGroup, styles.half]}>
                <Text style={styles.label}>End Date</Text>
                <TextInput
                  style={styles.input}
                  placeholder="YYYY-MM"
                  value={currentActivity.isOngoing ? 'Present' : currentActivity.endDate}
                  onChangeText={(text) => {
                    // Auto-format to YYYY-MM-DD by adding -01 if not specified
                    let formatted = text;
                    if (text.match(/^\d{4}-\d{2}$/)) {
                      formatted = text + '-01';
                    }
                    setCurrentActivity({ ...currentActivity, endDate: formatted })
                  }}
                  keyboardType="numbers-and-punctuation"
                  maxLength={10}
                  editable={!currentActivity.isOngoing}
                  style={[styles.input, currentActivity.isOngoing && styles.inputDisabled]}
                />
              </View>
            </View>

            {/* Ongoing Toggle */}
            <TouchableOpacity
              style={styles.toggle}
              onPress={() => setCurrentActivity({
                ...currentActivity,
                isOngoing: !currentActivity.isOngoing,
                endDate: ''
              })}
            >
              <View style={[styles.toggleCheckbox, currentActivity.isOngoing && styles.toggleCheckboxChecked]}>
                {currentActivity.isOngoing && <Text style={styles.checkmark}>✓</Text>}
              </View>
              <Text style={styles.toggleLabel}>I am currently participating in this activity</Text>
            </TouchableOpacity>

            {/* Hours Per Week */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Hours Per Week *</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., 5"
                value={currentActivity.hoursPerWeek}
                onChangeText={(text) => setCurrentActivity({ ...currentActivity, hoursPerWeek: text })}
                keyboardType="decimal-pad"
              />
            </View>

            {/* Description */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Description * (Max 150 words)</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                placeholder="Describe your achievements, responsibilities, and impact..."
                value={currentActivity.description}
                onChangeText={(text) => setCurrentActivity({ ...currentActivity, description: text })}
                multiline
                numberOfLines={4}
                textAlignVertical="top"
              />
              <Text style={[styles.wordCount, wordCount > 150 && styles.wordCountError]}>
                {wordCount}/150 words
              </Text>
            </View>

            {/* Add/Update Button */}
            <TouchableOpacity
              style={styles.addButton}
              onPress={validateAndAddActivity}
            >
              <Text style={styles.addButtonText}>
                {editingIndex !== null ? 'Update Activity' : 'Add Activity'}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Category Picker Modal */}
          {showCategoryPicker && (
            <View style={styles.modalOverlay}>
              <View style={styles.modalContent}>
                <Text style={styles.modalTitle}>Select Category</Text>
                <ScrollView style={styles.categoryList}>
                  {CATEGORIES.map((category) => (
                    <TouchableOpacity
                      key={category}
                      style={styles.categoryItem}
                      onPress={() => {
                        setCurrentActivity({ ...currentActivity, category });
                        setShowCategoryPicker(false);
                      }}
                    >
                      <Text style={styles.categoryName}>{category}</Text>
                      {currentActivity.category === category && (
                        <Text style={styles.checkmark}>✓</Text>
                      )}
                    </TouchableOpacity>
                  ))}
                </ScrollView>
                <TouchableOpacity
                  style={styles.modalClose}
                  onPress={() => setShowCategoryPicker(false)}
                >
                  <Text style={styles.modalCloseText}>Cancel</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          {/* Continue Button */}
          <TouchableOpacity
            style={[styles.continueButton, loading && styles.continueButtonDisabled]}
            onPress={handleNext}
            disabled={loading}
          >
            <Text style={styles.continueButtonText}>
              {loading ? 'Loading...' : `Continue (${activities.length}/5)`}
            </Text>
          </TouchableOpacity>

          {/* Skip Button */}
          <TouchableOpacity
            style={styles.skipButton}
            onPress={() => router.push('/(onboarding)/target-universities')}
          >
            <Text style={styles.skipButtonText}>Skip for now</Text>
          </TouchableOpacity>

          {/* Back Button */}
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
          >
            <Text style={styles.backButtonText}>← Back</Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  keyboardView: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 24,
    paddingTop: 20,
    paddingBottom: 24,
  },
  progressContainer: {
    marginBottom: 24,
  },
  progressBar: {
    height: 4,
    backgroundColor: '#E5E7EB',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#6366F1',
  },
  progressText: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 8,
    textAlign: 'center',
  },
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
  },
  activityList: {
    marginBottom: 24,
    gap: 12,
  },
  listTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 12,
  },
  activityCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  activityCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  activityTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    flex: 1,
  },
  activityActions: {
    flexDirection: 'row',
    gap: 16,
  },
  editButton: {
    fontSize: 14,
    color: '#6366F1',
    fontWeight: '500',
  },
  deleteButton: {
    fontSize: 14,
    color: '#EF4444',
    fontWeight: '500',
  },
  activityDetail: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
  form: {
    backgroundColor: '#F9FAFB',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    gap: 16,
  },
  formTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 8,
  },
  inputGroup: {
    gap: 8,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  input: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    placeholderTextColor: '#9CA3AF',
  },
  inputDisabled: {
    backgroundColor: '#F3F4F6',
    color: '#9CA3AF',
  },
  textArea: {
    minHeight: 100,
    paddingTop: 12,
  },
  picker: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: '#D1D5DB',
  },
  pickerText: {
    fontSize: 16,
    color: '#111827',
  },
  pickerPlaceholder: {
    fontSize: 16,
    color: '#9CA3AF',
  },
  pickerArrow: {
    fontSize: 12,
    color: '#6B7280',
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  half: {
    flex: 1,
  },
  toggle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 8,
  },
  toggleCheckbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: '#D1D5DB',
    alignItems: 'center',
    justifyContent: 'center',
  },
  toggleCheckboxChecked: {
    backgroundColor: '#6366F1',
    borderColor: '#6366F1',
  },
  checkmark: {
    fontSize: 14,
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  toggleLabel: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
  },
  wordCount: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'right',
  },
  wordCountError: {
    color: '#EF4444',
  },
  addButton: {
    backgroundColor: '#6366F1',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 8,
  },
  addButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    width: '90%',
    maxHeight: '70%',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  categoryList: {
    maxHeight: 400,
  },
  categoryItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  categoryName: {
    fontSize: 16,
    color: '#1F2937',
  },
  modalClose: {
    marginTop: 16,
    paddingVertical: 12,
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
  },
  modalCloseText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#6B7280',
  },
  continueButton: {
    backgroundColor: '#6366F1',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginBottom: 8,
  },
  continueButtonDisabled: {
    opacity: 0.6,
  },
  continueButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  skipButton: {
    paddingVertical: 12,
    alignItems: 'center',
    marginBottom: 8,
  },
  skipButtonText: {
    fontSize: 14,
    color: '#6B7280',
  },
  backButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  backButtonText: {
    fontSize: 14,
    color: '#6B7280',
  },
});
