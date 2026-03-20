import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

const COLORS = {
  surface: '#2A2A2A',
  border: '#3E3E3E',
  text: '#ECECEC',
  textSecondary: '#8E8E8E',
  primary: '#5B6AFF',
  warning: '#F59E0B',
  danger: '#EF4444',
};

interface Recommendation {
  id: string;
  type: 'focus' | 'replan' | 'accelerate' | 'info';
  message: string;
  actionText?: string;
  onAction?: () => void;
}

interface AIRecommendationPanelProps {
  recommendations: Recommendation[];
  onDismiss?: (id: string) => void;
}

export default function AIRecommendationPanel({
  recommendations,
  onDismiss,
}: AIRecommendationPanelProps) {
  if (recommendations.length === 0) return null;

  const getRecommendationIcon = (type: string) => {
    switch (type) {
      case 'focus':
        return 'target';
      case 'replan':
        return 'calendar-refresh';
      case 'accelerate':
        return 'rocket-launch';
      default:
        return 'information';
    }
  };

  const getRecommendationColor = (type: string) => {
    switch (type) {
      case 'focus':
        return COLORS.primary;
      case 'replan':
        return COLORS.warning;
      case 'accelerate':
        return COLORS.danger;
      default:
        return COLORS.textSecondary;
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.aiIcon}>
            <MaterialCommunityIcons name="robot" size={20} color={COLORS.primary} />
          </View>
          <Text style={styles.headerText}>AI Recommendations</Text>
        </View>
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.recommendationsContainer}
      >
        {recommendations.map((rec) => (
          <View key={rec.id} style={styles.recommendationCard}>
            {/* Icon & Type Indicator */}
            <View style={styles.cardHeader}>
              <View
                style={[
                  styles.typeIndicator,
                  { backgroundColor: `${getRecommendationColor(rec.type)}20` },
                ]}
              >
                <MaterialCommunityIcons
                  name={getRecommendationIcon(rec.type)}
                  size={18}
                  color={getRecommendationColor(rec.type)}
                />
              </View>
              {onDismiss && (
                <TouchableOpacity
                  onPress={() => onDismiss(rec.id)}
                  style={styles.dismissButton}
                >
                  <MaterialCommunityIcons name="close" size={16} color={COLORS.textSecondary} />
                </TouchableOpacity>
              )}
            </View>

            {/* Message */}
            <Text style={styles.message}>{rec.message}</Text>

            {/* Action Button */}
            {rec.actionText && rec.onAction && (
              <TouchableOpacity
                style={[styles.actionButton, { borderColor: getRecommendationColor(rec.type) }]}
                onPress={rec.onAction}
              >
                <Text style={[styles.actionText, { color: getRecommendationColor(rec.type) }]}>
                  {rec.actionText}
                </Text>
                <MaterialCommunityIcons
                  name="arrow-right"
                  size={16}
                  color={getRecommendationColor(rec.type)}
                />
              </TouchableOpacity>
            )}
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  aiIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(16, 163, 127, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  recommendationsContainer: {
    gap: 12,
    paddingRight: 16,
  },
  recommendationCard: {
    width: 280,
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  typeIndicator: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  dismissButton: {
    padding: 4,
  },
  message: {
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 20,
    marginBottom: 12,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1.5,
  },
  actionText: {
    fontSize: 13,
    fontWeight: '600',
  },
});
