import { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
} from "react-native";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";

const API_URL = process.env.EXPO_PUBLIC_API_URL || "http://192.168.0.210:8000";

interface WeeklyReviewData {
  week_start: string;
  week_end: string;
  stats: {
    total_tasks: number;
    completed: number;
    completion_rate: number;
    total_hours: number;
    avg_progress: number;
  };
  wins: Array<{
    type: string;
    title: string;
    message?: string;
    progress?: number;
  }>;
  blockers: Array<{
    type: string;
    title: string;
    task_id?: number;
    reason?: string;
  }>;
  streaks: {
    current_streak: number;
    longest_week_streak: number;
    daily_completion: Array<{
      date: string;
      completed: number;
      total: number;
      has_activity: boolean;
    }>;
  };
  next_week_plan: {
    total_tasks: number;
    total_hours: number;
    focus_areas: Array<{
      goal: string;
      task_count: number;
    }>;
  };
}

export default function WeeklyReviewScreen() {
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [reviewData, setReviewData] = useState<WeeklyReviewData | null>(null);
  const [selectedWeekStart, setSelectedWeekStart] = useState(() => {
    // Get last Monday
    const today = new Date();
    const dayOfWeek = today.getDay();
    const diff = today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1);
    return new Date(today.setDate(diff));
  });

  useEffect(() => {
    loadReview();
  }, [selectedWeekStart]);

  const loadReview = async () => {
    try {
      setLoading(true);
      const token = await AsyncStorage.getItem("access_token");
      const dateStr = selectedWeekStart.toISOString().split("T")[0];

      const response = await axios.get(
        `${API_URL}/todos/weekly-review/?week_start=${dateStr}`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setReviewData(response.data);
    } catch (error) {
      console.error("Failed to load review:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReview = async () => {
    try {
      setGenerating(true);
      const token = await AsyncStorage.getItem("access_token");
      const dateStr = selectedWeekStart.toISOString().split("T")[0];

      const response = await axios.post(
        `${API_URL}/todos/weekly-review/generate/`,
        { week_start: dateStr },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setReviewData(response.data);
    } catch (error) {
      console.error("Failed to generate review:", error);
    } finally {
      setGenerating(false);
    }
  };

  const navigateWeek = (direction: "prev" | "next") => {
    const newDate = new Date(selectedWeekStart);
    newDate.setDate(newDate.getDate() + (direction === "next" ? 7 : -7));
    setSelectedWeekStart(newDate);
  };

  if (loading) {
    return (
      <View style={[styles.container, styles.centered]}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Weekly Review</Text>
        <TouchableOpacity
          style={styles.generateButton}
          onPress={handleGenerateReview}
          disabled={generating}
        >
          {generating ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <>
              <MaterialCommunityIcons name="refresh" size={16} color="#fff" />
              <Text style={styles.generateButtonText}>Refresh</Text>
            </>
          )}
        </TouchableOpacity>
      </View>

      <ScrollView
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={loadReview} />
        }
      >
        {/* Week Selector */}
        <View style={styles.weekSelector}>
          <TouchableOpacity onPress={() => navigateWeek("prev")}>
            <MaterialCommunityIcons
              name="chevron-left"
              size={24}
              color="#ECECEC"
            />
          </TouchableOpacity>

          <Text style={styles.weekText}>
            {selectedWeekStart.toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            })}
            {" - "}
            {new Date(
              selectedWeekStart.getTime() + 6 * 24 * 60 * 60 * 1000,
            ).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
          </Text>

          <TouchableOpacity onPress={() => navigateWeek("next")}>
            <MaterialCommunityIcons
              name="chevron-right"
              size={24}
              color="#ECECEC"
            />
          </TouchableOpacity>
        </View>

        {reviewData ? (
          <>
            {/* Stats */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Statistics</Text>
              <View style={styles.statsGrid}>
                <View style={styles.statCard}>
                  <MaterialCommunityIcons
                    name="checkbox-marked-circle"
                    size={32}
                    color="#34C759"
                  />
                  <Text style={styles.statValue}>
                    {reviewData.stats.completed}
                  </Text>
                  <Text style={styles.statLabel}>Completed</Text>
                </View>
                <View style={styles.statCard}>
                  <MaterialCommunityIcons
                    name="percent"
                    size={32}
                    color="#007AFF"
                  />
                  <Text style={styles.statValue}>
                    {reviewData.stats.completion_rate}%
                  </Text>
                  <Text style={styles.statLabel}>Success Rate</Text>
                </View>
                <View style={styles.statCard}>
                  <MaterialCommunityIcons
                    name="clock"
                    size={32}
                    color="#FF9500"
                  />
                  <Text style={styles.statValue}>
                    {reviewData.stats.total_hours}h
                  </Text>
                  <Text style={styles.statLabel}>Time Invested</Text>
                </View>
              </View>
            </View>

            {/* Wins */}
            {reviewData.wins.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Wins 🎉</Text>
                {reviewData.wins.map((win, index) => (
                  <View key={index} style={styles.card}>
                    <MaterialCommunityIcons
                      name="trophy"
                      size={20}
                      color="#FFD700"
                    />
                    <View style={styles.cardContent}>
                      <Text style={styles.cardTitle}>{win.title}</Text>
                      {win.message && (
                        <Text style={styles.cardSubtitle}>{win.message}</Text>
                      )}
                    </View>
                  </View>
                ))}
              </View>
            )}

            {/* Blockers */}
            {reviewData.blockers.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Blockers ⚠️</Text>
                {reviewData.blockers.map((blocker, index) => (
                  <View key={index} style={[styles.card, styles.blockerCard]}>
                    <MaterialCommunityIcons
                      name="alert-circle"
                      size={20}
                      color="#FF3B30"
                    />
                    <View style={styles.cardContent}>
                      <Text style={styles.cardTitle}>{blocker.title}</Text>
                      {blocker.reason && (
                        <Text style={styles.cardSubtitle}>
                          {blocker.reason}
                        </Text>
                      )}
                    </View>
                  </View>
                ))}
              </View>
            )}

            {/* Streaks */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Streaks 🔥</Text>
              <View style={styles.streakCard}>
                <View style={styles.streakRow}>
                  <Text style={styles.streakLabel}>Current Streak:</Text>
                  <Text style={styles.streakValue}>
                    {reviewData.streaks.current_streak} days
                  </Text>
                </View>
                <View style={styles.streakRow}>
                  <Text style={styles.streakLabel}>Best This Week:</Text>
                  <Text style={styles.streakValue}>
                    {reviewData.streaks.longest_week_streak} days
                  </Text>
                </View>
              </View>

              {/* Daily Completion Dots */}
              <View style={styles.weekDots}>
                {reviewData.streaks.daily_completion.map((day, index) => (
                  <View key={index} style={styles.dayDot}>
                    <View
                      style={[styles.dot, day.has_activity && styles.dotActive]}
                    />
                    <Text style={styles.dayLabel}>
                      {new Date(day.date).toLocaleDateString("en-US", {
                        weekday: "short",
                      })}
                    </Text>
                  </View>
                ))}
              </View>
            </View>

            {/* Next Week */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Next Week Preview</Text>
              <View style={styles.previewCard}>
                <View style={styles.previewRow}>
                  <Text style={styles.previewLabel}>Planned Tasks:</Text>
                  <Text style={styles.previewValue}>
                    {reviewData.next_week_plan.total_tasks}
                  </Text>
                </View>
                <View style={styles.previewRow}>
                  <Text style={styles.previewLabel}>Estimated Time:</Text>
                  <Text style={styles.previewValue}>
                    {reviewData.next_week_plan.total_hours}h
                  </Text>
                </View>

                {reviewData.next_week_plan.focus_areas.length > 0 && (
                  <View style={styles.focusAreas}>
                    <Text style={styles.focusTitle}>Focus Areas:</Text>
                    {reviewData.next_week_plan.focus_areas.map(
                      (area, index) => (
                        <View key={index} style={styles.focusItem}>
                          <Text style={styles.focusGoal}>{area.goal}</Text>
                          <Text style={styles.focusCount}>
                            {area.task_count} tasks
                          </Text>
                        </View>
                      ),
                    )}
                  </View>
                )}
              </View>
            </View>
          </>
        ) : (
          <View style={styles.emptyState}>
            <MaterialCommunityIcons
              name="chart-line"
              size={64}
              color="#3E3E3E"
            />
            <Text style={styles.emptyText}>No review available</Text>
            <Text style={styles.emptySubtext}>
              Tap "Refresh" to generate your weekly review
            </Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#1A1A1A",
  },
  centered: {
    justifyContent: "center",
    alignItems: "center",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    paddingTop: 60,
    backgroundColor: "#2A2A2A",
    borderBottomWidth: 1,
    borderBottomColor: "#3E3E3E",
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#ECECEC",
  },
  generateButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: "#007AFF",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  generateButtonText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#fff",
  },
  weekSelector: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 16,
    backgroundColor: "#2A2A2A",
    borderBottomWidth: 1,
    borderBottomColor: "#3E3E3E",
  },
  weekText: {
    fontSize: 16,
    fontWeight: "600",
    color: "#ECECEC",
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#ECECEC",
    marginBottom: 12,
  },
  statsGrid: {
    flexDirection: "row",
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: "#2A2A2A",
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    gap: 8,
    borderWidth: 1,
    borderColor: "#3E3E3E",
  },
  statValue: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#ECECEC",
  },
  statLabel: {
    fontSize: 12,
    color: "#8E8E8E",
  },
  card: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
    backgroundColor: "#2A2A2A",
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: "#3E3E3E",
  },
  blockerCard: {
    borderColor: "#FF3B30",
  },
  cardContent: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: "600",
    color: "#ECECEC",
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 13,
    color: "#8E8E8E",
  },
  streakCard: {
    backgroundColor: "#2A2A2A",
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#3E3E3E",
  },
  streakRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  streakLabel: {
    fontSize: 15,
    color: "#ECECEC",
  },
  streakValue: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#FF9500",
  },
  weekDots: {
    flexDirection: "row",
    justifyContent: "space-around",
    paddingVertical: 12,
  },
  dayDot: {
    alignItems: "center",
    gap: 8,
  },
  dot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: "#3E3E3E",
  },
  dotActive: {
    backgroundColor: "#34C759",
  },
  dayLabel: {
    fontSize: 11,
    color: "#8E8E8E",
  },
  previewCard: {
    backgroundColor: "#2A2A2A",
    borderRadius: 8,
    padding: 16,
    borderWidth: 1,
    borderColor: "#3E3E3E",
  },
  previewRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  previewLabel: {
    fontSize: 15,
    color: "#ECECEC",
  },
  previewValue: {
    fontSize: 17,
    fontWeight: "600",
    color: "#007AFF",
  },
  focusAreas: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "#3E3E3E",
  },
  focusTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#ECECEC",
    marginBottom: 8,
  },
  focusItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 6,
  },
  focusGoal: {
    fontSize: 14,
    color: "#ECECEC",
  },
  focusCount: {
    fontSize: 14,
    color: "#8E8E8E",
  },
  emptyState: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: "600",
    color: "#8E8E8E",
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: "#666",
    marginTop: 8,
  },
});
