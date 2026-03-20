/**
 * University Shortlist Management Screen
 *
 * Allows users to:
 * - View saved universities
 * - Add notes to each university
 * - Remove universities from shortlist
 * - Compare selected universities
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { universityRecommenderAPI } from '@/services/universityRecommenderApi';
import { colors, spacing } from '@/theme';

interface ShortlistItem {
  id: number;
  university: {
    short_name: string;
    name: string;
    location: string;
    total_cost: number;
    acceptance_rate: number;
  };
  status: string;
  notes: string;
  added_at: string;
}

export default function UniversityShortlist() {
  const [loading, setLoading] = useState(true);
  const [shortlist, setShortlist] = useState<ShortlistItem[]>([]);
  const [editingNotes, setEditingNotes] = useState<{ [key: number]: string }>({});
  const [expandedCards, setExpandedCards] = useState<{ [key: number]: boolean }>({});
  const [selectedForCompare, setSelectedForCompare] = useState<number[]>([]);

  useEffect(() => {
    loadShortlist();
  }, []);

  const loadShortlist = async () => {
    try {
      setLoading(true);
      const response = await universityRecommenderAPI.getShortlist();
      setShortlist(response.data);
    } catch (error: any) {
      console.error('Failed to load shortlist:', error);
      Alert.alert('Error', 'Failed to load shortlist. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (shortName: string) => {
    Alert.alert(
      'Remove from Shortlist',
      'Are you sure you want to remove this university?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            try {
              await universityRecommenderAPI.removeFromShortlist(shortName);
              await loadShortlist();
            } catch (error: any) {
              console.error('Failed to remove:', error);
              Alert.alert('Error', 'Failed to remove university. Please try again.');
            }
          },
        },
      ]
    );
  };

  const handleUpdateNotes = async (itemId: number, notes: string) => {
    try {
      // Note: Backend would need an update endpoint for notes
      // For now, we'll just update local state
      setShortlist(prev =>
        prev.map(item =>
          item.id === itemId ? { ...item, notes } : item
        )
      );
      setEditingNotes(prev => ({ ...prev, [itemId]: '' }));
    } catch (error: any) {
      console.error('Failed to update notes:', error);
      Alert.alert('Error', 'Failed to update notes. Please try again.');
    }
  };

  const toggleCardExpanded = (itemId: number) => {
    setExpandedCards(prev => ({ ...prev, [itemId]: !prev[itemId] }));
  };

  const toggleCompareSelection = (itemId: number) => {
    setSelectedForCompare(prev => {
      if (prev.includes(itemId)) {
        return prev.filter(id => id !== itemId);
      }
      if (prev.length >= 4) {
        Alert.alert('Maximum Reached', 'You can compare up to 4 universities at a time.');
        return prev;
      }
      return [...prev, itemId];
    });
  };

  const handleCompare = () => {
    if (selectedForCompare.length < 2) {
      Alert.alert('Select More', 'Please select at least 2 universities to compare.');
      return;
    }
    const selectedItems = shortlist.filter(item => selectedForCompare.includes(item.id));
    const shortNames = selectedItems.map(item => item.university.short_name).join(',');
    router.push(`/university-recommender/compare?universities=${shortNames}`);
  };

  const renderShortlistCard = (item: ShortlistItem) => {
    const isExpanded = expandedCards[item.id];
    const isSelected = selectedForCompare.includes(item.id);
    const isEditing = editingNotes[item.id] !== undefined;

    return (
      <View key={item.id} style={[styles.card, isSelected && styles.cardSelected]}>
        {/* Header */}
        <TouchableOpacity
          style={styles.cardHeader}
          onPress={() => toggleCardExpanded(item.id)}
        >
          <View style={styles.cardHeaderLeft}>
            <Text style={styles.universityName}>{item.university.name}</Text>
            <Text style={styles.universityLocation}>{item.university.location}</Text>
          </View>
          <Ionicons
            name={isExpanded ? 'chevron-up' : 'chevron-down'}
            size={24}
            color={colors.textSecondary}
          />
        </TouchableOpacity>

        {/* Expanded Content */}
        {isExpanded && (
          <View style={styles.expandedContent}>
            {/* Stats */}
            <View style={styles.statsRow}>
              <View style={styles.statItem}>
                <Ionicons name="trending-up" size={16} color={colors.textSecondary} />
                <Text style={styles.statValue}>{item.university.acceptance_rate}%</Text>
                <Text style={styles.statLabel}>Acceptance</Text>
              </View>
              <View style={styles.statItem}>
                <Ionicons name="cash" size={16} color={colors.textSecondary} />
                <Text style={styles.statValue}>${item.university.total_cost.toLocaleString()}</Text>
                <Text style={styles.statLabel}>Cost/Year</Text>
              </View>
            </View>

            {/* Notes Section */}
            <View style={styles.notesSection}>
              <Text style={styles.notesLabel}>Notes:</Text>
              {isEditing ? (
                <View style={styles.notesEditContainer}>
                  <TextInput
                    style={styles.notesInput}
                    value={editingNotes[item.id] || item.notes}
                    onChangeText={(value) => setEditingNotes(prev => ({ ...prev, [item.id]: value }))}
                    placeholder="Add notes about this university..."
                    multiline
                    numberOfLines={3}
                  />
                  <View style={styles.notesEditActions}>
                    <TouchableOpacity
                      style={[styles.notesEditButton, styles.notesCancelButton]}
                      onPress={() => setEditingNotes(prev => ({ ...prev, [item.id]: undefined }))}
                    >
                      <Text style={styles.notesCancelButtonText}>Cancel</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.notesEditButton, styles.notesSaveButton]}
                      onPress={() => handleUpdateNotes(item.id, editingNotes[item.id] || item.notes)}
                    >
                      <Text style={styles.notesSaveButtonText}>Save</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ) : (
                <TouchableOpacity onPress={() => setEditingNotes(prev => ({ ...prev, [item.id]: item.notes }))}>
                  {item.notes ? (
                    <Text style={styles.notesText}>{item.notes}</Text>
                  ) : (
                    <Text style={styles.notesPlaceholder}>Tap to add notes...</Text>
                  )}
                </TouchableOpacity>
              )}
            </View>

            {/* Actions */}
            <View style={styles.cardActions}>
              <TouchableOpacity
                style={[styles.compareButton, isSelected && styles.compareButtonSelected]}
                onPress={() => toggleCompareSelection(item.id)}
              >
                <Ionicons
                  name={isSelected ? 'checkbox' : 'square-outline'}
                  size={18}
                  color={isSelected ? '#fff' : colors.primary}
                />
                <Text style={[styles.compareButtonText, isSelected && styles.compareButtonTextSelected]}>
                  {isSelected ? 'Selected' : 'Compare'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.removeButton}
                onPress={() => handleRemove(item.university.short_name)}
              >
                <Ionicons name="trash-outline" size={18} color={colors.error} />
                <Text style={styles.removeButtonText}>Remove</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading shortlist...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>My Shortlist</Text>
        <View style={styles.placeholder} />
      </View>

      {/* Compare Bar */}
      {selectedForCompare.length > 0 && (
        <View style={styles.compareBar}>
          <Text style={styles.compareBarText}>
            {selectedForCompare.length} university{selectedForCompare.length > 1 ? 's' : ''} selected
          </Text>
          <TouchableOpacity
            style={styles.compareBarButton}
            onPress={handleCompare}
          >
            <Text style={styles.compareBarButtonText}>Compare Now</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Content */}
      {shortlist.length === 0 ? (
        <View style={styles.centerContent}>
          <Ionicons name="bookmark-outline" size={64} color={colors.textSecondary} />
          <Text style={styles.emptyTitle}>Your shortlist is empty</Text>
          <Text style={styles.emptyText}>
            Save universities from your recommendations to compare them later
          </Text>
          <TouchableOpacity
            style={styles.browseButton}
            onPress={() => router.push('/university-recommender/results')}
          >
            <Text style={styles.browseButtonText}>Browse Recommendations</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          <View style={styles.shortlistInfo}>
            <Text style={styles.shortlistInfoText}>
              {shortlist.length} university{shortlist.length > 1 ? 's' : ''} saved
            </Text>
          </View>
          {shortlist.map(item => renderShortlistCard(item))}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backButton: {
    padding: spacing.xs,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text,
  },
  placeholder: {
    width: 24,
  },
  compareBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.primaryLight,
    borderBottomWidth: 1,
    borderBottomColor: colors.primary,
  },
  compareBarText: {
    fontSize: 14,
    color: colors.text,
    fontWeight: '500',
  },
  compareBarButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: 8,
  },
  compareBarButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
  content: {
    flex: 1,
    padding: spacing.md,
  },
  shortlistInfo: {
    marginBottom: spacing.md,
  },
  shortlistInfoText: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: 12,
    marginBottom: spacing.md,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  cardSelected: {
    borderColor: colors.primary,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: spacing.md,
  },
  cardHeaderLeft: {
    flex: 1,
  },
  universityName: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  universityLocation: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  expandedContent: {
    borderTopWidth: 1,
    borderTopColor: colors.border,
    padding: spacing.md,
    gap: spacing.md,
  },
  statsRow: {
    flexDirection: 'row',
    gap: spacing.lg,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  statValue: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
  },
  statLabel: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  notesSection: {
    gap: spacing.xs,
  },
  notesLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  notesText: {
    fontSize: 14,
    color: colors.text,
    lineHeight: 20,
  },
  notesPlaceholder: {
    fontSize: 14,
    color: colors.textSecondary,
    fontStyle: 'italic',
  },
  notesEditContainer: {
    gap: spacing.sm,
  },
  notesInput: {
    backgroundColor: colors.background,
    borderRadius: 8,
    padding: spacing.sm,
    fontSize: 14,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.border,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  notesEditActions: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  notesEditButton: {
    flex: 1,
    paddingVertical: spacing.sm,
    borderRadius: 8,
    alignItems: 'center',
  },
  notesCancelButton: {
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
  },
  notesSaveButton: {
    backgroundColor: colors.primary,
  },
  notesCancelButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.textSecondary,
  },
  notesSaveButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
  cardActions: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  compareButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
    paddingVertical: spacing.sm,
    borderRadius: 8,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  compareButtonSelected: {
    backgroundColor: colors.primary,
  },
  compareButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.primary,
  },
  compareButtonTextSelected: {
    color: '#fff',
  },
  removeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 8,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.error,
  },
  removeButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.error,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: spacing.md,
    padding: spacing.xl,
  },
  loadingText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
    marginTop: spacing.md,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.text,
  },
  emptyText: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  browseButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderRadius: 12,
    marginTop: spacing.md,
  },
  browseButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
});
