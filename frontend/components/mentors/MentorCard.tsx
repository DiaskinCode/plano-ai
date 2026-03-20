/**
 * MentorCard Component
 *
 * Full-width mentor card with:
 * - Photo, name, rating, university
 * - Bio (full text)
 * - Expertise area tags
 * - Footer with rate, availability, book button
 */

import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Image } from "react-native";
import { useRouter } from "expo-router";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { Mentor } from "@/types/mentor";

interface MentorCardProps {
  mentor: Mentor;
  userPlan: "basic" | "pro" | "premium";
  onPress?: () => void;
}

export const MentorCard: React.FC<MentorCardProps> = ({
  mentor,
  userPlan,
  onPress,
}) => {
  const router = useRouter();

  const hasAccess = userPlan === "pro" || userPlan === "premium";

  const handlePress = () => {
    if (onPress) {
      onPress();
    } else if (hasAccess) {
      router.push(`/mentor/${mentor.id}` as any);
    }
  };

  // Get university from expertise areas if available
  const university =
    mentor.expertise_areas?.find(
      (area) =>
        area.includes("University") ||
        area.includes("Stanford") ||
        area.includes("MIT") ||
        area.includes("Harvard") ||
        area.includes("Yale") ||
        area.includes("Columbia") ||
        area.includes("UCLA") ||
        area.includes("UC") ||
        area.includes("Berkeley"),
    ) ||
    mentor.education ||
    "";

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={handlePress}
      activeOpacity={0.7}
    >
      {/* Header: Photo, Name, Rating, University */}
      <View style={styles.header}>
        <View style={styles.photoContainer}>
          {mentor.photo_url ? (
            <Image source={{ uri: mentor.photo_url }} style={styles.photo} />
          ) : (
            <View style={styles.photoPlaceholder}>
              <Text style={styles.photoPlaceholderText}>
                {mentor.title.charAt(0)}
              </Text>
            </View>
          )}
        </View>

        <View style={styles.headerInfo}>
          <Text style={styles.name} numberOfLines={1}>
            {mentor.title}
          </Text>

          <View style={styles.ratingRow}>
            <MaterialCommunityIcons name="star" size={14} color="#F59E0B" />
            <Text style={styles.rating}>
              {parseFloat(mentor.rating).toFixed(1)}
            </Text>
            <Text style={styles.reviewCount}>
              ({mentor.total_sessions} sessions)
            </Text>
          </View>

          {university && (
            <Text style={styles.university} numberOfLines={1}>
              🎓 {university}
            </Text>
          )}
        </View>
      </View>

      {/* Bio */}
      <Text style={styles.bio} numberOfLines={3}>
        {mentor.bio}
      </Text>

      {/* Expertise Tags */}
      {mentor.expertise_areas && mentor.expertise_areas.length > 0 && (
        <View style={styles.expertiseContainer}>
          {mentor.expertise_areas.slice(0, 4).map((area, index) => (
            <View key={index} style={styles.tag}>
              <Text style={styles.tagText} numberOfLines={1}>
                {area}
              </Text>
            </View>
          ))}
          {mentor.expertise_areas.length > 4 && (
            <Text style={styles.moreText}>
              +{mentor.expertise_areas.length - 4} more
            </Text>
          )}
        </View>
      )}

      {/* Footer: Rate, Availability, Book Button */}
      <View style={styles.footer}>
        <View style={styles.footerLeft}>
          <Text style={styles.rate}>${mentor.hourly_rate}/hr</Text>
          {mentor.availability && (
            <Text
              style={[
                styles.availability,
                styles[`availability_${mentor.availability.toLowerCase()}`],
              ]}
            >
              {mentor.availability} Availability
            </Text>
          )}
        </View>

        <TouchableOpacity style={styles.bookButton}>
          <Text style={styles.bookButtonText}>Book Session</Text>
          <MaterialCommunityIcons
            name="chevron-right"
            size={16}
            color="#3B82F6"
          />
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    width: "100%",
    backgroundColor: "#1A1A1A",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#3E3E3E",
    padding: 14,
    marginBottom: 12,
  },
  header: {
    flexDirection: "row",
    marginBottom: 12,
  },
  photoContainer: {
    marginRight: 12,
  },
  photo: {
    width: 60,
    height: 60,
    borderRadius: 30,
    resizeMode: "cover",
  },
  photoPlaceholder: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: "#3B82F6",
    justifyContent: "center",
    alignItems: "center",
  },
  photoPlaceholderText: {
    fontSize: 24,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  headerInfo: {
    flex: 1,
    justifyContent: "center",
  },
  name: {
    fontSize: 17,
    fontWeight: "700",
    color: "#ECECEC",
    marginBottom: 4,
  },
  ratingRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 2,
    gap: 4,
  },
  rating: {
    fontSize: 13,
    fontWeight: "600",
    color: "#F59E0B",
  },
  reviewCount: {
    fontSize: 12,
    color: "#8E8E8E",
  },
  university: {
    fontSize: 13,
    color: "#3B82F6",
    marginTop: 4,
  },
  bio: {
    fontSize: 14,
    color: "#B8B8B8",
    lineHeight: 20,
    marginBottom: 10,
  },
  expertiseContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    marginBottom: 10,
  },
  tag: {
    backgroundColor: "#2A2A2A",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#3E3E3E",
  },
  tagText: {
    fontSize: 11,
    color: "#8E8E8E",
    fontWeight: "500",
  },
  moreText: {
    fontSize: 11,
    color: "#6B7280",
    fontStyle: "italic",
  },
  footer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: "#2A2A2A",
  },
  footerLeft: {
    flex: 1,
  },
  rate: {
    fontSize: 16,
    fontWeight: "700",
    color: "#10B981",
    marginBottom: 2,
  },
  availability: {
    fontSize: 11,
    marginTop: 2,
  },
  availability_high: {
    color: "#10B981",
  },
  availability_medium: {
    color: "#F59E0B",
  },
  availability_low: {
    color: "#EF4444",
  },
  bookButton: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#3B82F6",
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
    gap: 4,
  },
  bookButtonText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#FFFFFF",
  },
});
