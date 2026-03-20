import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useEffect } from 'react';

const COLORS = {
  bg: '#1A1A1A',
  surface: '#2A2A2A',
  border: '#3E3E3E',
  text: '#ECECEC',
  textSecondary: '#8E8E8E',
  primary: '#5B6AFF',
  success: '#10A37F',
  warning: '#FF9500',
};

export default function DemoScreen() {
  const router = useRouter();

  // Redirect logged-in users to home
  useEffect(() => {
    const checkAuthStatus = async () => {
      const guestMode = await AsyncStorage.getItem('isGuest');
      if (guestMode !== 'true') {
        router.replace('/(main)/home');
      }
    };
    checkAuthStatus();
  }, []);

  // Demo data - example goal and tasks
  const demoGoal = "Get accepted into Stanford Computer Science";
  const demoMilestones = [
    {
      title: "Research programs & requirements",
      weeks: "Weeks 1-2",
      tasks: 5,
      icon: "magnify"
    },
    {
      title: "Prepare application materials",
      weeks: "Weeks 3-6",
      tasks: 12,
      icon: "file-document-edit"
    },
    {
      title: "Get recommendation letters",
      weeks: "Weeks 7-8",
      tasks: 4,
      icon: "account-group"
    },
    {
      title: "Submit & prepare for interview",
      weeks: "Weeks 9-12",
      tasks: 8,
      icon: "send"
    },
  ];

  const demoTasks = [
    {
      title: "Visit MIT EECS website and note 3 research areas that interest you",
      duration: "30 min",
      difficulty: "Easy",
    },
    {
      title: "Email Professor Smith about AI research opportunities",
      duration: "20 min",
      difficulty: "Medium",
    },
    {
      title: "Draft personal statement introduction (100 words)",
      duration: "45 min",
      difficulty: "Hard",
    },
  ];

  const handleCreateAccount = async () => {
    // Clear guest mode
    await AsyncStorage.removeItem('isGuest');
    router.replace('/(auth)/register');
  };

  return (
    <ScrollView style={styles.container}>
      {/* Demo Banner */}
      <View style={styles.demoBanner}>
        <MaterialCommunityIcons name="eye-outline" size={20} color={COLORS.warning} />
        <Text style={styles.demoBannerText}>
          Preview Mode - Create account to build YOUR personalized plan
        </Text>
      </View>

      {/* Content */}
      <View style={styles.content}>
        {/* Example Goal Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <MaterialCommunityIcons name="target" size={24} color={COLORS.success} />
            <Text style={styles.sectionTitle}>Example Goal</Text>
          </View>

          <View style={styles.goalCard}>
            <LinearGradient
              colors={['rgba(16, 163, 127, 0.2)', 'rgba(16, 163, 127, 0.05)']}
              style={styles.goalGradient}
            >
              <Text style={styles.goalText}>{demoGoal}</Text>
              <View style={styles.goalStats}>
                <View style={styles.statBadge}>
                  <MaterialCommunityIcons name="calendar-clock" size={16} color={COLORS.textSecondary} />
                  <Text style={styles.statText}>12 weeks</Text>
                </View>
                <View style={styles.statBadge}>
                  <MaterialCommunityIcons name="format-list-checks" size={16} color={COLORS.textSecondary} />
                  <Text style={styles.statText}>29 tasks</Text>
                </View>
              </View>
            </LinearGradient>
          </View>
        </View>

        {/* AI-Generated Roadmap */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <MaterialCommunityIcons name="robot" size={24} color={COLORS.primary} />
            <Text style={styles.sectionTitle}>AI-Generated Roadmap</Text>
          </View>

          {demoMilestones.map((milestone, idx) => (
            <View key={idx} style={styles.milestoneCard}>
              <View style={styles.milestoneIconContainer}>
                <MaterialCommunityIcons
                  name={milestone.icon as any}
                  size={24}
                  color={COLORS.primary}
                />
              </View>
              <View style={styles.milestoneContent}>
                <Text style={styles.milestoneTitle}>
                  Milestone {idx + 1}: {milestone.title}
                </Text>
                <View style={styles.milestoneFooter}>
                  <Text style={styles.milestoneWeeks}>{milestone.weeks}</Text>
                  <Text style={styles.milestoneTasks}>{milestone.tasks} tasks</Text>
                </View>
              </View>
              <MaterialCommunityIcons name="chevron-right" size={20} color={COLORS.textSecondary} />
            </View>
          ))}
        </View>

        {/* Example Atomic Tasks */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <MaterialCommunityIcons name="flash" size={24} color={COLORS.warning} />
            <Text style={styles.sectionTitle}>Example Atomic Tasks</Text>
          </View>
          <Text style={styles.sectionSubtitle}>
            Small, actionable steps you can complete today
          </Text>

          {demoTasks.map((task, idx) => (
            <View key={idx} style={styles.taskCard}>
              <View style={styles.taskCheckbox}>
                <MaterialCommunityIcons
                  name="checkbox-blank-circle-outline"
                  size={24}
                  color={COLORS.textSecondary}
                />
              </View>
              <View style={styles.taskContent}>
                <Text style={styles.taskTitle}>{task.title}</Text>
                <View style={styles.taskMeta}>
                  <View style={styles.taskMetaItem}>
                    <MaterialCommunityIcons name="clock-outline" size={14} color={COLORS.textSecondary} />
                    <Text style={styles.taskMetaText}>{task.duration}</Text>
                  </View>
                  <View style={[
                    styles.difficultyBadge,
                    task.difficulty === 'Easy' && styles.difficultyEasy,
                    task.difficulty === 'Medium' && styles.difficultyMedium,
                    task.difficulty === 'Hard' && styles.difficultyHard,
                  ]}>
                    <Text style={styles.difficultyText}>{task.difficulty}</Text>
                  </View>
                </View>
              </View>
            </View>
          ))}
        </View>

        {/* Call to Action */}
        <View style={styles.ctaContainer}>
          <LinearGradient
            colors={['rgba(91, 106, 255, 0.2)', 'rgba(16, 163, 127, 0.2)']}
            style={styles.ctaGradient}
          >
            <MaterialCommunityIcons name="rocket-launch" size={32} color={COLORS.primary} />
            <Text style={styles.ctaTitle}>Ready to build YOUR personalized plan?</Text>
            <Text style={styles.ctaSubtitle}>
              Tell us your goal and get 30+ specific, actionable tasks in just 3 minutes
            </Text>

            <TouchableOpacity
              style={styles.ctaButton}
              onPress={handleCreateAccount}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#5B6AFF', '#10A37F']}
                style={styles.ctaButtonGradient}
              >
                <Text style={styles.ctaButtonText}>Create My Plan</Text>
                <MaterialCommunityIcons name="arrow-right" size={24} color="#fff" />
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.loginLink}
              onPress={() => router.replace('/(auth)/login')}
            >
              <Text style={styles.loginLinkText}>Already have an account? Log in</Text>
            </TouchableOpacity>
          </LinearGradient>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  demoBanner: {
    backgroundColor: 'rgba(255, 149, 0, 0.15)',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 149, 0, 0.3)',
    paddingVertical: 12,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  demoBannerText: {
    flex: 1,
    color: COLORS.warning,
    fontSize: 13,
    fontWeight: '600',
  },
  content: {
    padding: 16,
  },
  section: {
    marginBottom: 32,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginBottom: 16,
  },
  goalCard: {
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(16, 163, 127, 0.3)',
  },
  goalGradient: {
    padding: 20,
  },
  goalText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.success,
    marginBottom: 12,
  },
  goalStats: {
    flexDirection: 'row',
    gap: 12,
  },
  statBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  statText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    fontWeight: '500',
  },
  milestoneCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    gap: 12,
  },
  milestoneIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(91, 106, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  milestoneContent: {
    flex: 1,
  },
  milestoneTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 6,
  },
  milestoneFooter: {
    flexDirection: 'row',
    gap: 12,
  },
  milestoneWeeks: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  milestoneTasks: {
    fontSize: 13,
    color: COLORS.primary,
    fontWeight: '500',
  },
  taskCard: {
    flexDirection: 'row',
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    gap: 12,
  },
  taskCheckbox: {
    paddingTop: 2,
  },
  taskContent: {
    flex: 1,
  },
  taskTitle: {
    fontSize: 15,
    color: COLORS.text,
    marginBottom: 8,
    lineHeight: 20,
  },
  taskMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  taskMetaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  taskMetaText: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  difficultyBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  difficultyEasy: {
    backgroundColor: 'rgba(16, 163, 127, 0.2)',
  },
  difficultyMedium: {
    backgroundColor: 'rgba(255, 149, 0, 0.2)',
  },
  difficultyHard: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
  },
  difficultyText: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.text,
  },
  ctaContainer: {
    marginTop: 16,
    marginBottom: 32,
  },
  ctaGradient: {
    borderRadius: 20,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(91, 106, 255, 0.3)',
  },
  ctaTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: COLORS.text,
    textAlign: 'center',
    marginTop: 16,
    marginBottom: 8,
  },
  ctaSubtitle: {
    fontSize: 15,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 22,
  },
  ctaButton: {
    width: '100%',
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 16,
  },
  ctaButtonGradient: {
    paddingVertical: 16,
    paddingHorizontal: 24,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  ctaButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  loginLink: {
    paddingVertical: 8,
  },
  loginLinkText: {
    color: COLORS.primary,
    fontSize: 15,
    fontWeight: '500',
  },
});
