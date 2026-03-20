/**
 * Mentor Detail Screen
 *
 * View mentor profile, availability, and book sessions
 */

import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Image,
  Modal,
} from "react-native";
import { useRouter, useLocalSearchParams } from "expo-router";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import {
  getMentor,
  getMentorAvailability,
  bookSession,
  type Mentor,
  type TimeSlot,
} from "@/services/mentorship";
import { colors, spacing, borderRadius, typography } from "@/theme";
import LiquidGlassCard from "@/components/LiquidGlassCard";

type BookingStep = "view" | "date" | "time" | "confirm" | "success";

export default function MentorDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const mentorId = parseInt(id as string);

  const [mentor, setMentor] = useState<Mentor | null>(null);
  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [bookingLoading, setBookingLoading] = useState(false);

  // Booking state
  const [bookingStep, setBookingStep] = useState<BookingStep>("view");
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);
  const [sessionNotes, setSessionNotes] = useState("");
  const [sessionTopic, setSessionTopic] = useState("");

  useEffect(() => {
    if (mentorId) {
      loadMentor();
      loadAvailability();
    }
  }, [mentorId]);

  const loadMentor = async () => {
    try {
      setLoading(true);
      console.log("[MentorDetail] Loading mentor:", mentorId);
      const data = await getMentor(mentorId);
      console.log("[MentorDetail] Mentor data received:", data);
      setMentor(data);
    } catch (error: any) {
      console.error("[MentorDetail] Error loading mentor:", error);
      Alert.alert("Error", error.message || "Failed to load mentor");
      router.back();
    } finally {
      console.log("[MentorDetail] Setting loading to false");
      setLoading(false);
    }
  };

  const loadAvailability = async () => {
    try {
      const today = new Date();
      const nextWeek = new Date(today);
      nextWeek.setDate(today.getDate() + 7);

      const from = today.toISOString().split("T")[0];
      const to = nextWeek.toISOString().split("T")[0];

      const data = await getMentorAvailability(mentorId, from, to);
      setSlots(data.slots || []);
    } catch (error) {
      console.error("Error loading availability:", error);
    }
  };

  const handleStartBooking = () => {
    setBookingStep("confirm");
    setSelectedSlot(null);
    setSessionNotes("");
    setSessionTopic("");
  };

  const handleSelectSlot = (slot: TimeSlot) => {
    setSelectedSlot(slot);
    setBookingStep("confirm");
  };

  const handleConfirmBooking = async () => {
    if (!selectedSlot) return;

    if (!sessionTopic.trim()) {
      Alert.alert("Topic Required", "Please enter a session topic");
      return;
    }

    try {
      setBookingLoading(true);

      const booking = await bookSession(mentorId, {
        start_at: selectedSlot.start_at_utc,
        duration_minutes: selectedSlot.duration_minutes,
        topic: sessionTopic,
        notes: sessionNotes,
      });

      setBookingStep("success");
    } catch (error: any) {
      Alert.alert("Booking Failed", error.message || "Failed to book session");
    } finally {
      setBookingLoading(false);
    }
  };

  const handleCloseBooking = () => {
    setBookingStep("view");
    loadAvailability();
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      timeZoneName: "short",
    });
  };

  const groupSlotsByDate = () => {
    const grouped: { [key: string]: TimeSlot[] } = {};

    slots.forEach((slot) => {
      const date = new Date(slot.start_at_utc);
      const dateKey = date.toISOString().split("T")[0];

      if (!grouped[dateKey]) {
        grouped[dateKey] = [];
      }

      grouped[dateKey].push(slot);
    });

    return grouped;
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()}>
            <MaterialCommunityIcons
              name="arrow-left"
              size={24}
              color={colors.text}
            />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Mentor Profile</Text>
          <View style={styles.placeholder} />
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading mentor profile...</Text>
        </View>
      </View>
    );
  }

  if (!mentor) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()}>
            <MaterialCommunityIcons
              name="arrow-left"
              size={24}
              color={colors.text}
            />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Mentor Profile</Text>
          <View style={styles.placeholder} />
        </View>
        <View style={styles.errorContainer}>
          <MaterialCommunityIcons
            name="account-off"
            size={64}
            color={colors.textSecondary}
          />
          <Text style={styles.errorText}>Mentor not found</Text>
        </View>
      </View>
    );
  }

  const groupedSlots = groupSlotsByDate();
  const dates = Object.keys(groupedSlots).sort();

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView}>
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
          <Text style={styles.headerTitle}>Mentor Profile</Text>
          <View style={styles.placeholder} />
        </View>

        {/* Profile Card */}
        <LiquidGlassCard
          variant="default"
          intensity="medium"
          style={styles.profileCard}
        >
          <View style={styles.profileContent}>
            {mentor.photo_url ? (
              <Image source={{ uri: mentor.photo_url }} style={styles.avatar} />
            ) : (
              <View style={[styles.avatar, styles.avatarPlaceholder]}>
                <Text style={styles.avatarText}>
                  {mentor.title.charAt(0).toUpperCase()}
                </Text>
              </View>
            )}

            <View style={styles.nameRow}>
              <Text style={styles.title}>{mentor.title}</Text>
              {mentor.is_verified && (
                <MaterialCommunityIcons
                  name="check-decagram"
                  size={24}
                  color="#4CAF50"
                />
              )}
            </View>

            <View style={styles.ratingRow}>
              <MaterialCommunityIcons name="star" size={20} color="#FFD700" />
              <Text style={styles.rating}>
                {parseFloat(mentor.rating || "0").toFixed(1)}
              </Text>
              <Text style={styles.reviewCount}>
                ({mentor.total_sessions} sessions)
              </Text>
            </View>

            {mentor.education && (
              <View style={styles.educationRow}>
                <MaterialCommunityIcons
                  name="school"
                  size={18}
                  color={colors.textSecondary}
                />
                <Text style={styles.education}>{mentor.education}</Text>
              </View>
            )}
          </View>
        </LiquidGlassCard>

        {/* Bio */}
        <LiquidGlassCard
          variant="default"
          intensity="light"
          style={styles.sectionCard}
        >
          <Text style={styles.sectionTitle}>About</Text>
          <Text style={styles.bio}>{mentor.bio}</Text>
        </LiquidGlassCard>

        {/* Expertise */}
        {mentor.expertise_areas.length > 0 && (
          <LiquidGlassCard
            variant="default"
            intensity="light"
            style={styles.sectionCard}
          >
            <Text style={styles.sectionTitle}>Expertise</Text>
            <View style={styles.expertiseContainer}>
              {mentor.expertise_areas.map((area, index) => (
                <View key={index} style={styles.expertiseChip}>
                  <Text style={styles.expertiseText}>{area}</Text>
                </View>
              ))}
            </View>
          </LiquidGlassCard>
        )}

        {/* Session Info */}
        <LiquidGlassCard
          variant="default"
          intensity="light"
          style={styles.sectionCard}
        >
          <Text style={styles.sectionTitle}>Session Details</Text>

          <View style={styles.infoRow}>
            <MaterialCommunityIcons
              name="clock-outline"
              size={20}
              color={colors.textSecondary}
            />
            <Text style={styles.infoLabel}>Duration:</Text>
            <Text style={styles.infoValue}>15, 30, 45, or 60 minutes</Text>
          </View>

          <View style={styles.infoRow}>
            <MaterialCommunityIcons
              name="video-outline"
              size={20}
              color={colors.textSecondary}
            />
            <Text style={styles.infoLabel}>Platform:</Text>
            <Text style={styles.infoValue}>
              {mentor.meeting_link ? "Video Call" : "To be confirmed"}
            </Text>
          </View>

          <View style={styles.infoRow}>
            <MaterialCommunityIcons
              name="cash"
              size={20}
              color={colors.textSecondary}
            />
            <Text style={styles.infoLabel}>Rate:</Text>
            <Text style={styles.infoValue}>
              {mentor.hourly_rate_credits} credits/hour
            </Text>
          </View>

          <View style={styles.infoRow}>
            <MaterialCommunityIcons
              name="earth"
              size={20}
              color={colors.textSecondary}
            />
            <Text style={styles.infoLabel}>Timezone:</Text>
            <Text style={styles.infoValue}>{mentor.timezone}</Text>
          </View>
        </LiquidGlassCard>

        {/* Availability */}
        <LiquidGlassCard
          variant="default"
          intensity="light"
          style={styles.sectionCard}
        >
          <Text style={styles.sectionTitle}>Available Times</Text>

          {slots.length === 0 ? (
            <View style={styles.noSlots}>
              <MaterialCommunityIcons
                name="calendar-blank"
                size={48}
                color={colors.textSecondary}
              />
              <Text style={styles.noSlotsText}>
                No available slots this week
              </Text>
              <Text style={styles.noSlotsSubtext}>Check back later</Text>
            </View>
          ) : (
            <View style={styles.slotsContainer}>
              {dates.slice(0, 5).map((dateKey) => (
                <View key={dateKey} style={styles.dateGroup}>
                  <Text style={styles.dateHeader}>
                    {new Date(dateKey).toLocaleDateString("en-US", {
                      weekday: "long",
                      month: "short",
                      day: "numeric",
                    })}
                  </Text>
                  {groupedSlots[dateKey].map((slot, index) => (
                    <TouchableOpacity
                      key={index}
                      style={styles.slotItem}
                      onPress={() => handleSelectSlot(slot)}
                    >
                      <Text style={styles.slotTime}>
                        {new Date(slot.start_at_utc).toLocaleTimeString(
                          "en-US",
                          {
                            hour: "numeric",
                            minute: "2-digit",
                          },
                        )}
                      </Text>
                      <Text style={styles.slotDuration}>
                        {slot.duration_minutes} min
                      </Text>
                      <MaterialCommunityIcons
                        name="chevron-right"
                        size={20}
                        color={colors.primary}
                      />
                    </TouchableOpacity>
                  ))}
                </View>
              ))}
            </View>
          )}
        </LiquidGlassCard>

        {/* Book Button */}
        {slots.length > 0 && bookingStep === "view" && (
          <TouchableOpacity
            style={styles.bookButton}
            onPress={handleStartBooking}
          >
            <Text style={styles.bookButtonText}>Book a Session</Text>
          </TouchableOpacity>
        )}

        <View style={styles.bottomPadding} />
      </ScrollView>

      {/* Booking Modal */}
      <Modal
        visible={bookingStep === "confirm" || bookingStep === "success"}
        animationType="slide"
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={handleCloseBooking}>
              <MaterialCommunityIcons
                name="close"
                size={24}
                color={colors.text}
              />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>
              {bookingStep === "success"
                ? "Booking Confirmed!"
                : "Book Session"}
            </Text>
            <View style={styles.placeholder} />
          </View>

          <ScrollView style={styles.modalContent}>
            {bookingStep === "confirm" && selectedSlot && (
              <LiquidGlassCard
                variant="default"
                intensity="medium"
                style={styles.confirmCard}
              >
                <Text style={styles.confirmSectionTitle}>Session Details</Text>

                <View style={styles.confirmRow}>
                  <Text style={styles.confirmLabel}>Date & Time:</Text>
                  <Text style={styles.confirmValue}>
                    {formatDateTime(selectedSlot.start_at_utc)}
                  </Text>
                </View>

                <View style={styles.confirmRow}>
                  <Text style={styles.confirmLabel}>Duration:</Text>
                  <Text style={styles.confirmValue}>
                    {selectedSlot.duration_minutes} minutes
                  </Text>
                </View>

                <View style={styles.confirmRow}>
                  <Text style={styles.confirmLabel}>Mentor:</Text>
                  <Text style={styles.confirmValue}>{mentor.title}</Text>
                </View>

                <View style={styles.formSection}>
                  <Text style={styles.formLabel}>Topic *</Text>
                  <TextInput
                    style={styles.textInput}
                    placeholder="e.g., Essay Review, Plan Validation"
                    placeholderTextColor={colors.textSecondary}
                    value={sessionTopic}
                    onChangeText={setSessionTopic}
                  />
                </View>

                <View style={styles.formSection}>
                  <Text style={styles.formLabel}>Notes (optional)</Text>
                  <TextInput
                    style={[styles.textInput, styles.textArea]}
                    placeholder="What would you like to discuss?"
                    placeholderTextColor={colors.textSecondary}
                    value={sessionNotes}
                    onChangeText={setSessionNotes}
                    multiline
                    numberOfLines={4}
                    textAlignVertical="top"
                  />
                </View>

                <TouchableOpacity
                  style={[
                    styles.confirmButton,
                    bookingLoading && styles.confirmButtonDisabled,
                  ]}
                  onPress={handleConfirmBooking}
                  disabled={bookingLoading}
                >
                  {bookingLoading ? (
                    <ActivityIndicator color={colors.bg} />
                  ) : (
                    <Text style={styles.confirmButtonText}>
                      Confirm Booking
                    </Text>
                  )}
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.cancelButton}
                  onPress={handleCloseBooking}
                >
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
              </LiquidGlassCard>
            )}

            {bookingStep === "success" && (
              <LiquidGlassCard
                variant="default"
                intensity="medium"
                style={styles.successCard}
              >
                <View style={styles.successIcon}>
                  <MaterialCommunityIcons
                    name="check"
                    size={48}
                    color="#4CAF50"
                  />
                </View>
                <Text style={styles.successTitle}>Booking Request Sent!</Text>
                <Text style={styles.successText}>
                  Your session request has been sent to {mentor.title}. They
                  will review and confirm your booking.
                </Text>
                <Text style={styles.successNote}>
                  You'll receive a notification once the mentor confirms your
                  session.
                </Text>

                <TouchableOpacity
                  style={styles.doneButton}
                  onPress={handleCloseBooking}
                >
                  <Text style={styles.doneButtonText}>Done</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.viewBookingsButton}
                  onPress={() => {
                    handleCloseBooking();
                    router.push("/mentorship-bookings");
                  }}
                >
                  <Text style={styles.viewBookingsButtonText}>
                    View My Bookings
                  </Text>
                </TouchableOpacity>
              </LiquidGlassCard>
            )}
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
}

