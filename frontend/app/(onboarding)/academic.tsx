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

const STUDENT_STATUSES = [
  { value: 'high_school', label: 'High School Student' },
  { value: 'college_student', label: 'College Student' },
  { value: 'graduate_student', label: 'Graduate Student' },
  { value: 'gap_year', label: 'Gap Year' },
  { value: 'working_professional', label: 'Working Professional' },
];

const GPA_SCALES = [
  { value: '4.0', label: '4.0 Scale' },
  { value: '5.0', label: '5.0 Scale' },
  { value: '100', label: '100 Scale' },
  { value: 'letter', label: 'Letter Grade (A-F)' },
];

const SUBJECTS = [
  'Mathematics', 'Physics', 'Chemistry', 'Biology',
  'Computer Science', 'English', 'History', 'Economics',
  'Art', 'Music', 'Physical Education', 'Other'
];

interface FormData {
  studentStatus: string;
  schoolName: string;
  graduationYear: string;
  gpa: string;
  gpaScale: string;
  specialization: string;
  favoriteSubjects: string[];
}

export default function AcademicScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const { onboardingData, updateOnboardingData } = useOnboarding();

  const [formData, setFormData] = useState<FormData>({
    studentStatus: onboardingData.student_status || '',
    schoolName: onboardingData.school_name || '',
    graduationYear: onboardingData.graduation_year || '',
    gpa: onboardingData.gpa || '',
    gpaScale: onboardingData.gpa_scale || '4.0',
    specialization: onboardingData.specialization || '',
    favoriteSubjects: onboardingData.favorite_subjects || [],
  });

  const [showStatusPicker, setShowStatusPicker] = useState(false);
  const [showGpaScalePicker, setShowGpaScalePicker] = useState(false);
  const [showSubjectPicker, setShowSubjectPicker] = useState(false);
  const [loading, setLoading] = useState(false);

  const toggleSubject = (subject: string) => {
    const subjects = formData.favoriteSubjects.includes(subject)
      ? formData.favoriteSubjects.filter(s => s !== subject)
      : [...formData.favoriteSubjects, subject];

    if (subjects.length > 3) {
      Alert.alert('Maximum Reached', 'You can select up to 3 favorite subjects');
      return;
    }

    setFormData({ ...formData, favoriteSubjects: subjects });
  };

  const handleNext = async () => {
    // Validation
    if (!formData.studentStatus) {
      Alert.alert('Status Required', 'Please select your student status');
      return;
    }

    if (!formData.schoolName || formData.schoolName.trim().length < 2) {
      Alert.alert('School Required', 'Please enter your school name');
      return;
    }

    if (!formData.graduationYear || formData.graduationYear.length !== 4) {
      Alert.alert('Invalid Year', 'Please enter a valid graduation year');
      return;
    }

    const year = parseInt(formData.graduationYear);
    const currentYear = new Date().getFullYear();
    if (year < currentYear - 10 || year > currentYear + 10) {
      Alert.alert('Invalid Year', 'Please enter a valid graduation year');
      return;
    }

    if (!formData.gpa) {
      Alert.alert('GPA Required', 'Please enter your GPA');
      return;
    }

    if (!formData.specialization || formData.specialization.trim().length < 2) {
      Alert.alert('Specialization Required', 'Please enter your field of study');
      return;
    }

    if (formData.favoriteSubjects.length === 0) {
      Alert.alert('Subjects Required', 'Please select at least 1 favorite subject');
      return;
    }

    try {
      setLoading(true);

      // Save onboarding data
      updateOnboardingData({
        student_status: formData.studentStatus,
        school_name: formData.schoolName,
        graduation_year: formData.graduationYear,
        gpa: formData.gpa,
        gpa_scale: formData.gpaScale,
        specialization: formData.specialization,
        favorite_subjects: formData.favoriteSubjects,
      });

      router.push('/(onboarding)/test-scores');
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to save academic information');
    } finally {
      setLoading(false);
    }
  };

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
        >
          {/* Progress */}
          <View style={styles.progressContainer}>
            <View style={styles.progressBar}>
              <View style={[styles.progressFill, { width: '35%' }]} />
            </View>
            <Text style={styles.progressText}>Step 5 of 14</Text>
          </View>

          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Academic Background</Text>
            <Text style={styles.subtitle}>Help us understand your academic profile</Text>
          </View>

          {/* Form */}
          <View style={styles.form}>
            {/* Student Status */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Student Status *</Text>
              <TouchableOpacity
                style={styles.picker}
                onPress={() => setShowStatusPicker(true)}
              >
                <Text style={formData.studentStatus ? styles.pickerText : styles.pickerPlaceholder}>
                  {formData.studentStatus
                    ? STUDENT_STATUSES.find(s => s.value === formData.studentStatus)?.label
                    : 'Select your status'}
                </Text>
                <Text style={styles.pickerArrow}>▼</Text>
              </TouchableOpacity>
            </View>

            {/* School Name */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>School Name *</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter your school name"
                value={formData.schoolName}
                onChangeText={(text) => setFormData({ ...formData, schoolName: text })}
                autoCapitalize="words"
              />
            </View>

            {/* Graduation Year */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Graduation Year *</Text>
              <TextInput
                style={styles.input}
                placeholder="YYYY (e.g., 2025)"
                value={formData.graduationYear}
                onChangeText={(text) => {
                  const numericText = text.replace(/[^0-9]/g, '');
                  setFormData({ ...formData, graduationYear: numericText });
                }}
                keyboardType="number-pad"
                maxLength={4}
              />
            </View>

            {/* GPA & Scale */}
            <View style={styles.row}>
              <View style={[styles.inputGroup, styles.half]}>
                <Text style={styles.label}>GPA *</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Your GPA"
                  value={formData.gpa}
                  onChangeText={(text) => setFormData({ ...formData, gpa: text })}
                  keyboardType="decimal-pad"
                />
              </View>

              <View style={[styles.inputGroup, styles.half]}>
                <Text style={styles.label}>Scale *</Text>
                <TouchableOpacity
                  style={styles.picker}
                  onPress={() => setShowGpaScalePicker(true)}
                >
                  <Text style={styles.pickerTextSmall}>
                    {formData.gpaScale}
                  </Text>
                  <Text style={styles.pickerArrow}>▼</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Specialization */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Field of Study / Major *</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., Computer Science, Business, Arts"
                value={formData.specialization}
                onChangeText={(text) => setFormData({ ...formData, specialization: text })}
                autoCapitalize="words"
              />
            </View>

            {/* Favorite Subjects */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Favorite Subjects (Max 3) *</Text>
              <TouchableOpacity
                style={styles.subjectsButton}
                onPress={() => setShowSubjectPicker(true)}
              >
                <View style={styles.selectedSubjects}>
                  {formData.favoriteSubjects.length > 0 ? (
                    formData.favoriteSubjects.map((subject, index) => (
                      <View key={index} style={styles.subjectChip}>
                        <Text style={styles.subjectChipText}>{subject}</Text>
                      </View>
                    ))
                  ) : (
                    <Text style={styles.placeholder}>Select your favorite subjects</Text>
                  )}
                </View>
                <Text style={styles.pickerArrow}>▼</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Status Picker Modal */}
          {showStatusPicker && (
            <View style={styles.modalOverlay}>
              <View style={styles.modalContent}>
                <Text style={styles.modalTitle}>Select Status</Text>
                <ScrollView style={styles.optionList}>
                  {STUDENT_STATUSES.map((status) => (
                    <TouchableOpacity
                      key={status.value}
                      style={styles.optionItem}
                      onPress={() => {
                        setFormData({ ...formData, studentStatus: status.value });
                        setShowStatusPicker(false);
                      }}
                    >
                      <Text style={styles.optionText}>{status.label}</Text>
                      {formData.studentStatus === status.value && (
                        <Text style={styles.checkmark}>✓</Text>
                      )}
                    </TouchableOpacity>
                  ))}
                </ScrollView>
                <TouchableOpacity
                  style={styles.modalClose}
                  onPress={() => setShowStatusPicker(false)}
                >
                  <Text style={styles.modalCloseText}>Cancel</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          {/* GPA Scale Picker Modal */}
          {showGpaScalePicker && (
            <View style={styles.modalOverlay}>
              <View style={styles.modalContent}>
                <Text style={styles.modalTitle}>Select GPA Scale</Text>
                <ScrollView style={styles.optionList}>
                  {GPA_SCALES.map((scale) => (
                    <TouchableOpacity
                      key={scale.value}
                      style={styles.optionItem}
                      onPress={() => {
                        setFormData({ ...formData, gpaScale: scale.value });
                        setShowGpaScalePicker(false);
                      }}
                    >
                      <Text style={styles.optionText}>{scale.label}</Text>
                      {formData.gpaScale === scale.value && (
                        <Text style={styles.checkmark}>✓</Text>
                      )}
                    </TouchableOpacity>
                  ))}
                </ScrollView>
                <TouchableOpacity
                  style={styles.modalClose}
                  onPress={() => setShowGpaScalePicker(false)}
                >
                  <Text style={styles.modalCloseText}>Cancel</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          {/* Subject Picker Modal */}
          {showSubjectPicker && (
            <View style={styles.modalOverlay}>
              <View style={styles.modalContent}>
                <Text style={styles.modalTitle}>Select Favorite Subjects</Text>
                <Text style={styles.modalHint}>Select up to 3 subjects</Text>
                <ScrollView style={styles.optionList}>
                  {SUBJECTS.map((subject) => (
                    <TouchableOpacity
                      key={subject}
                      style={styles.optionItem}
                      onPress={() => toggleSubject(subject)}
                    >
                      <Text style={styles.optionText}>{subject}</Text>
                      {formData.favoriteSubjects.includes(subject) && (
                        <Text style={styles.checkmark}>✓</Text>
                      )}
                    </TouchableOpacity>
                  ))}
                </ScrollView>
                <TouchableOpacity
                  style={styles.modalClose}
                  onPress={() => setShowSubjectPicker(false)}
                >
                  <Text style={styles.modalCloseText}>
                    Done ({formData.favoriteSubjects.length}/3)
                  </Text>
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
              {loading ? 'Loading...' : 'Continue'}
            </Text>
          </TouchableOpacity>

          {/* Skip Button */}
          <TouchableOpacity
            style={styles.skipButton}
            onPress={() => router.push('/(onboarding)/test-scores')}
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
    backgroundColor: '#000000',
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
    backgroundColor: '#2A2A2A',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#5B6AFF',
  },
  progressText: {
    fontSize: 12,
    color: '#8E8E8E',
    marginTop: 8,
    textAlign: 'center',
  },
  header: {
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#ECECEC',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#8E8E8E',
  },
  form: {
    gap: 20,
    marginBottom: 24,
  },
  row: {
    flexDirection: 'row',
    gap: 16,
  },
  half: {
    flex: 1,
  },
  inputGroup: {
    gap: 8,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#ECECEC',
  },
  input: {
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#2A2A2A',
    color: '#ECECEC',
  },
  picker: {
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: '#2A2A2A',
  },
  pickerText: {
    fontSize: 16,
    color: '#ECECEC',
  },
  pickerTextSmall: {
    fontSize: 14,
    color: '#ECECEC',
  },
  pickerPlaceholder: {
    fontSize: 16,
    color: '#8E8E8E',
  },
  pickerArrow: {
    fontSize: 12,
    color: '#8E8E8E',
  },
  subjectsButton: {
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: '#2A2A2A',
    minHeight: 50,
  },
  selectedSubjects: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  subjectChip: {
    backgroundColor: '#1A1A1A',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: '#5B6AFF',
  },
  subjectChipText: {
    fontSize: 14,
    color: '#5B6AFF',
    fontWeight: '500',
  },
  placeholder: {
    fontSize: 16,
    color: '#8E8E8E',
  },
  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  modalContent: {
    backgroundColor: '#1A1A1A',
    borderRadius: 16,
    padding: 24,
    width: '90%',
    maxHeight: '70%',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#ECECEC',
    marginBottom: 8,
  },
  modalHint: {
    fontSize: 14,
    color: '#8E8E8E',
    marginBottom: 16,
  },
  optionList: {
    maxHeight: 400,
  },
  optionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  optionText: {
    fontSize: 16,
    color: '#ECECEC',
  },
  checkmark: {
    fontSize: 18,
    color: '#5B6AFF',
    fontWeight: 'bold',
  },
  modalClose: {
    marginTop: 16,
    paddingVertical: 12,
    alignItems: 'center',
    backgroundColor: '#2A2A2A',
    borderRadius: 8,
  },
  modalCloseText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#8E8E8E',
  },
  continueButton: {
    backgroundColor: '#5B6AFF',
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
    color: '#8E8E8E',
  },
  backButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  backButtonText: {
    fontSize: 14,
    color: '#8E8E8E',
  },
});
