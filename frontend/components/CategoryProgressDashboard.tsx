import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { insightsAPI } from '@/services/api';
import { MaterialCommunityIcons } from '@expo/vector-icons';

const COLORS = {
  bg: '#000000',
  surface: '#1A1A1A',
  border: '#2A2A2A',
  text: '#FFFFFF',
  textSecondary: '#8E8E8E',
  primary: '#5B6AFF',
  study: '#FF3B30',
  language: '#3B82F6',
  sport: '#34C759',
  career: '#06B6D4',
  personal: '#A855F7',
};

interface CategoryProgress {
  completed: number;
  total: number;
  percentage: number;
  on_track: boolean;
}

interface CategoryData {
  [key: string]: CategoryProgress;
}

export default function CategoryProgressDashboard() {
  const [categoryData, setCategoryData] = useState<CategoryData>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCategoryProgress();
  }, []);

  const loadCategoryProgress = async () => {
    try {
      setLoading(true);
      const response = await insightsAPI.getCategoryProgress();
      setCategoryData(response.data);
    } catch (error) {
      console.error('Failed to load category progress:', error);
      Alert.alert('Error', 'Failed to load category progress');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (category: string): string => {
    switch (category.toLowerCase()) {
      case 'study': return COLORS.study;
      case 'language': return COLORS.language;
      case 'sport': return COLORS.sport;
      case 'career': return COLORS.career;
      default: return COLORS.personal;
    }
  };

  const getCategoryIcon = (category: string): string => {
    switch (category.toLowerCase()) {
      case 'study': return 'school';
      case 'language': return 'translate';
      case 'sport': return 'dumbbell';
      case 'career': return 'briefcase';
      default: return 'star';
    }
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <Text style={styles.header}>Category Progress</Text>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      </View>
    );
  }

  if (Object.keys(categoryData).length === 0) {
    return (
      <View style={styles.container}>
        <Text style={styles.header}>Category Progress</Text>
        <Text style={styles.emptyText}>No category data available yet</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Category Progress</Text>
      <View style={styles.categoriesGrid}>
        {Object.entries(categoryData).map(([category, data]) => (
          <View key={category} style={styles.categoryCard}>
            <View style={styles.categoryHeader}>
              <View style={[styles.iconContainer, { backgroundColor: getCategoryColor(category) }]}>
                <MaterialCommunityIcons
                  name={getCategoryIcon(category) as any}
                  size={20}
                  color="#fff"
                />
              </View>
              <Text style={styles.categoryName}>
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </Text>
            </View>

            {/* Circular Progress */}
            <View style={styles.progressContainer}>
              <View style={styles.circularProgress}>
                <View
                  style={[
                    styles.progressCircle,
                    {
                      borderColor: getCategoryColor(category),
                      borderTopWidth: data.percentage > 0 ? 4 : 0,
                      borderRightWidth: data.percentage > 25 ? 4 : 0,
                      borderBottomWidth: data.percentage > 50 ? 4 : 0,
                      borderLeftWidth: data.percentage > 75 ? 4 : 0,
                    }
                  ]}
                >
                  <Text style={styles.percentageText}>{data.percentage}%</Text>
                </View>
              </View>
            </View>

            {/* Stats */}
            <View style={styles.statsRow}>
              <Text style={styles.statsText}>
                {data.completed}/{data.total} tasks
              </Text>
              {data.on_track ? (
                <View style={styles.onTrackBadge}>
                  <MaterialCommunityIcons name="check-circle" size={12} color="#34C759" />
                  <Text style={styles.onTrackText}>On track</Text>
                </View>
              ) : (
                <View style={styles.behindBadge}>
                  <MaterialCommunityIcons name="alert-circle" size={12} color="#FF9500" />
                  <Text style={styles.behindText}>Behind</Text>
                </View>
              )}
            </View>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: COLORS.bg,
  },
  header: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 16,
  },
  loadingContainer: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
    paddingVertical: 32,
  },
  categoriesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  categoryCard: {
    width: '48%',
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  categoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  iconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  categoryName: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
    flex: 1,
  },
  progressContainer: {
    alignItems: 'center',
    marginVertical: 12,
  },
  circularProgress: {
    width: 80,
    height: 80,
    alignItems: 'center',
    justifyContent: 'center',
  },
  progressCircle: {
    width: 70,
    height: 70,
    borderRadius: 35,
    borderWidth: 4,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
    transform: [{ rotate: '-90deg' }],
  },
  percentageText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.text,
    transform: [{ rotate: '90deg' }],
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statsText: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  onTrackBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    backgroundColor: 'rgba(52, 199, 89, 0.1)',
    borderRadius: 4,
  },
  onTrackText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#34C759',
  },
  behindBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    backgroundColor: 'rgba(255, 149, 0, 0.1)',
    borderRadius: 4,
  },
  behindText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#FF9500',
  },
});
