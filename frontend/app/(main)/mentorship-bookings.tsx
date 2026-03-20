/**
 * My Bookings Screen - Redesigned
 *
 * View and manage mentorship session bookings with tab-based filtering
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
  RefreshControl,
} from "react-native";
import { useRouter } from "expo-router";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import * as WebBrowser from "expo-web-browser";
import { getMyBookings, cancelBooking, rateBooking } from "@/services/mentorship";
import { MentorBooking } from "@/types/mentor";
import { colors, spacing, borderRadius, typography } from "@/theme";
import LiquidGlassCard from "@/components/LiquidGlassCard";

type BookingTab = "upcoming" | "past" | "cancelled";

export default function MentorshipBookingsScreen() {
  const router = useRouter();
  const [bookings, setBookings] = useState<MentorBooking[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<BookingTab>("upcoming");

  useEffect(() => {
    loadBookings();
  }, []);

  const loadBookings = async () => {
    try {
      setLoading(true);
      const data = await getMyBookings();
      setBookings(data);
    } catch (error) {
      console.error("Error loading bookings:", error);
      Alert.alert("Error", "Failed to load bookings");
      setBookings([]);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadBookings();
    setRefreshing(false);
  };

  const filterBookings = (tab: BookingTab): MentorBooking[] => {
    const now = new Date();

    switch (tab) {
      case "upcoming":
        return bookings.filter(
          (b) => b.status === "confirmed" && new Date(b.start_at_utc) > now
        );
      case "past":
        return bookings.filter(
          (b) =>
            b.status === "completed" ||
            (b.status === "confirmed" && new Date(b.start_at_utc) <= now)
        );
      case "cancelled":
        return bookings.filter((b) => b.status === "cancelled");
      default:
        return [];
    }
  };

  const handleCancelBooking = async (bookingId: number) => {
    Alert.alert(
      "Cancel Booking",
      "Are you sure you want to cancel this session?",
      [
        { text: "No", style: "cancel" },
        {
          text: "Yes, Cancel",
          style: "destructive",
          onPress: async () => {
            try {
              await cancelBooking(bookingId);
              await loadBookings();
              Alert.alert("Success", "Booking has been cancelled.");
            } catch (error: any) {
              Alert.alert("Error", error.message || "Failed to cancel booking");
            }
          },
        },
      ]
    );
  };

  const handleJoinMeeting = async (booking: MentorBooking) => {
    if (booking.meeting_url) {
      await WebBrowser.openBrowserAsync(booking.meeting_url);
    } else {
      Alert.alert(
        "No Meeting Link",
        "Please contact your mentor for the meeting link."
      );
    }
  };

  const handleRateSession = (bookingId: number) => {
    // TODO: Implement rating modal
    Alert.alert("Coming Soon", "Rating feature will be available soon!");
  };

  const filteredBookings = filterBookings(activeTab);

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <MaterialCommunityIcons name="arrow-left" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>My Sessions</Text>
        <TouchableOpacity
          style={styles.calendarButton}
          onPress={() => router.push("/(main)/calendar" as any)}
        >
          <MaterialCommunityIcons name="calendar" size={24} color={colors.primary} />
        </TouchableOpacity>
      </View>

      {/* Tab Bar */}
      <View style={styles.tabBar}>
        {(["upcoming", "past", "cancelled"] as BookingTab[]).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.activeTab]}
            onPress={() => setActiveTab(tab)}
          >
            <Text
              style={[styles.tabText, activeTab === tab && styles.activeTabText]}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </Text>
            {filterBookings(tab).length > 0 && (
              <View style={styles.tabBadge}>
                <Text style={styles.tabBadgeText}>
                  {filterBookings(tab).length}
                </Text>
              </View>
            )}
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading sessions...</Text>
        </View>
      ) : filteredBookings.length === 0 ? (
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        >
          <EmptyState
            icon={activeTab === "upcoming" ? "calendar-blank" : "history"}
            title={
              activeTab === "upcoming"
                ? "No upcoming sessions"
                : `No ${activeTab} sessions`
            }
            description={
              activeTab === "upcoming"
                ? "Book a session with a mentor to get started"
                : `Your ${activeTab} sessions will appear here`
            }
            actionLabel={activeTab === "upcoming" ? "Browse Mentors" : undefined}
            onAction={() => router.push("/(main)/mentors" as any)}
          />
        </ScrollView>
      ) : (
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        >
          {filteredBookings.map((booking) => (
            <BookingCard
              key={booking.id}
              booking={booking}
              onCancel={() => handleCancelBooking(booking.id)}
              onJoin={() => handleJoinMeeting(booking)}
              onRate={() => handleRateSession(booking.id)}
            />
          ))}
        </ScrollView>
      )}
    </View>
  );
}

