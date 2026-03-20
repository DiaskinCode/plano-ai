/**
 * University Recommendations Results Screen
 *
 * Displays personalized university recommendations with:
 * - Three buckets: Match, Safety, Reach
 * - LLM insights for top recommendations
 * - Fit, Chance, and Finance scores
 * - Add to shortlist functionality
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
  SafeAreaView,
  StatusBar,
  Dimensions,
  Image,
} from "react-native";
import { router } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import {
  universityRecommenderAPI,
  universityProfileAPI,
} from "@/services/universityRecommenderApi";
import onboardingApi from "@/services/onboardingApi";
import {
  saveRecommendations as saveRecommendationsToStorage,
  loadRecommendations as loadRecommendationsFromStorage,
  clearCache,
  getCacheAge,
} from "@/services/recommendationCache";
import { colors, spacing } from "@/theme";
import {
  EligibilityStatus,
  EligibilityReport,
} from "@/components/EligibilityStatus";

const { width } = Dimensions.get("window");

interface Recommendation {
  university: {
    short_name: string;
    name: string;
    location: string;
    country: string;
    acceptance_rate: number;
    total_cost: number;
    need_blind: boolean;
    international_aid: boolean;
    logo_url?: string;
    campus_photo_url?: string;
  };
  scores: {
    fit: number;
    chance: number;
    finance: number;
  };
  bucket: "Match" | "Safety" | "Reach";
  llm_insights: {
    confidence: string;
    reasons: string[];
    risks: string[];
    next_actions: string[];
  } | null;
}

interface RecommendationsResponse {
  recommendations: Recommendation[];
  log_id: number;
  total_found: number;
  bucket_counts: {
    Match: number;
    Safety: number;
    Reach: number;
  };
  eligibility_report?: EligibilityReport;
}

type BucketType = "all" | "Match" | "Safety" | "Reach";

export default function UniversityRecommendationsResults() {
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [bucketCounts, setBucketCounts] = useState({
    Match: 0,
    Safety: 0,
    Reach: 0,
  });
  const [selectedBucket, setSelectedBucket] = useState<BucketType>("all");
  const [useLLM, setUseLLM] = useState(true);
  const [isUsingCached, setIsUsingCached] = useState(false);
  const [cacheAge, setCacheAge] = useState<number | null>(null);
  const [forceRefresh, setForceRefresh] = useState(false);
  const [imageLoadErrors, setImageLoadErrors] = useState<Set<string>>(
    new Set(),
  );
  const [eligibilityReport, setEligibilityReport] =
    useState<EligibilityReport | null>(null);
  const [showEligibility, setShowEligibility] = useState(false);
  const [showEligibilityModal, setShowEligibilityModal] = useState(false);

  useEffect(() => {
    loadRecommendations();
  }, []);

  const loadRecommendations = async (forceBypassCache = false) => {
    try {
      setLoading(true);

      // Try to load from cache first (unless force bypass)
      if (!forceBypassCache) {
        const cachedData = await loadRecommendationsFromCache();
        if (cachedData) {
          setRecommendations(cachedData.recommendations);
          setBucketCounts(cachedData.bucket_counts);
          // Restore eligibility report from cache
          if (cachedData.eligibility_report) {
            setEligibilityReport(cachedData.eligibility_report);
          }
          setIsUsingCached(true);
          const age = await getCacheAge();
          setCacheAge(age);
          setLoading(false);
          return;
        }
      }

      // No cache or force bypass - fetch from API
      setIsUsingCached(false);
      setCacheAge(null);

      // Collect profile data to send to backend
      const profileData = {
        extracurriculars: [],
        achievements: [],
      };

      // Get user's profile to collect achievements and extracurriculars
      try {
        const profileResponse = await universityProfileAPI.getProfile();
        const profile = profileResponse.data;

        // Get spike achievement
        if (profile?.spike_achievement) {
          profileData.achievements = profile.spike_achievement;
        }

        // Get extracurriculars
        const extracurricularsResponse =
          await universityProfileAPI.getExtracurriculars();
        if (extracurricularsResponse?.data) {
          profileData.extracurriculars = extracurricularsResponse.data.map(
            (ex: any) => ({
              id: ex.id,
              category: ex.category,
              title: ex.title,
              role: ex.role,
              hours_per_week: ex.hours_per_week,
              weeks_per_year: ex.weeks_per_year,
              years_participated: ex.years_participated,
              impact_level: ex.impact_level,
            }),
          );
        }
      } catch (error) {
        console.log("Error loading profile for recommendations:", error);
      }

      const response = await universityRecommenderAPI.generateRecommendations(
        useLLM,
        profileData,
      );
      const data: RecommendationsResponse = response.data;

      // Debug: Log logo URLs
      console.log("Recommendations received:", data.recommendations.length);
      data.recommendations.forEach((rec, i) => {
        console.log(
          `[${i}] ${rec.university.name}: logo_url =`,
          rec.university.logo_url,
        );
      });

      setRecommendations(data.recommendations);
      setBucketCounts(data.bucket_counts);

      // Debug: Log all buckets in the data
      console.log("=== BUCKET DEBUG ===");
      console.log("Total recommendations:", data.recommendations.length);
      console.log("Bucket counts from backend:", data.bucket_counts);
      data.recommendations.forEach((rec, i) => {
        console.log(`  [${i}] ${rec.university.short_name}: bucket = "${rec.bucket}"`);
      });
      console.log("==================");

      // Save eligibility report if available
      if (data.eligibility_report) {
        setEligibilityReport(data.eligibility_report);
      }

      // Save to cache for future use
      await saveRecommendationsToCache(data);
    } catch (error: any) {
      console.error("Failed to load recommendations:", error);
      console.error("Error response data:", error.response?.data);
      console.error("Error status:", error.response?.status);

      let errorMessage =
        "Failed to generate recommendations. Please try again.";

      if (error.code === "ECONNABORTED" || error.code === "ECONNABORTED") {
        errorMessage = "Request timed out. The AI analysis is taking too long. Please try again with AI insights disabled, or contact support.";
      } else if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (typeof error.response?.data === "string") {
        errorMessage = error.response.data;
      }

      Alert.alert("Error", errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async () => {
    setGenerating(true);
    await loadRecommendations(true); // Force bypass cache
    setGenerating(false);
  };

  const loadRecommendationsFromCache = async () => {
    try {
      return await loadRecommendationsFromStorage();
    } catch (error) {
      console.error("Error loading from cache:", error);
      return null;
    }
  };

  const saveRecommendationsToCache = async (data: RecommendationsResponse) => {
    try {
      await saveRecommendationsToStorage(data);
    } catch (error) {
      console.error("Error saving to cache:", error);
    }
  };

  const handleAddToShortlist = async (shortName: string) => {
    try {
      await universityRecommenderAPI.addToShortlist(shortName);
      Alert.alert("Success", "Added to shortlist!");
    } catch (error: any) {
      console.error("Failed to add to shortlist:", error);
      Alert.alert(
        "Error",
        error.response?.data?.error || "Failed to add to shortlist",
      );
    }
  };

  const getFilteredRecommendations = () => {
    if (selectedBucket === "all") {
      return recommendations;
    }
    const filtered = recommendations.filter((rec) => {
      const match = rec.bucket.toLowerCase() === selectedBucket.toLowerCase();
      return match;
    });

    // If we expect items in this bucket (based on bucket_counts) but got none,
    // the cache might be stale - trigger a refresh
    if (filtered.length === 0 && bucketCounts[selectedBucket as keyof typeof bucketCounts] > 0) {
      console.log(`⚠️ Cache mismatch: Expected ${bucketCounts[selectedBucket]} ${selectedBucket} but found 0. Cache is stale!`);
      // Don't auto-refresh to avoid infinite loops, but log for debugging
    }

    return filtered;
  };

  const getBucketColor = (bucket: string) => {
    switch (bucket) {
      case "Match":
        return colors.success;
      case "Safety":
        return colors.info;
      case "Reach":
        return colors.warning;
      default:
        return colors.textSecondary;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return colors.success;
    if (score >= 40) return colors.warning;
    return colors.error;
  };

  const renderBucketTabs = () => (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      style={styles.bucketTabs}
    >
      <TouchableOpacity
        style={[
          styles.bucketTab,
          selectedBucket === "all" && styles.bucketTabActive,
        ]}
        onPress={() => setSelectedBucket("all")}
      >
        <Text
          style={[
            styles.bucketTabText,
            selectedBucket === "all" && styles.bucketTabTextActive,
          ]}
        >
          All ({recommendations.length})
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[
          styles.bucketTab,
          selectedBucket === "Match" && styles.bucketTabActive,
        ]}
        onPress={() => setSelectedBucket("Match")}
      >
        <Text
          style={[
            styles.bucketTabText,
            selectedBucket === "Match" && styles.bucketTabTextActive,
          ]}
        >
          Match ({bucketCounts.Match})
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[
          styles.bucketTab,
          selectedBucket === "Safety" && styles.bucketTabActive,
        ]}
        onPress={() => setSelectedBucket("Safety")}
      >
        <Text
          style={[
            styles.bucketTabText,
            selectedBucket === "Safety" && styles.bucketTabTextActive,
          ]}
        >
          Safety ({bucketCounts.Safety})
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[
          styles.bucketTab,
          selectedBucket === "Reach" && styles.bucketTabActive,
        ]}
        onPress={() => setSelectedBucket("Reach")}
      >
        <Text
          style={[
            styles.bucketTabText,
            selectedBucket === "Reach" && styles.bucketTabTextActive,
          ]}
        >
          Reach ({bucketCounts.Reach})
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );

  const renderScoreBar = (label: string, score: number, color: string) => (
    <View style={styles.scoreRow}>
      <Text style={styles.scoreLabel}>{label}</Text>
      <View style={styles.scoreBarContainer}>
        <View
          style={[
            styles.scoreBar,
            { width: `${score}%`, backgroundColor: color },
          ]}
        />
      </View>
      <Text style={[styles.scoreValue, { color }]}>{score}</Text>
    </View>
  );

  const renderUniversityCard = (item: Recommendation, index: number) => {
    return (
      <View key={`${item.university.short_name}-${index}`} style={styles.card}>
        {/* Header with Logo */}
        <View style={styles.cardHeader}>
          <View style={styles.cardHeaderLeft}>
            {/* University Logo */}
            {item.university.logo_url && item.university.logo_url.length > 0 ? (
              <View style={styles.logoContainer}>
                <Image
                  source={{ uri: item.university.logo_url }}
                  style={styles.logo}
                  resizeMode="contain"
                  onLoad={() =>
                    console.log("✅ Image loaded:", item.university.name)
                  }
                  onError={(error) => {
                    console.log(
                      "❌ Image load error for",
                      item.university.name,
                      ":",
                      error.nativeEvent.error,
                    );
                  }}
                />
              </View>
            ) : (
              <View style={styles.logoPlaceholder}>
                <Ionicons name="school" size={28} color={colors.textTertiary} />
              </View>
            )}
            <View style={styles.universityInfo}>
              <Text style={styles.universityName}>{item.university.name}</Text>
              <Text style={styles.universityLocation}>
                {item.university.location}
              </Text>
            </View>
          </View>
          <View
            style={[
              styles.bucketBadge,
              { backgroundColor: getBucketColor(item.bucket) },
            ]}
          >
            <Text style={styles.bucketText}>{item.bucket}</Text>
          </View>
        </View>

        {/* Campus Photo */}
        {item.university.campus_photo_url &&
          item.university.campus_photo_url.length > 0 && (
            <View style={styles.campusPhotoContainer}>
              <Image
                source={{ uri: item.university.campus_photo_url }}
                style={styles.campusPhoto}
                resizeMode="cover"
              />
            </View>
          )}

        {/* Key Stats */}
        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <Ionicons
              name="trending-up"
              size={16}
              color={colors.textSecondary}
            />
            <Text style={styles.statValue}>
              {item.university.acceptance_rate}%
            </Text>
            <Text style={styles.statLabel}>Acceptance</Text>
          </View>
          <View style={styles.statItem}>
            <Ionicons name="cash" size={16} color={colors.textSecondary} />
            <Text style={styles.statValue}>
              ${item.university.total_cost.toLocaleString()}
            </Text>
            <Text style={styles.statLabel}>Cost/Year</Text>
          </View>
          {item.university.need_blind && (
            <View style={styles.statItem}>
              <Ionicons
                name="shield-checkmark"
                size={16}
                color={colors.success}
              />
              <Text style={styles.statValue}>Need-Blind</Text>
            </View>
          )}
          {item.university.international_aid && (
            <View style={styles.statItem}>
              <Ionicons name="globe" size={16} color={colors.info} />
              <Text style={styles.statValue}>Intl Aid</Text>
            </View>
          )}
        </View>

        {/* Scores */}
        <View style={styles.scoresContainer}>
          {renderScoreBar(
            "Fit",
            item.scores.fit,
            getScoreColor(item.scores.fit),
          )}
          {renderScoreBar(
            "Chance",
            item.scores.chance,
            getScoreColor(item.scores.chance),
          )}
          {renderScoreBar(
            "Finance",
            item.scores.finance,
            getScoreColor(item.scores.finance),
          )}
        </View>

        {/* LLM Insights */}
        {item.llm_insights && (
          <View style={styles.insightsContainer}>
            <View style={styles.insightHeader}>
              <Ionicons name="bulb" size={18} color={colors.warning} />
              <Text style={styles.insightTitle}>AI Insights</Text>
              <View
                style={[
                  styles.confidenceBadge,
                  {
                    backgroundColor:
                      item.llm_insights.confidence === "high"
                        ? colors.successLight
                        : item.llm_insights.confidence === "medium"
                          ? colors.warningLight
                          : colors.errorLight,
                  },
                ]}
              >
                <Text style={styles.confidenceText}>
                  {item.llm_insights.confidence}
                </Text>
              </View>
            </View>

            {item.llm_insights.reasons.length > 0 && (
              <View style={styles.insightSection}>
                <Text style={styles.insightSectionTitle}>Why This Fit:</Text>
                {item.llm_insights.reasons.map((reason, i) => (
                  <Text key={i} style={styles.insightBullet}>
                    • {reason}
                  </Text>
                ))}
              </View>
            )}

            {item.llm_insights.risks.length > 0 && (
              <View style={styles.insightSection}>
                <Text style={styles.insightSectionTitle}>Risks:</Text>
                {item.llm_insights.risks.map((risk, i) => (
                  <Text key={i} style={styles.insightBullet}>
                    • {risk}
                  </Text>
                ))}
              </View>
            )}

            {item.llm_insights.next_actions.length > 0 && (
              <View style={styles.insightSection}>
                <Text style={styles.insightSectionTitle}>Next Steps:</Text>
                {item.llm_insights.next_actions.map((action, i) => (
                  <Text key={i} style={styles.insightBullet}>
                    • {action}
                  </Text>
                ))}
              </View>
            )}
          </View>
        )}

        {/* Actions */}
        <View style={styles.cardActions}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => handleAddToShortlist(item.university.short_name)}
          >
            <Ionicons
              name="bookmark-outline"
              size={18}
              color={colors.primary}
            />
            <Text style={styles.actionButtonText}>Save</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() =>
              router.push(`/university-profile/${item.university.short_name}`)
            }
          >
            <Ionicons
              name="information-circle-outline"
              size={18}
              color={colors.textSecondary}
            />
            <Text style={styles.actionButtonText}>Details</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Generating recommendations...</Text>
          <Text style={styles.loadingSubtext}>This may take a moment</Text>
        </View>
      </SafeAreaView>
    );
  }

  const filteredRecommendations = getFilteredRecommendations();

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
          <Text style={styles.headerTitle}>Your Recommendations</Text>
          {isUsingCached && cacheAge !== null && (
            <View style={styles.cacheBadge}>
              <Ionicons
                name="time-outline"
                size={12}
                color={colors.textSecondary}
              />
              <Text style={styles.cacheBadgeText}>
                Cached •{" "}
                {cacheAge < 60
                  ? `${cacheAge}m ago`
                  : `${Math.round(cacheAge / 60)}h ago`}
              </Text>
            </View>
          )}
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity
            style={[styles.iconButton, { marginRight: spacing.xs }]}
            onPress={() => setUseLLM(!useLLM)}
          >
            <Ionicons
              name={useLLM ? "bulb" : "bulb-outline"}
              size={24}
              color={useLLM ? colors.warning : colors.textSecondary}
            />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.refreshButton}
            onPress={handleRegenerate}
            disabled={generating}
          >
            <Ionicons
              name={generating ? "refresh" : "refresh-outline"}
              size={24}
              color={generating ? colors.textSecondary : colors.primary}
            />
          </TouchableOpacity>
        </View>
      </View>

      {/* Eligibility Summary Card - Always visible */}
      {eligibilityReport && !showEligibilityModal && (
        <TouchableOpacity
          style={styles.eligibilitySummaryCard}
          onPress={() => setShowEligibilityModal(true)}
          activeOpacity={0.7}
        >
          <View style={styles.eligibilitySummaryLeft}>
            <View style={[
              styles.eligibilitySummaryIcon,
              {
                backgroundColor: eligibilityReport.overall_status === "eligible"
                  ? colors.successLight + "20"
                  : eligibilityReport.overall_status === "partially_eligible"
                  ? colors.warningLight + "20"
                  : colors.errorLight + "20"
              }
            ]}>
              <Ionicons
                name={eligibilityReport.overall_status === "eligible"
                  ? "checkmark-circle"
                  : eligibilityReport.overall_status === "partially_eligible"
                  ? "warning"
                  : "close-circle"}
                size={24}
                color={eligibilityReport.overall_status === "eligible"
                  ? colors.success
                  : eligibilityReport.overall_status === "partially_eligible"
                  ? colors.warning
                  : colors.error}
              />
            </View>
            <View style={styles.eligibilitySummaryText}>
              <Text style={styles.eligibilitySummaryTitle}>Eligibility Status</Text>
              <Text style={styles.eligibilitySummarySubtitle}>
                {eligibilityReport.overall_status === "eligible"
                  ? "You meet all requirements"
                  : eligibilityReport.overall_status === "partially_eligible"
                  ? `${eligibilityReport.critical_gaps.length} gap${eligibilityReport.critical_gaps.length > 1 ? "s" : ""} to address`
                  : "Action required before applying"}
              </Text>
            </View>
          </View>
          <Ionicons name="chevron-forward" size={20} color={colors.textSecondary} />
        </TouchableOpacity>
      )}

      {/* Bucket Tabs */}
      {!showEligibilityModal && renderBucketTabs()}

      {/* Content */}
      {showEligibilityModal && eligibilityReport ? (
        <View style={styles.eligibilityModalContent}>
          <EligibilityStatus report={eligibilityReport} />
          <TouchableOpacity
            style={styles.closeEligibilityButton}
            onPress={() => setShowEligibilityModal(false)}
          >
            <Text style={styles.closeEligibilityButtonText}>Close</Text>
          </TouchableOpacity>
        </View>
      ) : filteredRecommendations.length === 0 ? (
        <View style={styles.centerContent}>
          <Ionicons name="search" size={64} color={colors.textSecondary} />
          <Text style={styles.emptyTitle}>No recommendations found</Text>
          <Text style={styles.emptyText}>
            Try adjusting your profile preferences
          </Text>
          <TouchableOpacity
            style={styles.editProfileButton}
            onPress={() => router.push("/university-profile/wizard")}
          >
            <Text style={styles.editProfileButtonText}>Edit Profile</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {filteredRecommendations.map((item, index) =>
            renderUniversityCard(item, index),
          )}
        </ScrollView>
      )}

      {/* Floating Action Button */}
      {!showEligibilityModal && (
        <TouchableOpacity
          style={styles.fab}
          onPress={() => router.push("/university-recommender/shortlist")}
        >
          <Ionicons name="bookmark" size={24} color="#fff" />
          <Text style={styles.fabText}>View Shortlist</Text>
        </TouchableOpacity>
      )}
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
  headerTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: colors.text,
  },
  headerTitleContainer: {
    flex: 1,
    alignItems: "center",
  },
  cacheBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    backgroundColor: colors.background,
    borderRadius: 12,
    marginTop: spacing.xs,
  },
  cacheBadgeText: {
    fontSize: 11,
    color: colors.textSecondary,
    fontWeight: "500",
  },
  headerActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  eligibilityButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    position: "relative",
  },
  eligibilityButtonActive: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primary,
  },
  gapCountBadge: {
    position: "absolute",
    top: -4,
    right: -4,
    backgroundColor: colors.error,
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 4,
  },
  gapCountText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#fff",
  },
  refreshButton: {
    padding: spacing.xs,
  },
  iconButton: {
    padding: spacing.xs,
  },
  bucketTabs: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    maxHeight: 50,
  },
  bucketTab: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: 20,
    marginRight: spacing.sm,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    maxHeight: 50,
  },
  bucketTabActive: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primary,
  },
  bucketTabText: {
    fontSize: 14,
    color: colors.textSecondary,
    fontWeight: "500",
  },
  bucketTabTextActive: {
    color: colors.primary,
    fontWeight: "600",
  },
  content: {
    flex: 1,
    padding: spacing.md,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.md,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: spacing.md,
  },
  cardHeaderLeft: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
  },
  logoContainer: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: "rgba(255, 255, 255, 0.1)",
    overflow: "hidden",
  },
  logo: {
    width: 50,
    height: 50,
  },
  logoPlaceholder: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    alignItems: "center",
    justifyContent: "center",
  },
  campusPhotoContainer: {
    width: "100%",
    height: 150,
    overflow: "hidden",
  },
  campusPhoto: {
    width: "100%",
    height: "100%",
  },
  universityInfo: {
    flex: 1,
  },
  universityName: {
    fontSize: 16,
    fontWeight: "600",
    color: colors.text,
    marginBottom: 2,
  },
  universityLocation: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  bucketBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: 12,
  },
  bucketText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#fff",
  },
  statsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  statItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
  },
  statValue: {
    fontSize: 12,
    fontWeight: "600",
    color: colors.text,
  },
  statLabel: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  scoresContainer: {
    marginBottom: spacing.md,
    gap: spacing.xs,
  },
  scoreRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  scoreLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: colors.textSecondary,
    width: 60,
  },
  scoreBarContainer: {
    flex: 1,
    height: 8,
    backgroundColor: colors.border,
    borderRadius: 4,
    overflow: "hidden",
  },
  scoreBar: {
    height: "100%",
    borderRadius: 4,
  },
  scoreValue: {
    fontSize: 12,
    fontWeight: "700",
    width: 30,
    textAlign: "right",
  },
  insightsContainer: {
    backgroundColor: colors.background,
    borderRadius: 8,
    padding: spacing.sm,
    marginBottom: spacing.md,
    gap: spacing.sm,
  },
  insightHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    marginBottom: spacing.xs,
  },
  insightTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.text,
    flex: 1,
  },
  confidenceBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: 8,
  },
  confidenceText: {
    fontSize: 10,
    fontWeight: "600",
    color: colors.text,
  },
  insightSection: {
    gap: spacing.xs,
  },
  insightSectionTitle: {
    fontSize: 12,
    fontWeight: "600",
    color: colors.text,
    marginTop: spacing.xs,
  },
  insightBullet: {
    fontSize: 12,
    color: colors.textSecondary,
    lineHeight: 18,
  },
  cardActions: {
    flexDirection: "row",
    gap: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: spacing.sm,
  },
  actionButton: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.xs,
    paddingVertical: spacing.sm,
    borderRadius: 8,
    backgroundColor: colors.background,
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: "500",
    color: colors.textSecondary,
  },
  fab: {
    position: "absolute",
    bottom: spacing.lg,
    right: spacing.md,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 24,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  fabText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#fff",
  },
  centerContent: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    gap: spacing.md,
    padding: spacing.xl,
  },
  loadingText: {
    fontSize: 16,
    fontWeight: "600",
    color: colors.text,
  },
  loadingSubtext: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: "600",
    color: colors.text,
  },
  emptyText: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: "center",
  },
  editProfileButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderRadius: 12,
    marginTop: spacing.md,
  },
  editProfileButtonText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#fff",
  },
  // Eligibility Summary Card
  eligibilitySummaryCard: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: colors.card,
    marginHorizontal: spacing.md,
    marginTop: spacing.md,
    marginBottom: spacing.sm,
    padding: spacing.md,
    borderRadius: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  eligibilitySummaryLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    flex: 1,
  },
  eligibilitySummaryIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: "center",
    justifyContent: "center",
  },
  eligibilitySummaryText: {
    flex: 1,
  },
  eligibilitySummaryTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: colors.text,
    marginBottom: 2,
  },
  eligibilitySummarySubtitle: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  eligibilityModalContent: {
    flex: 1,
  },
  closeEligibilityButton: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
    borderRadius: 12,
    margin: spacing.md,
    alignItems: "center",
  },
  closeEligibilityButtonText: {
    fontSize: 16,
    fontWeight: "600",
    color: "#fff",
  },
});
