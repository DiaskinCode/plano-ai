import { View, Text, StyleSheet, TouchableOpacity, Animated } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useEffect, useRef } from 'react';

interface MilestoneNodeProps {
  milestone: {
    id: number;
    name: string;
    state: string;
    percent: number;
    due: string;
    proofs: any[];
    risk_flags: any[];
  };
  onPress: () => void;
}

export default function MilestoneNode({ milestone, onPress }: MilestoneNodeProps) {
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (milestone.state === 'in_progress') {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.15,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      ).start();
    }
  }, [milestone.state]);

  const getNodeStyle = () => {
    switch (milestone.state) {
      case 'done':
        return styles.nodeDone;
      case 'in_progress':
        return styles.nodeInProgress;
      case 'next':
        return styles.nodeNext;
      case 'at_risk':
        return styles.nodeAtRisk;
      default:
        return styles.nodeLater;
    }
  };

  const getIcon = () => {
    if (milestone.state === 'done') {
      return <MaterialCommunityIcons name="check" size={24} color="#fff" />;
    } else if (milestone.state === 'at_risk') {
      return <MaterialCommunityIcons name="alert" size={24} color="#FF3B30" />;
    } else {
      return <Text style={styles.percentText}>{milestone.percent}%</Text>;
    }
  };

  const dueDate = new Date(milestone.due);
  const formattedDue = dueDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

  return (
    <TouchableOpacity onPress={onPress} style={styles.container}>
      {/* Connecting Line */}
      <View style={styles.lineContainer}>
        <View style={styles.line} />
      </View>

      {/* Node Circle */}
      <Animated.View style={[styles.node, getNodeStyle(), { transform: [{ scale: pulseAnim }] }]}>
        {getIcon()}
        {milestone.risk_flags?.length > 0 && (
          <View style={styles.riskDot} />
        )}
      </Animated.View>

      {/* Info */}
      <View style={styles.info}>
        <Text style={styles.name}>{milestone.name}</Text>
        <View style={styles.meta}>
          <Text style={styles.due}>Due {formattedDue}</Text>
          {milestone.proofs?.length > 0 && (
            <View style={styles.proofBadge}>
              <MaterialCommunityIcons name="check-circle" size={12} color="#5B6AFF" />
              <Text style={styles.proofCount}>{milestone.proofs.length} proofs</Text>
            </View>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 8,
    paddingLeft: 16,
  },
  lineContainer: {
    position: 'absolute',
    left: 47,
    top: 0,
    bottom: -16,
    width: 2,
  },
  line: {
    flex: 1,
    width: 2,
    backgroundColor: '#3E3E3E',
  },
  node: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#2A2A2A',
    position: 'relative',
    zIndex: 1,
  },
  nodeDone: {
    backgroundColor: '#34C759',
  },
  nodeInProgress: {
    backgroundColor: '#5B6AFF',
    borderColor: '#5B6AFF',
    borderWidth: 4,
  },
  nodeNext: {
    backgroundColor: '#1A1A1A',
    borderColor: '#5B6AFF',
    borderWidth: 3,
  },
  nodeLater: {
    backgroundColor: '#2A2A2A',
    borderColor: '#3E3E3E',
  },
  nodeAtRisk: {
    backgroundColor: '#1A1A1A',
    borderColor: '#FF3B30',
    borderWidth: 3,
  },
  percentText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ECECEC',
  },
  riskDot: {
    position: 'absolute',
    top: 4,
    right: 4,
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#FF3B30',
    borderWidth: 2,
    borderColor: '#1A1A1A',
  },
  info: {
    flex: 1,
    marginLeft: 16,
  },
  name: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ECECEC',
    marginBottom: 4,
  },
  meta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  due: {
    fontSize: 13,
    color: '#8E8E8E',
  },
  proofBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(16, 163, 127, 0.1)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
  },
  proofCount: {
    fontSize: 11,
    color: '#5B6AFF',
    fontWeight: '600',
  },
});
