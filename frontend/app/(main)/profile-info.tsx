import { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
} from 'react-native';
import { authAPI } from '@/services/api';
import { BlurView } from 'expo-blur';
import LiquidGlassCard from '@/components/LiquidGlassCard';
import { colors, spacing, borderRadius, typography } from '@/theme';

export default function ProfileInfoScreen() {
  const [profile, setProfile] = useState<any>(null);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await authAPI.getProfile();
      setProfile(response.data);
    } catch (error) {
      console.error('Failed to load profile:', error);
    }
  };

  const coachEmojis: any = {
    aggressive: '🔥',
    cute: '🌟',
    supportive: '💙',
    professional: '💼',
  };

  return (
    <ScrollView style={styles.container}>
      {/* Header with blur effect */}
      <View style={styles.headerContainer}>
        <BlurView intensity={60} tint="dark" style={styles.headerBlur}>
          <View style={styles.header}>
            <Text style={styles.headerTitle}>Profile Information</Text>
          </View>
        </BlurView>
      </View>

      <View style={styles.content}>
        {profile && (
          <>
            {/* Personal Information */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Personal Information</Text>
              <LiquidGlassCard variant="default" intensity="medium">
                <InfoRow label="Name" value={profile.name || 'Not set'} />
                <InfoRow label="Age" value={profile.age?.toString() || 'Not set'} />
                <InfoRow label="Country" value={profile.country || 'Not set'} />
                <InfoRow label="Languages" value={profile.languages?.join(', ') || 'Not set'} />
              </LiquidGlassCard>
            </View>

            {/* Goals & Career */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Goals & Career</Text>
              <LiquidGlassCard variant="default" intensity="medium">
                <View style={styles.infoRow}>
                  <Text style={styles.infoLabel}>Current Situation</Text>
                  <Text style={styles.infoValue}>{profile.current_situation || 'Not set'}</Text>
                </View>
                <View style={styles.infoRow}>
                  <Text style={styles.infoLabel}>Future Goals</Text>
                  <Text style={styles.infoValue}>{profile.future_goals || 'Not set'}</Text>
                </View>
                <View style={styles.infoRow}>
                  <Text style={styles.infoLabel}>Dream Career</Text>
                  <Text style={styles.infoValue}>{profile.dream_career || 'Not set'}</Text>
                </View>
              </LiquidGlassCard>
            </View>

            {/* AI Coach */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>AI Coach</Text>
              <LiquidGlassCard variant="elevated" intensity="heavy">
                <View style={styles.coachContent}>
                  <Text style={styles.coachEmoji}>
                    {coachEmojis[profile.coach_character] || '💙'}
                  </Text>
                  <Text style={styles.coachName}>
                    {profile.coach_character?.charAt(0)?.toUpperCase() +
                      profile.coach_character?.slice(1) || 'Supportive'} Coach
                  </Text>
                </View>
              </LiquidGlassCard>
            </View>

            {/* Budget & Timeline */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Budget & Timeline</Text>
              <LiquidGlassCard variant="default" intensity="medium">
                <InfoRow label="Budget" value={profile.budget_range || 'Not set'} />
                <InfoRow label="Timeline" value={profile.target_timeline || 'Not set'} />
              </LiquidGlassCard>
            </View>

            {/* Target Destinations */}
            {profile.destinations && profile.destinations.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Target Destinations</Text>
                <View style={styles.tagsContainer}>
                  {profile.destinations.map((dest: string, idx: number) => (
                    <LiquidGlassCard
                      key={idx}
                      variant="subtle"
                      intensity="light"
                      style={styles.tag}
                    >
                      <Text style={styles.tagText}>{dest}</Text>
                    </LiquidGlassCard>
                  ))}
                </View>
              </View>
            )}

            {/* Network */}
            {profile.network && Object.keys(profile.network).length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Network</Text>
                <LiquidGlassCard variant="default" intensity="medium">
                  {Object.entries(profile.network).map(([key, value]: any, idx) => (
                    <InfoRow key={idx} label={key} value={value} />
                  ))}
                </LiquidGlassCard>
              </View>
            )}
          </>
        )}
      </View>
    </ScrollView>
  );
}

const InfoRow = ({ label, value }: { label: string; value: string }) => (
  <View style={styles.infoRow}>
    <Text style={styles.infoLabel}>{label}</Text>
    <Text style={styles.infoValue}>{value}</Text>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  headerContainer: {
    position: 'relative',
  },
  headerBlur: {
    borderBottomWidth: 1,
    borderBottomColor: colors.liquidGlass.borderLight,
  },
  header: {
    padding: spacing.md,
    paddingTop: 60,
    paddingBottom: spacing.md,
    backgroundColor: colors.liquidGlass.overlayLight,
  },
  headerTitle: {
    ...typography.displayMedium,
    color: colors.text,
  },
  content: {
    padding: spacing.md,
  },
  section: {
    marginBottom: spacing.lg,
  },
  sectionTitle: {
    ...typography.headlineSmall,
    marginBottom: spacing.sm,
    color: colors.text,
  },
  infoRow: {
    marginBottom: spacing.sm,
  },
  infoLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: 4,
    textTransform: 'uppercase',
    fontWeight: '600',
  },
  infoValue: {
    ...typography.bodyMedium,
    color: colors.text,
  },
  coachContent: {
    alignItems: 'center',
    paddingVertical: spacing.sm,
  },
  coachEmoji: {
    fontSize: 48,
    marginBottom: spacing.xs,
  },
  coachName: {
    ...typography.headlineSmall,
    color: colors.text,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
  },
  tag: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  tagText: {
    color: colors.primary,
    ...typography.labelMedium,
  },
});
