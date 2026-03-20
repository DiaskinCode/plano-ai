/**
 * Mentors Discovery Screen (V1)
 *
 * Browse and discover mentors
 * Uses simplified V1 backend API
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  SafeAreaView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { listMentors } from '@/services/mentorship';
import { Mentor } from '@/types/mentor';
import { MentorCardV1 } from '@/components/mentors/MentorCardV1';

type SortOption = 'rating' | 'sessions' | 'price_asc' | 'price_desc';

export default function MentorsScreenV1() {
  const router = useRouter();
  const [mentors, setMentors] = useState<Mentor[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('rating');
  const [userPlan, setUserPlan] = useState<'basic' | 'pro' | 'premium'>('basic');

  // Expertise areas
  const expertiseAreas = [
    'Essay Writing',
    'Ivy League',
    'Stanford',
    'MIT',
    'Career Counseling',
    'SAT Prep',
    'Interview Prep',
  ];
  const [selectedExpertise, setSelectedExpertise] = useState<string | null>(null);

  useEffect(() => {
    loadMentors();
    loadUserPlan();
  }, [sortBy, selectedExpertise]);

  const loadMentors = async () => {
    try {
      setLoading(true);

      const params: {
        expertise?: string;
        search?: string;
        ordering?: SortOption;
      } = {};

      if (selectedExpertise) params.expertise = selectedExpertise;
      if (searchQuery.trim()) params.search = searchQuery.trim();
      if (sortBy) params.ordering = sortBy;

      const response = await listMentors(params);
      setMentors(response.results || []);
    } catch (error) {
      console.error('Error loading mentors:', error);
      // Show mock data on error for development
      setMentors([]);
    } finally {
      setLoading(false);
    }
  };

  const loadUserPlan = async () => {
    // TODO: Load from async storage or API
    setUserPlan('pro'); // Default to pro for testing
  };

  const handleRefresh = () => {
    loadMentors();
  };

  const handleMentorPress = (mentor: Mentor) => {
    router.push(`/mentor/${mentor.id}`);
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#fff" />

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Find a Mentor</Text>
        <Text style={styles.headerSubtitle}>
          Connect with experts who've been there
        </Text>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <MaterialCommunityIcons name="magnify" size={20} color="#999" />
        <TextInput
          style={styles.searchInput}
          placeholder="Search by name or expertise..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          onSubmitEditing={loadMentors}
          returnKeyType="search"
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => {
            setSearchQuery('');
            loadMentors();
          }}>
            <MaterialCommunityIcons name="close-circle" size={20} color="#999" />
          </TouchableOpacity>
        )}
      </View>

      {/* Expertise Filter */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.expertiseScroll}
        contentContainerStyle={styles.expertiseContent}
      >
        <TouchableOpacity
          style={[styles.chip, !selectedExpertise && styles.chipActive]}
          onPress={() => {
            setSelectedExpertise(null);
            loadMentors();
          }}
        >
          <Text style={[styles.chipText, !selectedExpertise && styles.chipTextActive]}>
            All
          </Text>
        </TouchableOpacity>
        {expertiseAreas.map((area) => (
          <TouchableOpacity
            key={area}
            style={[styles.chip, selectedExpertise === area && styles.chipActive]}
            onPress={() => {
              setSelectedExpertise(area === selectedExpertise ? null : area);
              loadMentors();
            }}
          >
            <Text style={[styles.chipText, selectedExpertise === area && styles.chipTextActive]}>
              {area}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Sort Options */}
      <View style={styles.sortContainer}>
        <Text style={styles.sortLabel}>Sort by:</Text>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.sortContent}
        >
          {[
            { key: 'rating', label: 'Top Rated' },
            { key: 'sessions', label: 'Most Sessions' },
            { key: 'price_asc', label: 'Price: Low to High' },
            { key: 'price_desc', label: 'Price: High to Low' },
          ].map((option) => (
            <TouchableOpacity
              key={option.key}
              onPress={() => setSortBy(option.key as SortOption)}
              style={styles.sortOption}
            >
              <Text
                style={[
                  styles.sortOptionText,
                  sortBy === option.key && styles.sortOptionTextActive,
                ]}
              >
                {option.label}
              </Text>
              {sortBy === option.key && (
                <MaterialCommunityIcons name="check" size={16} color="#0066cc" />
              )}
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Mentors List */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#0066cc" />
          <Text style={styles.loadingText}>Loading mentors...</Text>
        </View>
      ) : mentors.length === 0 ? (
        <View style={styles.emptyContainer}>
          <MaterialCommunityIcons name="account-search" size={64} color="#ccc" />
          <Text style={styles.emptyTitle}>No mentors found</Text>
          <Text style={styles.emptyText}>
            Try adjusting your search or filters
          </Text>
          <TouchableOpacity style={styles.retryButton} onPress={handleRefresh}>
            <Text style={styles.retryButtonText}>Clear Filters</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <ScrollView style={styles.listContainer}>
          <Text style={styles.resultsCount}>{mentors.length} mentors found</Text>
          {mentors.map((mentor) => (
            <MentorCardV1
              key={mentor.id}
              mentor={mentor}
              userPlan={userPlan}
            />
          ))}
        </ScrollView>
      )}

      {/* Pro Plan Banner */}
      {userPlan === 'basic' && (
        <View style={styles.proBanner}>
          <MaterialCommunityIcons name="crown" size={24} color="#FFD700" />
          <View style={styles.proBannerContent}>
            <Text style={styles.proBannerTitle}>Upgrade to Pro</Text>
            <Text style={styles.proBannerText}>
              Get access to verified mentors and 1-on-1 sessions
            </Text>
          </View>
          <TouchableOpacity
            style={styles.upgradeButton}
            onPress={() => router.push('/profile')}
          >
            <Text style={styles.upgradeButtonText}>Upgrade</Text>
          </TouchableOpacity>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 16,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginTop: 16,
    paddingHorizontal: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  searchInput: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    fontSize: 16,
  },
  expertiseScroll: {
    marginTop: 16,
  },
  expertiseContent: {
    paddingHorizontal: 20,
  },
  chip: {
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  chipActive: {
    backgroundColor: '#0066cc',
    borderColor: '#0066cc',
  },
  chipText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  chipTextActive: {
    color: '#fff',
  },
  sortContainer: {
    backgroundColor: '#fff',
    marginTop: 16,
    paddingHorizontal: 20,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  sortLabel: {
    fontSize: 12,
    color: '#999',
    fontWeight: '600',
    marginBottom: 8,
  },
  sortContent: {
    paddingRight: 20,
  },
  sortOption: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
  },
  sortOptionText: {
    fontSize: 14,
    color: '#666',
  },
  sortOptionTextActive: {
    color: '#0066cc',
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1a1a1a',
    marginTop: 16,
  },
  emptyText: {
    fontSize: 14,
    color: '#999',
    marginTop: 8,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 20,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#0066cc',
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  listContainer: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 16,
  },
  resultsCount: {
    fontSize: 14,
    color: '#999',
    marginBottom: 12,
  },
  proBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginBottom: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  proBannerContent: {
    flex: 1,
    marginLeft: 12,
  },
  proBannerTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  proBannerText: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  upgradeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#FFD700',
    borderRadius: 8,
  },
  upgradeButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1a1a1a',
  },
});
