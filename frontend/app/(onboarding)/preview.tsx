import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Image,
  Modal,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

interface Task {
  id: string;
  title: string;
  category: string;
  dueDate: string;
  completed: boolean;
}

interface Month {
  month: number;
  name: string;
  tasks: Task[];
  expanded: boolean;
  blurred: boolean;
}

export default function PreviewScreen() {
  const router = useRouter();
  const { t } = useTranslation();

  const [months, setMonths] = useState<Month[]>([
    {
      month: 1,
      name: 'Month 1',
      tasks: [
        { id: '1', title: 'Research target universities', category: 'Research', dueDate: 'Week 1', completed: false },
        { id: '2', title: 'Create application spreadsheet', category: 'Documents', dueDate: 'Week 1', completed: false },
        { id: '3', title: 'Request recommendation letters', category: 'Documents', dueDate: 'Week 2', completed: false },
        { id: '4', title: 'Draft personal statement', category: 'Essays', dueDate: 'Week 3', completed: false },
        { id: '5', title: 'Prepare activity list', category: 'Documents', dueDate: 'Week 4', completed: false },
      ],
      expanded: true,
      blurred: false,
    },
    {
      month: 2,
      name: 'Month 2',
      tasks: [],
      expanded: false,
      blurred: true,
    },
    {
      month: 3,
      name: 'Month 3',
      tasks: [],
      expanded: false,
      blurred: true,
    },
    {
      month: 4,
      name: 'Month 4',
      tasks: [],
      expanded: false,
      blurred: true,
    },
    {
      month: 5,
      name: 'Month 5',
      tasks: [],
      expanded: false,
      blurred: true,
    },
    {
      month: 6,
      name: 'Month 6',
      tasks: [],
      expanded: false,
      blurred: true,
    },
    {
      month: 7,
      name: 'Month 7',
      tasks: [],
      expanded: false,
      blurred: true,
    },
    {
      month: 8,
      name: 'Month 8',
      tasks: [],
      expanded: false,
      blurred: true,
    },
  ]);

  const [showSubscriptionModal, setShowSubscriptionModal] = useState(false);

  const toggleMonth = (monthIndex: number) => {
    if (months[monthIndex].blurred) {
      setShowSubscriptionModal(true);
      return;
    }

    const updatedMonths = [...months];
    updatedMonths[monthIndex].expanded = !updatedMonths[monthIndex].expanded;
    setMonths(updatedMonths);
  };

  const handleSubscribe = () => {
    router.push('/(onboarding)/subscription');
  };

  const handleStartFree = () => {
    // Navigate to home tab in main app
    router.replace('/(main)/home');
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
            <View style={[styles.progressFill, { width: '71%' }]} />
          </View>
          <Text style={styles.progressText}>Step 11 of 14</Text>
        </View>

        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Your Personalized Plan</Text>
          <Text style={styles.subtitle}>
            200+ tasks personalized for your journey
          </Text>
        </View>

        {/* Plan Overview Card */}
        <View style={styles.overviewCard}>
          <View style={styles.overviewHeader}>
            <View style={styles.overviewIcon}>
              <Text style={styles.overviewIconText}>🎯</Text>
            </View>
            <View style={styles.overviewInfo}>
              <Text style={styles.overviewTitle}>Goal: Harvard University</Text>
              <Text style={styles.overviewSubtitle}>Class of 2029 • Early Action</Text>
            </View>
          </View>
          <View style={styles.overviewStats}>
            <View style={styles.overviewStat}>
              <Text style={styles.overviewStatValue}>8</Text>
              <Text style={styles.overviewStatLabel}>Months</Text>
            </View>
            <View style={styles.overviewStat}>
              <Text style={styles.overviewStatValue}>247</Text>
              <Text style={styles.overviewStatLabel}>Tasks</Text>
            </View>
            <View style={styles.overviewStat}>
              <Text style={styles.overviewStatValue}>0%</Text>
              <Text style={styles.overviewStatLabel}>Complete</Text>
            </View>
          </View>
        </View>

        {/* Months List */}
        <View style={styles.monthsList}>
          {months.map((month, index) => (
            <View key={month.month}>
              <TouchableOpacity
                style={[styles.monthCard, month.blurred && styles.monthCardBlurred]}
                onPress={() => toggleMonth(index)}
                activeOpacity={month.blurred ? 1 : 0.7}
              >
                <View style={styles.monthHeader}>
                  <View style={styles.monthHeaderLeft}>
                    <Text style={[styles.monthName, month.blurred && styles.monthNameBlurred]}>
                      {month.name}
                    </Text>
                    {!month.blurred && month.tasks.length > 0 && (
                      <Text style={styles.monthTaskCount}>{month.tasks.length} tasks</Text>
                    )}
                  </View>
                  {month.blurred ? (
                    <View style={styles.lockIcon}>
                      <Text style={styles.lockIconText}>🔒</Text>
                    </View>
                  ) : (
                    <Text style={styles.expandArrow}>{month.expanded ? '▲' : '▼'}</Text>
                  )}
                </View>

                {month.expanded && !month.blurred && month.tasks.length > 0 && (
                  <View style={styles.tasksList}>
                    {month.tasks.map((task) => (
                      <View key={task.id} style={styles.taskItem}>
                        <View style={[styles.taskCheckbox]} />
                        <View style={styles.taskInfo}>
                          <Text style={styles.taskTitle}>{task.title}</Text>
                          <Text style={styles.taskMeta}>{task.category} • {task.dueDate}</Text>
                        </View>
                      </View>
                    ))}
                  </View>
                )}
              </TouchableOpacity>
            </View>
          ))}
        </View>

        {/* Deliverables Preview */}
        <View style={styles.deliverablesCard}>
          <Text style={styles.deliverablesTitle}>By the end of Month 1, you'll have:</Text>
          <View style={styles.deliverablesList}>
            <View style={styles.deliverableItem}>
              <Text style={styles.deliverableCheck}>✓</Text>
              <Text style={styles.deliverableText}>Target universities finalized</Text>
            </View>
            <View style={styles.deliverableItem}>
              <Text style={styles.deliverableCheck}>✓</Text>
              <Text style={styles.deliverableText}>Recommendation letters requested</Text>
            </View>
            <View style={styles.deliverableItem}>
              <Text style={styles.deliverableCheck}>✓</Text>
              <Text style={styles.deliverableText}>Personal statement draft</Text>
            </View>
            <View style={styles.deliverableItem}>
              <Text style={styles.deliverableCheck}>✓</Text>
              <Text style={styles.deliverableText}>Application timeline created</Text>
            </View>
          </View>
        </View>

        {/* Unlock Banner */}
        <TouchableOpacity style={styles.unlockBanner} onPress={handleSubscribe}>
          <View style={styles.unlockBannerLeft}>
            <Text style={styles.unlockBannerTitle}>Unlock Full Plan</Text>
            <Text style={styles.unlockBannerSubtitle}>
              Get access to all 8 months and 247 tasks
            </Text>
          </View>
          <View style={styles.unlockBannerArrow}>
            <Text style={styles.unlockArrowText}>→</Text>
          </View>
        </TouchableOpacity>

        {/* Action Buttons */}
        <TouchableOpacity style={styles.subscribeButton} onPress={handleSubscribe}>
          <Text style={styles.subscribeButtonText}>Subscribe to Unlock Full Plan</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.freeButton} onPress={handleStartFree}>
          <Text style={styles.freeButtonText}>Continue with Free (Month 1 Only)</Text>
        </TouchableOpacity>

        {/* Back Button */}
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>← Back</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Subscription Modal */}
      <Modal
        visible={showSubscriptionModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowSubscriptionModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalIcon}>
              <Text style={styles.modalIconText}>🔒</Text>
            </View>
            <Text style={styles.modalTitle}>Unlock Your Full Plan</Text>
            <Text style={styles.modalSubtitle}>
              Get unlimited access to all 8 months, 247 tasks, AI mentor, and community features
            </Text>

            <View style={styles.modalFeatures}>
              <View style={styles.modalFeature}>
                <Text style={styles.modalFeatureCheck}>✓</Text>
                <Text style={styles.modalFeatureText}>Full 8-month plan</Text>
              </View>
              <View style={styles.modalFeature}>
                <Text style={styles.modalFeatureCheck}>✓</Text>
                <Text style={styles.modalFeatureText}>247 personalized tasks</Text>
              </View>
              <View style={styles.modalFeature}>
                <Text style={styles.modalFeatureCheck}>✓</Text>
                <Text style={styles.modalFeatureText}>AI-powered guidance</Text>
              </View>
              <View style={styles.modalFeature}>
                <Text style={styles.modalFeatureCheck}>✓</Text>
                <Text style={styles.modalFeatureText}>Community support</Text>
              </View>
            </View>

            <TouchableOpacity
              style={styles.modalButton}
              onPress={() => {
                setShowSubscriptionModal(false);
                router.push('/(onboarding)/subscription');
              }}
            >
              <Text style={styles.modalButtonText}>View Subscription Plans</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.modalClose}
              onPress={() => setShowSubscriptionModal(false)}
            >
              <Text style={styles.modalCloseText}>Maybe Later</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
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
  overviewCard: {
    backgroundColor: '#EEF2FF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  overviewHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    marginBottom: 20,
  },
  overviewIcon: {
    width: 56,
    height: 56,
    borderRadius: 14,
    backgroundColor: '#6366F1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  overviewIconText: {
    fontSize: 28,
  },
  overviewInfo: {
    flex: 1,
  },
  overviewTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  overviewSubtitle: {
    fontSize: 14,
    color: '#6366F1',
  },
  overviewStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  overviewStat: {
    alignItems: 'center',
  },
  overviewStatValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#4338CA',
  },
  overviewStatLabel: {
    fontSize: 12,
    color: '#6366F1',
    marginTop: 2,
  },
  monthsList: {
    gap: 12,
    marginBottom: 24,
  },
  monthCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    overflow: 'hidden',
  },
  monthCardBlurred: {
    backgroundColor: '#F3F4F6',
  },
  monthHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
  },
  monthHeaderLeft: {
    flex: 1,
  },
  monthName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  monthNameBlurred: {
    color: '#9CA3AF',
  },
  monthTaskCount: {
    fontSize: 14,
    color: '#6B7280',
  },
  expandArrow: {
    fontSize: 14,
    color: '#6B7280',
  },
  lockIcon: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 8,
  },
  lockIconText: {
    fontSize: 16,
  },
  tasksList: {
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  taskItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  taskCheckbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: '#D1D5DB',
  },
  taskInfo: {
    flex: 1,
  },
  taskTitle: {
    fontSize: 15,
    fontWeight: '500',
    color: '#111827',
    marginBottom: 2,
  },
  taskMeta: {
    fontSize: 13,
    color: '#6B7280',
  },
  deliverablesCard: {
    backgroundColor: '#F0FDF4',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  deliverablesTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#166534',
    marginBottom: 12,
  },
  deliverablesList: {
    gap: 8,
  },
  deliverableItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  deliverableCheck: {
    fontSize: 16,
    color: '#166534',
  },
  deliverableText: {
    flex: 1,
    fontSize: 14,
    color: '#166534',
  },
  unlockBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#6366F1',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  unlockBannerLeft: {
    flex: 1,
  },
  unlockBannerTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  unlockBannerSubtitle: {
    fontSize: 13,
    color: '#E0E7FF',
  },
  unlockBannerArrow: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  unlockArrowText: {
    fontSize: 18,
    color: '#6366F1',
    fontWeight: 'bold',
  },
  subscribeButton: {
    backgroundColor: '#6366F1',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  subscribeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  freeButton: {
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 12,
  },
  freeButtonText: {
    fontSize: 15,
    fontWeight: '500',
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
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 24,
    width: '100%',
  },
  modalIcon: {
    width: 64,
    height: 64,
    borderRadius: 16,
    backgroundColor: '#EEF2FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    alignSelf: 'center',
  },
  modalIconText: {
    fontSize: 32,
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#111827',
    textAlign: 'center',
    marginBottom: 12,
  },
  modalSubtitle: {
    fontSize: 15,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 22,
  },
  modalFeatures: {
    gap: 12,
    marginBottom: 24,
  },
  modalFeature: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  modalFeatureCheck: {
    fontSize: 18,
    color: '#10B981',
  },
  modalFeatureText: {
    fontSize: 15,
    color: '#374151',
  },
  modalButton: {
    backgroundColor: '#6366F1',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  modalButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  modalClose: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  modalCloseText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#6B7280',
  },
});
