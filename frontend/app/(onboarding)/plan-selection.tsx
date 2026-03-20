import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { useOnboarding } from '@/components/onboarding/OnboardingContext';

interface PlanType {
  id: string;
  name: string;
  description: string;
  duration: string;
  taskCount: number;
  icon: string;
  color: string;
  subOptions?: string[];
  required: boolean;
}

const PLAN_TYPES: PlanType[] = [
  {
    id: 'university',
    name: 'University Acceptance',
    description: 'Complete application roadmap with essays, documents, and deadlines',
    duration: '8 months',
    taskCount: 200,
    icon: '🎓',
    color: '#6366F1',
    required: true,
  },
  {
    id: 'exams',
    name: 'Exam Preparation',
    description: 'SAT, ACT, CSEE test prep with practice schedules',
    duration: '6 months',
    taskCount: 120,
    icon: '📊',
    color: '#F59E0B',
    required: false,
    subOptions: ['SAT', 'ACT', 'CSEE'],
  },
  {
    id: 'language',
    name: 'Language Tests',
    description: 'IELTS, TOEFL, HSK, DELF preparation plans',
    duration: '4 months',
    taskCount: 80,
    icon: '🗣️',
    color: '#10B981',
    required: false,
    subOptions: ['IELTS', 'TOEFL', 'HSK', 'DELF'],
  },
];

