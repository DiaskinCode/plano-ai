/**
 * QuickActions Component
 *
 * Compact icon row for quick navigation in Community header
 * - Find People (user search)
 * - Messages (DMs)
 * - Create Community
 * - Mentors
 */

import React from 'react';
import { View, TouchableOpacity, StyleSheet, Text } from 'react-native';
import { useRouter } from 'expo-router';

interface QuickAction {
  id: string;
  icon: string;
  label: string;
  route: string;
  badge?: number;
}

const QUICK_ACTIONS: QuickAction[] = [
  { id: 'find-people', icon: '👥', label: 'Find People', route: '/search' },
  { id: 'messages', icon: '📨', label: 'Messages', route: '/messages' },
  { id: 'create', icon: '✏️', label: 'Create', route: '/community/create' },
  { id: 'mentors', icon: '👨‍🏫', label: 'Mentors', route: '/mentors' },
];

interface QuickActionsProps {
  style?: object;
}

export const QuickActions: React.FC<QuickActionsProps> = ({ style }) => {
  const router = useRouter();

  const handlePress = (route: string) => {
    router.push(route as any);
  };

  return (
    <View style={[styles.container, style]}>
      {QUICK_ACTIONS.map((action) => (
        <TouchableOpacity
          key={action.id}
          style={styles.iconButton}
          onPress={() => handlePress(action.route)}
          activeOpacity={0.7}
        >
          <Text style={styles.icon}>{action.icon}</Text>
          {action.badge !== undefined && action.badge > 0 && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>
                {action.badge > 9 ? '9+' : action.badge}
              </Text>
            </View>
          )}
        </TouchableOpacity>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    gap: 32,
    alignItems: 'center',
  },
  iconButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  icon: {
    fontSize: 22,
  },
  badge: {
    position: 'absolute',
    top: 4,
    right: 4,
    backgroundColor: '#EF4444',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
    borderWidth: 2,
    borderColor: '#121212',
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
    lineHeight: 16,
  },
});
