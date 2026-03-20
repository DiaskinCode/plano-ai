/**
 * University Comparison Screen
 *
 * Allows side-by-side comparison of 2-4 universities
 * Universities are passed via query params: ?universities=mit,stanford,harvard
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  SafeAreaView,
  StatusBar,
  Dimensions,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { universityRecommenderAPI } from '@/services/universityRecommenderApi';
import { colors, spacing } from '@/theme';

const { width } = Dimensions.get('window');

interface UniversityData {
  short_name: string;
  name: string;
  location: string;
  acceptance_rate: number;
  total_cost: number;
  need_blind: boolean;
  international_aid: boolean;
  campus_type: string;
  undergraduate_enrollment: number;
  popular_majors: string[];
  employed_within_6_months: number | null;
  [key: string]: any;
}

type ComparisonCategory = 'overview' | 'academics' | 'costs' | 'outcomes';

const CATEGORIES = [
  { key: 'overview' as ComparisonCategory, title: 'Overview', icon: 'information-circle' },
  { key: 'academics' as ComparisonCategory, title: 'Academics', icon: 'school' },
  { key: 'costs' as ComparisonCategory, title: 'Costs & Aid', icon: 'cash' },
  { key: 'outcomes' as ComparisonCategory, title: 'Outcomes', icon: 'trending-up' },
];

export default function UniversityCompare() {
  const params = useLocalSearchParams();
  const universitiesParam = params.universities as string;

  const [loading, setLoading] = useState(true);
  const [universities, setUniversities] = useState<UniversityData[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<ComparisonCategory>('overview');

  useEffect(() => {
    loadUniversities();
  }, [universitiesParam]);

  const loadUniversities = async () => {
    if (!universitiesParam) {
      router.back();
      return;
    }

    try {
      setLoading(true);
      const shortNames = universitiesParam.split(',').filter(Boolean);

      // Fetch each university's data
      const promises = shortNames.map(async (shortName) => {
        try {
          const response = await universityRecommenderAPI.searchUniversities(shortName);
          const uni = response.data.find((u: any) => u.short_name === shortName);
          return uni;
        } catch (error) {
          console.error(`Failed to load ${shortName}:`, error);
          return null;
        }
      });

      const results = await Promise.all(promises);
      const validUniversities = results.filter(Boolean);

      if (validUniversities.length === 0) {
        router.back();
        return;
      }

      setUniversities(validUniversities);
    } catch (error: any) {
      console.error('Failed to load universities:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderCategoryTabs = () => (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      style={styles.categoryTabs}
      contentContainerStyle={styles.categoryTabsContent}
    >
      {CATEGORIES.map((category) => (
        <TouchableOpacity
          key={category.key}
          style={[
            styles.categoryTab,
            selectedCategory === category.key && styles.categoryTabActive,
          ]}
          onPress={() => setSelectedCategory(category.key)}
        >
          <Ionicons
            name={category.icon as any}
            size={20}
            color={selectedCategory === category.key ? colors.primary : colors.textSecondary}
          />
          <Text
            style={[
              styles.categoryTabText,
              selectedCategory === category.key && styles.categoryTabTextActive,
            ]}
          >
            {category.title}
          </Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );

  const renderUniversityHeader = (uni: UniversityData, index: number) => (
    <View key={uni.short_name} style={[styles.uniColumn, { width: (width - 60) / universities.length }]}>
      <View style={styles.uniHeader}>
        <Text style={styles.uniName}>{uni.name}</Text>
        <Text style={styles.uniLocation}>{uni.location}</Text>
      </View>
    </View>
  );

  const renderComparisonRow = (
    icon: string,
    label: string,
    values: (string | number | boolean | null)[],
    highlight: boolean = false
  ) => (
    <View style={[styles.comparisonRow, highlight && styles.comparisonRowHighlight]}>
      <View style={styles.rowLabel}>
        <Ionicons name={icon as any} size={18} color={colors.textSecondary} />
        <Text style={styles.rowLabelText}>{label}</Text>
      </View>
      <View style={styles.rowValues}>
        {values.map((value, index) => (
          <View
            key={index}
            style={[styles.rowValue, { width: (width - 60) / universities.length }]}
          >
            <Text style={styles.rowValueText}>
              {value === null ? '—' :
               typeof value === 'boolean' ? (value ? '✓' : '✗') :
               typeof value === 'number' ? value.toLocaleString() :
               value}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );

  const renderMultiRow = (
    icon: string,
    label: string,
    arrays: (string[] | null)[]
  ) => (
    <View style={styles.comparisonRow}>
      <View style={styles.rowLabel}>
        <Ionicons name={icon as any} size={18} color={colors.textSecondary} />
        <Text style={styles.rowLabelText}>{label}</Text>
      </View>
      <View style={styles.rowValues}>
        {arrays.map((array, index) => (
          <View
            key={index}
            style={[styles.rowValue, styles.multiLineValue, { width: (width - 60) / universities.length }]}
          >
            {array && array.length > 0 ? (
              array.map((item, i) => (
                <Text key={i} style={styles.listItem}>• {item}</Text>
              ))
            ) : (
              <Text style={styles.rowValueText}>—</Text>
            )}
          </View>
        ))}
      </View>
    </View>
  );

  const renderOverview = () => (
    <View style={styles.comparisonSection}>
      {renderComparisonRow('locate', 'Location', universities.map(u => u.location))}
      {renderComparisonRow(
        'people',
        'Enrollment',
        universities.map(u => u.undergraduate_enrollment || null)
      )}
      {renderComparisonRow(
        'home',
        'Campus Type',
        universities.map(u => u.campus_type || 'N/A')
      )}
      {renderComparisonRow(
        'trending-up',
        'Acceptance Rate',
        universities.map(u => `${u.acceptance_rate}%`),
        true
      )}
      {renderComparisonRow(
        'shield-checkmark',
        'Need-Blind',
        universities.map(u => u.need_blind),
        true
      )}
      {renderComparisonRow(
        'globe',
        'International Aid',
        universities.map(u => u.international_aid),
        true
      )}
    </View>
  );

  const renderAcademics = () => (
    <View style={styles.comparisonSection}>
      {renderMultiRow(
        'book',
        'Popular Majors',
        universities.map(u => u.popular_majors || null)
      )}
      {renderComparisonRow(
        'school',
        'Undergraduates',
        universities.map(u => u.undergraduate_enrollment || null)
      )}
    </View>
  );

  const renderCosts = () => (
    <View style={styles.comparisonSection}>
      {renderComparisonRow(
        'cash',
        'Total Cost/Year',
        universities.map(u => `$${(u.total_cost || 0).toLocaleString()}`),
        true
      )}
      {renderComparisonRow(
        'shield-checkmark',
        'Need-Blind',
        universities.map(u => u.need_blind),
        true
      )}
      {renderComparisonRow(
        'globe',
        'International Aid',
        universities.map(u => u.international_aid),
        true
      )}
    </View>
  );

  const renderOutcomes = () => (
    <View style={styles.comparisonSection}>
      {renderComparisonRow(
        'briefcase',
        'Employed within 6 months',
        universities.map(u => u.employed_within_6_months ? `${u.employed_within_6_months}%` : null),
        true
      )}
    </View>
  );

  const renderCategoryContent = () => {
    switch (selectedCategory) {
      case 'overview':
        return renderOverview();
      case 'academics':
        return renderAcademics();
      case 'costs':
        return renderCosts();
      case 'outcomes':
        return renderOutcomes();
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading comparison...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Compare Universities</Text>
        <View style={styles.placeholder} />
      </View>

      {/* University Headers */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.uniHeaders}
        contentContainerStyle={styles.uniHeadersContent}
      >
        {universities.map((uni, index) => renderUniversityHeader(uni, index))}
      </ScrollView>

      {/* Category Tabs */}
      {renderCategoryTabs()}

      {/* Comparison Content */}
      <ScrollView
        style={styles.content}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.contentContainer}
      >
        {renderCategoryContent()}
      </ScrollView>

      {/* Footer Actions */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.footerButton}
          onPress={() => router.push('/university-recommender/results')}
        >
          <Text style={styles.footerButtonText}>Back to Results</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
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
    fontWeight: '600',
    color: colors.text,
  },
  placeholder: {
    width: 24,
  },
  uniHeaders: {
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: colors.card,
  },
  uniHeadersContent: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    gap: spacing.md,
  },
  uniColumn: {
    gap: spacing.xs,
  },
  uniHeader: {
    gap: spacing.xs,
  },
  uniName: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text,
  },
  uniLocation: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  categoryTabs: {
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: colors.card,
  },
  categoryTabsContent: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    gap: spacing.sm,
  },
  categoryTab: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 20,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
  },
  categoryTabActive: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primary,
  },
  categoryTabText: {
    fontSize: 14,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  categoryTabTextActive: {
    color: colors.primary,
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    paddingVertical: spacing.md,
  },
  comparisonSection: {
    gap: spacing.sm,
  },
  comparisonRow: {
    flexDirection: 'row',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    alignItems: 'flex-start',
  },
  comparisonRowHighlight: {
    backgroundColor: colors.primaryLight,
  },
  rowLabel: {
    width: 120,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  rowLabelText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textSecondary,
    flex: 1,
  },
  rowValues: {
    flex: 1,
    flexDirection: 'row',
  },
  rowValue: {
    alignItems: 'center',
    paddingVertical: spacing.xs,
  },
  multiLineValue: {
    alignItems: 'flex-start',
  },
  rowValueText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    textAlign: 'center',
  },
  listItem: {
    fontSize: 12,
    color: colors.text,
    marginBottom: spacing.xs,
  },
  footer: {
    padding: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.card,
  },
  footerButton: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.md,
    borderRadius: 12,
    alignItems: 'center',
  },
  footerButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: spacing.md,
  },
  loadingText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
    marginTop: spacing.md,
  },
});