export default function PlanSelectionScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const { onboardingData, updateOnboardingData } = useOnboarding();

  const [selectedPlans, setSelectedPlans] = useState<string[]>(['university']); // University always selected
  const [selectedExams, setSelectedExams] = useState<string[]>([]);
  const [selectedLanguageTests, setSelectedLanguageTests] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const togglePlan = (planId: string) => {
    // University plan cannot be deselected
    if (planId === 'university') return;

    if (selectedPlans.includes(planId)) {
      // Deselecting a plan clears its sub-options
      if (planId === 'exams') setSelectedExams([]);
      if (planId === 'language') setSelectedLanguageTests([]);
      setSelectedPlans(prev => prev.filter(id => id !== planId));
    } else {
      setSelectedPlans(prev => [...prev, planId]);
    }
  };

  const toggleExam = (exam: string) => {
    if (selectedExams.includes(exam)) {
      setSelectedExams(prev => prev.filter(e => e !== exam));
      // If no exams selected, deselect exams plan
      if (selectedExams.length === 1) {
        setSelectedPlans(prev => prev.filter(id => id !== 'exams'));
      }
    } else {
      setSelectedExams(prev => [...prev, exam]);
      // Ensure exams plan is selected
      if (!selectedPlans.includes('exams')) {
        setSelectedPlans(prev => [...prev, 'exams']);
      }
    }
  };

  const toggleLanguageTest = (test: string) => {
    if (selectedLanguageTests.includes(test)) {
      setSelectedLanguageTests(prev => prev.filter(t => t !== test));
      // If no tests selected, deselect language plan
      if (selectedLanguageTests.length === 1) {
        setSelectedPlans(prev => prev.filter(id => id !== 'language'));
      }
    } else {
      setSelectedLanguageTests(prev => [...prev, test]);
      // Ensure language plan is selected
      if (!selectedPlans.includes('language')) {
        setSelectedPlans(prev => [...prev, 'language']);
      }
    }
  };

  const calculateTotalTasks = () => {
    let total = 0;
    selectedPlans.forEach(planId => {
      const plan = PLAN_TYPES.find(p => p.id === planId);
      if (plan) {
        if (plan.id === 'exams' && selectedExams.length > 0) {
          total += Math.round(plan.taskCount * (selectedExams.length / 3));
        } else if (plan.id === 'language' && selectedLanguageTests.length > 0) {
          total += Math.round(plan.taskCount * (selectedLanguageTests.length / 4));
        } else {
          total += plan.taskCount;
        }
      }
    });
    return total;
  };

  const handleNext = async () => {
    try {
      setLoading(true);

      // Save onboarding data
      updateOnboardingData({
        selected_plans: selectedPlans,
        selected_exams: selectedExams,
        selected_language_tests: selectedLanguageTests,
        total_task_count: calculateTotalTasks(),
      });

      router.push('/(onboarding)/generating');
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to save plan selection');
    } finally {
      setLoading(false);
    }
  };

  const renderSubOptions = (planId: string, options: string[]) => {
    const selectedOptions = planId === 'exams' ? selectedExams : selectedLanguageTests;
    const toggle = planId === 'exams' ? toggleExam : toggleLanguageTest;

    return (
      <View style={styles.subOptions}>
        <Text style={styles.subOptionsTitle}>Select tests:</Text>
        <View style={styles.subOptionsGrid}>
          {options.map((option) => (
            <TouchableOpacity
              key={option}
              style={[
                styles.subOptionChip,
                selectedOptions.includes(option) && styles.subOptionChipSelected,
              ]}
              onPress={() => toggle(option)}
            >
              <Text style={[
                styles.subOptionChipText,
                selectedOptions.includes(option) && styles.subOptionChipTextSelected
              ]}>
                {option}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
    );
  };

  const totalTasks = calculateTotalTasks();

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
            <View style={[styles.progressFill, { width: '64%' }]} />
          </View>
          <Text style={styles.progressText}>Step 9 of 14</Text>
        </View>

        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Choose Your Plan</Text>
          <Text style={styles.subtitle}>
            Select the plans you need. You can always adjust later.
          </Text>
        </View>

        {/* Plan Types */}
        <View style={styles.planList}>
          {PLAN_TYPES.map((plan) => {
            const isSelected = selectedPlans.includes(plan.id);
            return (
              <TouchableOpacity
                key={plan.id}
                style={[
                  styles.planCard,
                  { borderColor: isSelected ? plan.color : '#E5E7EB' },
                  isSelected && { backgroundColor: plan.color + '10' },
                ]}
                onPress={() => togglePlan(plan.id)}
                activeOpacity={0.7}
              >
                <View style={styles.planHeader}>
                  <View style={styles.planHeaderLeft}>
                    <View style={[styles.planIcon, { backgroundColor: plan.color + '20' }]}>
                      <Text style={styles.planIconText}>{plan.icon}</Text>
                    </View>
                    <View style={styles.planHeaderInfo}>
                      <View style={styles.planTitleRow}>
                        <Text style={styles.planName}>{plan.name}</Text>
                        {plan.required && (
                          <View style={styles.requiredBadge}>
                            <Text style={styles.requiredBadgeText}>Required</Text>
                          </View>
                        )}
                      </View>
                      <Text style={styles.planDescription}>{plan.description}</Text>
                    </View>
                  </View>
                  <View style={[styles.checkbox, { borderColor: plan.color }, isSelected && { backgroundColor: plan.color }]}>
                    {isSelected && <Text style={styles.checkmark}>✓</Text>}
                    </View>
                  </View>

                  <View style={styles.planStats}>
                    <View style={styles.planStat}>
                      <Text style={styles.planStatLabel}>Duration</Text>
                      <Text style={styles.planStatValue}>{plan.duration}</Text>
                    </View>
                    <View style={styles.planStat}>
                      <Text style={styles.planStatLabel}>Tasks</Text>
                      <Text style={styles.planStatValue}>
                        {plan.id === 'exams' && selectedExams.length > 0
                          ? Math.round(plan.taskCount * (selectedExams.length / 3))
                          : plan.id === 'language' && selectedLanguageTests.length > 0
                          ? Math.round(plan.taskCount * (selectedLanguageTests.length / 4))
                          : plan.taskCount}
                      </Text>
                    </View>
                  </View>

                  {isSelected && plan.subOptions && renderSubOptions(plan.id, plan.subOptions)}
                </TouchableOpacity>
              );
          })}
        </View>

        {/* Summary Card */}
        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Your Personalized Plan</Text>
          <View style={styles.summaryStats}>
            <View style={styles.summaryStat}>
              <Text style={styles.summaryStatValue}>{totalTasks}</Text>
              <Text style={styles.summaryStatLabel}>Total Tasks</Text>
            </View>
            <View style={styles.summaryDivider} />
            <View style={styles.summaryStat}>
              <Text style={styles.summaryStatValue}>8</Text>
              <Text style={styles.summaryStatLabel}>Months</Text>
            </View>
            <View style={styles.summaryDivider} />
            <View style={styles.summaryStat}>
              <Text style={styles.summaryStatValue}>{selectedPlans.length}</Text>
              <Text style={styles.summaryStatLabel}>Plan Types</Text>
            </View>
          </View>
        </View>

        {/* Info Box */}
        <View style={styles.infoBox}>
          <Text style={styles.infoIcon}>ℹ️</Text>
          <Text style={styles.infoText}>
            Your plan will be personalized based on your target universities and deadlines
          </Text>
        </View>

        {/* Continue Button */}
        <TouchableOpacity
          style={[styles.continueButton, loading && styles.continueButtonDisabled]}
          onPress={handleNext}
          disabled={loading}
        >
          <Text style={styles.continueButtonText}>
            {loading ? 'Loading...' : 'Generate My Plan'}
          </Text>
        </TouchableOpacity>

        {/* Back Button */}
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Text style={styles.backButtonText}>← Back</Text>
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
    backgroundColor: '#6366F1',
  },
  progressText: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 8,
    textAlign: 'center',
  },
  header: {
    marginBottom: 32,
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
    lineHeight: 22,
  },
  planList: {
    gap: 20,
    marginBottom: 24,
  },
  planCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 16,
    padding: 20,
    borderWidth: 2,
  },
  planHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  planHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 16,
    flex: 1,
  },
  planIcon: {
    width: 56,
    height: 56,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  planIconText: {
    fontSize: 28,
  },
  planHeaderInfo: {
    flex: 1,
  },
  planTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  planName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  requiredBadge: {
    backgroundColor: '#DEF7EC',
    borderRadius: 4,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  requiredBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#03543F',
  },
  planDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  checkbox: {
    width: 28,
    height: 28,
    borderRadius: 8,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkmark: {
    fontSize: 16,
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  planStats: {
    flexDirection: 'row',
    gap: 24,
    marginBottom: 16,
  },
  planStat: {
    flex: 1,
  },
  planStatLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 2,
  },
  planStatValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  subOptions: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  subOptionsTitle: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 12,
  },
  subOptionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  subOptionChip: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
  },
  subOptionChipSelected: {
    backgroundColor: '#6366F1',
    borderColor: '#6366F1',
  },
  subOptionChipText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  subOptionChipTextSelected: {
    color: '#FFFFFF',
  },
  summaryCard: {
    backgroundColor: '#EEF2FF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#4338CA',
    marginBottom: 16,
  },
  summaryStats: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
  },
  summaryStat: {
    alignItems: 'center',
  },
  summaryStatValue: {
    fontSize: 28,
    fontWeight: '700',
    color: '#4338CA',
  },
  summaryStatLabel: {
    fontSize: 12,
    color: '#6366F1',
    marginTop: 2,
  },
  summaryDivider: {
    width: 1,
    height: 40,
    backgroundColor: '#C7D2FE',
  },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    gap: 12,
  },
  infoIcon: {
    fontSize: 20,
  },
  infoText: {
    flex: 1,
    fontSize: 14,
    color: '#92400E',
    lineHeight: 20,
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
  backButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  backButtonText: {
    fontSize: 14,
    color: '#6B7280',
  },
});