// Booking Card Component
interface BookingCardProps {
  booking: MentorBooking;
  onCancel: () => void;
  onJoin: () => void;
  onRate: () => void;
}

function BookingCard({ booking, onCancel, onJoin, onRate }: BookingCardProps) {
  const isUpcoming =
    booking.status === "confirmed" && new Date(booking.start_at_utc) > new Date();

  const canJoin =
    isUpcoming &&
    new Date(booking.start_at_utc) <=
      new Date(Date.now() + 15 * 60 * 1000); // 15 min before

  return (
    <LiquidGlassCard variant="default" intensity="medium" style={styles.bookingCard}>
      {/* Status Badge */}
      <View
        style={[
          styles.statusBadge,
          { backgroundColor: getStatusColor(booking.status) },
        ]}
      >
        <MaterialCommunityIcons
          name={getStatusIcon(booking.status)}
          size={12}
          color="#fff"
        />
        <Text style={styles.statusText}>{getStatusLabel(booking.status)}</Text>
      </View>

      {/* Mentor Info */}
      <View style={styles.mentorInfo}>
        <View style={styles.mentorAvatar}>
          <MaterialCommunityIcons
            name="account-tie"
            size={32}
            color={colors.primary}
          />
        </View>
        <View style={styles.mentorDetails}>
          <Text style={styles.mentorTitle}>
            {booking.mentor_title || "Mentor Session"}
          </Text>
          {booking.topic && <Text style={styles.topic}>{booking.topic}</Text>}
        </View>
      </View>

      {/* Date & Time */}
      <View style={styles.dateTimeSection}>
        <View style={styles.dateTimeRow}>
          <MaterialCommunityIcons
            name="calendar"
            size={20}
            color={colors.textSecondary}
          />
          <Text style={styles.dateTime}>{formatDateTime(booking.start_at_utc)}</Text>
        </View>
        <View style={styles.dateTimeRow}>
          <MaterialCommunityIcons
            name="clock"
            size={20}
            color={colors.textSecondary}
          />
          <Text style={styles.dateTime}>
            {booking.duration_minutes} minutes
          </Text>
        </View>
      </View>

      {/* Notes */}
      {booking.student_notes && (
        <View style={styles.notesSection}>
          <Text style={styles.notesLabel}>Your Notes:</Text>
          <Text style={styles.notesText}>{booking.student_notes}</Text>
        </View>
      )}

      {/* Actions */}
      {isUpcoming && (
        <View style={styles.actionsRow}>
          <TouchableOpacity
            style={[styles.actionButton, styles.joinButton]}
            onPress={onJoin}
          >
            <MaterialCommunityIcons name="video" size={18} color="#fff" />
            <Text style={styles.joinButtonText}>Join Meeting</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionButton, styles.cancelButton]}
            onPress={onCancel}
          >
            <MaterialCommunityIcons name="close" size={18} color={colors.error} />
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      )}

      {booking.status === "requested" && (
        <View style={styles.pendingBanner}>
          <MaterialCommunityIcons name="clock-outline" size={16} color={colors.warning} />
          <Text style={styles.pendingText}>
            Waiting for mentor confirmation...
          </Text>
        </View>
      )}

      {booking.status === "completed" && !booking.rating && (
        <TouchableOpacity style={styles.rateButton} onPress={onRate}>
          <MaterialCommunityIcons name="star" size={18} color={colors.primary} />
          <Text style={styles.rateButtonText}>Rate Session</Text>
        </TouchableOpacity>
      )}
    </LiquidGlassCard>
  );
}

