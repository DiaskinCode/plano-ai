/**
 * Become a Mentor / Mentor Profile Screen
 *
 * Multi-step form for mentor registration
 * Hidden tab bar for clean form experience
 */

import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { router } from "expo-router";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import {
  getMyMentorProfile,
  updateMyMentorProfile,
  getMyAvailabilityRules,
} from "@/services/mentorship";
import { colors, spacing, borderRadius, typography } from "@/theme";
import { SafeAreaView } from "react-native-safe-area-context";

export default function MentorProfileScreen() {
  const [isMentor, setIsMentor] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Form fields
  const [fullName, setFullName] = useState("");
  const [title, setTitle] = useState("");
  const [bio, setBio] = useState("");
  const [education, setEducation] = useState("");
  const [expertiseAreas, setExpertiseAreas] = useState<string[]>([]);
  const [expertiseInput, setExpertiseInput] = useState("");
  const [hourlyRate, setHourlyRate] = useState("100");
  const [timezone, setTimezone] = useState("America/New_York");
  const [meetingLink, setMeetingLink] = useState("");

  // Verification fields
  const [videoUrl, setVideoUrl] = useState("");
  const [verificationStatus, setVerificationStatus] = useState<string | null>(null);
  const [verificationNotes, setVerificationNotes] = useState("");

  const timezones = [
    "America/New_York",
    "America/Los_Angeles",
    "America/Chicago",
    "America/Denver",
    "America/Phoenix",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Asia/Tokyo",
    "Asia/Shanghai",
  ];

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const profile = await getMyMentorProfile();
      setIsMentor(true);

      setFullName(profile.title || "");
      setTitle(""); // Separate title from name
      setBio(profile.bio || "");
      setEducation(profile.education || "");
      setExpertiseAreas(profile.expertise_areas || []);
      setHourlyRate(profile.hourly_rate_credits?.toString() || "100");
      setTimezone(profile.timezone || "America/New_York");
      setMeetingLink(profile.meeting_link || "");

      // Load verification fields
      setVideoUrl(profile.verification_video_url || "");
      setVerificationStatus(profile.verification_status || null);
      setVerificationNotes(profile.verification_notes || "");
    } catch (error) {
      console.log("Not a mentor yet");
      setIsMentor(false);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!fullName.trim()) {
      Alert.alert("Required", "Please enter your full name");
      return;
    }

    if (!bio.trim()) {
      Alert.alert("Required", "Please write a short bio");
      return;
    }

    if (expertiseAreas.length === 0) {
      Alert.alert("Required", "Please add at least one area of expertise");
      return;
    }

    // Video URL is required for new mentors
    if (!isMentor && !videoUrl.trim()) {
      Alert.alert(
        "Required",
        "Please provide a video introduction URL (YouTube, Vimeo, or Loom)"
      );
      return;
    }

    try {
      setSaving(true);

      // Combine name and title for display
      const displayName = title.trim()
        ? `${title.trim()} ${fullName.trim()}`
        : fullName.trim();

      const data: any = {
        title: displayName,
        bio: bio.trim(),
        education: education.trim(),
        expertise_areas: expertiseAreas,
        hourly_rate_credits: parseInt(hourlyRate),
        timezone,
        meeting_link: meetingLink.trim(),
      };

      // Include video URL
      if (videoUrl.trim()) {
        data.verification_video_url = videoUrl.trim();
      }

      await updateMyMentorProfile(data);

      Alert.alert(
        "Success",
        isMentor
          ? "Your mentor profile has been updated!"
          : "Your profile has been submitted for verification. You'll receive an email once approved.",
        [{ text: "OK", onPress: () => router.replace("/(main)/profile") }],
      );
    } catch (error: any) {
      Alert.alert("Error", error.message || "Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  const addExpertise = () => {
    const area = expertiseInput.trim();
    if (area && !expertiseAreas.includes(area)) {
      setExpertiseAreas([...expertiseAreas, area]);
      setExpertiseInput("");
    }
  };

  const removeExpertise = (area: string) => {
    setExpertiseAreas(expertiseAreas.filter((a) => a !== area));
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={styles.keyboardView}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            onPress={() => router.back()}
            style={styles.backButton}
          >
            <MaterialCommunityIcons
              name="arrow-left"
              size={24}
              color={colors.text}
            />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>
            {isMentor ? "Edit Profile" : "Become a Mentor"}
          </Text>
          {isMentor && (
            <TouchableOpacity
              style={styles.dashboardButton}
              onPress={() => router.push("/mentor-dashboard")}
            >
              <MaterialCommunityIcons
                name="view-dashboard"
                size={20}
                color={colors.primary}
              />
            </TouchableOpacity>
          )}
          <View style={styles.headerSpacer} />
        </View>

        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Required Note */}
          <View style={styles.requiredNote}>
            <Text style={styles.requiredNoteText}>* Required fields</Text>
          </View>

          {/* Name Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Basic Information</Text>

            <View style={styles.field}>
              <Text style={styles.label}>Full Name *</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., Sarah Chen"
                placeholderTextColor={colors.textSecondary}
                value={fullName}
                onChangeText={setFullName}
              />
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>Title (optional)</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., Dr., Mr., Ms."
                placeholderTextColor={colors.textSecondary}
                value={title}
                onChangeText={setTitle}
              />
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>Bio *</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                placeholder="Brief description of your background and expertise..."
                placeholderTextColor={colors.textTertiary}
                value={bio}
                onChangeText={setBio}
                multiline
                numberOfLines={4}
                textAlignVertical="top"
              />
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>Education</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., Ph.D. Education, Stanford University"
                placeholderTextColor={colors.textSecondary}
                value={education}
                onChangeText={setEducation}
              />
            </View>
          </View>

          {/* Expertise */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Areas of Expertise *</Text>
            <Text style={styles.sectionSubtitle}>
              Add your areas of expertise (e.g., "Essay Writing", "Interview
              Prep")
            </Text>

            <View style={styles.field}>
              <View style={styles.tagInputContainer}>
                <TextInput
                  style={styles.tagInput}
                  placeholder="Type expertise and press +"
                  placeholderTextColor={colors.textSecondary}
                  value={expertiseInput}
                  onChangeText={setExpertiseInput}
                  onSubmitEditing={addExpertise}
                />
                <TouchableOpacity
                  style={styles.tagAddButton}
                  onPress={addExpertise}
                >
                  <MaterialCommunityIcons
                    name="plus"
                    size={18}
                    color={colors.primary}
                  />
                </TouchableOpacity>
              </View>

              {expertiseAreas.length > 0 && (
                <View style={styles.tagList}>
                  {expertiseAreas.map((area, index) => (
                    <View key={index} style={styles.tag}>
                      <Text style={styles.tagText}>{area}</Text>
                      <TouchableOpacity onPress={() => removeExpertise(area)}>
                        <MaterialCommunityIcons
                          name="close"
                          size={16}
                          color={colors.textSecondary}
                        />
                      </TouchableOpacity>
                    </View>
                  ))}
                </View>
              )}
            </View>
          </View>

          {/* Session Settings */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Session Settings</Text>

            <View style={styles.field}>
              <Text style={styles.label}>Hourly Rate (credits per hour)</Text>
              <TextInput
                style={styles.input}
                keyboardType="numeric"
                placeholderTextColor={colors.textSecondary}
                value={hourlyRate}
                onChangeText={setHourlyRate}
              />
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>Timezone</Text>
              <View style={styles.timezoneContainer}>
                {timezones.map((tz) => (
                  <TouchableOpacity
                    key={tz}
                    style={[
                      styles.timezoneChip,
                      timezone === tz && styles.timezoneChipActive,
                    ]}
                    onPress={() => setTimezone(tz)}
                  >
                    <Text
                      style={[
                        styles.timezoneText,
                        timezone === tz && styles.timezoneTextActive,
                      ]}
                    >
                      {tz.replace("America/", "")}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>Video Meeting Link</Text>
              <TextInput
                style={styles.input}
                placeholder="https://meet.google.com/xxx-xxx-xxx"
                placeholderTextColor={colors.textSecondary}
                value={meetingLink}
                onChangeText={setMeetingLink}
                autoCapitalize="none"
                keyboardType="url"
              />
            </View>

            {/* Verification Status Badge */}
            {verificationStatus && (
              <View
                style={[
                  styles.verificationBadge,
                  {
                    backgroundColor:
                      verificationStatus === "approved"
                        ? "#D1FAE5"
                        : verificationStatus === "pending"
                        ? "#FEF3C7"
                        : "#FEE2E2",
                  },
                ]}
              >
                <MaterialCommunityIcons
                  name={
                    verificationStatus === "approved"
                      ? "check-circle"
                      : verificationStatus === "pending"
                      ? "clock-outline"
                      : "alert-circle"
                  }
                  size={20}
                  color={
                    verificationStatus === "approved"
                      ? colors.success
                      : verificationStatus === "pending"
                      ? colors.warning
                      : colors.error
                  }
                />
                <Text
                  style={[
                    styles.verificationText,
                    {
                      color:
                        verificationStatus === "approved"
                          ? colors.success
                          : verificationStatus === "pending"
                          ? colors.warning
                          : colors.error,
                    },
                  ]}
                >
                  {verificationStatus === "approved"
                    ? "Verified"
                    : verificationStatus === "pending"
                    ? "Pending Review"
                    : verificationStatus === "rejected"
                    ? "Needs Updates"
                    : "Suspended"}
                </Text>
              </View>
            )}

            {/* Rejection Notes */}
            {verificationNotes && verificationStatus === "rejected" && (
              <View style={styles.rejectionNotesBox}>
                <Text style={styles.rejectionNotesTitle}>Feedback:</Text>
                <Text style={styles.rejectionNotesText}>{verificationNotes}</Text>
              </View>
            )}

            {/* Video Introduction URL */}
            <View style={styles.field}>
              <Text style={styles.label}>
                Video Introduction URL {(!isMentor || verificationStatus === "rejected") && "*"}
              </Text>
              <Text style={styles.hint}>
                Share a 1-2 minute video introduction (YouTube, Vimeo, or Loom link)
              </Text>
              <TextInput
                style={styles.input}
                placeholder="https://youtube.com/watch?v=..."
                placeholderTextColor={colors.textSecondary}
                value={videoUrl}
                onChangeText={setVideoUrl}
                autoCapitalize="none"
                keyboardType="url"
              />
            </View>
          </View>

          {/* Info */}
          <View style={styles.section}>
            <View style={styles.infoBox}>
              <MaterialCommunityIcons
                name="information"
                size={20}
                color={colors.primary}
              />
              <Text style={styles.infoText}>
                After saving, your profile will be submitted for verification.
                Once verified, you'll appear in the mentor directory.
              </Text>
            </View>
          </View>

          {/* Save Button */}
          <View style={styles.buttonContainer}>
            <TouchableOpacity
              style={[styles.saveButton, saving && styles.saveButtonDisabled]}
              onPress={handleSave}
              disabled={saving}
            >
              {saving ? (
                <ActivityIndicator color={colors.bg} />
              ) : (
                <Text style={styles.saveButtonText}>
                  {isMentor ? "Save Changes" : "Submit Profile"}
                </Text>
              )}
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  loadingText: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    marginTop: spacing.md,
  },
  keyboardView: {
    flex: 1,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.bg,
    borderBottomWidth: 1,
    borderBottomColor: colors.liquidGlass.borderLight,
  },
  backButton: {
    padding: spacing.xs,
  },
  headerTitle: {
    ...typography.titleLarge,
    color: colors.text,
    flex: 1,
  },
  dashboardButton: {
    padding: spacing.xs,
  },
  headerSpacer: {
    width: 32,
  },
  requiredNote: {
    backgroundColor: colors.primary + "15",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.sm,
    marginHorizontal: spacing.md,
    marginTop: spacing.md,
    marginBottom: spacing.sm,
  },
  requiredNoteText: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: "600",
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: spacing.xxxl,
  },
  section: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
    paddingBottom: spacing.xl,
    marginBottom: spacing.sm,
    backgroundColor: colors.liquidGlass.overlayMedium,
    borderRadius: borderRadius.lg,
    marginHorizontal: spacing.lg,
  },
  sectionTitle: {
    ...typography.titleMedium,
    color: colors.text,
    marginBottom: spacing.md,
  },
  sectionSubtitle: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },
  field: {
    marginBottom: spacing.lg,
  },
  label: {
    ...typography.labelMedium,
    color: colors.text,
    marginBottom: spacing.sm,
  },
  input: {
    backgroundColor: colors.bg,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: 16,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.liquidGlass.borderLight,
  },
  textArea: {
    minHeight: 100,
  },
  tagInputContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.bg,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.liquidGlass.borderLight,
    paddingHorizontal: spacing.sm,
  },
  tagInput: {
    flex: 1,
    paddingVertical: spacing.sm,
    fontSize: 16,
    color: colors.text,
  },
  tagAddButton: {
    width: 40,
    height: 40,
    borderRadius: borderRadius.md,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
    marginLeft: spacing.sm,
  },
  tagList: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  tag: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.primary + "20",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
  },
  tagText: {
    ...typography.labelMedium,
    color: colors.primary,
    marginRight: spacing.xs,
  },
  timezoneContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  timezoneChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
    borderWidth: 1,
    borderColor: colors.liquidGlass.borderLight,
  },
  timezoneChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  timezoneText: {
    ...typography.labelMedium,
    color: colors.textSecondary,
  },
  timezoneTextActive: {
    color: colors.bg,
  },
  verificationBadge: {
    flexDirection: "row",
    alignItems: "center",
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginBottom: spacing.md,
  },
  verificationText: {
    ...typography.labelMedium,
    marginLeft: spacing.sm,
    fontWeight: "600",
  },
  rejectionNotesBox: {
    backgroundColor: "#FEE2E2",
    borderLeftWidth: 4,
    borderLeftColor: colors.error,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderRadius: borderRadius.sm,
  },
  rejectionNotesTitle: {
    ...typography.labelMedium,
    color: colors.error,
    marginBottom: spacing.xs,
  },
  rejectionNotesText: {
    ...typography.bodyMedium,
    color: colors.text,
    lineHeight: 22,
  },
  hint: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  infoBox: {
    flexDirection: "row",
    alignItems: "flex-start",
    backgroundColor: colors.primary + "10",
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginHorizontal: spacing.lg,
    marginBottom: spacing.lg,
    gap: spacing.sm,
  },
  infoText: {
    ...typography.bodyMedium,
    color: colors.text,
    flex: 1,
  },
  buttonContainer: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xl,
  },
  saveButton: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.lg,
    borderRadius: borderRadius.lg,
    alignItems: "center",
  },
  saveButtonDisabled: {
    backgroundColor: colors.textSecondary,
  },
  saveButtonText: {
    ...typography.labelLarge,
    color: colors.bg,
    fontWeight: "700",
  },
});
