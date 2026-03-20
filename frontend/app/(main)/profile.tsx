import { useState, useEffect } from "react";
import { View, Text, ScrollView, StyleSheet, Alert } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { authAPI } from "@/services/api";
import { getMyBookings } from "@/services/mentorship";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { useTranslation } from "react-i18next";
import i18n from "@/services/i18n";
import analytics from "@/services/analytics";
import { colors, spacing, borderRadius, typography } from "@/theme";
import { BlurView } from "expo-blur";
import LiquidGlassCard from "@/components/LiquidGlassCard";
import { planStorage, type UserPlan } from "@/utils/planStorage";

const LANGUAGES = [
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "ru", label: "Русский", flag: "🇷🇺" },
];

interface ProgressData {
  overall: {
    total_tasks: number;
    completed_tasks: number;
    remaining_tasks: number;
    progress_percentage: number;
  };
  streak: {
    current_streak: number;
    longest_streak: number;
    total_days_active: number;
  };
  timeline: {
    completed_this_week: number;
    completed_this_month: number;
    upcoming_tasks: number;
    overdue_tasks: number;
  };
}

// Quick Action Card Component (now full-width row)
const QuickActionCard = ({
  icon,
  iconColor,
  label,
  description,
  onPress,
}: {
  icon: string;
  iconColor: string;
  label: string;
  description: string;
  onPress: () => void;
}) => (
  <LiquidGlassCard
    variant="default"
    intensity="medium"
    onPress={onPress}
    style={quickActionStyles.card}
  >
    <View style={quickActionStyles.row}>
      <View style={quickActionStyles.iconContainer}>
        <MaterialCommunityIcons
          name={icon as any}
          size={24}
          color={iconColor}
        />
      </View>

      <View style={quickActionStyles.content}>
        <Text style={quickActionStyles.title} numberOfLines={1}>
          {label}
        </Text>
        <Text style={quickActionStyles.description} numberOfLines={1}>
          {description}
        </Text>
      </View>

      <MaterialCommunityIcons
        name="chevron-right"
        size={24}
        color={colors.textSecondary}
      />
    </View>
  </LiquidGlassCard>
);

const quickActionStyles = StyleSheet.create({
  card: {
    marginBottom: spacing.sm,
    width: "100%",
  },
  row: {
    flexDirection: "row" as const,
    alignItems: "center" as const,
    paddingVertical: 10,
    paddingHorizontal: 12,
    width: "100%",
    minHeight: 56,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.liquidGlass.overlayLight,
    alignItems: "center" as const,
    justifyContent: "center" as const,
    marginRight: 12,
  },
  content: {
    flex: 1,
    minWidth: 0,
  },
  title: {
    ...typography.labelLarge,
    color: colors.text,
    marginBottom: 1,
  },
  description: {
    ...typography.caption,
    color: colors.textSecondary,
  },
});

// Profile Stat Card Component
const ProfileStatCard = ({
  icon,
  iconColor,
  value,
  label,
}: {
  icon: string;
  iconColor: string;
  value: string | number;
  label: string;
}) => (
  <View style={statCardStyles.card}>
    <MaterialCommunityIcons name={icon as any} size={24} color={iconColor} />
    <Text style={statCardStyles.number}>{value}</Text>
    <Text style={statCardStyles.label}>{label}</Text>
  </View>
);

const statCardStyles = StyleSheet.create({
  card: {
    flex: 1,
    alignItems: "center",
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xs,
    backgroundColor: colors.liquidGlass.overlayMedium,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.liquidGlass.borderLight,
    minHeight: 80,
  },
  number: {
    fontSize: 20,
    fontWeight: "bold",
    color: colors.text,
    marginTop: spacing.xs,
  },
  label: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
    textAlign: "center",
  },
});

