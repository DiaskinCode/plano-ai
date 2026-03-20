import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { useOnboarding } from '@/components/onboarding/OnboardingContext';
import { generateAIPlan } from '@/services/onboardingApi';

const CHECKLIST_ITEMS = [
  { id: 1, text: 'Analyzing your profile', duration: 2000 },
  { id: 2, text: 'Creating milestones', duration: 1500 },
  { id: 3, text: 'Generating tasks', duration: 3000 },
  { id: 4, text: 'Matching deadlines', duration: 2000 },
  { id: 5, text: 'Personalizing your plan', duration: 2500 },
];

const FUN_FACTS = [
  'Did you know? Top universities look for consistent commitment in extracurriculars.',
  'Tip: Start your essays early to allow time for multiple revisions.',
  'Fact: Most successful applicants apply to 7-10 universities.',
  'Remember: Quality of activities matters more than quantity.',
  'Tip: Request recommendation letters at least 3 weeks before deadlines.',
];

export default function GeneratingScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const { updateOnboardingData, onboardingData } = useOnboarding();

  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [funFactIndex, setFunFactIndex] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(15);
  const [hasGenerated, setHasGenerated] = useState(false); // Track if we've already generated

  useEffect(() => {
    let totalDuration = 0;
    let currentStepId = 0;

    CHECKLIST_ITEMS.forEach((item) => {
      const timer = setTimeout(() => {
        setCompletedSteps((prev) => [...prev, item.id]);
        setCurrentStep(currentStepId + 1);
        currentStepId++;
      }, totalDuration + item.duration);
      totalDuration += item.duration;
    });

    // Generate the AI plan after animation starts (only once)
    const generatePlanTimer = setTimeout(async () => {
      if (hasGenerated) return; // Prevent multiple calls
      setHasGenerated(true);

      try {
        console.log('📋 [GENERATING] Calling generateAIPlan API...');
        console.log('📊 [GENERATING] Onboarding data keys:', Object.keys(onboardingData));
        console.log('🎯 [GENERATING] Extracurriculars:', onboardingData.extracurriculars);
        console.log('🎓 [GENERATING] Target universities:', onboardingData.target_universities || onboardingData.suggested_universities);

        // Get selected exam types from onboarding data
        const selectedExams = onboardingData.selected_exams || [];
        const selectedLanguageTests = onboardingData.selected_language_tests || [];
        const examTypes = [...selectedExams, ...selectedLanguageTests];

        console.log('✍️ [GENERATING] Exam types:', examTypes);

        const response = await generateAIPlan({
          includeTimeline: true,
          includeTasks: true,
          includeMilestones: true,
          startDate: new Date().toISOString(),
          examTypes,
          // Pass onboarding data directly since backend OnboardingState might be empty
          onboardingData: {
            academic_profile: {
              gpa: onboardingData.gpa,
              student_status: onboardingData.student_status,
              school_name: onboardingData.school_name,
              graduation_year: onboardingData.graduation_year,
            },
            test_scores: {
              sat_score: onboardingData.sat_score,
              act_score: onboardingData.act_score,
            },
            // Include extracurriculars from onboarding flow
            extracurriculars: onboardingData.extracurriculars || [],
            // target_universities is set by target-universities.tsx
            // Map to suggested_universities format expected by backend
            suggested_universities: onboardingData.target_universities || onboardingData.suggested_universities,
          },
        });

        console.log('✅ [GENERATING] Plan generated successfully');
        console.log('📊 [GENERATING] Tasks:', response.plan?.tasks?.length);
        console.log('📅 [GENERATING] Milestones:', response.plan?.milestones?.length);

        // Store the generated plan in onboarding data
        updateOnboardingData({
          generated_plan: response.plan,
          plan_is_preview: response.plan?.is_preview || false,
        });

        console.log('💾 [GENERATING] Plan saved to onboarding data');
      } catch (error: any) {
        console.error('❌ [GENERATING] Failed to generate plan:', error);
        console.error('❌ [GENERATING] Error response:', error.response?.data);
        console.error('❌ [GENERATING] Error message:', error.message);

        // Show detailed error information
        let errorMessage = 'Failed to generate your plan. Please try again.';
        if (error.response?.data) {
          const errorData = error.response.data;
          if (typeof errorData === 'string') {
            errorMessage = errorData;
          } else if (errorData.detail) {
            errorMessage = errorData.detail;
          } else if (errorData.error) {
            errorMessage = errorData.error;
          } else if (typeof errorData === 'object') {
            // Show all validation errors
            const errors = Object.entries(errorData)
              .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
              .join('\n');
            errorMessage = `Validation errors:\n${errors}`;
          }
        } else if (error.message) {
          errorMessage = error.message;
        }

        Alert.alert(
          'Generation Failed',
          errorMessage,
          [
            {
              text: 'Retry',
              onPress: () => router.back(),
            },
          ]
        );
      }
    }, 1000); // Start API call after 1 second

    // Navigate after all steps complete
    const navigationTimer = setTimeout(() => {
      router.replace('/(onboarding)/preview');
    }, totalDuration + 1000);

    // Cycle through fun facts
    const factTimer = setInterval(() => {
      setFunFactIndex((prev) => (prev + 1) % FUN_FACTS.length);
    }, 4000);

    // Countdown timer
    const countdownTimer = setInterval(() => {
      setTimeRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => {
      CHECKLIST_ITEMS.forEach((item) => {
        // Clear all timers (cleanup handled by the setTimeout returns)
      });
      clearTimeout(generatePlanTimer);
      clearTimeout(navigationTimer);
      clearInterval(factTimer);
      clearInterval(countdownTimer);
    };
  }, []); // Empty deps - only run once on mount

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Logo */}
        <View style={styles.logoContainer}>
          <View style={styles.logo}>
            <Text style={styles.logoText}>P</Text>
          </View>
          <Text style={styles.appName}>PathAI</Text>
        </View>

        {/* Loading Animation */}
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#6366F1" />
          <Text style={styles.loadingTitle}>Creating Your Personalized Plan...</Text>
        </View>

        {/* Progress Checklist */}
        <View style={styles.checklistContainer}>
          <Text style={styles.checklistTitle}>Progress</Text>
          <View style={styles.checklist}>
            {CHECKLIST_ITEMS.map((item, index) => {
              const isCompleted = completedSteps.includes(item.id);
              const isCurrent = !isCompleted && (index === currentStep || index === completedSteps.length);

              return (
                <View key={item.id} style={styles.checklistItem}>
                  <View style={[styles.checklistIcon, isCompleted && styles.checklistIconCompleted]}>
                    {isCompleted ? (
                      <Text style={styles.checkmark}>✓</Text>
                    ) : isCurrent ? (
                      <ActivityIndicator size="small" color="#6366F1" />
                    ) : (
                      <View style={styles.checklistIconPending} />
                    )}
                  </View>
                  <Text style={[styles.checklistText, isCompleted && styles.checklistTextCompleted]}>
                    {item.text}
                  </Text>
                </View>
              );
            })}
          </View>
        </View>

        {/* Fun Fact */}
        <View style={styles.factCard}>
          <Text style={styles.factIcon}>💡</Text>
          <Text style={styles.factText}>{FUN_FACTS[funFactIndex]}</Text>
        </View>

        {/* Estimated Time */}
        <Text style={styles.estimatedTime}>
          Estimated time remaining: ~{timeRemaining} seconds
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  content: {
    flex: 1,
    paddingHorizontal: 32,
    paddingTop: 60,
    alignItems: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 60,
  },
  logo: {
    width: 80,
    height: 80,
    borderRadius: 20,
    backgroundColor: '#6366F1',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  logoText: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  appName: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1F2937',
  },
  loadingContainer: {
    alignItems: 'center',
    marginBottom: 48,
  },
  loadingTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginTop: 16,
  },
  checklistContainer: {
    width: '100%',
    marginBottom: 32,
  },
  checklistTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  checklist: {
    gap: 16,
  },
  checklistItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  checklistIcon: {
    width: 24,
    height: 24,
    borderRadius: 6,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  checklistIconCompleted: {
    backgroundColor: '#10B981',
  },
  checklistIconPending: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#D1D5DB',
  },
  checkmark: {
    fontSize: 14,
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  checklistText: {
    flex: 1,
    fontSize: 15,
    color: '#6B7280',
  },
  checklistTextCompleted: {
    color: '#111827',
  },
  factCard: {
    backgroundColor: '#EEF2FF',
    borderRadius: 12,
    padding: 16,
    width: '100%',
    marginBottom: 24,
  },
  factIcon: {
    fontSize: 20,
    marginBottom: 8,
  },
  factText: {
    fontSize: 14,
    color: '#4338CA',
    lineHeight: 20,
  },
  estimatedTime: {
    fontSize: 14,
    color: '#9CA3AF',
  },
});
