/**
 * Category Filter Component
 *
 * Horizontal scrollable filter chips for task categories
 * Shows category icon, name, and color
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { getCategoriesWithCache, type TaskCategory } from '@/services/taskCategoriesApi';

interface CategoryFilterProps {
  selectedCategory: number | null;
  onCategoryChange: (categoryId: number | null) => void;
  showAllOption?: boolean;
  allOptionLabel?: string;
}

export function CategoryFilter({
  selectedCategory,
  onCategoryChange,
  showAllOption = true,
  allOptionLabel = 'All Tasks',
}: CategoryFilterProps) {
  const [categories, setCategories] = useState<TaskCategory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      setLoading(true);
      const data = await getCategoriesWithCache();
      setCategories(data);
    } catch (error) {
      console.error('Failed to load categories:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="small" color="#5B6AFF" />
      </View>
    );
  }

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.container}
    >
      {showAllOption && (
        <CategoryChip
          label={allOptionLabel}
          icon="list"
          color="#6B7280"
          selected={selectedCategory === null}
          onPress={() => onCategoryChange(null)}
        />
      )}

      {categories.map((category) => (
        <CategoryChip
          key={category.id}
          label={category.name}
          icon={category.icon}
          color={category.color}
          selected={selectedCategory === category.id}
          onPress={() => onCategoryChange(category.id)}
        />
      ))}
    </ScrollView>
  );
}

interface CategoryChipProps {
  label: string;
  icon: string;
  color: string;
  selected: boolean;
  onPress: () => void;
}

function CategoryChip({ label, icon, color, selected, onPress }: CategoryChipProps) {
  // Check if icon is an emoji (most category icons will be)
  const isEmoji = icon.length <= 2;

  return (
    <TouchableOpacity
      style={[
        styles.chip,
        selected && { backgroundColor: color + '20', borderColor: color },
      ]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      {isEmoji ? (
        <Text style={styles.emojiIcon}>{icon}</Text>
      ) : (
        <Ionicons name={icon as any} size={18} color={selected ? color : '#8E8E8E'} />
      )}
      <Text style={[styles.chipLabel, selected && { color }]}>{label}</Text>
      {selected && <View style={[styles.dot, { backgroundColor: color }]} />}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
  },
  loadingContainer: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#3E3E3E',
    backgroundColor: '#2A2A2A',
    gap: 6,
  },
  emojiIcon: {
    fontSize: 16,
  },
  chipLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E8E',
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
});