// Settings Row Card Component
const SettingsRowCard = ({
  icon,
  iconColor,
  iconBg,
  title,
  description,
  onPress,
}: {
  icon: string;
  iconColor: string;
  iconBg?: string;
  title: string;
  description: string;
  onPress: () => void;
}) => (
  <LiquidGlassCard
    variant="default"
    intensity="medium"
    onPress={onPress}
    style={settingsRowStyles.card}
  >
    <View style={settingsRowStyles.row}>
      <View
        style={[
          settingsRowStyles.iconContainer,
          iconBg && { backgroundColor: iconBg },
        ]}
      >
        <MaterialCommunityIcons
          name={icon as any}
          size={24}
          color={iconColor}
        />
      </View>

      <View style={settingsRowStyles.content}>
        <Text style={settingsRowStyles.title} numberOfLines={1}>
          {title}
        </Text>
        <Text style={settingsRowStyles.description} numberOfLines={2}>
          {description}
        </Text>
      </View>

      <View style={settingsRowStyles.trailing}>
        <MaterialCommunityIcons
          name="chevron-right"
          size={24}
          color={colors.textSecondary}
        />
      </View>
    </View>
  </LiquidGlassCard>
);

const settingsRowStyles = StyleSheet.create({
  card: {
    marginBottom: spacing.sm,
    width: "100%",
  },
  row: {
    flexDirection: "row" as const,
    alignItems: "center" as const,
    paddingVertical: 10,
    paddingHorizontal: 12,
    width: "100%",
    minHeight: 56,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.liquidGlass.overlayLight,
    alignItems: "center" as const,
    justifyContent: "center" as const,
    marginRight: 12,
  },
  content: {
    flex: 1,
    minWidth: 0,
  },
  title: {
    ...typography.labelLarge,
    color: colors.text,
    marginBottom: 1,
  },
  description: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  trailing: {
    marginLeft: 12,
    alignItems: "flex-end" as const,
    justifyContent: "center" as const,
  },
});

// Danger Button Card Component
const DangerButtonCard = ({
  icon,
  label,
  onPress,
}: {
  icon: string;
  label: string;
  onPress: () => void;
}) => (
  <LiquidGlassCard
    variant="subtle"
    intensity="light"
    onPress={onPress}
    style={dangerButtonStyles.card}
  >
    <MaterialCommunityIcons name={icon as any} size={20} color={colors.error} />
    <Text style={dangerButtonStyles.text}>{label}</Text>
  </LiquidGlassCard>
);

const dangerButtonStyles = StyleSheet.create({
  card: {
    flexDirection: "row" as const,
    alignItems: "center" as const,
    justifyContent: "center" as const,
    gap: spacing.sm,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
    marginBottom: spacing.xs,
    borderWidth: 1,
    borderColor: colors.error + "40",
  },
  text: {
    ...typography.labelMedium,
    color: colors.error,
  },
});

