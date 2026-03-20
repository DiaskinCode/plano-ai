import { View, StyleSheet, ScrollView } from 'react-native';
import { useState } from 'react';
import GoalCard from './GoalCard';

const COLORS = {
  connector: '#3E3E3E',
};

interface Goal {
  id: number;
  title: string;
  description?: string;
  progress: number;
  status: 'on_track' | 'at_risk' | 'stalled';
  linkedTasksCount: number;
  motivationalText?: string;
  children?: Goal[];
  level: number; // 0 = long-term, 1 = mid-term, 2 = short-term
}

interface GoalHierarchyTreeProps {
  goals: Goal[];
  onGoalPress?: (goal: Goal) => void;
}

export default function GoalHierarchyTree({ goals, onGoalPress }: GoalHierarchyTreeProps) {
  const [expandedGoals, setExpandedGoals] = useState<Set<number>>(new Set());

  const toggleExpanded = (goalId: number) => {
    const newExpanded = new Set(expandedGoals);
    if (newExpanded.has(goalId)) {
      newExpanded.delete(goalId);
    } else {
      newExpanded.add(goalId);
    }
    setExpandedGoals(newExpanded);
  };

  const renderGoal = (goal: Goal) => {
    const isExpanded = expandedGoals.has(goal.id);
    const hasChildren = goal.children && goal.children.length > 0;

    return (
      <View key={goal.id} style={styles.goalContainer}>
        {/* Connector Line for child goals */}
        {goal.level > 0 && <View style={[styles.connector, { left: (goal.level - 1) * 20 }]} />}

        <GoalCard
          goal={goal}
          level={goal.level}
          onPress={() => onGoalPress && onGoalPress(goal)}
          onExpand={hasChildren ? () => toggleExpanded(goal.id) : undefined}
          isExpanded={isExpanded}
        />

        {/* Render children if expanded */}
        {isExpanded && hasChildren && (
          <View style={styles.childrenContainer}>
            {goal.children!.map((child) => renderGoal(child))}
          </View>
        )}
      </View>
    );
  };

  return (
    <ScrollView
      style={styles.container}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.scrollContent}
    >
      {goals.map((goal) => renderGoal(goal))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 100,
  },
  goalContainer: {
    position: 'relative',
  },
  connector: {
    position: 'absolute',
    top: 0,
    width: 2,
    height: '100%',
    backgroundColor: COLORS.connector,
    marginLeft: 10,
  },
  childrenContainer: {
    marginTop: 8,
  },
});
