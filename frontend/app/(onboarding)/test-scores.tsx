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

interface TestScore {
  status: 'not_taken' | 'taken' | 'planning';
  score?: string;
  testDate?: string;
  mathScore?: string;
  readingScore?: string;
}

interface TestScores {
  sat: TestScore;
  act: TestScore;
  ielts: TestScore;
  toefl: TestScore;
  hsk: TestScore;
}

export default function TestScoresScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const { onboardingData, updateOnboardingData } = useOnboarding();

  const [testScores, setTestScores] = useState<TestScores>({
    sat: onboardingData.sat_score || { status: 'not_taken' },
    act: onboardingData.act_score || { status: 'not_taken' },
    ielts: onboardingData.ielts_score || { status: 'not_taken' },
    toefl: onboardingData.toefl_score || { status: 'not_taken' },
    hsk: onboardingData.hsk_score || { status: 'not_taken' },
  });

  const [expandedTest, setExpandedTest] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const updateTest = (testName: keyof TestScores, updates: Partial<TestScore>) => {
    setTestScores({
      ...testScores,
      [testName]: { ...testScores[testName], ...updates },
    });
  };

  const handleNext = async () => {
    try {
      setLoading(true);

      // Save onboarding data
      updateOnboardingData({
        sat_score: testScores.sat,
        act_score: testScores.act,
        ielts_score: testScores.ielts,
        toefl_score: testScores.toefl,
        hsk_score: testScores.hsk,
      });

      router.push('/(onboarding)/extracurriculars');
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to save test scores');
    } finally {
      setLoading(false);
    }
  };

  const renderTestCard = (testKey: keyof TestScores, testName: string, testLabel: string) => {
    const test = testScores[testKey];
    const isExpanded = expandedTest === testKey;

    return (
      <View key={testKey} style={styles.testCard}>
        <TouchableOpacity
          style={styles.testCardHeader}
          onPress={() => setExpandedTest(isExpanded ? null : testKey)}
        >
          <View style={styles.testCardInfo}>
            <Text style={styles.testName}>{testName}</Text>
            <Text style={styles.testStatus}>
              {test.status === 'taken' && '✓ Score Added'}
              {test.status === 'planning' && '📅 Planning to Take'}
              {test.status === 'not_taken' && 'Not Taken'}
            </Text>
          </View>
          <Text style={styles.expandArrow}>{isExpanded ? '▲' : '▼'}</Text>
        </TouchableOpacity>

        {isExpanded && (
          <View style={styles.testCardBody}>
            {/* Status Selection */}
            <View style={styles.statusButtons}>
              <TouchableOpacity
                style={[styles.statusButton, test.status === 'not_taken' && styles.statusButtonActive]}
                onPress={() => updateTest(testKey, { status: 'not_taken', score: undefined, testDate: undefined })}
              >
                <Text style={[styles.statusButtonText, test.status === 'not_taken' && styles.statusButtonTextActive]}>
                  Not Taken
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.statusButton, test.status === 'taken' && styles.statusButtonActive]}
                onPress={() => updateTest(testKey, { status: 'taken' })}
              >
                <Text style={[styles.statusButtonText, test.status === 'taken' && styles.statusButtonTextActive]}>
                  Taken
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.statusButton, test.status === 'planning' && styles.statusButtonActive]}
                onPress={() => updateTest(testKey, { status: 'planning' })}
              >
                <Text style={[styles.statusButtonText, test.status === 'planning' && styles.statusButtonTextActive]}>
                  Planning
                </Text>
              </TouchableOpacity>
            </View>

            {test.status !== 'not_taken' && (
              <>
                {/* Score Input */}
                <View style={styles.inputGroup}>
                  <Text style={styles.label}>
                    {testKey === 'sat' ? 'Total Score (400-1600)' :
                     testKey === 'act' ? 'Composite Score (1-36)' :
                     testKey === 'ielts' ? 'Overall Band (0-9)' :
                     testKey === 'toefl' ? 'Total Score (0-120)' :
                     'HSK Level (1-6)'}
                  </Text>
                  <TextInput
                    style={styles.input}
                    placeholder="Enter your score"
                    value={test.score || ''}
                    onChangeText={(text) => updateTest(testKey, { score: text })}
                    keyboardType="number-pad"
                  />
                </View>

                {/* SAT Section Scores */}
                {testKey === 'sat' && test.status === 'taken' && (
                  <View style={styles.row}>
                    <View style={[styles.inputGroup, styles.half]}>
                      <Text style={styles.label}>Math (200-800)</Text>
                      <TextInput
                        style={styles.input}
                        placeholder="Math"
                        value={test.mathScore || ''}
                        onChangeText={(text) => updateTest(testKey, { mathScore: text })}
                        keyboardType="number-pad"
                      />
                    </View>
                    <View style={[styles.inputGroup, styles.half]}>
                      <Text style={styles.label}>Reading/Writing (200-800)</Text>
                      <TextInput
                        style={styles.input}
                        placeholder="R/W"
                        value={test.readingScore || ''}
                        onChangeText={(text) => updateTest(testKey, { readingScore: text })}
                        keyboardType="number-pad"
                      />
                    </View>
                  </View>
                )}

                {/* Test Date */}
                <View style={styles.inputGroup}>
                  <Text style={styles.label}>Test Date (Optional)</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="YYYY-MM-DD"
                    value={test.testDate || ''}
                    onChangeText={(text) => updateTest(testKey, { testDate: text })}
                    keyboardType="numbers-and-punctuation"
                    maxLength={10}
                  />
                </View>
              </>
            )}
          </View>
        )}
      </View>
    );
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
              <View style={[styles.progressFill, { width: '42%' }]} />
            </View>
            <Text style={styles.progressText}>Step 6 of 14</Text>
          </View>

          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Test Scores</Text>
            <Text style={styles.subtitle}>
              Add any standardized test scores (Optional - can add later)
            </Text>
          </View>

          {/* Test Cards */}
          <View style={styles.testList}>
            {renderTestCard('sat', 'SAT', 'SAT Score')}
            {renderTestCard('act', 'ACT', 'ACT Score')}
            {renderTestCard('ielts', 'IELTS', 'IELTS Score')}
            {renderTestCard('toefl', 'TOEFL', 'TOEFL Score')}
            {renderTestCard('hsk', 'HSK', 'HSK Score')}
          </View>

          {/* Info Box */}
          <View style={styles.infoBox}>
            <Text style={styles.infoIcon}>ℹ️</Text>
            <Text style={styles.infoText}>
              You can add or update test scores later in your profile
            </Text>
          </View>

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
            onPress={() => router.push('/(onboarding)/extracurriculars')}
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
  testList: {
    gap: 16,
    marginBottom: 24,
  },
  testCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    overflow: 'hidden',
  },
  testCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
  },
  testCardInfo: {
    flex: 1,
  },
  testName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  testStatus: {
    fontSize: 14,
    color: '#6B7280',
  },
  expandArrow: {
    fontSize: 16,
    color: '#6B7280',
  },
  testCardBody: {
    paddingTop: 16,
    paddingHorizontal: 16,
    paddingBottom: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    gap: 16,
  },
  statusButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  statusButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    alignItems: 'center',
  },
  statusButtonActive: {
    backgroundColor: '#EEF2FF',
    borderColor: '#6366F1',
  },
  statusButtonText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#6B7280',
  },
  statusButtonTextActive: {
    color: '#6366F1',
    fontWeight: '600',
  },
  row: {
    flexDirection: 'row',
    gap: 12,
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
  },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#EEF2FF',
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
    color: '#4338CA',
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
