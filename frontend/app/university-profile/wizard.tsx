/**
 * University Profile Wizard
 *
 * Multi-step form for creating/editing university seeker profile:
 * - Step 1: Academic Profile (GPA, test scores, course rigor)
 * - Step 2: Personal & Financial (country, citizenship, budget)
 * - Step 3: Academic Interests (majors, spike)
 * - Step 4: Campus Preferences (size, location, region)
 * - Step 5: Review & Submit
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { universityProfileAPI } from '@/services/universityRecommenderApi';
import { colors, spacing } from '@/theme';

type Step = 'academic' | 'personal' | 'interests' | 'campus' | 'review';

interface FormData {
  // Academic
  gpa: string;
  gpa_scale: '4.0' | '5.0' | '100';
  sat_score: string;
  sat_english: string;
  sat_math: string;
  act_score: string;
  toefl_score: string;
  ielts_score: string;
  duolingo_score: string;
  course_rigor: string;

  // Personal & Financial
  country: string;
  citizenship: string;
  budget_currency: string;
  max_budget: string;
  financial_need: string;
  need_blind_preference: boolean;
  merit_aid_required: boolean;

  // Academic Interests
  intended_major_1: string;
  intended_major_2: string;
  intended_major_3: string;
  academic_interests: string;
  spike_area: string;
  spike_achievement: string;

  // Campus Preferences
  preferred_size: string;
  preferred_location: string;
  preferred_region: string;
  test_optional_flexible: boolean;
  early_decision_willing: boolean;
  early_action_willing: boolean;

  // Constraints
  target_countries: string;
}

const STEPS: { key: Step; title: string; icon: string }[] = [
  { key: 'academic', title: 'Academic', icon: 'school' },
  { key: 'personal', title: 'Personal', icon: 'person' },
  { key: 'interests', title: 'Interests', icon: 'book' },
  { key: 'campus', title: 'Campus', icon: 'location' },
  { key: 'review', title: 'Review', icon: 'checkmark-circle' },
];

export default function UniversityProfileWizard() {
  const [currentStep, setCurrentStep] = useState<Step>('academic');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [completion, setCompletion] = useState(0);
  const [profileExists, setProfileExists] = useState(false);

  const [formData, setFormData] = useState<FormData>({
    // Academic
    gpa: '',
    gpa_scale: '4.0',
    sat_score: '',
    sat_english: '',
    sat_math: '',
    act_score: '',
    toefl_score: '',
    ielts_score: '',
    duolingo_score: '',
    course_rigor: 'regular',

    // Personal & Financial
    country: '',
    citizenship: '',
    budget_currency: 'USD',
    max_budget: '',
    financial_need: 'none',
    need_blind_preference: false,
    merit_aid_required: false,

    // Academic Interests
    intended_major_1: '',
    intended_major_2: '',
    intended_major_3: '',
    academic_interests: '',
    spike_area: '',
    spike_achievement: '',

    // Campus Preferences
    preferred_size: '',
    preferred_location: '',
    preferred_region: '',
    test_optional_flexible: false,
    early_decision_willing: false,
    early_action_willing: true,

    // Constraints
    target_countries: '',
  });

  useEffect(() => {
    loadExistingProfile();
  }, []);

  const loadExistingProfile = async () => {
    try {
      setLoading(true);
      const response = await universityProfileAPI.getProfile();
      const profile = response.data;

      if (profile && !profile.error) {
        // Profile exists - load existing data
        setProfileExists(true);

        setFormData({
          gpa: profile.gpa?.toString() || '',
          gpa_scale: profile.gpa_scale || '4.0',
          sat_score: profile.sat_score?.toString() || '',
          sat_english: profile.sat_english?.toString() || '',
          sat_math: profile.sat_math?.toString() || '',
          act_score: profile.act_score?.toString() || '',
          toefl_score: profile.toefl_score?.toString() || '',
          ielts_score: profile.ielts_score?.toString() || '',
          duolingo_score: profile.duolingo_score?.toString() || '',
          course_rigor: profile.course_rigor || 'regular',

          country: profile.country || '',
          citizenship: profile.citizenship || '',
          budget_currency: profile.budget_currency || 'USD',
          max_budget: profile.max_budget?.toString() || '',
          financial_need: profile.financial_need || 'none',
          need_blind_preference: profile.need_blind_preference || false,
          merit_aid_required: profile.merit_aid_required || false,

          intended_major_1: profile.intended_major_1 || '',
          intended_major_2: profile.intended_major_2 || '',
          intended_major_3: profile.intended_major_3 || '',
          academic_interests: profile.academic_interests || '',
          spike_area: profile.spike_area || '',
          spike_achievement: profile.spike_achievement || '',

          preferred_size: profile.preferred_size || '',
          preferred_location: profile.preferred_location || '',
          preferred_region: profile.preferred_region || '',
          test_optional_flexible: profile.test_optional_flexible || false,
          early_decision_willing: profile.early_decision_willing || false,
          early_action_willing: profile.early_action_willing !== false,

          target_countries: profile.target_countries?.join(', ') || '',
        });
      }

      // Load completion status
      const completionResponse = await universityProfileAPI.getCompletion();
      if (completionResponse.data) {
        setCompletion(completionResponse.data.completion_percentage || 0);
      }
    } catch (error: any) {
      console.error('Failed to load profile:', error);
      // 404 means no profile exists yet - this is normal for new users
      if (error.response?.status !== 404) {
        // Only show alert for non-404 errors
        Alert.alert('Error', 'Failed to load profile. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const updateField = (field: keyof FormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const getCurrentStepIndex = () => {
    return STEPS.findIndex(step => step.key === currentStep);
  };

  const goToStep = (step: Step) => {
    setCurrentStep(step);
  };

  const goToNextStep = () => {
    const currentIndex = getCurrentStepIndex();
    if (currentIndex < STEPS.length - 1) {
      setCurrentStep(STEPS[currentIndex + 1].key);
    }
  };

  const goToPreviousStep = () => {
    const currentIndex = getCurrentStepIndex();
    if (currentIndex > 0) {
      setCurrentStep(STEPS[currentIndex - 1].key);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);

      // Prepare data for API
      const data: any = {
        gpa: parseFloat(formData.gpa) || 0,
        gpa_scale: formData.gpa_scale,
        sat_score: formData.sat_score ? parseInt(formData.sat_score) : null,
        sat_english: formData.sat_english ? parseInt(formData.sat_english) : null,
        sat_math: formData.sat_math ? parseInt(formData.sat_math) : null,
        act_score: formData.act_score ? parseInt(formData.act_score) : null,
        toefl_score: formData.toefl_score ? parseInt(formData.toefl_score) : null,
        ielts_score: formData.ielts_score ? parseFloat(formData.ielts_score) : null,
        duolingo_score: formData.duolingo_score ? parseInt(formData.duolingo_score) : null,
        course_rigor: formData.course_rigor,

        country: formData.country,
        citizenship: formData.citizenship,
        budget_currency: formData.budget_currency,
        max_budget: formData.max_budget ? parseInt(formData.max_budget) : null,
        financial_need: formData.financial_need,
        need_blind_preference: formData.need_blind_preference,
        merit_aid_required: formData.merit_aid_required,

        intended_major_1: formData.intended_major_1,
        intended_major_2: formData.intended_major_2,
        intended_major_3: formData.intended_major_3,
        academic_interests: formData.academic_interests,
        spike_area: formData.spike_area,
        spike_achievement: formData.spike_achievement,

        preferred_size: formData.preferred_size,
        preferred_location: formData.preferred_location,
        preferred_region: formData.preferred_region,
        test_optional_flexible: formData.test_optional_flexible,
        early_decision_willing: formData.early_decision_willing,
        early_action_willing: formData.early_action_willing,

        target_countries: formData.target_countries ? formData.target_countries.split(',').map(s => s.trim()) : [],
      };

      // Use createProfile for new profiles, updateProfile for existing ones
      if (profileExists) {
        await universityProfileAPI.updateProfile(data);
      } else {
        await universityProfileAPI.createProfile(data);
      }

      Alert.alert(
        profileExists ? 'Profile Updated!' : 'Profile Created!',
        profileExists
          ? 'Your university profile has been updated successfully.'
          : 'Your university profile is ready! View your personalized university recommendations now.',
        profileExists
          ? [{ text: 'OK', onPress: () => router.replace('/(main)/home') }]
          : [
              { text: 'Not Now', style: 'cancel', onPress: () => router.replace('/(main)/home') },
              {
                text: 'View Recommendations',
                onPress: () => router.push('/university-recommender/results'),
              },
              {
                text: 'Add Activities',
                onPress: () => router.push('/university-profile/activities'),
              },
            ]
      );
    } catch (error: any) {
      console.error('Failed to save profile:', error);
      Alert.alert('Error', 'Failed to save profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const renderStepIndicator = () => (
    <View style={styles.stepIndicator}>
      {STEPS.map((step, index) => (
        <TouchableOpacity
          key={step.key}
          style={[styles.stepDot, currentStep === step.key && styles.stepDotActive]}
          onPress={() => goToStep(step.key as Step)}
        >
          <Ionicons
            name={step.icon as any}
            size={20}
            color={currentStep === step.key ? colors.primary : colors.textSecondary}
          />
          <Text style={[styles.stepLabel, currentStep === step.key && styles.stepLabelActive]}>
            {step.title}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );

  const renderAcademicStep = () => (
    <ScrollView style={styles.stepContent}>
      <Text style={styles.stepTitle}>Academic Profile</Text>
      <Text style={styles.stepDescription}>Tell us about your academic performance</Text>

      <Text style={styles.sectionTitle}>Test Scores</Text>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>GPA *</Text>
        <View style={styles.row}>
          <TextInput
            style={[styles.input, { flex: 1 }]}
            placeholder="3.5"
            placeholderTextColor={colors.textSecondary}
            value={formData.gpa}
            onChangeText={(value) => updateField('gpa', value)}
            keyboardType="decimal-pad"
          />
          <TextInput
            style={[styles.picker, { flex: 1 }]}
            value={formData.gpa_scale}
            onChangeText={(value) => updateField('gpa_scale', value)}
          />
        </View>
        <Text style={styles.helperText}>Enter your cumulative GPA on your school's scale</Text>
      </View>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>SAT Score (out of 1600)</Text>
        <TextInput
          style={styles.input}
          placeholder="1500"
          placeholderTextColor={colors.textSecondary}
          value={formData.sat_score}
          onChangeText={(value) => updateField('sat_score', value)}
          keyboardType="number-pad"
        />
        <Text style={styles.helperText}>Leave blank if you haven't taken the SAT</Text>
      </View>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>SAT Section Scores</Text>
        <View style={styles.row}>
          <TextInput
            style={[styles.input, { flex: 1 }]}
            placeholder="Math: 750"
            placeholderTextColor={colors.textSecondary}
            value={formData.sat_math}
            onChangeText={(value) => updateField('sat_math', value)}
            keyboardType="number-pad"
          />
          <TextInput
            style={[styles.input, { flex: 1 }]}
            placeholder="English: 750"
            placeholderTextColor={colors.textSecondary}
            value={formData.sat_english}
            onChangeText={(value) => updateField('sat_english', value)}
            keyboardType="number-pad"
          />
        </View>
      </View>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>ACT Score (out of 36)</Text>
        <TextInput
          style={styles.input}
          placeholder="32"
          placeholderTextColor={colors.textSecondary}
          value={formData.act_score}
          onChangeText={(value) => updateField('act_score', value)}
          keyboardType="number-pad"
        />
      </View>

      <View style={styles.sectionDivider} />

      <Text style={styles.sectionTitle}>English Proficiency</Text>
      <Text style={[styles.helperText, { marginBottom: spacing.md }]}>
        For international students or non-native English speakers
      </Text>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>English Proficiency Tests (Optional)</Text>
        <TextInput
          style={styles.input}
          placeholder="TOEFL (out of 120)"
          placeholderTextColor={colors.textSecondary}
          value={formData.toefl_score}
          onChangeText={(value) => updateField('toefl_score', value)}
          keyboardType="number-pad"
        />
        <View style={{ height: spacing.sm }} />
        <TextInput
          style={styles.input}
          placeholder="IELTS (out of 9.0)"
          placeholderTextColor={colors.textSecondary}
          value={formData.ielts_score}
          onChangeText={(value) => updateField('ielts_score', value)}
          keyboardType="decimal-pad"
        />
        <View style={{ height: spacing.sm }} />
        <TextInput
          style={styles.input}
          placeholder="Duolingo (out of 160)"
          placeholderTextColor={colors.textSecondary}
          value={formData.duolingo_score}
          onChangeText={(value) => updateField('duolingo_score', value)}
          keyboardType="number-pad"
        />
      </View>

      <View style={styles.sectionDivider} />

      <Text style={styles.sectionTitle}>Academic Rigor</Text>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Course Rigor</Text>
        <View style={styles.options}>
          {['ap_ib_ib_plus', 'ap_ib', 'honors', 'regular'].map((option) => (
            <TouchableOpacity
              key={option}
              style={[styles.option, formData.course_rigor === option && styles.optionSelected]}
              onPress={() => updateField('course_rigor', option)}
            >
              <Text style={formData.course_rigor === option ? styles.optionTextSelected : styles.optionText}>
                {option === 'ap_ib_ib_plus' ? 'AP+IB+' :
                 option === 'ap_ib' ? 'AP/IB' :
                 option === 'honors' ? 'Honors' :
                 'Regular'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
        <Text style={styles.helperText}>Select the most advanced level of courses you've taken</Text>
      </View>
    </ScrollView>
  );

  const renderPersonalStep = () => (
    <ScrollView style={styles.stepContent}>
      <Text style={styles.stepTitle}>Personal & Financial</Text>
      <Text style={styles.stepDescription}>Your location and financial preferences</Text>

      <Text style={styles.sectionTitle}>Location</Text>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Country of Residence *</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g., USA, UK, Canada"
          placeholderTextColor={colors.textSecondary}
          value={formData.country}
          onChangeText={(value) => updateField('country', value)}
        />
      </View>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Citizenship *</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g., USA, UK, Canada"
          placeholderTextColor={colors.textSecondary}
          value={formData.citizenship}
          onChangeText={(value) => updateField('citizenship', value)}
        />
        <Text style={styles.helperText}>Important for financial aid and visa considerations</Text>
      </View>

      <View style={styles.sectionDivider} />

      <Text style={styles.sectionTitle}>Financial Information</Text>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Maximum Budget per Year (USD)</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g., 50000"
          placeholderTextColor={colors.textSecondary}
          value={formData.max_budget}
          onChangeText={(value) => updateField('max_budget', value)}
          keyboardType="number-pad"
        />
        <Text style={styles.helperText}>Including tuition, room, and board</Text>
      </View>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Financial Need</Text>
        <View style={styles.options}>
          {['full_ride', 'significant', 'moderate', 'none'].map((option) => (
            <TouchableOpacity
              key={option}
              style={[styles.option, formData.financial_need === option && styles.optionSelected]}
              onPress={() => updateField('financial_need', option)}
            >
              <Text style={formData.financial_need === option ? styles.optionTextSelected : styles.optionText}>
                {option === 'full_ride' ? 'Full Ride' :
                 option === 'significant' ? 'High Need' :
                 option === 'moderate' ? 'Some Aid' :
                 'No Need'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
        <Text style={styles.helperText}>How much financial aid do you need?</Text>
      </View>

      <View style={styles.fieldGroup}>
        <TouchableOpacity
          style={[styles.checkbox, formData.need_blind_preference && styles.checkboxSelected]}
          onPress={() => updateField('need_blind_preference', !formData.need_blind_preference)}
        >
          <Ionicons
            name={formData.need_blind_preference ? 'checkbox' : 'square-outline'}
            size={24}
            color={colors.primary}
          />
          <Text style={styles.checkboxLabel}>Prefer need-blind schools (meet 100% of demonstrated need)</Text>
        </TouchableOpacity>
        <Text style={styles.helperText}>These schools don't consider finances in admissions</Text>
      </View>

      <View style={styles.fieldGroup}>
        <TouchableOpacity
          style={[styles.checkbox, formData.merit_aid_required && styles.checkboxSelected]}
          onPress={() => updateField('merit_aid_required', !formData.merit_aid_required)}
        >
          <Ionicons
            name={formData.merit_aid_required ? 'checkbox' : 'square-outline'}
            size={24}
            color={colors.primary}
          />
          <Text style={styles.checkboxLabel}>Require merit-based aid</Text>
        </TouchableOpacity>
        <Text style={styles.helperText}>Scholarships based on achievements</Text>
      </View>
    </ScrollView>
  );

  const renderInterestsStep = () => (
    <ScrollView style={styles.stepContent}>
      <Text style={styles.stepTitle}>Academic Interests</Text>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Primary Intended Major *</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g., Computer Science"
          value={formData.intended_major_1}
          onChangeText={(value) => updateField('intended_major_1', value)}
        />
      </View>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Secondary Intended Major</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g., Mathematics"
          value={formData.intended_major_2}
          onChangeText={(value) => updateField('intended_major_2', value)}
        />
      </View>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Tertiary Intended Major</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g., Data Science"
          value={formData.intended_major_3}
          onChangeText={(value) => updateField('intended_major_3', value)}
        />
      </View>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Why are you interested in these fields?</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          placeholder="Explain your academic interests and motivations..."
          value={formData.academic_interests}
          onChangeText={(value) => updateField('academic_interests', value)}
          multiline
          numberOfLines={4}
        />
      </View>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Spike Area (Exceptional Achievement)</Text>
        <View style={styles.options}>
          {['research_olympiad', 'athletics', 'arts', 'leadership', ''].map((option) => (
            <TouchableOpacity
              key={option || 'none'}
              style={[styles.option, formData.spike_area === option && styles.optionSelected]}
              onPress={() => updateField('spike_area', option)}
            >
              <Text style={formData.spike_area === option ? styles.optionTextSelected : styles.optionText}>
                {option === 'research_olympiad' ? 'Research/Olympiad (IMO, IPhO)' :
                 option === 'athletics' ? 'Athletics (Recruited)' :
                 option === 'arts' ? 'Arts' :
                 option === 'leadership' ? 'Leadership' :
                 'None'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {formData.spike_area && (
        <View style={styles.fieldGroup}>
          <Text style={styles.label}>Describe your achievement</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            placeholder="Describe your exceptional achievement..."
            value={formData.spike_achievement}
            onChangeText={(value) => updateField('spike_achievement', value)}
            multiline
            numberOfLines={3}
          />
        </View>
      )}
    </ScrollView>
  );

  const renderCampusStep = () => (
    <ScrollView style={styles.stepContent}>
      <Text style={styles.stepTitle}>Campus Preferences</Text>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Preferred University Size</Text>
        <View style={styles.options}>
          {['small', 'medium', 'large'].map((option) => (
            <TouchableOpacity
              key={option}
              style={[styles.option, formData.preferred_size === option && styles.optionSelected]}
              onPress={() => updateField('preferred_size', option)}
            >
              <Text style={formData.preferred_size === option ? styles.optionTextSelected : styles.optionText}>
                {option === 'small' ? 'Small (< 5,000 students)' :
                 option === 'medium' ? 'Medium (5,000 - 15,000)' :
                 'Large (> 15,000)'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Preferred Location</Text>
        <View style={styles.options}>
          {['urban', 'suburban', 'rural'].map((option) => (
            <TouchableOpacity
              key={option}
              style={[styles.option, formData.preferred_location === option && styles.optionSelected]}
              onPress={() => updateField('preferred_location', option)}
            >
              <Text style={formData.preferred_location === option ? styles.optionTextSelected : styles.optionText}>
                {option.charAt(0).toUpperCase() + option.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Preferred Region</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g., Northeast, West Coast, Midwest"
          value={formData.preferred_region}
          onChangeText={(value) => updateField('preferred_region', value)}
        />
      </View>

      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Target Countries (comma-separated)</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g., USA, UK, Canada"
          value={formData.target_countries}
          onChangeText={(value) => updateField('target_countries', value)}
        />
      </View>

      <View style={styles.fieldGroup}>
        <TouchableOpacity
          style={[styles.checkbox, formData.test_optional_flexible && styles.checkboxSelected]}
          onPress={() => updateField('test_optional_flexible', !formData.test_optional_flexible)}
        >
          <Ionicons
            name={formData.test_optional_flexible ? 'checkbox' : 'square-outline'}
            size={24}
            color={colors.primary}
          />
          <Text style={styles.checkboxLabel}>Flexible about test-optional schools</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.fieldGroup}>
        <TouchableOpacity
          style={[styles.checkbox, formData.early_decision_willing && styles.checkboxSelected]}
          onPress={() => updateField('early_decision_willing', !formData.early_decision_willing)}
        >
          <Ionicons
            name={formData.early_decision_willing ? 'checkbox' : 'square-outline'}
            size={24}
            color={colors.primary}
          />
          <Text style={styles.checkboxLabel}>Willing to apply Early Decision</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.fieldGroup}>
        <TouchableOpacity
          style={[styles.checkbox, !formData.early_action_willing && styles.checkboxSelected]}
          onPress={() => updateField('early_action_willing', !formData.early_action_willing)}
        >
          <Ionicons
            name={!formData.early_action_willing ? 'checkbox' : 'square-outline'}
            size={24}
            color={colors.primary}
          />
          <Text style={styles.checkboxLabel}>Willing to apply Early Action</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );

  const renderReviewStep = () => (
    <ScrollView style={styles.stepContent}>
      <Text style={styles.stepTitle}>Review Your Profile</Text>

      <View style={styles.reviewCard}>
        <Text style={styles.reviewSection}>Completion: {completion.toFixed(0)}%</Text>

        <View style={styles.reviewItem}>
          <Text style={styles.reviewLabel}>GPA:</Text>
          <Text style={styles.reviewValue}>{formData.gpa || 'Not set'} ({formData.gpa_scale} scale)</Text>
        </View>

        <View style={styles.reviewItem}>
          <Text style={styles.reviewLabel}>Country:</Text>
          <Text style={styles.reviewValue}>{formData.country || 'Not set'}</Text>
        </View>

        <View style={styles.reviewItem}>
          <Text style={styles.reviewLabel}>Citizenship:</Text>
          <Text style={styles.reviewValue}>{formData.citizenship || 'Not set'}</Text>
        </View>

        <View style={styles.reviewItem}>
          <Text style={styles.reviewLabel}>Intended Major:</Text>
          <Text style={styles.reviewValue}>{formData.intended_major_1 || 'Not set'}</Text>
        </View>

        <View style={styles.reviewItem}>
          <Text style={styles.reviewLabel}>Financial Need:</Text>
          <Text style={styles.reviewValue}>{formData.financial_need || 'Not set'}</Text>
        </View>

        {completion < 40 && (
          <Text style={styles.warning}>
            ⚠️ Complete required fields for better recommendations
          </Text>
        )}
      </View>
    </ScrollView>
  );

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 'academic':
        return renderAcademicStep();
      case 'personal':
        return renderPersonalStep();
      case 'interests':
        return renderInterestsStep();
      case 'campus':
        return renderCampusStep();
      case 'review':
        return renderReviewStep();
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading profile...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.replace('/(main)/home')} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>University Profile</Text>
        <View style={styles.placeholder} />
      </View>

      {renderStepIndicator()}

      {renderCurrentStep()}

      <View style={styles.footer}>
        {getCurrentStepIndex() > 0 && (
          <TouchableOpacity
            style={[styles.navButton, styles.secondaryNavButton]}
            onPress={goToPreviousStep}
          >
            <Text style={styles.secondaryNavButtonText}>Previous</Text>
          </TouchableOpacity>
        )}

        {getCurrentStepIndex() < STEPS.length - 1 ? (
          <TouchableOpacity
            style={styles.navButton}
            onPress={goToNextStep}
          >
            <Text style={styles.navButtonText}>Next</Text>
            <Ionicons name="arrow-forward" size={20} color="#fff" />
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={styles.navButton}
            onPress={handleSave}
            disabled={saving}
          >
            {saving ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.navButtonText}>Save Profile</Text>
            )}
          </TouchableOpacity>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backButton: {
    padding: spacing.xs,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text,
  },
  placeholder: {
    width: 24,
  },
  stepIndicator: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  stepDot: {
    alignItems: 'center',
    opacity: 0.5,
  },
  stepDotActive: {
    opacity: 1,
  },
  stepLabel: {
    fontSize: 10,
    marginTop: spacing.xs,
    color: colors.textSecondary,
  },
  stepLabelActive: {
    color: colors.primary,
    fontWeight: '600',
  },
  stepContent: {
    flex: 1,
    padding: spacing.md,
  },
  stepTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  stepDescription: {
    fontSize: 15,
    color: colors.textSecondary,
    marginBottom: spacing.xl,
  },
  sectionDivider: {
    height: 1,
    backgroundColor: colors.border,
    marginVertical: spacing.xl,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.primary,
    marginTop: spacing.lg,
    marginBottom: spacing.md,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  fieldGroup: {
    marginBottom: spacing.lg,
  },
  label: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  helperText: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: spacing.xs,
    lineHeight: 18,
  },
  input: {
    backgroundColor: colors.card,
    borderRadius: 12,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 2,
    fontSize: 16,
    color: colors.text,
    borderWidth: 1.5,
    borderColor: colors.border,
    placeholderTextColor: colors.textSecondary,
  },
  picker: {
    backgroundColor: colors.card,
    borderRadius: 12,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 2,
    fontSize: 16,
    color: colors.text,
    borderWidth: 1.5,
    borderColor: colors.border,
    marginLeft: spacing.sm,
  },
  textArea: {
    minHeight: 100,
    textAlignVertical: 'top',
  },
  row: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  options: {
    gap: spacing.sm,
  },
  option: {
    flex: 1,
    padding: spacing.md,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.card,
    alignItems: 'center',
    minHeight: 56,
    justifyContent: 'center',
  },
  optionSelected: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primary,
    borderWidth: 2,
  },
  optionText: {
    fontSize: 13,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
  },
  optionTextSelected: {
    color: colors.primary,
    fontWeight: '700',
  },
  checkbox: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    borderRadius: 12,
    backgroundColor: colors.card,
    borderWidth: 1.5,
    borderColor: colors.border,
    gap: spacing.sm,
  },
  checkboxSelected: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primary,
    borderWidth: 2,
  },
  checkboxLabel: {
    fontSize: 15,
    color: colors.text,
    flex: 1,
  },
  reviewCard: {
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: spacing.md,
    gap: spacing.md,
  },
  reviewSection: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  reviewItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  reviewLabel: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  reviewValue: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
  },
  warning: {
    fontSize: 12,
    color: colors.warning,
    marginTop: spacing.sm,
  },
  secondaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  secondaryButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.primary,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    gap: spacing.sm,
    backgroundColor: colors.background,
  },
  navButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    backgroundColor: colors.primary,
    borderRadius: 14,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  navButtonDisabled: {
    opacity: 0.5,
  },
  secondaryNavButton: {
    backgroundColor: colors.card,
    borderWidth: 1.5,
    borderColor: colors.border,
  },
  navButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  secondaryNavButtonText: {
    color: colors.text,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: spacing.md,
  },
  loadingText: {
    fontSize: 14,
    color: colors.textSecondary,
  },
});
