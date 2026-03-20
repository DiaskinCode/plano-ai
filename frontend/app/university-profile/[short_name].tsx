/**
 * University Profile Detail Screen
 *
 * Displays detailed information about a specific university
 * using the short_name (e.g., "mit", "stanford")
 */

import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  Alert,
  SafeAreaView,
  StatusBar,
  Dimensions,
  Image,
} from "react-native";
import { useRouter, useLocalSearchParams } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { universityRecommenderAPI } from "@/services/universityRecommenderApi";
import { colors, spacing } from "@/theme";

const { width } = Dimensions.get("window");

interface UniversityData {
  short_name: string;
  name: string;
  location: string;
  country: string;
  acceptance_rate: number;
  total_cost: number;
  need_blind: boolean;
  international_aid: boolean;
  campus_type: string;
  undergraduate_enrollment: number;
  popular_majors: string[];
  employed_within_6_months: number | null;
  logo_url?: string;
  campus_photo_url?: string;
}

export default function UniversityProfileDetail() {
  const router = useRouter();
  const { short_name } = useLocalSearchParams();
  const [loading, setLoading] = useState(true);
  const [university, setUniversity] = useState<UniversityData | null>(null);
  const [isInShortlist, setIsInShortlist] = useState(false);

  useEffect(() => {
    loadUniversityDetails();
    checkShortlistStatus();
  }, [short_name]);

  const loadUniversityDetails = async () => {
    if (!short_name) {
      router.back();
      return;
    }

    try {
      setLoading(true);
      const response =
        await universityRecommenderAPI.searchUniversities(short_name);
      const found = response.data.find((u: any) => u.short_name === short_name);

      if (found) {
        setUniversity(found);
      } else {
        Alert.alert("Not Found", "University not found");
        router.back();
      }
    } catch (error: any) {
      console.error("Failed to load university:", error);
      Alert.alert("Error", "Failed to load university details");
      router.back();
    } finally {
      setLoading(false);
    }
  };

  const checkShortlistStatus = async () => {
    try {
      const response = await universityRecommenderAPI.getShortlist();
      const inShortlist = response.data.some(
        (item: any) => item.university.short_name === short_name,
      );
      setIsInShortlist(inShortlist);
    } catch (error) {
      console.error("Failed to check shortlist status:", error);
    }
  };

  const handleToggleShortlist = async () => {
    try {
      if (isInShortlist) {
        await universityRecommenderAPI.removeFromShortlist(short_name);
        setIsInShortlist(false);
        Alert.alert("Removed", "Removed from your shortlist");
      } else {
        await universityRecommenderAPI.addToShortlist(short_name);
        setIsInShortlist(true);
        Alert.alert("Added", "Added to your shortlist");
      }
    } catch (error: any) {
      console.error("Failed to toggle shortlist:", error);
      Alert.alert("Error", "Failed to update shortlist");
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading university details...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!university) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.centerContent}>
          <Text style={styles.errorTitle}>University Not Found</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <View style={styles.headerTitleContainer}>
          {university.logo_url && university.logo_url.length > 0 && (
            <Image
              source={{ uri: university.logo_url }}
              style={styles.headerLogo}
              resizeMode="contain"
            />
          )}
          <Text style={styles.headerTitle}>{university.name}</Text>
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity
            style={[
              styles.headerButton,
              isInShortlist && styles.headerButtonActive,
            ]}
            onPress={handleToggleShortlist}
          >
            <Ionicons
              name={isInShortlist ? "bookmark" : "bookmark-outline"}
              size={24}
              color={isInShortlist ? colors.primary : colors.textSecondary}
            />
          </TouchableOpacity>
        </View>
      </View>

      {/* Campus Photo Hero Image */}
      {university.campus_photo_url &&
        university.campus_photo_url.length > 0 && (
          <View style={styles.heroImageContainer}>
            <Image
              source={{ uri: university.campus_photo_url }}
              style={styles.heroImage}
              resizeMode="cover"
            />
          </View>
        )}

      {/* Content */}
      <ScrollView
        style={styles.content}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.contentContainer}
      >
        {/* Quick Stats */}
        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <Ionicons name="trending-up" size={24} color={colors.info} />
            <Text style={styles.statValue}>{university.acceptance_rate}%</Text>
            <Text style={styles.statLabel}>Acceptance Rate</Text>
          </View>
          <View style={styles.statCard}>
            <Ionicons name="cash" size={24} color={colors.success} />
            <Text style={styles.statValue}>
              ${university.total_cost?.toLocaleString() || "N/A"}
            </Text>
            <Text style={styles.statLabel}>Cost/Year</Text>
          </View>
          {university.need_blind && (
            <View style={styles.statCard}>
              <Ionicons
                name="shield-checkmark"
                size={24}
                color={colors.primary}
              />
              <Text style={styles.statValue}>Yes</Text>
              <Text style={styles.statLabel}>Need-Blind</Text>
            </View>
          )}
          {university.international_aid && (
            <View style={styles.statCard}>
              <Ionicons name="globe" size={24} color={colors.warning} />
              <Text style={styles.statValue}>Yes</Text>
              <Text style={styles.statLabel}>Intl Aid</Text>
            </View>
          )}
        </View>

        {/* Basic Info */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Basic Information</Text>
          <View style={styles.infoCard}>
            <View style={styles.infoRow}>
              <Ionicons name="locate" size={20} color={colors.textSecondary} />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Location</Text>
                <Text style={styles.infoValue}>{university.location}</Text>
              </View>
            </View>
            <View style={styles.infoRow}>
              <Ionicons name="flag" size={20} color={colors.textSecondary} />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Country</Text>
                <Text style={styles.infoValue}>{university.country}</Text>
              </View>
            </View>
            <View style={styles.infoRow}>
              <Ionicons name="school" size={20} color={colors.textSecondary} />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Campus Type</Text>
                <Text style={styles.infoValue}>{university.campus_type}</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Enrollment & Outcomes */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Enrollment & Outcomes</Text>
          <View style={styles.infoCard}>
            {university.undergraduate_enrollment && (
              <View style={styles.infoRow}>
                <Ionicons
                  name="people"
                  size={20}
                  color={colors.textSecondary}
                />
                <View style={styles.infoContent}>
                  <Text style={styles.infoLabel}>Undergraduate Enrollment</Text>
                  <Text style={styles.infoValue}>
                    {university.undergraduate_enrollment.toLocaleString()}
                  </Text>
                </View>
              </View>
            )}
            {university.employed_within_6_months !== null && (
              <View style={styles.infoRow}>
                <Ionicons
                  name="briefcase"
                  size={20}
                  color={colors.textSecondary}
                />
                <View style={styles.infoContent}>
                  <Text style={styles.infoLabel}>Employed within 6 months</Text>
                  <Text style={styles.infoValue}>
                    {university.employed_within_6_months}%
                  </Text>
                </View>
              </View>
            )}
          </View>
        </View>

        {/* Popular Majors */}
        {university.popular_majors && university.popular_majors.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Popular Majors</Text>
            <View style={styles.majorsContainer}>
              {university.popular_majors.map((major, index) => (
                <View key={index} style={styles.majorTag}>
                  <Text style={styles.majorText}>{major}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Actions */}
        <View style={styles.actionButtons}>
          <TouchableOpacity
            style={[styles.actionButton, styles.primaryButton]}
            onPress={handleToggleShortlist}
          >
            <Ionicons
              name={isInShortlist ? "bookmark" : "bookmark-outline"}
              size={20}
              color="#fff"
            />
            <Text style={styles.actionButtonText}>
              {isInShortlist ? "Remove from Shortlist" : "Add to Shortlist"}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.actionButton, styles.secondaryButton]}
            onPress={() => router.push("/university-recommender/shortlist")}
          >
            <Ionicons name="list" size={20} color={colors.primary} />
            <Text style={[styles.actionButtonText, styles.secondaryButtonText]}>
              View Shortlist
            </Text>
          </TouchableOpacity>
        </View>

        {/* Bottom Spacing */}
        <View style={styles.bottomSpacing} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backButton: {
    padding: spacing.xs,
  },
  headerTitleContainer: {
    flex: 1,
    flexDirection: "column",
    alignItems: "center",
    marginLeft: spacing.sm,
  },
  headerLogo: {
    width: 40,
    height: 40,
    marginBottom: 4,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: colors.text,
  },
  headerActions: {
    flexDirection: "row",
    gap: spacing.sm,
  },
  headerButton: {
    padding: spacing.xs,
  },
  headerButtonActive: {
    backgroundColor: colors.primaryLight,
    borderRadius: 20,
  },
  centerContent: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    gap: spacing.md,
  },
  loadingText: {
    fontSize: 16,
    fontWeight: "600",
    color: colors.text,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: "600",
    color: colors.text,
  },
  heroImageContainer: {
    width: "100%",
    height: 200,
    backgroundColor: colors.background,
  },
  heroImage: {
    width: "100%",
    height: "100%",
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: spacing.md,
  },
  statsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  statCard: {
    flex: 1,
    minWidth: (width - 60) / 3,
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: spacing.md,
    alignItems: "center",
    gap: spacing.xs,
    borderWidth: 1,
    borderColor: colors.border,
  },
  statValue: {
    fontSize: 20,
    fontWeight: "700",
    color: colors.text,
  },
  statLabel: {
    fontSize: 12,
    fontWeight: "500",
    color: colors.textSecondary,
  },
  section: {
    marginBottom: spacing.lg,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: colors.text,
    marginBottom: spacing.md,
  },
  infoCard: {
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: spacing.md,
    gap: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  infoRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    paddingVertical: spacing.xs,
  },
  infoContent: {
    flex: 1,
  },
  infoLabel: {
    fontSize: 12,
    fontWeight: "500",
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  infoValue: {
    fontSize: 15,
    fontWeight: "600",
    color: colors.text,
  },
  majorsContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  majorTag: {
    backgroundColor: colors.primaryLight,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  majorText: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.primary,
  },
  actionButtons: {
    flexDirection: "row",
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  actionButton: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: spacing.md,
    borderRadius: 12,
    gap: spacing.sm,
  },
  primaryButton: {
    backgroundColor: colors.primary,
  },
  secondaryButton: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  actionButtonText: {
    fontSize: 15,
    fontWeight: "600",
    color: "#fff",
  },
  secondaryButtonText: {
    color: colors.primary,
  },
  bottomSpacing: {
    height: 100,
  },
});
