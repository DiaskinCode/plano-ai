/**
 * Mentor Profile Detail Screen (V1)
 *
 * Shows mentor details, availability calendar, and booking options
 */

import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  SafeAreaView,
  Image,
  Alert,
} from "react-native";
import { useRouter, useLocalSearchParams } from "expo-router";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import {
  getMentor,
  getMentorAvailability,
  bookSession,
} from "@/services/mentorship";
import { Mentor, TimeSlot } from "@/types/mentor";

export default function MentorDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const mentorId = parseInt(id);

  const [mentor, setMentor] = useState<Mentor | null>(null);
  const [availability, setAvailability] = useState<TimeSlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingAvailability, setLoadingAvailability] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState(new Date());

  useEffect(() => {
    if (mentorId) {
      loadMentor();
      loadAvailability();
    }
  }, [mentorId, selectedMonth]);

  const loadMentor = async () => {
    try {
      setLoading(true);
      const data = await getMentor(mentorId);
      setMentor(data);
    } catch (error) {
      console.error("Error loading mentor:", error);
      Alert.alert("Error", "Failed to load mentor profile");
    } finally {
      setLoading(false);
    }
  };

  const loadAvailability = async () => {
    try {
      setLoadingAvailability(true);
      const startDate = new Date(selectedMonth);
      startDate.setDate(1); // First day of month
      startDate.setHours(0, 0, 0, 0);

      const endDate = new Date(selectedMonth);
      endDate.setMonth(endDate.getMonth() + 1);
      endDate.setDate(0); // Last day of month

      const data = await getMentorAvailability(
        mentorId,
        startDate.toISOString().split("T")[0],
        endDate.toISOString().split("T")[0],
        60,
      );
      setAvailability(data.slots);
    } catch (error) {
      console.error("Error loading availability:", error);
    } finally {
      setLoadingAvailability(false);
    }
  };

  const handleBookSession = (slot: TimeSlot) => {
    router.push({
      pathname: "/mentor/book",
      params: {
        mentorId: mentorId.toString(),
        startAt: slot.start_at_utc,
        duration: slot.duration_minutes.toString(),
      },
    });
  };

  const formatSlotDate = (slot: TimeSlot) => {
    const date = new Date(slot.start_at_utc);
    return date.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
  };

  const formatSlotTime = (slot: TimeSlot) => {
    const date = new Date(slot.start_at_utc);
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      timeZone: mentor?.timezone || "UTC",
    });
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#0066cc" />
        </View>
      </SafeAreaView>
    );
  }

  if (!mentor) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <MaterialCommunityIcons name="account-off" size={64} color="#ccc" />
          <Text style={styles.errorTitle}>Mentor not found</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.profileSection}>
            {mentor.photo_url ? (
              <Image source={{ uri: mentor.photo_url }} style={styles.avatar} />
            ) : (
              <View style={[styles.avatar, styles.avatarPlaceholder]}>
                <MaterialCommunityIcons name="account" size={48} color="#999" />
              </View>
            )}
            <View style={styles.profileInfo}>
              <View style={styles.nameRow}>
                <Text style={styles.name}>{mentor.title}</Text>
                {mentor.is_verified && (
                  <MaterialCommunityIcons
                    name="check-decagram"
                    size={24}
                    color="#4CAF50"
                  />
                )}
              </View>
              <Text style={styles.education}>{mentor.education}</Text>
              <View style={styles.statsRow}>
                <View style={styles.statItem}>
                  <MaterialCommunityIcons
                    name="star"
                    size={18}
                    color="#FFD700"
                  />
                  <Text style={styles.statValue}>
                    {mentor.rating.toFixed(1)}
                  </Text>
                </View>
                <View style={styles.statItem}>
                  <MaterialCommunityIcons
                    name="calendar-check"
                    size={18}
                    color="#0066cc"
                  />
                  <Text style={styles.statValue}>{mentor.total_sessions}</Text>
                </View>
                <Text style={styles.timezone}>{mentor.timezone}</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Bio */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>
          <Text style={styles.bio}>{mentor.bio}</Text>
        </View>

        {/* Expertise */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Expertise</Text>
          <View style={styles.expertiseContainer}>
            {mentor.expertise_areas.map((area, index) => (
              <View key={index} style={styles.expertiseChip}>
                <Text style={styles.expertiseText}>{area}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Pricing */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Session Rate</Text>
          <View style={styles.priceContainer}>
            <MaterialCommunityIcons
              name="clock-outline"
              size={24}
              color="#0066cc"
            />
            <Text style={styles.price}>
              {mentor.hourly_rate_credits} credits/hour
            </Text>
          </View>
        </View>

        {/* Availability Calendar */}
        <View style={styles.section}>
          <View style={styles.availabilityHeader}>
            <Text style={styles.sectionTitle}>Available Times</Text>
            <Text style={styles.timezoneNote}>
              Times shown in {mentor.timezone}
            </Text>
          </View>

          {loadingAvailability ? (
            <ActivityIndicator size="small" color="#0066cc" />
          ) : availability.length === 0 ? (
            <View style={styles.noAvailability}>
              <MaterialCommunityIcons
                name="calendar-blank"
                size={48}
                color="#ccc"
              />
              <Text style={styles.noAvailabilityText}>
                No available times this month
              </Text>
              <Text style={styles.noAvailabilitySubtext}>
                Try next month or contact the mentor directly
              </Text>
            </View>
          ) : (
            <View style={styles.slotsContainer}>
              {availability.map((slot, index) => {
                const date = formatSlotDate(slot);
                const showDate =
                  index === 0 ||
                  (availability[index - 1] &&
                    formatSlotDate(availability[index - 1]) !== date);

                return (
                  <View key={index}>
                    {showDate && <Text style={styles.dateHeader}>{date}</Text>}
                    <TouchableOpacity
                      style={styles.slotItem}
                      onPress={() => handleBookSession(slot)}
                    >
                      <View style={styles.slotTime}>
                        <Text style={styles.slotTimeText}>
                          {formatSlotTime(slot)}
                        </Text>
                        <Text style={styles.slotDuration}>
                          {slot.duration_minutes} min
                        </Text>
                      </View>
                      <MaterialCommunityIcons
                        name="chevron-right"
                        size={20}
                        color="#0066cc"
                      />
                    </TouchableOpacity>
                  </View>
                );
              })}
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8f9fa",
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  errorContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  errorTitle: {
    fontSize: 18,
    color: "#666",
    marginTop: 16,
  },
  header: {
    backgroundColor: "#fff",
    padding: 20,
  },
  profileSection: {
    flexDirection: "row",
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginRight: 16,
  },
  avatarPlaceholder: {
    backgroundColor: "#f0f0f0",
    justifyContent: "center",
    alignItems: "center",
  },
  profileInfo: {
    flex: 1,
  },
  nameRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 4,
  },
  name: {
    fontSize: 24,
    fontWeight: "700",
    color: "#1a1a1a",
    marginRight: 8,
  },
  education: {
    fontSize: 14,
    color: "#666",
    marginBottom: 8,
  },
  statsRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  statItem: {
    flexDirection: "row",
    alignItems: "center",
    marginRight: 16,
  },
  statValue: {
    fontSize: 16,
    fontWeight: "600",
    color: "#1a1a1a",
    marginLeft: 4,
  },
  timezone: {
    fontSize: 12,
    color: "#999",
  },
  section: {
    backgroundColor: "#fff",
    marginTop: 12,
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#1a1a1a",
    marginBottom: 12,
  },
  bio: {
    fontSize: 16,
    color: "#333",
    lineHeight: 24,
  },
  expertiseContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
  },
  expertiseChip: {
    backgroundColor: "#f0f7ff",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 8,
  },
  expertiseText: {
    fontSize: 14,
    color: "#0066cc",
    fontWeight: "500",
  },
  priceContainer: {
    flexDirection: "row",
    alignItems: "center",
  },
  price: {
    fontSize: 24,
    fontWeight: "700",
    color: "#0066cc",
    marginLeft: 12,
  },
  availabilityHeader: {
    marginBottom: 16,
  },
  timezoneNote: {
    fontSize: 12,
    color: "#999",
    marginTop: 4,
  },
  noAvailability: {
    alignItems: "center",
    paddingVertical: 40,
  },
  noAvailabilityText: {
    fontSize: 16,
    fontWeight: "600",
    color: "#666",
    marginTop: 12,
  },
  noAvailabilitySubtext: {
    fontSize: 14,
    color: "#999",
    marginTop: 4,
    textAlign: "center",
  },
  slotsContainer: {
    borderWidth: 1,
    borderColor: "#e0e0e0",
    borderRadius: 8,
  },
  dateHeader: {
    fontSize: 14,
    fontWeight: "600",
    color: "#666",
    marginTop: 16,
    marginBottom: 8,
  },
  slotItem: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#f0f0f0",
  },
  slotTime: {
    flex: 1,
  },
  slotTimeText: {
    fontSize: 16,
    fontWeight: "600",
    color: "#1a1a1a",
  },
  slotDuration: {
    fontSize: 12,
    color: "#999",
    marginLeft: 8,
  },
});
