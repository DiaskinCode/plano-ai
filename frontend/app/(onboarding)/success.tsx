import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Image,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { useOnboarding } from '@/components/onboarding/OnboardingContext';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authAPI, todosAPI } from '@/services/api';
import { generateAIPlan } from '@/services/onboardingApi';

const QUICK_SETUP_ITEMS = [
  { id: 1, icon: '📅', title: 'Connect calendar', description: 'Sync with Google, Apple, or Outlook' },
  { id: 2, icon: '🔔', title: 'Enable notifications', description: 'Never miss a deadline' },
  { id: 3, icon: '👥', title: 'Join communities', description: 'Connect with other applicants' },
  { id: 4, icon: '📝', title: 'Schedule mentor call', description: 'Get personalized guidance' },
];

export default function SuccessScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const { updateOnboardingData, onboardingData } = useOnboarding();

  const [selectedPlan] = React.useState('pro');
  const [mentorAssigned, setMentorAssigned] = React.useState(true);
  const [isCreatingTasks, setIsCreatingTasks] = useState(false);
  const [isCompletingBackend, setIsCompletingBackend] = useState(false);

  useEffect(() => {
    const completeOnboardingProcess = async () => {
      try {
        setIsCompletingBackend(true);
        console.log('📋 [SUCCESS] Completing onboarding process...');

        // 1. Call backend to mark onboarding as complete
        try {
          await authAPI.completeOnboarding({
            onboarding_completed: true,
            completed_at: new Date().toISOString(),
          });
          console.log('✅ [SUCCESS] Backend notified: onboarding completed');
        } catch (backendError) {
          console.error('❌ [SUCCESS] Failed to notify backend:', backendError);
          // Continue anyway - user already paid
        }

        // 2. Mark onboarding as complete locally
        updateOnboardingData({
          is_onboarding_complete: true,
          onboarding_completed_at: new Date().toISOString(),
        });

        // 3. Clear guest mode flag
        await AsyncStorage.removeItem('isGuest');
        console.log('✅ [SUCCESS] Guest mode cleared');

        // 4. Regenerate full plan (now that payment is done)
        // The preview only had Month 1, now we need the full 8-month plan
        await regenerateFullPlan();

        // 5. Create tasks from onboarding plan
        await createTasksFromPlan();
        console.log('✅ [SUCCESS] Onboarding process complete');
      } catch (error) {
        console.error('❌ [SUCCESS] Error completing onboarding:', error);
        // Still show success screen even if backend call fails
      } finally {
        setIsCompletingBackend(false);
      }
    };

    completeOnboardingProcess();
  }, []);

  const regenerateFullPlan = async () => {
    try {
      console.log('🔄 [SUCCESS] Regenerating full plan after payment...');

      // Get selected exam types from onboarding data
      const selectedExams = onboardingData.selected_exams || [];
      const selectedLanguageTests = onboardingData.selected_language_tests || [];
      const examTypes = [...selectedExams, ...selectedLanguageTests];

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
          // target_universities is set by target-universities.tsx
          // Map to suggested_universities format expected by backend
          suggested_universities: onboardingData.target_universities || onboardingData.suggested_universities,
        },
      });

      console.log('✅ [SUCCESS] Full plan regenerated');
      console.log('📊 [SUCCESS] Tasks:', response.plan?.tasks?.length);
      console.log('📅 [SUCCESS] Milestones:', response.plan?.milestones?.length);

      // Store the full plan in onboarding data
      updateOnboardingData({
        generated_plan: response.plan,
        plan_is_preview: false,
      });

      console.log('💾 [SUCCESS] Full plan saved to onboarding data');
    } catch (error: any) {
      console.error('❌ [SUCCESS] Failed to regenerate full plan:', error);
      // Don't throw - we can still work with the preview plan
    }
  };

  const createTasksFromPlan = async () => {
    try {
      setIsCreatingTasks(true);

      // Get the generated plan from onboarding data
      const plan = onboardingData.generated_plan;
      if (!plan || !plan.tasks) {
        console.log('⚠️ [SUCCESS] No tasks to create from onboarding plan');
        console.log('📋 [SUCCESS] Plan data:', plan);
        return;
      }

      console.log(`📝 [SUCCESS] Creating ${plan.tasks.length} tasks from plan...`);

      // Create tasks via API
      let createdCount = 0;
      let errorCount = 0;

      for (const task of plan.tasks) {
        try {
          // Calculate scheduled_date from month number
          // Month 1 = this month, Month 2 = next month, etc.
          const taskMonth = task.month || 1;
          const scheduledDate = new Date();
          scheduledDate.setMonth(scheduledDate.getMonth() + (taskMonth - 1));
          // Set to first day of that month
          scheduledDate.setDate(1);

          console.log(`Creating task: "${task.title}" (Month ${taskMonth}, scheduled for ${scheduledDate.toISOString().split('T')[0]})`);

          const newTask = await todosAPI.createTodo({
            title: task.title,
            description: task.description || '',
            scheduled_date: scheduledDate.toISOString().split('T')[0], // YYYY-MM-DD format
            priority: task.priority === 'high' ? 3 : task.priority === 'low' ? 1 : 2,
            timebox_minutes: task.estimated_minutes || 30,
            energy_level: 'medium',
            cognitive_load: 3,
            task_type: 'manual',
            source: 'ai_generated',
            status: 'ready',
            metadata: {
              generated_from_onboarding: true,
              month: taskMonth,
              task_id: task.id,
            },
          });
          createdCount++;
        } catch (error) {
          console.error(`❌ Failed to create task: "${task.title}"`, error);
          errorCount++;
        }
      }

      console.log(`✅ [SUCCESS] Created ${createdCount} tasks successfully (${errorCount} errors)`);
    } catch (error) {
      console.error('❌ [SUCCESS] Error creating tasks from plan:', error);
    } finally {
      setIsCreatingTasks(false);
    }
  };

  const handleGoToDashboard = async () => {
    try {
      console.log('🚀 [SUCCESS] Going to dashboard...');

      // Ensure backend knows onboarding is complete
      try {
        await authAPI.completeOnboarding({
          onboarding_completed: true,
        });
        console.log('✅ [SUCCESS] Backend confirmed onboarding complete');
      } catch (backendError) {
        console.error('❌ [SUCCESS] Backend confirmation failed:', backendError);
        // Navigate anyway - local state is sufficient
      }

      // Clear guest mode
      await AsyncStorage.removeItem('isGuest');

      // Navigate to home tab in main app
      console.log('✅ [SUCCESS] Navigating to home dashboard...');
      router.replace('/(main)/home');
    } catch (error) {
      console.error('❌ [SUCCESS] Error before navigation:', error);
      // Navigate anyway
      router.replace('/(main)/home');
    }
  };

  const handleQuickSetup = (itemId: number) => {
    // TODO: Implement quick setup actions
    console.log('Quick setup item:', itemId);
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Progress */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: '100%' }]} />
          </View>
          <Text style={styles.progressText}>Step 14 of 14 - Complete!</Text>
        </View>

        {/* Celebration */}
        <View style={styles.celebration}>
          <View style={styles.celebrationIcon}>
            <Text style={styles.celebrationEmoji}>🎉</Text>
          </View>
          <Text style={styles.celebrationTitle}>Congratulations!</Text>
          <Text style={styles.celebrationSubtitle}>
            Your personalized plan is ready
          </Text>
        </View>

        {/* Payment Confirmation */}
        {selectedPlan !== 'free' && (
          <View style={styles.paymentConfirmation}>
            <View style={styles.successBadge}>
              <Text style={styles.successBadgeIcon}>✓</Text>
            </View>
            <View style={styles.paymentConfirmationContent}>
              <Text style={styles.paymentConfirmationTitle}>Payment Successful</Text>
              <Text style={styles.paymentConfirmationText}>
                You're now subscribed to the {selectedPlan === 'pro' ? 'Pro' : 'Premium'} plan
              </Text>
            </View>
          </View>
        )}

        {/* Mentor Assignment */}
        {mentorAssigned && (selectedPlan === 'pro' || selectedPlan === 'premium') && (
          <View style={styles.mentorCard}>
            <Text style={styles.mentorCardTitle}>Your AI Mentor is Ready!</Text>
            <View style={styles.mentorInfo}>
              <View style={styles.mentorAvatar}>
                <Text style={styles.mentorAvatarText}>🤖</Text>
              </View>
              <View style={styles.mentorDetails}>
                <Text style={styles.mentorName}>PathAI Assistant</Text>
                <Text style={styles.mentorRole}>Your Personal College Coach</Text>
                <Text style={styles.mentorAvailability}>Available 24/7</Text>
              </View>
            </View>
          </View>
        )}

        {/* Plan Summary */}
        <View style={styles.planSummary}>
          <Text style={styles.planSummaryTitle}>Your Plan is Ready</Text>
          <View style={styles.planStats}>
            <View style={styles.planStat}>
              <Text style={styles.planStatValue}>247</Text>
              <Text style={styles.planStatLabel}>Tasks</Text>
            </View>
            <View style={styles.planStat}>
              <Text style={styles.planStatValue}>8</Text>
              <Text style={styles.planStatLabel}>Months</Text>
            </View>
            <View style={styles.planStat}>
              <Text style={styles.planStatValue}>5</Text>
              <Text style={styles.planStatLabel}>Universities</Text>
            </View>
          </View>
        </View>

        {/* Quick Setup Checklist */}
        <View style={styles.quickSetup}>
          <Text style={styles.quickSetupTitle}>Quick Setup (Optional)</Text>
          <Text style={styles.quickSetupSubtitle}>
            Complete these steps to get the most out of PathAI
          </Text>

          <View style={styles.quickSetupList}>
            {QUICK_SETUP_ITEMS.map((item) => (
              <TouchableOpacity
                key={item.id}
                style={styles.quickSetupItem}
                onPress={() => handleQuickSetup(item.id)}
              >
                <View style={styles.quickSetupIcon}>
                  <Text style={styles.quickSetupIconText}>{item.icon}</Text>
                </View>
                <View style={styles.quickSetupContent}>
                  <Text style={styles.quickSetupItemTitle}>{item.title}</Text>
                  <Text style={styles.quickSetupItemDescription}>{item.description}</Text>
                </View>
                <Text style={styles.quickSetupArrow}>→</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Next Steps */}
        <View style={styles.nextSteps}>
          <Text style={styles.nextStepsTitle}>What's Next?</Text>
          <View style={styles.nextStepsList}>
            <View style={styles.nextStepItem}>
              <View style={styles.nextStepNumber}>
                <Text style={styles.nextStepNumberText}>1</Text>
              </View>
              <Text style={styles.nextStepText}>
                Start with your Week 1 tasks to build momentum
              </Text>
            </View>
            <View style={styles.nextStepItem}>
              <View style={styles.nextStepNumber}>
                <Text style={styles.nextStepNumberText}>2</Text>
              </View>
              <Text style={styles.nextStepText}>
                Join communities to connect with other applicants
              </Text>
            </View>
            <View style={styles.nextStepItem}>
              <View style={styles.nextStepNumber}>
                <Text style={styles.nextStepNumberText}>3</Text>
              </View>
              <Text style={styles.nextStepText}>
                Schedule your first mentor call for personalized guidance
              </Text>
            </View>
          </View>
        </View>

        {/* Go to Dashboard Button */}
        <TouchableOpacity
          style={[
            styles.dashboardButton,
            (isCreatingTasks || isCompletingBackend) && styles.dashboardButtonDisabled
          ]}
          onPress={handleGoToDashboard}
          disabled={isCreatingTasks || isCompletingBackend}
        >
          {(isCreatingTasks || isCompletingBackend) ? (
            <View style={styles.loadingContent}>
              <ActivityIndicator size="small" color="#FFFFFF" />
              <Text style={styles.dashboardButtonText}>
                {isCompletingBackend ? 'Finalizing setup...' : 'Creating your tasks...'}
              </Text>
            </View>
          ) : (
            <Text style={styles.dashboardButtonText}>Go to Dashboard</Text>
          )}
        </TouchableOpacity>

        {/* Skip Setup */}
        <TouchableOpacity
          style={styles.skipButton}
          onPress={handleGoToDashboard}
          disabled={isCreatingTasks || isCompletingBackend}
        >
          <Text style={[
            styles.skipButtonText,
            (isCreatingTasks || isCompletingBackend) && styles.skipButtonTextDisabled
          ]}>
            Skip setup and explore
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
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
    backgroundColor: '#10B981',
  },
  progressText: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 8,
    textAlign: 'center',
    fontWeight: '500',
  },
  celebration: {
    alignItems: 'center',
    marginBottom: 32,
  },
  celebrationIcon: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#EEF2FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  celebrationEmoji: {
    fontSize: 50,
  },
  celebrationTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  celebrationSubtitle: {
    fontSize: 16,
    color: '#6B7280',
  },
  paymentConfirmation: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDF4',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    gap: 12,
  },
  successBadge: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#10B981',
    alignItems: 'center',
    justifyContent: 'center',
  },
  successBadgeIcon: {
    fontSize: 24,
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  paymentConfirmationContent: {
    flex: 1,
  },
  paymentConfirmationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#166534',
    marginBottom: 4,
  },
  paymentConfirmationText: {
    fontSize: 14,
    color: '#166534',
  },
  mentorCard: {
    backgroundColor: '#EEF2FF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  mentorCardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#4338CA',
    marginBottom: 16,
  },
  mentorInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  mentorAvatar: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#6366F1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  mentorAvatarText: {
    fontSize: 28,
  },
  mentorDetails: {
    flex: 1,
  },
  mentorName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  mentorRole: {
    fontSize: 14,
    color: '#6366F1',
    marginBottom: 2,
  },
  mentorAvailability: {
    fontSize: 13,
    color: '#6B7280',
  },
  planSummary: {
    backgroundColor: '#F9FAFB',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  planSummaryTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  planStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  planStat: {
    alignItems: 'center',
  },
  planStatValue: {
    fontSize: 32,
    fontWeight: '700',
    color: '#6366F1',
    marginBottom: 4,
  },
  planStatLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  quickSetup: {
    marginBottom: 24,
  },
  quickSetupTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 8,
  },
  quickSetupSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 16,
  },
  quickSetupList: {
    gap: 12,
  },
  quickSetupItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    gap: 12,
  },
  quickSetupIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  quickSetupIconText: {
    fontSize: 24,
  },
  quickSetupContent: {
    flex: 1,
  },
  quickSetupItemTitle: {
    fontSize: 15,
    fontWeight: '500',
    color: '#111827',
    marginBottom: 2,
  },
  quickSetupItemDescription: {
    fontSize: 13,
    color: '#6B7280',
  },
  quickSetupArrow: {
    fontSize: 20,
    color: '#6B7280',
  },
  nextSteps: {
    backgroundColor: '#FFFBEB',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  nextStepsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#92400E',
    marginBottom: 16,
  },
  nextStepsList: {
    gap: 12,
  },
  nextStepItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  nextStepNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#F59E0B',
    alignItems: 'center',
    justifyContent: 'center',
  },
  nextStepNumberText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  nextStepText: {
    flex: 1,
    fontSize: 14,
    color: '#78350F',
    lineHeight: 20,
  },
  dashboardButton: {
    backgroundColor: '#6366F1',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  dashboardButtonDisabled: {
    opacity: 0.6,
  },
  dashboardButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  loadingContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  skipButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  skipButtonText: {
    fontSize: 14,
    color: '#6B7280',
  },
  skipButtonTextDisabled: {
    opacity: 0.4,
  },
});
