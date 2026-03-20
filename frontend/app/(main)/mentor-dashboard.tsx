/**
 * Mentor Dashboard Screen
 *
 * Central hub for mentors to manage their profile, availability, bookings, and reviews
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
  Modal,
  TextInput,
} from "react-native";
import { useRouter } from "expo-router";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import {
  getMyMentorProfile,
  getMyAvailabilityRules,
  createAvailabilityRule,
  getMyBookings,
  confirmBooking,
  getMyReviews,
} from "@/services/mentorship";
import { colors, spacing, borderRadius, typography } from "@/theme";
import LiquidGlassCard from "@/components/LiquidGlassCard";

export default function MentorDashboardScreen() {
  const router = useRouter();

  // Profile & Stats
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Availability
  const [availabilityRules, setAvailabilityRules] = useState<any[]>([]);
  const [showAvailabilityModal, setShowAvailabilityModal] = useState(false);
  const [selectedDay, setSelectedDay] = useState<number>(1);
  const [startTime, setStartTime] = useState<string>("09:00");
  const [endTime, setEndTime] = useState<string>("17:00");

  // Bookings
  const [bookings, setBookings] = useState<any[]>([]);
  const [pendingBookings, setPendingBookings] = useState<any[]>([]);

  // Reviews
  const [reviews, setReviews] = useState<any[]>([]);
  const [pendingReviews, setPendingReviews] = useState<any[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);

      // Load profile
      const profileData = await getMyMentorProfile();
      setProfile(profileData);

      // Load availability
      const availabilityData = await getMyAvailabilityRules();
      setAvailabilityRules(availabilityData);

      // Load bookings
      const bookingsData = await getMyBookings();
      setBookings(bookingsData);
      setPendingBookings(
        bookingsData.filter((b: any) => b.status === "requested"),
      );

      // Load reviews
      const reviewsData = await getMyReviews();
      setReviews(reviewsData);
      setPendingReviews(reviewsData.filter((r: any) => r.status === "pending"));
    } catch (error: any) {
      console.error("Error loading mentor data:", error);
      Alert.alert("Error", "Failed to load mentor dashboard");
    } finally {
      setLoading(false);
    }
  };

  const handleAddAvailability = async () => {
    try {
      // Convert time to minutes
      const [startHour, startMin] = startTime.split(":").map(Number);
      const [endHour, endMin] = endTime.split(":").map(Number);
      const startMinute = startHour * 60 + startMin;
      const endMinute = endHour * 60 + endMin;

      if (startMinute >= endMinute) {
        Alert.alert("Error", "End time must be after start time");
        return;
      }

      await createAvailabilityRule({
        day_of_week: selectedDay,
        start_minute: startMinute,
        end_minute: endMinute,
      });

      setShowAvailabilityModal(false);
      await loadData();
      Alert.alert("Success", "Availability added!");
    } catch (error: any) {
      Alert.alert("Error", error.message || "Failed to add availability");
    }
  };

  const handleConfirmBooking = async (bookingId: number) => {
    Alert.alert("Confirm Booking", "Accept this booking request?", [
      { text: "No", style: "cancel" },
      {
        text: "Yes, Accept",
        onPress: async () => {
          try {
            await confirmBooking(bookingId);
            await loadData();
            Alert.alert("Success", "Booking confirmed!");
          } catch (error: any) {
            Alert.alert("Error", error.message || "Failed to confirm booking");
          }
        },
      },
    ]);
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  const getDayName = (dayOfWeek: number) => {
    const days = [
      "Monday",
      "Tuesday",
      "Wednesday",
      "Thursday",
      "Friday",
      "Saturday",
      "Sunday",
    ];
    return days[dayOfWeek];
  };

  const formatMinutes = (minutes: number) => {
    const hour = Math.floor(minutes / 60);
    const min = minutes % 60;
    return `${hour.toString().padStart(2, "0")}:${min.toString().padStart(2, "0")}`;
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.loadingText}>Loading Mentor Dashboard...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => router.replace("/(main)/profile")}
          style={styles.backButton}
        >
          <MaterialCommunityIcons
            name="arrow-left"
            size={24}
            color={colors.text}
          />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Mentor Dashboard</Text>
        <TouchableOpacity
          onPress={() => router.push("/mentor-profile")}
          style={styles.editButton}
        >
          <MaterialCommunityIcons
            name="pencil"
            size={20}
            color={colors.primary}
          />
          <Text style={styles.editButtonText}>Edit Profile</Text>
        </TouchableOpacity>
      </View>

      {/* Stats Card */}
      <LiquidGlassCard style={styles.statsCard}>
        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{profile?.total_sessions || 0}</Text>
            <Text style={styles.statLabel}>Sessions</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statValue}>
              {parseFloat(profile?.rating || "0").toFixed(1)}
            </Text>
            <Text style={styles.statLabel}>Rating</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{pendingBookings.length}</Text>
            <Text style={styles.statLabel}>Pending</Text>
          </View>
        </View>
      </LiquidGlassCard>

      {/* Pending Bookings */}
      {pendingBookings.length > 0 && (
        <LiquidGlassCard style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <MaterialCommunityIcons
              name="calendar-clock"
              size={24}
              color={colors.warning}
            />
            <Text style={styles.sectionTitle}>
              Pending Bookings ({pendingBookings.length})
            </Text>
          </View>
          {pendingBookings.map((booking) => (
            <View key={booking.id} style={styles.bookingItem}>
              <View style={styles.bookingInfo}>
                <Text style={styles.bookingStudent}>
                  {booking.student_email}
                </Text>
                <Text style={styles.bookingTime}>
                  {formatDateTime(booking.start_at_utc)}
                </Text>
                <Text style={styles.bookingTopic}>
                  {booking.topic || "No topic specified"}
                </Text>
              </View>
              <TouchableOpacity
                style={styles.confirmButton}
                onPress={() => handleConfirmBooking(booking.id)}
              >
                <MaterialCommunityIcons
                  name="check"
                  size={20}
                  color={colors.bg}
                />
                <Text style={styles.confirmButtonText}>Accept</Text>
              </TouchableOpacity>
            </View>
          ))}
        </LiquidGlassCard>
      )}

      {/* Availability */}
      <LiquidGlassCard style={styles.sectionCard}>
        <View style={styles.sectionHeader}>
          <MaterialCommunityIcons
            name="calendar-clock"
            size={24}
            color={colors.primary}
          />
          <Text style={styles.sectionTitle}>My Availability</Text>
          <TouchableOpacity
            onPress={() => setShowAvailabilityModal(true)}
            style={styles.addButton}
          >
            <MaterialCommunityIcons
              name="plus"
              size={20}
              color={colors.primary}
            />
          </TouchableOpacity>
        </View>
        {availabilityRules.length === 0 ? (
          <Text style={styles.emptyText}>
            No availability set. Add your hours!
          </Text>
        ) : (
          availabilityRules.map((rule) => (
            <View key={rule.id} style={styles.availabilityItem}>
              <Text style={styles.availabilityDay}>
                {getDayName(rule.day_of_week)}
              </Text>
              <Text style={styles.availabilityTime}>
                {formatMinutes(rule.start_minute)} -{" "}
                {formatMinutes(rule.end_minute)}
              </Text>
            </View>
          ))
        )}
      </LiquidGlassCard>

      {/* All Bookings */}
      <LiquidGlassCard style={styles.sectionCard}>
        <View style={styles.sectionHeader}>
          <MaterialCommunityIcons
            name="calendar"
            size={24}
            color={colors.textSecondary}
          />
          <Text style={styles.sectionTitle}>
            All Bookings ({bookings.length})
          </Text>
        </View>
        {bookings.length === 0 ? (
          <Text style={styles.emptyText}>No bookings yet</Text>
        ) : (
          bookings.map((booking) => (
            <View key={booking.id} style={styles.bookingItem}>
              <View style={styles.bookingInfo}>
                <Text style={styles.bookingStudent}>
                  {booking.student_email}
                </Text>
                <Text style={styles.bookingTime}>
                  {formatDateTime(booking.start_at_utc)}
                </Text>
              </View>
              <View
                style={[
                  styles.statusBadge,
                  {
                    backgroundColor:
                      booking.status === "confirmed"
                        ? colors.success
                        : colors.warning,
                  },
                ]}
              >
                <Text style={styles.statusText}>{booking.status}</Text>
              </View>
            </View>
          ))
        )}
      </LiquidGlassCard>

      {/* Availability Modal */}
      <Modal
        visible={showAvailabilityModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowAvailabilityModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Add Availability</Text>

            <Text style={styles.label}>Day of Week</Text>
            <View style={styles.daySelector}>
              {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(
                (day, index) => (
                  <TouchableOpacity
                    key={day}
                    style={[
                      styles.dayButton,
                      selectedDay === index && styles.dayButtonSelected,
                    ]}
                    onPress={() => setSelectedDay(index)}
                  >
                    <Text
                      style={[
                        styles.dayButtonText,
                        selectedDay === index && styles.dayButtonTextSelected,
                      ]}
                    >
                      {day}
                    </Text>
                  </TouchableOpacity>
                ),
              )}
            </View>

            <Text style={styles.label}>Start Time</Text>
            <TextInput
              style={styles.input}
              value={startTime}
              onChangeText={setStartTime}
              placeholder="09:00"
            />

            <Text style={styles.label}>End Time</Text>
            <TextInput
              style={styles.input}
              value={endTime}
              onChangeText={setEndTime}
              placeholder="17:00"
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => setShowAvailabilityModal(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.saveButton]}
                onPress={handleAddAvailability}
              >
                <Text style={styles.saveButtonText}>Add</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </ScrollView>
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
    backgroundColor: colors.bg,
  },
  loadingText: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    marginTop: spacing.md,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.lg,
    gap: spacing.sm,
  },
  backButton: {
    padding: spacing.xs,
  },
  headerTitle: {
    ...typography.titleLarge,
    color: colors.text,
    flex: 1,
  },
  editButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
  },
  editButtonText: {
    ...typography.labelMedium,
    color: colors.primary,
  },
  statsCard: {
    marginHorizontal: spacing.lg,
    marginBottom: spacing.md,
  },
  statsRow: {
    flexDirection: "row",
    justifyContent: "space-around",
    alignItems: "center",
    paddingVertical: spacing.lg,
  },
  statItem: {
    alignItems: "center",
  },
  statValue: {
    ...typography.headlineLarge,
    color: colors.text,
    fontWeight: "600",
  },
  statLabel: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  statDivider: {
    width: 1,
    height: 40,
    backgroundColor: colors.liquidGlass.borderLight,
  },
  sectionCard: {
    marginHorizontal: spacing.lg,
    marginBottom: spacing.md,
  },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.md,
    gap: spacing.sm,
  },
  sectionTitle: {
    ...typography.titleMedium,
    color: colors.text,
    flex: 1,
  },
  addButton: {
    padding: spacing.sm,
  },
  emptyText: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    textAlign: "center",
    paddingVertical: spacing.lg,
  },
  bookingItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.liquidGlass.borderLight,
  },
  bookingInfo: {
    flex: 1,
  },
  bookingStudent: {
    ...typography.labelMedium,
    color: colors.text,
  },
  bookingTime: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  bookingTopic: {
    ...typography.bodySmall,
    color: colors.textTertiary,
    marginTop: spacing.xs,
  },
  confirmButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    backgroundColor: colors.success,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.md,
  },
  confirmButtonText: {
    ...typography.labelMedium,
    color: colors.bg,
    fontWeight: "600",
  },
  statusBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
  },
  statusText: {
    ...typography.caption,
    color: colors.bg,
    fontWeight: "600",
    textTransform: "capitalize",
  },
  availabilityItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.liquidGlass.borderLight,
  },
  availabilityDay: {
    ...typography.labelMedium,
    color: colors.text,
  },
  availabilityTime: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
  },
  // Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    alignItems: "center",
  },
  modalContent: {
    backgroundColor: colors.bg,
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
    width: "90%",
    maxWidth: 400,
  },
  modalTitle: {
    ...typography.titleLarge,
    color: colors.text,
    marginBottom: spacing.lg,
  },
  label: {
    ...typography.labelMedium,
    color: colors.text,
    marginBottom: spacing.sm,
    marginTop: spacing.md,
  },
  input: {
    backgroundColor: colors.liquidGlass.overlayMedium,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: 16,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.liquidGlass.borderLight,
  },
  daySelector: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  dayButton: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.md,
    backgroundColor: colors.liquidGlass.overlayMedium,
    borderWidth: 1,
    borderColor: colors.liquidGlass.borderLight,
    minWidth: 50,
    alignItems: "center",
  },
  dayButtonSelected: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  dayButtonText: {
    ...typography.labelSmall,
    color: colors.text,
  },
  dayButtonTextSelected: {
    color: colors.bg,
    fontWeight: "600",
  },
  modalButtons: {
    flexDirection: "row",
    gap: spacing.md,
    marginTop: spacing.xl,
  },
  modalButton: {
    flex: 1,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
    alignItems: "center",
  },
  cancelButton: {
    backgroundColor: colors.liquidGlass.overlayMedium,
  },
  cancelButtonText: {
    ...typography.labelMedium,
    color: colors.text,
  },
  saveButton: {
    backgroundColor: colors.primary,
  },
  saveButtonText: {
    ...typography.labelMedium,
    color: colors.bg,
    fontWeight: "600",
  },
});