// Empty State Component
interface EmptyStateProps {
  icon: string;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <View style={styles.emptyContainer}>
      <MaterialCommunityIcons name={icon as any} size={64} color={colors.textSecondary} />
      <Text style={styles.emptyTitle}>{title}</Text>
      <Text style={styles.emptyText}>{description}</Text>
      {actionLabel && onAction && (
        <TouchableOpacity style={styles.emptyButton} onPress={onAction}>
          <Text style={styles.emptyButtonText}>{actionLabel}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

// Helper Functions
function getStatusColor(status: string): string {
  switch (status) {
    case "confirmed":
      return "#4CAF50";
    case "requested":
      return "#FFA726";
    case "completed":
      return "#2196F3";
    case "cancelled":
      return "#9E9E9E";
    default:
      return "#9E9E9E";
  }
}

function getStatusIcon(status: string): string {
  switch (status) {
    case "confirmed":
      return "check-circle";
    case "requested":
      return "clock-outline";
    case "completed":
      return "check-circle-outline";
    case "cancelled":
      return "cancel";
    default:
      return "help-circle";
  }
}

function getStatusLabel(status: string): string {
  switch (status) {
    case "confirmed":
      return "Confirmed";
    case "requested":
      return "Pending";
    case "completed":
      return "Completed";
    case "cancelled":
      return "Cancelled";
    default:
      return status;
  }
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  });
}

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
    paddingTop: 55,
    paddingBottom: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.liquidGlass.borderLight,
  },
  backButton: {
    padding: spacing.xs,
  },
  headerTitle: {
    ...typography.titleLarge,
    color: colors.text,
  },
  calendarButton: {
    padding: spacing.xs,
  },
  tabBar: {
    flexDirection: "row",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    gap: spacing.sm,
    backgroundColor: colors.bg,
  },
  tab: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: borderRadius.md,
    backgroundColor: colors.liquidGlass.overlayLight,
    gap: spacing.xs,
  },
  activeTab: {
    backgroundColor: colors.primary + "20",
  },
  tabText: {
    ...typography.labelMedium,
    color: colors.textSecondary,
  },
  activeTabText: {
    color: colors.primary,
    fontWeight: "700",
  },
  tabBadge: {
    backgroundColor: colors.primary,
    borderRadius: 10,
    paddingHorizontal: 6,
    paddingVertical: 2,
    minWidth: 20,
    alignItems: "center",
  },
  tabBadgeText: {
    ...typography.caption,
    color: "#fff",
    fontWeight: "700",
    fontSize: 10,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  loadingText: {
    ...typography.bodyLarge,
    color: colors.textSecondary,
    marginTop: spacing.md,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: spacing.md,
  },
  bookingCard: {
    marginBottom: spacing.md,
    padding: spacing.lg,
  },
  statusBadge: {
    alignSelf: "flex-start",
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
    marginBottom: spacing.md,
  },
  statusText: {
    ...typography.caption,
    color: colors.bg,
    fontWeight: "700",
    textTransform: "uppercase",
    fontSize: 10,
  },
  mentorInfo: {
    flexDirection: "row",
    marginBottom: spacing.md,
  },
  mentorAvatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary + "20",
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.md,
  },
  mentorDetails: {
    flex: 1,
    justifyContent: "center",
  },
  mentorTitle: {
    ...typography.titleMedium,
    color: colors.text,
    marginBottom: spacing.xs,
  },
  topic: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
  },
  dateTimeSection: {
    backgroundColor: colors.liquidGlass.overlayLight,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginBottom: spacing.md,
  },
  dateTimeRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    marginBottom: spacing.xs,
  },
  dateTime: {
    ...typography.bodyMedium,
    color: colors.text,
  },
  notesSection: {
    backgroundColor: colors.liquidGlass.overlayLight,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginBottom: spacing.md,
  },
  notesLabel: {
    ...typography.labelMedium,
    color: colors.text,
    marginBottom: spacing.xs,
  },
  notesText: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
  },
  actionsRow: {
    flexDirection: "row",
    gap: spacing.sm,
  },
  actionButton: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
  },
  joinButton: {
    backgroundColor: colors.primary,
  },
  joinButtonText: {
    ...typography.labelMedium,
    color: "#fff",
    fontWeight: "700",
  },
  cancelButton: {
    backgroundColor: colors.error + "15",
    borderWidth: 1,
    borderColor: colors.error + "40",
  },
  cancelButtonText: {
    ...typography.labelMedium,
    color: colors.error,
  },
  pendingBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    padding: spacing.md,
    backgroundColor: colors.warning + "15",
    borderRadius: borderRadius.md,
  },
  pendingText: {
    ...typography.caption,
    color: colors.warning,
    fontStyle: "italic",
  },
  rateButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
    paddingVertical: spacing.md,
    backgroundColor: colors.primary + "20",
    borderRadius: borderRadius.md,
  },
  rateButtonText: {
    ...typography.labelMedium,
    color: colors.primary,
    fontWeight: "600",
  },
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.xxl * 2,
  },
  emptyTitle: {
    ...typography.titleLarge,
    color: colors.text,
    marginTop: spacing.lg,
  },
  emptyText: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    marginTop: spacing.sm,
    textAlign: "center",
  },
  emptyButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
    marginTop: spacing.lg,
  },
  emptyButtonText: {
    ...typography.labelMedium,
    color: colors.bg,
  },
});