import { TextInput } from "react-native";

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.md,
    paddingTop: 60,
    paddingBottom: spacing.md,
  },
  backButton: {
    padding: spacing.xs,
  },
  headerTitle: {
    ...typography.titleLarge,
    color: colors.text,
  },
  placeholder: {
    width: 32,
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
  errorContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: spacing.xl,
  },
  errorText: {
    ...typography.titleLarge,
    color: colors.text,
    marginTop: spacing.lg,
  },
  scrollView: {
    flex: 1,
  },
  profileCard: {
    marginHorizontal: spacing.md,
    marginBottom: spacing.md,
  },
  profileContent: {
    alignItems: "center",
    padding: spacing.xl,
  },
  avatar: {
    width: 96,
    height: 96,
    borderRadius: 48,
    marginBottom: spacing.md,
  },
  avatarPlaceholder: {
    backgroundColor: colors.liquidGlass.overlayLight,
    justifyContent: "center",
    alignItems: "center",
  },
  avatarText: {
    ...typography.displayLarge,
    color: colors.primary,
  },
  nameRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.sm,
  },
  title: {
    ...typography.headlineMedium,
    color: colors.text,
    marginRight: spacing.xs,
  },
  ratingRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.sm,
  },
  rating: {
    ...typography.labelLarge,
    color: colors.text,
    marginLeft: spacing.xs,
  },
  reviewCount: {
    ...typography.caption,
    color: colors.textSecondary,
    marginLeft: spacing.xs,
  },
  educationRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  education: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    marginLeft: spacing.sm,
  },
  sectionCard: {
    marginHorizontal: spacing.md,
    marginBottom: spacing.md,
    padding: spacing.lg,
  },
  sectionTitle: {
    ...typography.titleMedium,
    color: colors.text,
    marginBottom: spacing.md,
  },
  bio: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    lineHeight: 22,
  },
  expertiseContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
  },
  expertiseChip: {
    backgroundColor: colors.liquidGlass.overlayLight,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
    marginRight: spacing.sm,
    marginBottom: spacing.sm,
  },
  expertiseText: {
    ...typography.labelMedium,
    color: colors.primary,
    fontWeight: "600",
  },
  infoRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.md,
  },
  infoLabel: {
    ...typography.labelMedium,
    color: colors.text,
    marginLeft: spacing.sm,
    marginRight: spacing.xs,
  },
  infoValue: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
  },
  noSlots: {
    alignItems: "center",
    paddingVertical: spacing.xxl,
  },
  noSlotsText: {
    ...typography.titleMedium,
    color: colors.textSecondary,
    marginTop: spacing.md,
  },
  noSlotsSubtext: {
    ...typography.bodyMedium,
    color: colors.textTertiary,
    marginTop: spacing.xs,
  },
  slotsContainer: {
    gap: spacing.lg,
  },
  dateGroup: {
    marginBottom: spacing.md,
  },
  dateHeader: {
    ...typography.labelLarge,
    color: colors.text,
    marginBottom: spacing.sm,
  },
  slotItem: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.liquidGlass.overlayMedium,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.md,
    marginBottom: spacing.sm,
  },
  slotTime: {
    ...typography.labelLarge,
    color: colors.text,
    marginRight: spacing.sm,
  },
  slotDuration: {
    ...typography.caption,
    color: colors.textSecondary,
    marginRight: "auto",
  },
  bookButton: {
    backgroundColor: colors.primary,
    marginHorizontal: spacing.md,
    marginBottom: spacing.md,
    paddingVertical: spacing.lg,
    borderRadius: borderRadius.lg,
    alignItems: "center",
  },
  bookButtonText: {
    ...typography.labelLarge,
    color: colors.bg,
    fontWeight: "700",
  },
  bottomPadding: {
    height: spacing.xl,
  },
  // Modal
  modalContainer: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  modalHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.md,
    paddingTop: 60,
    paddingBottom: spacing.md,
  },
  modalTitle: {
    ...typography.titleLarge,
    color: colors.text,
  },
  modalContent: {
    flex: 1,
    padding: spacing.md,
  },
  confirmCard: {
    padding: spacing.xl,
  },
  confirmSectionTitle: {
    ...typography.titleMedium,
    color: colors.text,
    marginBottom: spacing.lg,
  },
  confirmRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: spacing.md,
  },
  confirmLabel: {
    ...typography.labelMedium,
    color: colors.text,
  },
  confirmValue: {
    ...typography.bodyMedium,
    color: colors.text,
    textAlign: "right",
    maxWidth: "60%",
  },
  formSection: {
    marginTop: spacing.md,
    marginBottom: spacing.sm,
  },
  formLabel: {
    ...typography.labelMedium,
    color: colors.text,
    marginBottom: spacing.sm,
  },
  textInput: {
    backgroundColor: colors.liquidGlass.overlayMedium,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    ...typography.bodyMedium,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.liquidGlass.borderLight,
  },
  textArea: {
    minHeight: 80,
  },
  confirmButton: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.lg,
    borderRadius: borderRadius.lg,
    alignItems: "center",
    marginTop: spacing.xl,
  },
  confirmButtonDisabled: {
    backgroundColor: colors.textSecondary,
  },
  confirmButtonText: {
    ...typography.labelLarge,
    color: colors.bg,
    fontWeight: "700",
  },
  cancelButton: {
    paddingVertical: spacing.lg,
    alignItems: "center",
    marginTop: spacing.sm,
  },
  cancelButtonText: {
    ...typography.labelMedium,
    color: colors.textSecondary,
  },
  successCard: {
    padding: spacing.xl,
    alignItems: "center",
  },
  successIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: "rgba(76, 175, 80, 0.2)",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.lg,
  },
  successTitle: {
    ...typography.titleLarge,
    color: colors.text,
    marginBottom: spacing.sm,
    textAlign: "center",
    fontWeight: "700",
  },
  successText: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    textAlign: "center",
    lineHeight: 22,
  },
  successNote: {
    ...typography.caption,
    color: colors.textTertiary,
    textAlign: "center",
    marginTop: spacing.sm,
  },
  doneButton: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.lg,
    paddingHorizontal: spacing.xl,
    borderRadius: borderRadius.lg,
    marginTop: spacing.xl,
    width: "100%",
    alignItems: "center",
  },
  doneButtonText: {
    ...typography.labelLarge,
    color: colors.bg,
    fontWeight: "700",
  },
  viewBookingsButton: {
    marginTop: spacing.md,
    width: "100%",
    alignItems: "center",
  },
  viewBookingsButtonText: {
    ...typography.labelMedium,
    color: colors.primary,
  },
});
