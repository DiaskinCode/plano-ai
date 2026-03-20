import { View, Text, StyleSheet, TouchableOpacity, Dimensions, Animated } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useEffect, useRef } from 'react';
import Svg, { Path } from 'react-native-svg';

const { width } = Dimensions.get('window');

interface IslandRoadmapProps {
  milestones: any[];
  onMilestonePress: (milestone: any) => void;
}

export default function IslandRoadmap({ milestones, onMilestonePress }: IslandRoadmapProps) {
  // Calculate positions for winding path (reversed - trophy at top)
  const getCardPosition = (index: number, total: number) => {
    const verticalSpacing = 100; // Reduced spacing for cards

    // Reverse the index so last milestone is at top
    const reversedIndex = total - 1 - index;

    // Center horizontally
    const xOffset = (width - 40) / 2;
    const yOffset = 40 + (reversedIndex * verticalSpacing);

    return { x: xOffset, y: yOffset };
  };

  // Determine card size based on milestone type/importance
  const getCardSize = (milestone: any, index: number, total: number) => {
    // Final achievement milestone is biggest
    if (milestone.is_final) return 'large';

    // Monthly milestones are medium
    if (milestone.is_monthly) {
      return 'medium';
    }

    // Weekly milestones are small
    return 'small';
  };

  const totalHeight = (milestones.length + 1) * 100 + 80;

  return (
    <View style={[styles.container, { height: totalHeight }]}>
      {/* Connecting Path */}
      <Svg height={totalHeight} width={width} style={styles.pathSvg}>
        {milestones.map((_, index) => {
          if (index === milestones.length - 1) return null;
          const start = getCardPosition(index, milestones.length);
          const end = getCardPosition(index + 1, milestones.length);

          // Create straight vertical line at center
          const centerX = width / 2;
          const pathData = `M ${centerX} ${start.y + 50} L ${centerX} ${end.y - 50}`;

          return (
            <Path
              key={index}
              d={pathData}
              stroke="rgba(255, 255, 255, 0.15)"
              strokeWidth="1.5"
              fill="none"
              strokeDasharray="4 4"
            />
          );
        })}
      </Svg>

      {/* Card Milestones */}
      {milestones.map((milestone, index) => {
        const position = getCardPosition(index, milestones.length);
        const size = getCardSize(milestone, index, milestones.length);

        return (
          <CardNode
            key={milestone.id}
            milestone={milestone}
            position={position}
            size={size}
            isFirst={index === 0}
            isLast={index === milestones.length - 1}
            onPress={() => onMilestonePress(milestone)}
          />
        );
      })}
    </View>
  );
}

interface CardNodeProps {
  milestone: any;
  position: { x: number; y: number };
  size: 'small' | 'medium' | 'large';
  isFirst: boolean;
  isLast: boolean;
  onPress: () => void;
}

function CardNode({ milestone, position, size, isFirst, isLast, onPress }: CardNodeProps) {
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (milestone.state === 'in_progress') {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.02,
            duration: 2000,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 2000,
            useNativeDriver: true,
          }),
        ])
      ).start();
    }
  }, [milestone.state]);

  const getCardDimensions = () => {
    switch (size) {
      case 'large':
        return { width: width - 60, height: 120, padding: 20 };
      case 'medium':
        return { width: width - 80, height: 90, padding: 18 };
      default:
        return { width: width - 100, height: 80, padding: 16 };
    }
  };

  const getBorderColor = () => {
    if (isLast) return 'rgba(255, 255, 255, 0.2)'; // White for final goal
    if (milestone.state === 'done') return 'rgba(52, 199, 89, 0.4)';
    if (milestone.state === 'at_risk') return 'rgba(255, 59, 48, 0.4)';
    if (milestone.state === 'in_progress') return 'rgba(16, 163, 127, 0.5)';
    if (milestone.state === 'next') return 'rgba(255, 184, 0, 0.4)';
    return 'rgba(255, 255, 255, 0.15)';
  };

  const getCardBackground = () => {
    if (isLast) return '#FFFFFF'; // White background for final goal
    if (size === 'medium') return '#2F2F2F'; // Monthly cards
    return '#171717'; // Weekly cards
  };

  const cardDims = getCardDimensions();
  const borderColor = getBorderColor();
  const cardBackground = getCardBackground();

  return (
    <TouchableOpacity
      style={[
        styles.cardContainer,
        {
          left: position.x - cardDims.width / 2,
          top: position.y - cardDims.height / 2,
        },
      ]}
      onPress={onPress}
      activeOpacity={0.85}
    >
      <Animated.View
        style={[
          styles.card,
          {
            width: cardDims.width,
            height: cardDims.height,
            padding: cardDims.padding,
            borderColor: borderColor,
            backgroundColor: cardBackground,
            transform: [{ scale: pulseAnim }],
            shadowOpacity: isLast ? 0.3 : 1,
            shadowRadius: isLast ? 20 : 12,
            elevation: isLast ? 12 : 8,
          },
        ]}
      >
        {size === 'small' ? (
          // Weekly card - centered content
          <View style={styles.weeklyCardContent}>
            <Text style={styles.weeklyTitle}>{milestone.name}</Text>
            {milestone.task_count > 0 && (
              <Text style={styles.weeklyTaskCount}>{milestone.task_count} Tasks</Text>
            )}
            <Text style={styles.weeklyDetails}>see details</Text>
          </View>
        ) : (
          // Monthly/Large card - normal layout
          <View style={styles.cardContent}>
            <View style={styles.cardHeader}>
              <Text style={[styles.cardTitle, { fontSize: size === 'large' ? 20 : 16, color: isLast ? '#000000' : '#FFFFFF' }]}>
                {milestone.name}
              </Text>
              {milestone.state === 'done' && (
                <MaterialCommunityIcons name="check-circle" size={20} color="#34C759" />
              )}
              {isLast && (
                <MaterialCommunityIcons name="trophy" size={24} color="#FFD700" />
              )}
            </View>

            <View style={styles.cardFooter}>
              <Text style={[styles.cardDate, { color: isLast ? 'rgba(0, 0, 0, 0.6)' : 'rgba(255, 255, 255, 0.6)' }]}>
                {new Date(milestone.due).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </Text>

              {!isLast && milestone.state !== 'done' && (
                <Text style={styles.cardDetails}>see details</Text>
              )}
            </View>
          </View>
        )}
      </Animated.View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    backgroundColor: 'transparent',
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  pathSvg: {
    position: 'absolute',
    top: 0,
    left: 0,
  },
  cardContainer: {
    position: 'absolute',
    alignItems: 'center',
  },
  card: {
    borderRadius: 20,
    borderWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 1,
    shadowRadius: 12,
    elevation: 8,
  },
  cardContent: {
    flex: 1,
    justifyContent: 'space-between',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  cardTitle: {
    fontWeight: '600',
    color: '#FFFFFF',
    flex: 1,
    marginRight: 8,
  },
  cardFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  cardDate: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
    fontWeight: '500',
  },
  cardDetails: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.5)',
    fontWeight: '400',
  },
  weeklyCardContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 4,
  },
  weeklyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    textAlign: 'center',
  },
  weeklyTaskCount: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.7)',
    fontWeight: '500',
    textAlign: 'center',
  },
  weeklyDetails: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.5)',
    fontWeight: '400',
    textAlign: 'center',
  },
});
