import { View, Text, StyleSheet, TouchableOpacity, Animated } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useState, useRef, useEffect } from 'react';

const COLORS = {
  surface: '#2A2A2A',
  border: '#3E3E3E',
  text: '#ECECEC',
  textSecondary: '#8E8E8E',
  primary: '#5B6AFF',
  onTrack: '#5B6AFF',
  atRisk: '#F59E0B',
  stalled: '#EF4444',
};

interface GoalCardProps {
  goal: {
    id: number;
    title: string;
    description?: string;
    progress: number; // 0-100
    status: 'on_track' | 'at_risk' | 'stalled';
    linkedTasksCount: number;
    motivationalText?: string;
  };
  level: number; // 0 = long-term, 1 = mid-term, 2 = short-term
  onPress?: () => void;
  onExpand?: () => void;
  isExpanded?: boolean;
}

export default function GoalCard({
  goal,
  level,
  onPress,
  onExpand,
  isExpanded = false,
}: GoalCardProps) {
  const [expanded, setExpanded] = useState(isExpanded);
  const animatedHeight = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(animatedHeight, {
      toValue: expanded ? 1 : 0,
      duration: 300,
      useNativeDriver: false,
    }).start();
  }, [expanded]);

  const handleExpand = () => {
    setExpanded(!expanded);
    if (onExpand) onExpand();
  };

  const getStatusColor = () => {
    switch (goal.status) {
      case 'on_track':
        return COLORS.onTrack;
      case 'at_risk':
        return COLORS.atRisk;
      case 'stalled':
        return COLORS.stalled;
      default:
        return COLORS.textSecondary;
    }
  };

  const getStatusIcon = () => {
    switch (goal.status) {
      case 'on_track':
        return 'check-circle';
      case 'at_risk':
        return 'alert-circle';
      case 'stalled':
        return 'close-circle';
      default:
        return 'help-circle';
    }
  };

  const getStatusText = () => {
    switch (goal.status) {
      case 'on_track':
        return 'On track';
      case 'at_risk':
        return 'At risk';
      case 'stalled':
        return 'Stalled';
      default:
        return 'Unknown';
    }
  };

  const levelIndent = level * 20;

  return (
    <View style={[styles.container, { marginLeft: levelIndent }]}>
      <TouchableOpacity
        style={[styles.card, { borderLeftColor: getStatusColor(), borderLeftWidth: 4 }]}
        onPress={onPress}
        activeOpacity={0.7}
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.titleContainer}>
            <Text style={styles.title} numberOfLines={2}>
              {goal.title}
            </Text>
            {goal.linkedTasksCount > 0 && (
              <View style={styles.tasksBadge}>
                <MaterialCommunityIcons name="link-variant" size={12} color={COLORS.primary} />
                <Text style={styles.tasksBadgeText}>{goal.linkedTasksCount}</Text>
              </View>
            )}
          </View>
          {onExpand && (
            <TouchableOpacity onPress={handleExpand} style={styles.expandButton}>
              <MaterialCommunityIcons
                name={expanded ? 'chevron-up' : 'chevron-down'}
                size={24}
                color={COLORS.textSecondary}
              />
            </TouchableOpacity>
          )}
        </View>

        {/* Progress Bar */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${goal.progress}%` }]} />
          </View>
          <Text style={styles.progressText}>{Math.round(goal.progress)}%</Text>
        </View>

        {/* Status & Motivational Text */}
        <View style={styles.footer}>
          <View style={styles.statusBadge}>
            <MaterialCommunityIcons
              name={getStatusIcon()}
              size={14}
              color={getStatusColor()}
            />
            <Text style={[styles.statusText, { color: getStatusColor() }]}>
              {getStatusText()}
            </Text>
          </View>
          {goal.motivationalText && (
            <Text style={styles.motivationalText} numberOfLines={1}>
              "{goal.motivationalText}"
            </Text>
          )}
        </View>
      </TouchableOpacity>

      {/* Expanded Description */}
      {expanded && goal.description && (
        <Animated.View
          style={[
            styles.expandedContent,
            {
              opacity: animatedHeight,
              maxHeight: animatedHeight.interpolate({
                inputRange: [0, 1],
                outputRange: [0, 200],
              }),
            },
          ]}
        >
          <Text style={styles.description}>{goal.description}</Text>
        </Animated.View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 12,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  titleContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    flex: 1,
  },
  tasksBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(16, 163, 127, 0.1)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  tasksBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
  },
  expandButton: {
    padding: 4,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  progressBar: {
    flex: 1,
    height: 6,
    backgroundColor: COLORS.border,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: COLORS.primary,
    borderRadius: 3,
  },
  progressText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textSecondary,
    minWidth: 38,
    textAlign: 'right',
  },
  footer: {
    gap: 8,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    alignSelf: 'flex-start',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  motivationalText: {
    fontSize: 12,
    fontStyle: 'italic',
    color: COLORS.textSecondary,
  },
  expandedContent: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    marginTop: 8,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    overflow: 'hidden',
  },
  description: {
    fontSize: 14,
    color: COLORS.textSecondary,
    lineHeight: 20,
  },
});