export default function ProfileScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [profile, setProfile] = useState<any>(null);
  const [isMentor, setIsMentor] = useState(false);
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [currentLanguage, setCurrentLanguage] = useState(i18n.language || "en");
  const [userPlan, setUserPlan] = useState<UserPlan>("basic");
  const [upcomingSessionCount, setUpcomingSessionCount] = useState(0);

  useEffect(() => {
    loadProfile();
    loadProgress();
    loadPlan();
    loadSessionCount();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await authAPI.getProfile();
      setProfile(response.data);
      if (response.data.preferred_language) {
        setCurrentLanguage(response.data.preferred_language);
      }

      // Check if user is a mentor
      const { getMyMentorProfile } = await import("@/services/mentorship");
      try {
        await getMyMentorProfile();
        setIsMentor(true);
      } catch (error) {
        setIsMentor(false);
      }
    } catch (error) {
      console.error("Failed to load profile:", error);
    }
  };

  const loadProgress = async () => {
    try {
      const response = await authAPI.getProgress();
      setProgress(response.data);
    } catch (error) {
      console.error("Failed to load progress:", error);
    }
  };

  const loadPlan = async () => {
    try {
      const plan = await planStorage.getPlan();
      setUserPlan(plan);
    } catch (error) {
      console.error("Failed to load plan:", error);
      setUserPlan("basic");
    }
  };

  const loadSessionCount = async () => {
    try {
      const bookings = await getMyBookings();
      const now = new Date();

      // Filter for confirmed upcoming meetings
      const upcomingCount = bookings.filter(
        (b) => b.status === "confirmed" && new Date(b.start_at_utc) > now
      ).length;

      console.log("Upcoming sessions count:", upcomingCount);
      setUpcomingSessionCount(upcomingCount);
    } catch (error) {
      console.error("Failed to load session count:", error);
      setUpcomingSessionCount(0);
    }
  };

  const handleSetDebugPlan = async (plan: UserPlan) => {
    await planStorage.setPlan(plan);
    setUserPlan(plan);
    Alert.alert(
      "Success",
      `Plan set to ${plan}\n\nGo to Mentors tab to see the effect.`,
    );
  };

  const handlePlanLongPress = () => {
    Alert.alert(
      "Debug: Set Plan",
      "Choose a plan for testing (long-press to access)",
      [
        { text: "Basic", onPress: () => handleSetDebugPlan("basic") },
        { text: "Pro", onPress: () => handleSetDebugPlan("pro") },
        { text: "Premium", onPress: () => handleSetDebugPlan("premium") },
        { text: "Cancel", style: "cancel" },
      ],
    );
  };

  const changeLanguage = async (languageCode: string) => {
    try {
      const oldLanguage = currentLanguage;
      setCurrentLanguage(languageCode);
      await i18n.changeLanguage(languageCode);
      await authAPI.updateProfile({ preferred_language: languageCode });
      analytics.trackLanguageChanged(oldLanguage, languageCode);
    } catch (error) {
      console.error("Failed to change language:", error);
      setCurrentLanguage(i18n.language);
      Alert.alert("Error", "Failed to update language. Please try again.");
    }
  };

  const handleLogout = () => {
    Alert.alert(t("profile.logout"), t("profile.logoutConfirm"), [
      { text: t("common.cancel"), style: "cancel" },
      {
        text: t("profile.logout"),
        style: "destructive",
        onPress: async () => {
          analytics.trackUserLoggedOut();
          await AsyncStorage.multiRemove([
            "access_token",
            "refresh_token",
            "onboarding_completed",
          ]);
          router.replace("/(auth)/login");
        },
      },
    ]);
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      "Delete Account",
      "Are you sure you want to delete your account? This action cannot be undone and all your data will be permanently deleted.",
      [
        { text: t("common.cancel"), style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              await authAPI.deleteAccount();
              await AsyncStorage.multiRemove([
                "access_token",
                "refresh_token",
                "onboarding_completed",
              ]);
              router.replace("/(auth)/login");
            } catch (error) {
              console.error("Failed to delete account:", error);
              Alert.alert(
                t("common.error"),
                "Failed to delete account. Please try again.",
              );
            }
          },
        },
      ],
    );
  };

  const handleLanguagePress = () => {
    Alert.alert(t("profile.language"), "Select your preferred language", [
      ...LANGUAGES.map((lang) => ({
        text: `${lang.flag} ${lang.label}`,
        onPress: () => changeLanguage(lang.code),
      })),
      { text: t("common.cancel"), style: "cancel" },
    ]);
  };

  const progressPercentage = progress?.overall?.progress_percentage ?? 0;
  const streakDays = progress?.streak?.current_streak ?? 0;
  const goalsCount = progress?.timeline?.upcoming_tasks ?? 0;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={[
        styles.contentContainer,
        { paddingBottom: spacing.xl + insets.bottom },
      ]}
      showsVerticalScrollIndicator={false}
    >
      {/* Modern Hero Section */}
      <View style={styles.heroSection}>
        <BlurView intensity={80} tint="dark" style={styles.heroBlur}>
          <View style={styles.heroContent}>
            {/* Avatar with gradient ring */}
            <View style={styles.avatarRing}>
              <View style={styles.avatar}>
                <Text style={styles.avatarText}>
                  {profile?.name?.charAt(0)?.toUpperCase() || "?"}
                </Text>
              </View>
            </View>

            <Text style={styles.heroName}>{profile?.name || "User"}</Text>
            <Text style={styles.heroEmail}>{profile?.user?.email || ""}</Text>

            {/* Stats Grid - Now using real progress data */}
            <View style={styles.statsGrid}>
              <ProfileStatCard
                icon="fire"
                iconColor={colors.warning}
                value={streakDays}
                label="Day Streak"
              />
              <ProfileStatCard
                icon="target"
                iconColor={colors.success}
                value={goalsCount}
                label="Goals"
              />
              <ProfileStatCard
                icon="chart-timeline-variant"
                iconColor={colors.primary}
                value={`${progressPercentage}%`}
                label="Progress"
              />
            </View>
          </View>
        </BlurView>
      </View>

      <View style={styles.content}>
        {profile && (
          <>
            {/* Quick Actions */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Quick Actions</Text>

              <QuickActionCard
                icon="account-details"
                iconColor={colors.primary}
                label="Edit Profile"
                description="Manage your personal details"
                onPress={() => router.push("/(main)/profile-info")}
              />

              <QuickActionCard
                icon="calendar-clock"
                iconColor={colors.warning}
                label="My Sessions"
                description={
                  upcomingSessionCount === 0
                    ? "No upcoming sessions"
                    : upcomingSessionCount === 1
                      ? "1 upcoming session"
                      : `${upcomingSessionCount} upcoming sessions`
                }
                onPress={() => router.push("/(main)/mentorship-bookings")}
              />

              <QuickActionCard
                icon="school"
                iconColor={colors.success}
                label="University"
                description="Update your target schools"
                onPress={() => router.push("/university-profile/wizard")}
              />

              <QuickActionCard
                icon={isMentor ? "view-dashboard" : "account-tie"}
                iconColor="#8B5CF6"
                label={isMentor ? "Mentor Dashboard" : "Become a Mentor"}
                description={
                  isMentor
                    ? "Manage your mentorship"
                    : "Share your expertise and help others"
                }
                onPress={() =>
                  isMentor
                    ? router.push("/(main)/mentor-dashboard")
                    : router.replace("/(main)/mentor-profile")
                }
              />

              <QuickActionCard
                icon="bell-ring"
                iconColor={colors.warning}
                label="Notifications"
                description="Configure your alerts"
                onPress={() => router.push("/(main)/notification-settings")}
              />

              {profile?.is_super_admin && (
                <QuickActionCard
                  icon="shield-account"
                  iconColor={colors.error}
                  label="Admin Panel"
                  description="Manage community approvals"
                  onPress={() => router.push("/(main)/community-approvals")}
                />
              )}
            </View>

            {/* Subscription Plan Card */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Subscription</Text>

              <LiquidGlassCard
                variant="default"
                intensity="medium"
                onPress={handlePlanLongPress}
                style={styles.planRowCard}
              >
                <View style={styles.planRow}>
                  <View style={styles.planIconContainer}>
                    <MaterialCommunityIcons
                      name={
                        userPlan === "premium"
                          ? "crown"
                          : userPlan === "pro"
                            ? "star"
                            : "account"
                      }
                      size={24}
                      color={userPlan === "basic" ? "#8E8E8E" : "#F59E0B"}
                    />
                  </View>

                  <View style={styles.planContent}>
                    <Text style={styles.planTitle} numberOfLines={1}>
                      {userPlan === "premium"
                        ? "Premium Plan"
                        : userPlan === "pro"
                          ? "Pro Plan"
                          : "Basic Plan"}
                    </Text>
                    <Text style={styles.planDescription} numberOfLines={1}>
                      {userPlan === "basic"
                        ? "Long-press to upgrade for testing"
                        : "Full access to all features"}
                    </Text>
                  </View>

                  <View
                    style={[
                      styles.planBadge,
                      userPlan === "premium"
                        ? styles.planBadgePremium
                        : userPlan === "pro"
                          ? styles.planBadgePro
                          : styles.planBadgeBasic,
                    ]}
                  >
                    <Text style={styles.planBadgeText}>
                      {userPlan.toUpperCase()}
                    </Text>
                  </View>
                </View>
              </LiquidGlassCard>

              {userPlan === "basic" && (
                <LiquidGlassCard
                  variant="elevated"
                  intensity="heavy"
                  onPress={() => router.push("/(onboarding)/subscription")}
                  style={styles.upgradeCard}
                >
                  <View style={styles.upgradeRow}>
                    <View style={styles.upgradeIconContainer}>
                      <MaterialCommunityIcons
                        name="rocket-launch"
                        size={24}
                        color="#3B82F6"
                      />
                    </View>

                    <View style={styles.upgradeContent}>
                      <Text style={styles.upgradeTitle} numberOfLines={1}>
                        Upgrade to Pro
                      </Text>
                      <Text style={styles.upgradeDescription} numberOfLines={1}>
                        Unlock mentors and premium features
                      </Text>
                    </View>

                    <MaterialCommunityIcons
                      name="chevron-right"
                      size={24}
                      color="#3B82F6"
                    />
                  </View>
                </LiquidGlassCard>
              )}
            </View>

            {/* Language Selection */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>{t("profile.language")}</Text>

              <LiquidGlassCard
                variant="default"
                intensity="medium"
                onPress={handleLanguagePress}
                style={styles.languageRowCard}
              >
                <View style={styles.languageRow}>
                  <View style={styles.languageIconContainer}>
                    <Text style={styles.languageFlag}>
                      {LANGUAGES.find((l) => l.code === currentLanguage)
                        ?.flag || "🌐"}
                    </Text>
                  </View>

                  <View style={styles.languageContent}>
                    <Text style={styles.languageTitle} numberOfLines={1}>
                      {LANGUAGES.find((l) => l.code === currentLanguage)
                        ?.label || "Language"}
                    </Text>
                    <Text style={styles.languageSubtitle} numberOfLines={1}>
                      Tap to change language
                    </Text>
                  </View>

                  <MaterialCommunityIcons
                    name="chevron-right"
                    size={24}
                    color={colors.textSecondary}
                  />
                </View>
              </LiquidGlassCard>
            </View>

            {/* Social Features */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Social</Text>
              <SettingsRowCard
                icon="account-search"
                iconColor="#3B82F6"
                title="Discover People"
                description="Find and connect with other users"
                onPress={() => router.push("/search")}
              />
              <SettingsRowCard
                icon="message-text"
                iconColor="#10B981"
                title="Messages"
                description="View your conversations"
                onPress={() => router.push("/messages")}
              />
              <SettingsRowCard
                icon="account-edit"
                iconColor="#8B5CF6"
                title="Edit Social Profile"
                description="Update bio, location, target schools"
                onPress={() => router.push("/profile/edit")}
              />
            </View>

            {/* Settings */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Settings</Text>
              <SettingsRowCard
                icon="account-circle"
                iconColor={colors.primary}
                title="Profile Information"
                description="Manage your personal details"
                onPress={() => router.push("/(main)/profile-info")}
              />
              <SettingsRowCard
                icon="bell-ring"
                iconColor={colors.warning}
                title="Notifications"
                description="Configure your alerts"
                onPress={() => router.push("/(main)/notification-settings")}
              />
            </View>

            {/* Danger Zone */}
            <View style={styles.section}>
              <Text style={styles.dangerTitle}>Danger Zone</Text>
              <DangerButtonCard
                icon="logout"
                label={t("profile.logout")}
                onPress={handleLogout}
              />
              <DangerButtonCard
                icon="delete-forever"
                label="Delete Account"
                onPress={handleDeleteAccount}
              />
            </View>
          </>
        )}

        <Text style={styles.version}>Plano v1.0.0</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  contentContainer: {
    paddingHorizontal: spacing.md,
  },
  // Hero Section
  heroSection: {
    position: "relative",
    marginBottom: spacing.lg,
  },
  heroBlur: {
    paddingTop: 60,
    paddingBottom: spacing.xl,
  },
  heroContent: {
    alignItems: "center",
    paddingHorizontal: spacing.md,
  },
  avatarRing: {
    padding: 4,
    borderRadius: 60,
    shadowColor: colors.primary,
    shadowOpacity: 0.5,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 8 },
  },
  avatar: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: colors.primary,
    justifyContent: "center",
    alignItems: "center",
  },
  avatarText: {
    fontSize: 40,
    fontWeight: "bold",
    color: "#fff",
  },
  heroName: {
    ...typography.displayLarge,
    color: colors.text,
    marginTop: spacing.md,
  },
  heroEmail: {
    ...typography.bodyLarge,
    color: colors.textSecondary,
    marginTop: 4,
  },
  // Stats Grid
  statsGrid: {
    flexDirection: "row",
    gap: spacing.sm,
    marginTop: spacing.lg,
    paddingHorizontal: spacing.xs,
  },
  // Content
  content: {
    paddingTop: spacing.sm,
  },
  section: {
    width: "100%",
    marginBottom: spacing.lg,
  },
  sectionTitle: {
    ...typography.headlineSmall,
    marginBottom: spacing.md,
    color: colors.text,
  },
  // Language Row Card
  languageRowCard: {
    width: "100%",
  },
  languageRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
    paddingHorizontal: 12,
    minHeight: 56,
  },
  languageIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.liquidGlass.overlayLight,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  languageFlag: {
    fontSize: 20,
  },
  languageContent: {
    flex: 1,
    minWidth: 0,
  },
  languageTitle: {
    ...typography.labelLarge,
    color: colors.text,
    marginBottom: 1,
  },
  languageSubtitle: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  // Settings Cards (removed - now using planRow styles below)

  // Subscription Plan Row
  planRowCard: {
    width: "100%",
  },
  planRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
    paddingHorizontal: 12,
    minHeight: 56,
  },
  planIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.liquidGlass.overlayLight,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  planContent: {
    flex: 1,
    minWidth: 0,
  },
  planTitle: {
    ...typography.labelLarge,
    color: colors.text,
    marginBottom: 1,
  },
  planDescription: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  planBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
  },
  planBadgeBasic: {
    backgroundColor: "rgba(142, 142, 142, 0.2)",
    borderColor: "#8E8E8E",
  },
  planBadgePro: {
    backgroundColor: "rgba(59, 130, 246, 0.2)",
    borderColor: "#3B82F6",
  },
  planBadgePremium: {
    backgroundColor: "rgba(245, 158, 11, 0.2)",
    borderColor: "#F59E0B",
  },
  planBadgeText: {
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.5,
    color: colors.text,
  },
  // Upgrade Card Row
  upgradeCard: {
    marginTop: spacing.sm,
    borderWidth: 1,
    borderColor: "#3B82F6",
    backgroundColor: "rgba(59, 130, 246, 0.08)",
  },
  upgradeRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
    paddingHorizontal: 12,
    minHeight: 56,
  },
  upgradeIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "rgba(59, 130, 246, 0.18)",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  upgradeContent: {
    flex: 1,
    minWidth: 0,
  },
  upgradeTitle: {
    ...typography.labelLarge,
    color: "#3B82F6",
    fontWeight: "700",
    marginBottom: 1,
  },
  upgradeDescription: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  // Danger Zone
  dangerTitle: {
    ...typography.labelLarge,
    color: colors.error,
    marginBottom: spacing.sm,
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  version: {
    textAlign: "center",
    color: colors.textTertiary,
    fontSize: 12,
    marginTop: spacing.xl,
  },
});
