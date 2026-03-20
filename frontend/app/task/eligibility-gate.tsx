import { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const COLORS = {
  bg: '#131313',
  surface: '#2A2A2A',
  border: '#3E3E3E',
  text: '#ECECEC',
  textSecondary: '#8E8E8E',
  primary: '#5B6AFF',
  success: '#34C759',
  warning: '#FF9500',
  danger: '#EF4444',
};

// Types
interface EligibilityBlocker {
  type: string;
  title: string;
  description: string;
  current_value: string;
  required_value: string;
  is_blocker: boolean;
  alternative_path: string;
  resolution_tasks: string[];
}

interface UniversityEligibility {
  short_name: string;
  name: string;
  status: 'eligible' | 'partially_eligible' | 'not_eligible';
  can_apply_direct: boolean;
  can_apply_foundation: boolean;
  foundation_available: boolean;
  blockers: EligibilityBlocker[];
  gaps_count: number;
}

interface EligibilityResponse {
  profile_status: string;
  overall_eligibility: string;
  current_strategy: string;
  universities: UniversityEligibility[];
  has_blockers: boolean;
  has_missing_data: boolean;
  needs_strategy_choice: boolean;
}

export default function EligibilityGateScreen() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [checkingEligibility, setCheckingEligibility] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generationStage, setGenerationStage] = useState<string>('');
  const [eligibilityData, setEligibilityData] = useState<EligibilityResponse | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<'direct' | 'foundation' | 'change_shortlist' | ''>('');

  useEffect(() => {
    checkEligibility();
  }, []);

  const getAPIUrl = () => {
    return process.env.EXPO_PUBLIC_API_URL
      ? `${process.env.EXPO_PUBLIC_API_URL}/api`
      : 'http://192.168.0.210:8000/api';
  };

  const getAuthHeaders = async () => {
    const token = await AsyncStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  };

  const checkEligibility = async () => {
    try {
      setCheckingEligibility(true);
      const headers = await getAuthHeaders();
      const response = await axios.get(
        `${getAPIUrl()}/todos/eligibility/check/`,
        { headers }
      );

      if (response.data.status === 'profile_required') {
        Alert.alert(
          'Profile Required',
          'Please complete your university profile first.',
          [
            { text: 'OK', onPress: () => router.push('/university-profile/wizard') }
          ]
        );
        return;
      }

      if (response.data.status === 'no_shortlist') {
        Alert.alert(
          'No Shortlist',
          'Please add universities to your shortlist first.',
          [
            { text: 'OK', onPress: () => router.push('/university-recommender/shortlist') }
          ]
        );
        return;
      }

      setEligibilityData(response.data);

      // Auto-select strategy if no structural blockers
      const hasStructuralBlockers = response.data.universities?.some((uni: any) =>
        uni.blockers?.some((b: any) => b.gap_type === 'education_years')
      );

      if (!hasStructuralBlockers) {
        // No education system mismatch → auto-set direct strategy
        setSelectedStrategy('direct');
      } else if (response.data.current_strategy) {
        // Has blockers but user already chose strategy
        setSelectedStrategy(response.data.current_strategy as any);
      }
      // Else: has structural blockers → require user to choose strategy manually
    } catch (error: any) {
      console.error('Eligibility check failed:', error);
      Alert.alert(
        'Error',
        error.response?.data?.error || 'Failed to check eligibility. Please try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setCheckingEligibility(false);
      setLoading(false);
    }
  };

  const handleGenerateTasks = async () => {
    if (!selectedStrategy) {
      Alert.alert('Strategy Required', 'Please select a path to continue.');
      return;
    }

    try {
      setGenerating(true);
      setGenerationStage('Generating admission plan...');

      const headers = await getAuthHeaders();

      // ✅ Call NEW plan generation endpoint (Requirement Engine)
      const response = await axios.post(
        `${getAPIUrl()}/todos/plan/generate/`,
        {
          track: selectedStrategy,  // ✅ Use 'track' instead of 'strategy'
          intake: '',
          degree_level: '',
          citizenship: '',
        },
        { headers }
      );

      if (response.data.status === 'success') {
        const { tasks_stats, coverage, trace_id, timings_ms, counts } = response.data;
        const { created, updated, deleted } = tasks_stats;

        console.log('Plan generation result:', response.data);

        setGenerationStage(`Created ${created} tasks`);

        // ✅ CRITICAL: Refetch eligibility after generating plan
        // This updates coverage with fresh RequirementInstance data
        try {
          await checkEligibility();
          console.log('Eligibility refetched after plan generation');
        } catch (eligibilityError) {
          console.warn('Failed to refetch eligibility:', eligibilityError);
          // Don't fail - plan was created successfully
        }

        Alert.alert(
          'Plan Generated Successfully!',
          `${created} tasks created, ${updated} updated, ${deleted} removed.\n\nCoverage: ${coverage.verified_percent}% verified (${coverage.assumed_percent}% with assumptions)\n\n⏱️ Timings: ${timings_ms.total}ms`,
          [
            {
              text: 'View My Tasks',
              onPress: () => router.push('/(main)/todos')
            }
          ]
        );
      } else {
        Alert.alert('Error', response.data.error || 'Failed to generate plan.', [{ text: 'OK' }]);
      }
    } catch (error: any) {
      console.error('Plan generation failed:', error);
      Alert.alert(
        'Error',
        error.response?.data?.error || 'Failed to generate plan. Please try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setGenerating(false);
      setGenerationStage('');
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Checking eligibility...</Text>
      </View>
    );
  }

  if (!eligibilityData) {
    return (
      <View style={styles.centerContainer}>
        <MaterialCommunityIcons name="alert-circle" size={48} color={COLORS.danger} />
        <Text style={styles.errorText}>Failed to load eligibility data</Text>
        <TouchableOpacity style={styles.retryButton} onPress={checkEligibility}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const { universities, has_blockers, needs_strategy_choice } = eligibilityData;

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Eligibility Check</Text>
        <Text style={styles.headerSubtitle}>
          {has_blockers
            ? 'Some gaps need to be addressed before applying'
            : 'Great! You can start your application tasks'}
        </Text>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Overall Status Banner */}
        <View style={[
          styles.statusBanner,
          has_blockers ? styles.statusBannerWarning : styles.statusBannerSuccess
        ]}>
          <MaterialCommunityIcons
            name={has_blockers ? 'alert' : 'check-circle'}
            size={24}
            color={has_blockers ? COLORS.warning : COLORS.success}
          />
          <View style={styles.statusBannerContent}>
            <Text style={[
              styles.statusBannerTitle,
              has_blockers ? styles.textWarning : styles.textSuccess
            ]}>
              {has_blockers ? 'Action Required' : 'Ready to Apply'}
            </Text>
            <Text style={styles.statusBannerText}>
              {has_blockers
                ? 'Some requirements need attention before you can apply'
                : 'You meet the basic requirements for your shortlisted universities'}
            </Text>
          </View>
        </View>

        {/* Strategy Selection (if needed) */}
        {needs_strategy_choice && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Choose Your Path</Text>
            <Text style={styles.sectionDescription}>
              Your education system doesn't match some universities. How would you like to proceed?
            </Text>

            <TouchableOpacity
              style={[
                styles.strategyCard,
                selectedStrategy === 'direct' && styles.strategyCardSelected
              ]}
              onPress={() => setSelectedStrategy('direct')}
            >
              <View style={styles.strategyCardHeader}>
                <MaterialCommunityIcons
                  name="school"
                  size={24}
                  color={selectedStrategy === 'direct' ? COLORS.primary : COLORS.textSecondary}
                />
                <View style={styles.strategyCardHeaderContent}>
                  <Text style={[
                    styles.strategyTitle,
                    selectedStrategy === 'direct' && styles.textPrimary
                  ]}>
                    Direct Application
                  </Text>
                  <Text style={styles.strategyDescription}>
                    Apply only to universities accepting my education system
                  </Text>
                </View>
                <MaterialCommunityIcons
                  name={selectedStrategy === 'direct' ? 'radiobox-marked' : 'radiobox-blank'}
                  size={24}
                  color={selectedStrategy === 'direct' ? COLORS.primary : COLORS.textSecondary}
                />
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.strategyCard,
                selectedStrategy === 'foundation' && styles.strategyCardSelected
              ]}
              onPress={() => setSelectedStrategy('foundation')}
            >
              <View style={styles.strategyCardHeader}>
                <MaterialCommunityIcons
                  name="layers-plus"
                  size={24}
                  color={selectedStrategy === 'foundation' ? COLORS.primary : COLORS.textSecondary}
                />
                <View style={styles.strategyCardHeaderContent}>
                  <Text style={[
                    styles.strategyTitle,
                    selectedStrategy === 'foundation' && styles.textPrimary
                  ]}>
                    Foundation Year
                  </Text>
                  <Text style={styles.strategyDescription}>
                    Take a foundation year to meet education requirements
                  </Text>
                </View>
                <MaterialCommunityIcons
                  name={selectedStrategy === 'foundation' ? 'radiobox-marked' : 'radiobox-blank'}
                  size={24}
                  color={selectedStrategy === 'foundation' ? COLORS.primary : COLORS.textSecondary}
                />
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.strategyCard,
                selectedStrategy === 'change_shortlist' && styles.strategyCardSelected
              ]}
              onPress={() => setSelectedStrategy('change_shortlist')}
            >
              <View style={styles.strategyCardHeader}>
                <MaterialCommunityIcons
                  name="pencil"
                  size={24}
                  color={selectedStrategy === 'change_shortlist' ? COLORS.primary : COLORS.textSecondary}
                />
                <View style={styles.strategyCardHeaderContent}>
                  <Text style={[
                    styles.strategyTitle,
                    selectedStrategy === 'change_shortlist' && styles.textPrimary
                  ]}>
                    Modify Shortlist
                  </Text>
                  <Text style={styles.strategyDescription}>
                    Remove incompatible universities and add others
                  </Text>
                </View>
                <MaterialCommunityIcons
                  name={selectedStrategy === 'change_shortlist' ? 'radiobox-marked' : 'radiobox-blank'}
                  size={24}
                  color={selectedStrategy === 'change_shortlist' ? COLORS.primary : COLORS.textSecondary}
                />
              </View>
            </TouchableOpacity>
          </View>
        )}

        {/* University List with Blockers */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>University Eligibility</Text>

          {universities.map((uni) => (
            <View key={uni.short_name} style={styles.uniCard}>
              <View style={styles.uniCardHeader}>
                <Text style={styles.uniName}>{uni.name}</Text>
                <View style={[
                  styles.statusBadge,
                  uni.status === 'eligible' ? styles.statusBadgeSuccess :
                  uni.status === 'partially_eligible' ? styles.statusBadgeWarning :
                  styles.statusBadgeDanger
                ]}>
                  <MaterialCommunityIcons
                    name={uni.status === 'eligible' ? 'check' : uni.status === 'partially_eligible' ? 'alert' : 'close'}
                    size={16}
                    color={uni.status === 'eligible' ? COLORS.success : uni.status === 'partially_eligible' ? COLORS.warning : COLORS.danger}
                  />
                  <Text style={[
                    styles.statusText,
                    uni.status === 'eligible' ? styles.textSuccess :
                    uni.status === 'partially_eligible' ? styles.textWarning :
                    styles.textDanger
                  ]}>
                    {uni.status === 'eligible' ? 'Eligible' :
                     uni.status === 'partially_eligible' ? 'Partial' : 'Not Eligible'}
                  </Text>
                </View>
              </View>

              {/* Blockers */}
              {uni.blockers.length > 0 && (
                <View style={styles.blockersContainer}>
                  <Text style={styles.blockersTitle}>Requirements to Address:</Text>
                  {uni.blockers.map((blocker, index) => (
                    <View key={index} style={styles.blockerItem}>
                      <MaterialCommunityIcons name="alert-circle" size={20} color={COLORS.warning} />
                      <View style={styles.blockerContent}>
                        <Text style={styles.blockerTitle}>{blocker.title}</Text>
                        <Text style={styles.blockerDescription}>{blocker.description}</Text>
                        {blocker.alternative_path ? (
                          <Text style={styles.alternativeText}>
                            💡 Alternative: {blocker.alternative_path}
                          </Text>
                        ) : null}
                      </View>
                    </View>
                  ))}
                </View>
              )}

              {/* Foundation Available Badge */}
              {uni.foundation_available && uni.status !== 'eligible' && (
                <View style={styles.foundationBadge}>
                  <MaterialCommunityIcons name="information" size={16} color={COLORS.primary} />
                  <Text style={styles.foundationText}>Foundation program available</Text>
                </View>
              )}
            </View>
          ))}
        </View>

        <View style={styles.bottomSpacer} />
      </ScrollView>

      {/* Generate Button */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={[
            styles.generateButton,
            (!selectedStrategy || generating) && styles.generateButtonDisabled
          ]}
          onPress={handleGenerateTasks}
          disabled={!selectedStrategy || generating}
        >
          {generating ? (
            <ActivityIndicator color={COLORS.bg} />
          ) : (
            <>
              <MaterialCommunityIcons name="rocket-launch" size={20} color={COLORS.bg} />
              <Text style={styles.generateButtonText}>
                {has_blockers ? 'Generate Gap Tasks' : 'Generate Application Tasks'}
              </Text>
            </>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  centerContainer: {
    flex: 1,
    backgroundColor: COLORS.bg,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    color: COLORS.textSecondary,
    marginTop: 16,
    fontSize: 16,
  },
  errorText: {
    color: COLORS.danger,
    marginTop: 16,
    fontSize: 16,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 20,
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
  },
  retryButtonText: {
    color: COLORS.bg,
    fontWeight: '600',
  },
  header: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  content: {
    flex: 1,
  },
  statusBanner: {
    margin: 16,
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusBannerWarning: {
    backgroundColor: 'rgba(255, 149, 0, 0.1)',
    borderWidth: 1,
    borderColor: COLORS.warning,
  },
  statusBannerSuccess: {
    backgroundColor: 'rgba(52, 199, 89, 0.1)',
    borderWidth: 1,
    borderColor: COLORS.success,
  },
  statusBannerContent: {
    flex: 1,
    marginLeft: 12,
  },
  statusBannerTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  statusBannerText: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  textWarning: { color: COLORS.warning },
  textSuccess: { color: COLORS.success },
  textDanger: { color: COLORS.danger },
  textPrimary: { color: COLORS.primary },
  section: {
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 8,
  },
  sectionDescription: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginBottom: 16,
  },
  strategyCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  strategyCardSelected: {
    borderColor: COLORS.primary,
  },
  strategyCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  strategyCardHeaderContent: {
    flex: 1,
    marginLeft: 12,
  },
  strategyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 4,
  },
  strategyDescription: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  uniCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  uniCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  uniName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    flex: 1,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  statusBadgeSuccess: {
    backgroundColor: 'rgba(52, 199, 89, 0.2)',
  },
  statusBadgeWarning: {
    backgroundColor: 'rgba(255, 149, 0, 0.2)',
  },
  statusBadgeDanger: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  blockersContainer: {
    marginTop: 8,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  blockersTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.warning,
    marginBottom: 8,
  },
  blockerItem: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  blockerContent: {
    flex: 1,
    marginLeft: 8,
  },
  blockerTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 2,
  },
  blockerDescription: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginBottom: 4,
  },
  alternativeText: {
    fontSize: 12,
    color: COLORS.primary,
  },
  foundationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(91, 106, 255, 0.1)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    marginTop: 8,
    alignSelf: 'flex-start',
  },
  foundationText: {
    fontSize: 12,
    color: COLORS.primary,
    marginLeft: 6,
  },
  bottomSpacer: {
    height: 100,
  },
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: COLORS.bg,
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  generateButton: {
    backgroundColor: COLORS.primary,
    paddingVertical: 16,
    borderRadius: 12,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  generateButtonDisabled: {
    opacity: 0.5,
  },
  generateButtonText: {
    color: COLORS.bg,
    fontSize: 16,
    fontWeight: '600',
  },
});
