/**
 * Eligibility Status Component
 *
 * Displays user's eligibility for their selected universities, including:
 * - Overall eligibility status (eligible, partially eligible, not eligible)
 * - Critical gaps that need to be addressed
 * - University-by-university breakdown
 * - Solutions and timelines for addressing gaps
 */

import React from "react";
import { View, Text, StyleSheet, ScrollView } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors, spacing } from "@/theme";

export interface CriticalGap {
  gap: string;
  affected_universities: string[];
  solution: string;
  timeline: string;
}

export interface UniversityEligibility {
  status: "eligible" | "partially_eligible" | "not_eligible";
  gaps: string[];
  missing_requirements: string[];
  solutions: string[];
  fastest_path: string;
  timeline?: string;
}

export interface EligibilityReport {
  overall_status: "eligible" | "partially_eligible" | "not_eligible";
  by_university: Record<string, UniversityEligibility>;
  critical_gaps: CriticalGap[];
}

interface EligibilityStatusProps {
  report: EligibilityReport;
}

export const EligibilityStatus: React.FC<EligibilityStatusProps> = ({
  report,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "eligible":
        return colors.success;
      case "partially_eligible":
        return colors.warning;
      case "not_eligible":
        return colors.error;
      default:
        return colors.textSecondary;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "eligible":
        return "checkmark-circle";
      case "partially_eligible":
        return "warning";
      case "not_eligible":
        return "close-circle";
      default:
        return "help-circle";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "eligible":
        return "Eligible";
      case "partially_eligible":
        return "Partially Eligible";
      case "not_eligible":
        return "Not Eligible";
      default:
        return "Unknown";
    }
  };

  const renderOverallStatus = () => (
    <View
      style={[
        styles.overallStatusCard,
        {
          borderLeftColor: getStatusColor(report.overall_status),
        },
      ]}
    >
      <View style={styles.overallStatusHeader}>
        <Ionicons
          name={getStatusIcon(report.overall_status)}
          size={24}
          color={getStatusColor(report.overall_status)}
        />
        <Text style={styles.overallStatusTitle}>Overall Eligibility</Text>
      </View>
      <Text
        style={[
          styles.overallStatusText,
          { color: getStatusColor(report.overall_status) },
        ]}
      >
        {getStatusLabel(report.overall_status)}
      </Text>
      {report.overall_status === "eligible" ? (
        <Text style={styles.overallStatusDescription}>
          Your profile meets the basic requirements for your chosen universities.
        </Text>
      ) : report.overall_status === "partially_eligible" ? (
        <Text style={styles.overallStatusDescription}>
          You have some gaps that may affect admission to certain universities.
        </Text>
      ) : (
        <Text style={styles.overallStatusDescription}>
          You have critical gaps that need to be addressed before applying.
        </Text>
      )}
    </View>
  );

  const renderCriticalGaps = () => {
    if (report.critical_gaps.length === 0) {
      return (
        <View style={styles.noGapsCard}>
          <Ionicons name="checkmark-circle" size={48} color={colors.success} />
          <Text style={styles.noGapsTitle}>No Critical Gaps</Text>
          <Text style={styles.noGapsDescription}>
            Your profile meets the basic requirements for your chosen universities.
          </Text>
        </View>
      );
    }

    return (
      <View style={styles.sectionContainer}>
        <View style={styles.sectionHeader}>
          <Ionicons name="alert-circle" size={20} color={colors.error} />
          <Text style={styles.sectionTitle}>Action Required</Text>
        </View>
        <Text style={styles.sectionDescription}>
          You have {report.critical_gaps.length} gap
          {report.critical_gaps.length > 1 ? "s" : ""} that need to be addressed:
        </Text>

        {report.critical_gaps.map((gap, index) => (
          <View key={index} style={styles.gapCard}>
            <View style={styles.gapHeader}>
              <Ionicons name="warning" size={18} color={colors.error} />
              <Text style={styles.gapTitle}>{gap.gap}</Text>
            </View>

            <View style={styles.gapSection}>
              <Text style={styles.gapSectionLabel}>Affected Universities:</Text>
              <View style={styles.universitiesList}>
                {gap.affected_universities.map((uni, i) => (
                  <View key={i} style={styles.universityTag}>
                    <Text style={styles.universityTagText}>
                      {typeof uni === "string"
                        ? uni.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())
                        : uni}
                    </Text>
                  </View>
                ))}
              </View>
            </View>

            <View style={styles.gapSection}>
              <Text style={styles.gapSectionLabel}>Solution:</Text>
              <Text style={styles.gapSolutionText}>{gap.solution}</Text>
            </View>

            <View style={styles.gapSection}>
              <Text style={styles.gapSectionLabel}>Timeline:</Text>
              <View style={styles.timelineContainer}>
                <Ionicons name="time" size={16} color={colors.info} />
                <Text style={styles.timelineText}>{gap.timeline}</Text>
              </View>
            </View>
          </View>
        ))}
      </View>
    );
  };

  const renderUniversityBreakdown = () => {
    const universities = Object.entries(report.by_university);

    if (universities.length === 0) {
      return null;
    }

    return (
      <View style={styles.sectionContainer}>
        <View style={styles.sectionHeader}>
          <Ionicons name="list" size={20} color={colors.primary} />
          <Text style={styles.sectionTitle}>University Breakdown</Text>
        </View>

        {universities.map(([uniSlug, uniData]) => (
          <View key={uniSlug} style={styles.uniCard}>
            <View style={styles.uniHeader}>
              <Text style={styles.uniName}>
                {uniSlug.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
              </Text>
              <View
                style={[
                  styles.uniStatusBadge,
                  { backgroundColor: getStatusColor(uniData.status) + "20" },
                ]}
              >
                <Ionicons
                  name={getStatusIcon(uniData.status)}
                  size={16}
                  color={getStatusColor(uniData.status)}
                />
                <Text
                  style={[
                    styles.uniStatusText,
                    { color: getStatusColor(uniData.status) },
                  ]}
                >
                  {getStatusLabel(uniData.status)}
                </Text>
              </View>
            </View>

            {uniData.gaps.length > 0 && (
              <View style={styles.uniSection}>
                <Text style={styles.uniSectionLabel}>Gaps:</Text>
                {uniData.gaps.map((gap, i) => {
                  const gapText = typeof gap === "string" ? gap : gap.gap || gap.status || "Unknown gap";
                  return (
                    <Text key={i} style={styles.uniBullet}>
                      • {gapText}
                    </Text>
                  );
                })}
              </View>
            )}

            {uniData.solutions.length > 0 && (
              <View style={styles.uniSection}>
                <Text style={styles.uniSectionLabel}>Solutions:</Text>
                {uniData.solutions.map((solution, i) => {
                  const solutionText = typeof solution === "string" ? solution : solution.toString();
                  return (
                    <Text key={i} style={styles.uniBullet}>
                      • {solutionText}
                    </Text>
                  );
                })}
              </View>
            )}

            {uniData.fastest_path && (
              <View style={styles.uniSection}>
                <Text style={styles.uniSectionLabel}>Fastest Path:</Text>
                <Text style={styles.uniFastestPath}>{uniData.fastest_path}</Text>
              </View>
            )}
          </View>
        ))}
      </View>
    );
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {renderOverallStatus()}
      {renderCriticalGaps()}
      {renderUniversityBreakdown()}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  overallStatusCard: {
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: spacing.md,
    marginHorizontal: spacing.md,
    marginTop: spacing.md,
    borderLeftWidth: 4,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  overallStatusHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  overallStatusTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: colors.text,
  },
  overallStatusText: {
    fontSize: 24,
    fontWeight: "700",
    marginBottom: spacing.xs,
  },
  overallStatusDescription: {
    fontSize: 14,
    color: colors.textSecondary,
    lineHeight: 20,
  },
  sectionContainer: {
    marginTop: spacing.lg,
    paddingHorizontal: spacing.md,
  },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: colors.text,
  },
  sectionDescription: {
    fontSize: 14,
    color: colors.textSecondary,
    marginBottom: spacing.md,
    marginLeft: 28,
  },
  noGapsCard: {
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: spacing.xl,
    marginHorizontal: spacing.md,
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  noGapsTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: colors.text,
    marginTop: spacing.md,
  },
  noGapsDescription: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: "center",
    marginTop: spacing.sm,
  },
  gapCard: {
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
  gapHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  gapTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: colors.text,
    flex: 1,
  },
  gapSection: {
    marginTop: spacing.sm,
  },
  gapSectionLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: colors.textSecondary,
    marginBottom: spacing.xs,
    textTransform: "uppercase",
  },
  universitiesList: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.xs,
  },
  universityTag: {
    backgroundColor: colors.background,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: 8,
  },
  universityTagText: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  gapSolutionText: {
    fontSize: 14,
    color: colors.text,
    lineHeight: 20,
  },
  timelineContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
  },
  timelineText: {
    fontSize: 14,
    color: colors.info,
    fontWeight: "500",
  },
  uniCard: {
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
  uniHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: spacing.sm,
  },
  uniName: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.text,
    flex: 1,
  },
  uniStatusBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: 12,
  },
  uniStatusText: {
    fontSize: 12,
    fontWeight: "600",
  },
  uniSection: {
    marginTop: spacing.sm,
  },
  uniSectionLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  uniBullet: {
    fontSize: 13,
    color: colors.textSecondary,
    marginLeft: spacing.sm,
    lineHeight: 18,
  },
  uniFastestPath: {
    fontSize: 13,
    color: colors.primary,
    fontWeight: "500",
    marginLeft: spacing.sm,
  },
});

export default EligibilityStatus;
