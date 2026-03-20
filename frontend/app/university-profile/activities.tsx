/**
 * Extracurricular Activities Management Screen
 *
 * Allows users to:
 * - View all extracurricular activities
 * - Add new activities
 * - Edit existing activities
 * - Delete activities
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
  Modal,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { universityProfileAPI } from '@/services/universityRecommenderApi';
import { colors, spacing } from '@/theme';

interface ExtracurricularActivity {
  id: number;
  category: string;
  title: string;
  role: string;
  hours_per_week: number;
  weeks_per_year: number;
  years_participated: number;
  impact_level: string;
  leadership_position: boolean;
  achievements: string;
  achievements_impact: string;
}

type FormMode = 'add' | 'edit';

const CATEGORIES = [
  'leadership',
  'research',
  'volunteering',
  'sports',
  'arts',
  'work',
];

const IMPACT_LEVELS = [
  'low',
  'medium',
  'high',
  'national',
  'international',
];

const ACHIEVEMENTS_IMPACT = [
  'school',
  'state',
  'national',
  'international',
];

export default function ExtracurricularActivities() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [hasProfile, setHasProfile] = useState(true);
  const [activities, setActivities] = useState<ExtracurricularActivity[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [formMode, setFormMode] = useState<FormMode>('add');
  const [editingActivity, setEditingActivity] = useState<ExtracurricularActivity | null>(null);

  // Form state
  const [category, setCategory] = useState('');
  const [title, setTitle] = useState('');
  const [role, setRole] = useState('');
  const [hoursPerWeek, setHoursPerWeek] = useState('');
  const [weeksPerYear, setWeeksPerYear] = useState('');
  const [yearsParticipated, setYearsParticipated] = useState('');
  const [impactLevel, setImpactLevel] = useState('medium');
  const [leadershipPosition, setLeadershipPosition] = useState(false);
  const [achievements, setAchievements] = useState('');
  const [achievementsImpact, setAchievementsImpact] = useState('school');

  useEffect(() => {
    loadActivities();
  }, []);

  const loadActivities = async () => {
    try {
      setLoading(true);
      const response = await universityProfileAPI.getExtracurriculars();
      // API returns paginated data with results array
      const activitiesData = response.data.results || response.data || [];

      // Only set hasProfile to true if we successfully got data (not 404)
      // A 200 OK with empty array means profile exists but has no activities
      // A 404 means no profile exists
      if (response.status === 200 || response.status === 201) {
        setHasProfile(true);
        setActivities(activitiesData);
      }
    } catch (error: any) {
      console.error('Failed to load activities:', error);

      // Set activities to empty array on any error
      setActivities([]);

      // Check if error is due to missing profile
      const errorDataStr = JSON.stringify(error.response?.data || {});
      if (error.response?.status === 404 ||
          errorDataStr.includes('No profile found') ||
          errorDataStr.includes('No university profile') ||
          errorDataStr.includes('create a profile first')) {
        setHasProfile(false);
      } else {
        // For other errors, be conservative and assume no profile
        // User will see "Create Profile First" screen
        setHasProfile(false);
      }
    } finally {
      setLoading(false);
    }
  };

  const openAddModal = () => {
    if (!hasProfile) {
      Alert.alert(
        'Profile Required',
        'Please create your university profile first before adding activities.',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Create Profile',
            onPress: () => router.push('/university-profile/wizard'),
          },
        ]
      );
      return;
    }
    setFormMode('add');
    resetForm();
    setModalVisible(true);
  };

  const openEditModal = (activity: ExtracurricularActivity) => {
    setFormMode('edit');
    setEditingActivity(activity);
    setCategory(activity.category);
    setTitle(activity.title);
    setRole(activity.role);
    setHoursPerWeek(activity.hours_per_week.toString());
    setWeeksPerYear(activity.weeks_per_year.toString());
    setYearsParticipated(activity.years_participated.toString());
    setImpactLevel(activity.impact_level);
    setLeadershipPosition(activity.leadership_position);
    setAchievements(activity.achievements || '');
    setAchievementsImpact(activity.achievements_impact || 'school');
    setModalVisible(true);
  };

  const resetForm = () => {
    setCategory('');
    setTitle('');
    setRole('');
    setHoursPerWeek('');
    setWeeksPerYear('');
    setYearsParticipated('');
    setImpactLevel('medium');
    setLeadershipPosition(false);
    setAchievements('');
    setAchievementsImpact('school');
    setEditingActivity(null);
  };

  const handleSubmit = async () => {
    // Validation
    if (!category || !title || !role) {
      Alert.alert('Required Fields', 'Please fill in Category, Title, and Role');
      return;
    }

    if (!hoursPerWeek || !weeksPerYear || !yearsParticipated) {
      Alert.alert('Required Fields', 'Please fill in Time Commitment (hours/week, weeks/year, years)');
      return;
    }

    const data = {
      category,
      title,
      role,
      hours_per_week: parseInt(hoursPerWeek) || 0,
      weeks_per_year: parseInt(weeksPerYear) || 0,
      years_participated: parseInt(yearsParticipated) || 0,
      impact_level: impactLevel,
      leadership_position: leadershipPosition,
      achievements: achievements,
      achievements_impact: achievementsImpact,
    };

    try {
      if (formMode === 'add') {
        await universityProfileAPI.addExtracurricular(data);
      } else if (editingActivity) {
        await universityProfileAPI.updateExtracurricular(editingActivity.id, data);
      }

      await loadActivities();
      setModalVisible(false);
      resetForm();
      Alert.alert('Success', formMode === 'add' ? 'Activity added!' : 'Activity updated!');
    } catch (error: any) {
      console.error('❌ Failed to save activity:', error);
      console.error('❌ Error response:', error.response?.data);
      console.error('❌ Error status:', error.response?.status);
      console.error('❌ Data being sent:', JSON.stringify(data, null, 2));

      // Check if error is due to missing profile
      const errorDataStr = JSON.stringify(error.response?.data || {});
      if (error.response?.status === 404 ||
          errorDataStr.includes('No profile found') ||
          errorDataStr.includes('No university profile') ||
          errorDataStr.includes('create a profile first')) {
        // Update state to reflect that there's no profile
        setHasProfile(false);
        setModalVisible(false);
        Alert.alert(
          'Profile Required',
          'Please create your university profile first before adding activities.',
          [
            { text: 'Cancel', style: 'cancel' },
            {
              text: 'Create Profile',
              onPress: () => router.push('/university-profile/wizard'),
            },
          ]
        );
      } else if (error.response?.data) {
        // Show detailed error from backend
        const errorData = error.response.data;
        let errorMessage = 'Failed to save activity.';
        let errorTitle = 'Error';

        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.error) {
          errorMessage = errorData.error;
        } else if (typeof errorData === 'object') {
          // Handle Django REST Framework validation errors
          const errors = Object.entries(errorData)
            .filter(([key]) => key !== 'detail' && key !== 'error')
            .map(([key, value]) => {
              const fieldName = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
              const errorMsg = Array.isArray(value) ? value.join(', ') : value;
              return `${fieldName}: ${errorMsg}`;
            });

          if (errors.length > 0) {
            errorMessage = errors.join('\n');
            errorTitle = 'Validation Errors';
          }
        }

        Alert.alert(errorTitle, errorMessage);
      } else {
        Alert.alert('Error', 'Failed to save activity. Please try again.');
      }
    }
  };

  const handleDelete = (activity: ExtracurricularActivity) => {
    Alert.alert(
      'Delete Activity',
      `Are you sure you want to delete "${activity.title}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await universityProfileAPI.deleteExtracurricular(activity.id);
              await loadActivities();
            } catch (error: any) {
              console.error('Failed to delete activity:', error);
              Alert.alert('Error', 'Failed to delete activity. Please try again.');
            }
          },
        },
      ]
    );
  };

  const renderActivityCard = (activity: ExtracurricularActivity) => (
    <View key={activity.id} style={styles.card}>
      <View style={styles.cardHeader}>
        <View style={styles.cardHeaderLeft}>
          <View style={[styles.categoryBadge, { backgroundColor: getCategoryColor(activity.category) }]}>
            <Text style={styles.categoryText}>{getCategoryLabel(activity.category)}</Text>
          </View>
          <Text style={styles.activityTitle}>{activity.title}</Text>
          <Text style={styles.activityRole}>{activity.role}</Text>
        </View>
        {activity.leadership_position && (
          <Ionicons name="ribbon" size={24} color={colors.warning} />
        )}
      </View>

      <View style={styles.cardBody}>
        <View style={styles.statRow}>
          <Ionicons name="time" size={16} color={colors.textSecondary} />
          <Text style={styles.statText}>
            {activity.hours_per_week}h/week × {activity.weeks_per_year} weeks/year
          </Text>
        </View>
        <View style={styles.statRow}>
          <Ionicons name="calendar" size={16} color={colors.textSecondary} />
          <Text style={styles.statText}>{activity.years_participated} year(s)</Text>
        </View>
        <View style={styles.statRow}>
          <Ionicons name="trending-up" size={16} color={colors.textSecondary} />
          <Text style={styles.statText}>Impact: {activity.impact_level}</Text>
        </View>
      </View>

      {activity.achievements && (
        <View style={styles.achievementsSection}>
          <Text style={styles.achievementsLabel}>Achievements:</Text>
          <Text style={styles.achievementsText}>{activity.achievements}</Text>
          {activity.achievements_impact && (
            <View style={[styles.impactBadge, { backgroundColor: getImpactColor(activity.achievements_impact) }]}>
              <Text style={styles.impactText}>{activity.achievements_impact}</Text>
            </View>
          )}
        </View>
      )}

      <View style={styles.cardActions}>
        <TouchableOpacity
          style={styles.editButton}
          onPress={() => openEditModal(activity)}
        >
          <Ionicons name="create-outline" size={18} color={colors.primary} />
          <Text style={styles.editButtonText}>Edit</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.deleteButton}
          onPress={() => handleDelete(activity)}
        >
          <Ionicons name="trash-outline" size={18} color={colors.error} />
          <Text style={styles.deleteButtonText}>Delete</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const getCategoryLabel = (category: string) => {
    const labels: { [key: string]: string } = {
      leadership: 'Leadership',
      research: 'Research',
      volunteering: 'Volunteering',
      sports: 'Sports',
      arts: 'Arts',
      work: 'Work',
    };
    return labels[category] || category;
  };

  const getCategoryColor = (category: string) => {
    const colors_map: { [key: string]: string } = {
      leadership: colors.primary,
      research: colors.info,
      volunteering: colors.success,
      sports: colors.warning,
      arts: colors.purple,
      work: colors.error,
    };
    return colors_map[category] || colors.textSecondary;
  };

  const getImpactColor = (impact: string) => {
    const colors_map: { [key: string]: string } = {
      school: colors.textSecondary,
      state: colors.info,
      national: colors.warning,
      international: colors.error,
    };
    return colors_map[impact] || colors.textSecondary;
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading activities...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Extracurricular Activities</Text>
        <TouchableOpacity
          onPress={() => {
            // Check profile exists before opening modal
            if (!hasProfile) {
              Alert.alert(
                'Profile Required',
                'Please create your university profile first before adding extracurricular activities.',
                [
                  { text: 'Cancel', style: 'cancel' },
                  {
                    text: 'Create Profile',
                    onPress: () => router.push('/university-profile/wizard'),
                  },
                ]
              );
            } else {
              openAddModal();
            }
          }}
          style={styles.addButton}
        >
          <Ionicons name="add-circle" size={28} color={colors.primary} />
        </TouchableOpacity>
      </View>

      {/* Content */}
      {!hasProfile ? (
        <View style={styles.centerContent}>
          <Ionicons name="person-outline" size={64} color={colors.textSecondary} />
          <Text style={styles.emptyTitle}>Create Your Profile First</Text>
          <Text style={styles.emptyText}>
            You need to create a university profile before adding extracurricular activities.
          </Text>
          <TouchableOpacity
            style={styles.ctaButton}
            onPress={() => router.push('/university-profile/wizard')}
          >
            <Text style={styles.ctaButtonText}>Create Profile</Text>
          </TouchableOpacity>
        </View>
      ) : !Array.isArray(activities) || activities.length === 0 ? (
        <View style={styles.centerContent}>
          <Ionicons name="fitness-outline" size={64} color={colors.textSecondary} />
          <Text style={styles.emptyTitle}>No activities yet</Text>
          <Text style={styles.emptyText}>
            Add your extracurricular activities to enhance your profile
          </Text>
          <TouchableOpacity
            style={styles.ctaButton}
            onPress={() => {
              // Double-check profile exists before opening modal
              if (!hasProfile) {
                Alert.alert(
                  'Profile Required',
                  'Please create your university profile first before adding extracurricular activities.',
                  [
                    { text: 'Cancel', style: 'cancel' },
                    {
                      text: 'Create Profile',
                      onPress: () => router.push('/university-profile/wizard'),
                    },
                  ]
                );
              } else {
                openAddModal();
              }
            }}
          >
            <Text style={styles.ctaButtonText}>Add Your First Activity</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {Array.isArray(activities) && activities.map(activity => renderActivityCard(activity))}
        </ScrollView>
      )}

      {/* Add/Edit Modal */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={styles.modalContainer}>
          <StatusBar barStyle="dark-content" />

          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setModalVisible(false)} style={styles.modalBackButton}>
              <Ionicons name="close" size={24} color={colors.text} />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>
              {formMode === 'add' ? 'Add Activity' : 'Edit Activity'}
            </Text>
            <TouchableOpacity onPress={handleSubmit} style={styles.modalSaveButton}>
              <Text style={styles.modalSaveButtonText}>Save</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent} showsVerticalScrollIndicator={false}>
            {/* Category */}
            <View style={styles.fieldGroup}>
              <Text style={styles.label}>Category *</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                {CATEGORIES.map((cat) => (
                  <TouchableOpacity
                    key={cat}
                    style={[styles.categoryOption, category === cat && styles.categoryOptionSelected]}
                    onPress={() => setCategory(cat)}
                  >
                    <Text style={category === cat ? styles.categoryOptionTextSelected : styles.categoryOptionText}>
                      {getCategoryLabel(cat)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>

            {/* Title */}
            <View style={styles.fieldGroup}>
              <Text style={styles.label}>Activity Title *</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., Debate Club President"
                value={title}
                onChangeText={setTitle}
              />
            </View>

            {/* Role */}
            <View style={styles.fieldGroup}>
              <Text style={styles.label}>Your Role *</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., Captain, President, Member"
                value={role}
                onChangeText={setRole}
              />
            </View>

            {/* Time Commitment */}
            <View style={styles.fieldGroup}>
              <Text style={styles.label}>Time Commitment</Text>
              <View style={styles.row}>
                <View style={styles.rowItem}>
                  <Text style={styles.rowLabel}>Hours/week</Text>
                  <TextInput
                    style={styles.numericInput}
                    placeholder="5"
                    value={hoursPerWeek}
                    onChangeText={setHoursPerWeek}
                    keyboardType="number-pad"
                  />
                </View>
                <View style={styles.rowItem}>
                  <Text style={styles.rowLabel}>Weeks/year</Text>
                  <TextInput
                    style={styles.numericInput}
                    placeholder="40"
                    value={weeksPerYear}
                    onChangeText={setWeeksPerYear}
                    keyboardType="number-pad"
                  />
                </View>
                <View style={styles.rowItem}>
                  <Text style={styles.rowLabel}>Years</Text>
                  <TextInput
                    style={styles.numericInput}
                    placeholder="3"
                    value={yearsParticipated}
                    onChangeText={setYearsParticipated}
                    keyboardType="number-pad"
                  />
                </View>
              </View>
            </View>

            {/* Impact Level */}
            <View style={styles.fieldGroup}>
              <Text style={styles.label}>Impact Level</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                {IMPACT_LEVELS.map((level) => (
                  <TouchableOpacity
                    key={level}
                    style={[styles.impactOption, impactLevel === level && styles.impactOptionSelected]}
                    onPress={() => setImpactLevel(level)}
                  >
                    <Text style={impactLevel === level ? styles.impactOptionTextSelected : styles.impactOptionText}>
                      {level.charAt(0).toUpperCase() + level.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>

            {/* Leadership Position */}
            <TouchableOpacity
              style={[styles.checkbox, leadershipPosition && styles.checkboxSelected]}
              onPress={() => setLeadershipPosition(!leadershipPosition)}
            >
              <Ionicons
                name={leadershipPosition ? 'checkbox' : 'square-outline'}
                size={24}
                color={colors.primary}
              />
              <Text style={styles.checkboxLabel}>Leadership Position</Text>
            </TouchableOpacity>

            {/* Achievements */}
            <View style={styles.fieldGroup}>
              <Text style={styles.label}>Achievements & Recognition</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                placeholder="Describe any awards, recognition, or notable achievements..."
                value={achievements}
                onChangeText={setAchievements}
                multiline
                numberOfLines={4}
              />
            </View>

            {/* Achievement Impact */}
            {achievements && (
              <View style={styles.fieldGroup}>
                <Text style={styles.label}>Achievement Impact Level</Text>
                <View style={styles.row}>
                  {ACHIEVEMENTS_IMPACT.map((level) => (
                    <TouchableOpacity
                      key={level}
                      style={[styles.achievementImpactOption, achievementsImpact === level && styles.achievementImpactOptionSelected]}
                      onPress={() => setAchievementsImpact(level)}
                    >
                      <Text style={achievementsImpact === level ? styles.achievementImpactOptionTextSelected : styles.achievementImpactOptionText}>
                        {level.charAt(0).toUpperCase() + level.slice(1)}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            )}
          </ScrollView>
        </SafeAreaView>
      </Modal>
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
    flex: 1,
    textAlign: 'center',
  },
  addButton: {
    padding: spacing.xs,
  },
  content: {
    flex: 1,
    padding: spacing.md,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  cardHeaderLeft: {
    flex: 1,
    gap: spacing.xs,
  },
  categoryBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: 12,
  },
  categoryText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  activityTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text,
  },
  activityRole: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  cardBody: {
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  statRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  statText: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  achievementsSection: {
    backgroundColor: colors.background,
    borderRadius: 8,
    padding: spacing.sm,
    marginBottom: spacing.md,
    gap: spacing.xs,
  },
  achievementsLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  achievementsText: {
    fontSize: 14,
    color: colors.text,
    lineHeight: 20,
  },
  impactBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: 8,
  },
  impactText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#fff',
  },
  cardActions: {
    flexDirection: 'row',
    gap: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: spacing.sm,
  },
  editButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
    paddingVertical: spacing.sm,
    borderRadius: 8,
    backgroundColor: colors.background,
  },
  editButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.primary,
  },
  deleteButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
    paddingVertical: spacing.sm,
    borderRadius: 8,
    backgroundColor: colors.background,
  },
  deleteButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.error,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: spacing.md,
    padding: spacing.xl,
  },
  loadingText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
    marginTop: spacing.md,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.text,
  },
  emptyText: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  ctaButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderRadius: 12,
    marginTop: spacing.md,
  },
  ctaButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: colors.background,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  modalBackButton: {
    padding: spacing.xs,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text,
  },
  modalSaveButton: {
    padding: spacing.xs,
  },
  modalSaveButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.primary,
  },
  modalContent: {
    flex: 1,
    padding: spacing.md,
  },
  fieldGroup: {
    marginBottom: spacing.lg,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  input: {
    backgroundColor: colors.card,
    borderRadius: 8,
    padding: spacing.sm,
    fontSize: 16,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.border,
    placeholderTextColor: colors.textSecondary,
  },
  textArea: {
    minHeight: 100,
    textAlignVertical: 'top',
  },
  row: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  rowItem: {
    flex: 1,
  },
  rowLabel: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  numericInput: {
    backgroundColor: colors.card,
    borderRadius: 8,
    padding: spacing.sm,
    fontSize: 16,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.border,
    textAlign: 'center',
    placeholderTextColor: colors.textSecondary,
  },
  categoryOption: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 20,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    marginRight: spacing.sm,
  },
  categoryOptionSelected: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primary,
  },
  categoryOptionText: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  categoryOptionTextSelected: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.primary,
  },
  impactOption: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 20,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    marginRight: spacing.sm,
  },
  impactOptionSelected: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primary,
  },
  impactOptionText: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  impactOptionTextSelected: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.primary,
  },
  achievementImpactOption: {
    flex: 1,
    paddingVertical: spacing.sm,
    borderRadius: 8,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
  },
  achievementImpactOptionSelected: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primary,
  },
  achievementImpactOptionText: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  achievementImpactOptionTextSelected: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.primary,
  },
  checkbox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    padding: spacing.sm,
    borderRadius: 8,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.lg,
  },
  checkboxSelected: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primary,
  },
  checkboxLabel: {
    fontSize: 14,
    color: colors.text,
  },
});
