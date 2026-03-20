/**
 * MentorBlur Component
 *
 * Subtle lock indicator for Basic users
 * - Pro/Premium users see normal content with full access
 * - Basic users see preview with small lock badge in corner
 * - No full blur overlay - users can preview mentors
 */

import React from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';

interface MentorBlurProps {
  children: React.ReactNode;
  userPlan: 'basic' | 'pro' | 'premium';
  requiredPlan?: 'pro' | 'premium';
  onUpgradePress?: () => void;
}

export const MentorBlur: React.FC<MentorBlurProps> = ({
  children,
  userPlan,
  requiredPlan = 'pro',
  onUpgradePress,
}) => {
  const hasAccess = userPlan === 'pro' || userPlan === 'premium';

  if (hasAccess) {
    return <>{children}</>;
  }

  return (
    <View style={styles.container}>
      {children}

      {/* Subtle lock badge in top-right corner */}
      <TouchableOpacity
        style={styles.lockBadge}
        onPress={onUpgradePress}
        activeOpacity={0.8}
      >
        <MaterialCommunityIcons name="lock" size={16} color="#FFFFFF" />
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'relative',
  },
  lockBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    borderRadius: 12,
    width: 28,
    height: 28,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
});
