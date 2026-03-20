/**
 * Calendar View Mode Selector
 *
 * Allows users to switch between different calendar views:
 * - Day: Single day view with hourly slots
 * - Week: 7-day week view
 * - Month: Monthly grid view
 * - List: Vertical list of upcoming tasks
 */

import React from 'react';
import { View, TouchableOpacity, StyleSheet, Text } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export type ViewMode = 'day' | 'week' | 'month' | 'list';

interface ViewModeSelectorProps {
  currentMode: ViewMode;
  onModeChange: (mode: ViewMode) => void;
  darkMode?: boolean;
}

const VIEW_MODES: Array<{
  mode: ViewMode;
  icon: string;
  label: string;
}> = [
  { mode: 'day', icon: 'today-outline', label: 'Day' },
  { mode: 'week', icon: 'calendar-outline', label: 'Week' },
  { mode: 'month', icon: 'grid-outline', label: 'Month' },
  { mode: 'list', icon: 'list-outline', label: 'List' },
];

export function ViewModeSelector({ currentMode, onModeChange, darkMode = true }: ViewModeSelectorProps) {
  return (
    <View style={[styles.container, darkMode && styles.darkContainer]}>
      {VIEW_MODES.map(({ mode, icon, label }) => (
        <TouchableOpacity
          key={mode}
          style={[styles.modeButton, currentMode === mode && styles.activeButton]}
          onPress={() => onModeChange(mode)}
          activeOpacity={0.7}
        >
          <Ionicons
            name={icon as any}
            size={20}
            color={currentMode === mode ? '#5B6AFF' : '#8E8E8E'}
          />
          <Text
            style={[
              styles.modeLabel,
              currentMode === mode && styles.activeLabel,
            ]}
          >
            {label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 8,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  darkContainer: {
    backgroundColor: '#1A1A1A',
    borderBottomColor: '#3E3E3E',
  },
  modeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    gap: 6,
    backgroundColor: '#F3F4F6',
  },
  activeButton: {
    backgroundColor: '#5B6AFF20',
  },
  modeLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
  activeLabel: {
    color: '#5B6AFF',
  },
});
