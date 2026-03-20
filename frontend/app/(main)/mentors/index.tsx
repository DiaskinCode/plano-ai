/**
 * Mentors Discovery Screen
 *
 * Browse and discover mentors - Connected to Backend
 */

import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  RefreshControl,
  Image,
} from "react-native";
import { useRouter } from "expo-router";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { listMentors } from "@/services/mentorship";
import { Mentor } from "@/types/mentor";
import { colors, spacing, borderRadius, typography } from "@/theme";
import LiquidGlassCard from "@/components/LiquidGlassCard";
import { SafeAreaView } from "react-native-safe-area-context";

type SortOption = "rating" | "sessions" | "price_asc" | "price_desc";

export default function MentorsScreen() {
  const router = useRouter();
  const [mentors, setMentors] = useState<Mentor[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedExpertise, setSelectedExpertise] = useState<string | null>(
    null,
  );
  const [sortBy, setSortBy] = useState<SortOption>("rating");

  useEffect(() => {
    loadMentors();
  }, [sortBy, selectedExpertise]);

  const loadMentors = async () => {
    try {
      setLoading(true);
      const params: {
        expertise?: string;
        search?: string;
        ordering?: SortOption;
      } = {};

      if (selectedExpertise) params.expertise = selectedExpertise;
      if (searchQuery.trim()) params.search = searchQuery.trim();
      if (sortBy) params.ordering = sortBy;

      const response = await listMentors(params);
      setMentors(response.results || []);
    } catch (error) {
      console.error("Error loading mentors:", error);
      setMentors([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadMentors().then(() => setRefreshing(false));
  };

  const handleMentorPress = (mentor: Mentor) => {
    router.push(`/mentors/${mentor.id}`);
  };

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <MaterialCommunityIcons
          name="school"
          size={32}
          color={colors.primary}
        />
        <View style={styles.headerTextContainer}>
          <Text style={styles.headerTitle}>Find a Mentor</Text>
          <Text style={styles.headerSubtitle}>
            Connect with experts who can help you succeed
          </Text>
        </View>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <MaterialCommunityIcons
          name="magnify"
          size={24}
          color={colors.textSecondary}
        />
        <TextInput
          style={styles.searchInput}
          placeholder="Search by name or expertise..."
          placeholderTextColor={colors.textSecondary}
          value={searchQuery}
          onChangeText={setSearchQuery}
          onSubmitEditing={loadMentors}
          returnKeyType="search"
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity
            onPress={() => {
              setSearchQuery("");
              loadMentors();
            }}
          >
            <MaterialCommunityIcons
              name="close-circle"
              size={24}
              color={colors.textSecondary}
            />
          </TouchableOpacity>
        )}
      </View>

      {/* Sort & Filter */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filterScroll}
        contentContainerStyle={styles.filterScrollContent}
      >
        {[
          { key: "rating", label: "Top Rated", icon: "star" },
          { key: "sessions", label: "Most Sessions", icon: "calendar-check" },
          { key: "price_asc", label: "Price: Low", icon: "tag" },
          { key: "price_desc", label: "Price: High", icon: "tag-outline" },
        ].map((option) => (
          <TouchableOpacity
            key={option.key}
            style={[
              styles.filterChip,
              sortBy === option.key && styles.filterChipActive,
            ]}
            onPress={() => {
              setSortBy(option.key as SortOption);
              loadMentors();
            }}
          >
            <MaterialCommunityIcons
              name={option.icon as any}
              size={16}
              color={sortBy === option.key ? colors.bg : colors.textSecondary}
            />
            <Text
              style={[
                styles.filterChipText,
                sortBy === option.key && styles.filterChipTextActive,
              ]}
            >
              {option.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Content */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading mentors...</Text>
        </View>
      ) : mentors.length === 0 ? (
        <View style={styles.emptyContainer}>
          <LiquidGlassCard
            variant="subtle"
            intensity="light"
            style={styles.emptyCard}
          >
            <MaterialCommunityIcons
              name="account-search"
              size={64}
              color={colors.textSecondary}
            />
            <Text style={styles.emptyTitle}>No mentors found</Text>
            <Text style={styles.emptyText}>
              {searchQuery
                ? "Try a different search"
                : "No mentors available yet"}
            </Text>
            {searchQuery && (
              <TouchableOpacity
                style={styles.retryButton}
                onPress={() => {
                  setSearchQuery("");
                  loadMentors();
                }}
              >
                <Text style={styles.retryButtonText}>Clear Search</Text>
              </TouchableOpacity>
            )}
          </LiquidGlassCard>
        </View>
      ) : (
        <ScrollView
          style={styles.listContainer}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
          }
        >
          <Text style={styles.resultsCount}>
            {mentors.length} mentor{mentors.length !== 1 ? "s" : ""} found
          </Text>

          {mentors.map((mentor) => (
            <LiquidGlassCard
              key={mentor.id}
              variant="default"
              intensity="medium"
              onPress={() => handleMentorPress(mentor)}
              style={styles.mentorCard}
            >
              {/* Header */}
              <View style={styles.cardHeader}>
                <View style={styles.profileInfo}>
                  {mentor.photo_url ? (
                    <Image
                      source={{ uri: mentor.photo_url }}
                      style={styles.avatar}
                    />
                  ) : (
                    <View style={[styles.avatar, styles.avatarPlaceholder]}>
                      <Text style={styles.avatarText}>
                        {mentor.title.charAt(0).toUpperCase()}
                      </Text>
                    </View>
                  )}
                  <View style={styles.textContainer}>
                    <View style={styles.nameRow}>
                      <Text style={styles.title}>{mentor.title}</Text>
                      {mentor.is_verified && (
                        <MaterialCommunityIcons
                          name="check-decagram"
                          size={18}
                          color="#4CAF50"
                        />
                      )}
                    </View>
                    <View style={styles.statsRow}>
                      <View style={styles.ratingContainer}>
                        <MaterialCommunityIcons
                          name="star"
                          size={16}
                          color="#FFD700"
                        />
                        <Text style={styles.rating}>
                          {parseFloat(mentor.rating).toFixed(1)}
                        </Text>
                        <Text style={styles.reviewCount}>
                          ({mentor.total_sessions} sessions)
                        </Text>
                      </View>
                    </View>
                  </View>
                </View>
              </View>

              {/* Bio */}
              <Text style={styles.bio} numberOfLines={2}>
                {mentor.bio}
              </Text>

              {/* Expertise */}
              {mentor.expertise_areas.length > 0 && (
                <View style={styles.expertiseContainer}>
                  {mentor.expertise_areas.slice(0, 3).map((area, index) => (
                    <View key={index} style={styles.expertiseChip}>
                      <Text style={styles.expertiseText}>{area}</Text>
                    </View>
                  ))}
                  {mentor.expertise_areas.length > 3 && (
                    <Text style={styles.moreText}>
                      +{mentor.expertise_areas.length - 3}
                    </Text>
                  )}
                </View>
              )}

              {/* Footer */}
              <View style={styles.cardFooter}>
                <View style={styles.priceContainer}>
                  <MaterialCommunityIcons
                    name="cash"
                    size={16}
                    color={colors.primary}
                  />
                  <Text style={styles.price}>
                    {mentor.hourly_rate_credits} credits/hr
                  </Text>
                </View>
                <View style={styles.availableContainer}>
                  <View style={[styles.dot, { backgroundColor: "#4CAF50" }]} />
                  <Text style={styles.availableText}>Available</Text>
                </View>
              </View>
            </LiquidGlassCard>
          ))}

          <View style={styles.bottomPadding} />
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
    paddingBottom: spacing.xl,
    gap: spacing.md,
  },
  headerTextContainer: {
    flex: 1,
  },
  headerTitle: {
    ...typography.headlineMedium,
    color: colors.text,
    marginBottom: 4,
    fontWeight: "700",
  },
  headerSubtitle: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    marginTop: 2,
  },
  searchContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.liquidGlass.overlayMedium,
    marginHorizontal: spacing.lg,
    marginBottom: spacing.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.liquidGlass.borderLight,
    minHeight: 48,
  },
  searchInput: {
    flex: 1,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.sm,
    fontSize: 16,
    color: colors.text,
  },
  filterScroll: {
    marginBottom: spacing.md,
    maxHeight: 60,
  },
  filterScrollContent: {
    paddingHorizontal: spacing.lg,
  },
  filterChip: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.full,
    marginRight: spacing.sm,
    backgroundColor: colors.liquidGlass.overlayMedium,
    borderWidth: 1,
    borderColor: colors.liquidGlass.borderLight,
    minHeight: 40,
    justifyContent: "center",
  },
  filterChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterChipText: {
    ...typography.labelMedium,
    color: colors.textSecondary,
    fontSize: 14,
  },
  filterChipTextActive: {
    color: colors.bg,
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
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: spacing.xl,
  },
  emptyCard: {
    padding: spacing.xl,
    alignItems: "center",
  },
  emptyTitle: {
    ...typography.headlineSmall,
    color: colors.text,
    marginTop: spacing.lg,
  },
  emptyText: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    marginTop: spacing.sm,
    textAlign: "center",
  },
  retryButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
    marginTop: spacing.lg,
  },
  retryButtonText: {
    ...typography.labelMedium,
    color: colors.bg,
  },
  listContainer: {
    flex: 1,
  },
  listContent: {
    paddingHorizontal: spacing.lg,
  },
  resultsCount: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  mentorCard: {
    marginBottom: spacing.md,
  },
  cardHeader: {
    marginBottom: spacing.md,
  },
  profileInfo: {
    flexDirection: "row",
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    marginRight: spacing.md,
  },
  avatarPlaceholder: {
    backgroundColor: colors.liquidGlass.overlayLight,
    justifyContent: "center",
    alignItems: "center",
  },
  avatarText: {
    ...typography.headlineMedium,
    color: colors.primary,
  },
  textContainer: {
    flex: 1,
  },
  nameRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.xs,
  },
  title: {
    ...typography.titleMedium,
    color: colors.text,
    marginRight: spacing.xs,
  },
  statsRow: {
    flexDirection: "row",
  },
  ratingContainer: {
    flexDirection: "row",
    alignItems: "center",
  },
  rating: {
    ...typography.labelMedium,
    color: colors.text,
    marginLeft: spacing.xs,
  },
  reviewCount: {
    ...typography.caption,
    color: colors.textSecondary,
    marginLeft: spacing.xs,
  },
  bio: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    lineHeight: 22,
    marginBottom: spacing.md,
  },
  expertiseContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginBottom: spacing.md,
  },
  expertiseChip: {
    backgroundColor: colors.liquidGlass.overlayLight,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
    marginRight: spacing.xs,
    marginBottom: spacing.xs,
  },
  expertiseText: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: "600",
  },
  moreText: {
    ...typography.caption,
    color: colors.textSecondary,
    marginLeft: spacing.xs,
  },
  cardFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    borderTopWidth: 1,
    borderTopColor: colors.liquidGlass.borderLight,
    paddingTop: spacing.md,
  },
  priceContainer: {
    flexDirection: "row",
    alignItems: "center",
  },
  price: {
    ...typography.labelMedium,
    color: colors.text,
    marginLeft: spacing.xs,
  },
  availableContainer: {
    flexDirection: "row",
    alignItems: "center",
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: spacing.xs,
  },
  availableText: {
    ...typography.caption,
    color: "#4CAF50",
    fontWeight: "600",
  },
  bottomPadding: {
    height: spacing.xl,
  },
});
