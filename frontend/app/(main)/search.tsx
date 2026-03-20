/**
 * User Search Screen
 *
 * Search for other users with filters:
 * - Search by username/email
 * - Filter by location
 * - Filter by target university
 * - Filter by SAT score
 * - Filter by GPA
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
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { router } from 'expo-router';
import { socialAPI } from '@/services/api';
import { UserCard } from '@/components/social/UserCard';

interface User {
  id: number;
  username: string;
  avatar_url?: string;
  bio?: string;
  location?: string;
  follower_count: number;
  target_universities?: string[];
  is_following?: boolean;
}

export default function UserSearchScreen() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Filters
  const [locationFilter, setLocationFilter] = useState('');
  const [universityFilter, setUniversityFilter] = useState('');
  const [minSat, setMinSat] = useState('');
  const [minGpa, setMinGpa] = useState('');

  useEffect(() => {
    loadUsers();
  }, [searchQuery, locationFilter, universityFilter, minSat, minGpa]);

  const loadUsers = async () => {
    try {
      setLoading(true);

      const params: any = {};

      if (searchQuery) {
        params.search = searchQuery;
      }
      if (locationFilter) {
        params.location = locationFilter;
      }
      if (universityFilter) {
        params.target_university = universityFilter;
      }
      if (minSat) {
        params.min_sat = parseInt(minSat);
      }
      if (minGpa) {
        params.min_gpa = parseFloat(minGpa);
      }

      const response = await socialAPI.searchUsers(params);
      setUsers(response.data.results || response.data);
    } catch (error) {
      console.error('Failed to search users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFollow = async (userId: number) => {
    const user = users.find(u => u.id === userId);
    if (!user) return;

    try {
      await socialAPI.followUser(user.username);
      setUsers(users.map(u =>
        u.id === userId ? { ...u, is_following: true } : u
      ));
    } catch (error) {
      console.error('Failed to follow:', error);
    }
  };

  const handleUnfollow = async (userId: number) => {
    const user = users.find(u => u.id === userId);
    if (!user) return;

    try {
      await socialAPI.unfollowUser(user.username);
      setUsers(users.map(u =>
        u.id === userId ? { ...u, is_following: false } : u
      ));
    } catch (error) {
      console.error('Failed to unfollow:', error);
    }
  };

  const handleMessage = (userId: number) => {
    router.push(`/messages/${userId}`);
  };

  const hasActiveFilters = locationFilter || universityFilter || minSat || minGpa;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor="#121212" />
      {/* Search Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Discover People</Text>

        {/* Search Bar */}
        <View style={styles.searchContainer}>
          <TextInput
            style={styles.searchInput}
            placeholder="Search by username..."
            placeholderTextColor="#6B7280"
            value={searchQuery}
            onChangeText={setSearchQuery}
            autoCapitalize="none"
            autoCorrect={false}
          />

          <TouchableOpacity
            style={styles.filterButton}
            onPress={() => setShowFilters(!showFilters)}
          >
            <Text style={styles.filterIcon}>⚙️</Text>
          </TouchableOpacity>
        </View>

        {/* Active Filters Badge */}
        {hasActiveFilters && (
          <TouchableOpacity
            style={styles.clearFiltersButton}
            onPress={() => {
              setLocationFilter('');
              setUniversityFilter('');
              setMinSat('');
              setMinGpa('');
            }}
          >
            <Text style={styles.clearFiltersText}>Clear filters</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Filters Panel */}
      {showFilters && (
        <View style={styles.filtersPanel}>
          <Text style={styles.filterTitle}>Filters</Text>

          <TextInput
            style={styles.filterInput}
            placeholder="Location (e.g., New York)"
            placeholderTextColor="#6B7280"
            value={locationFilter}
            onChangeText={setLocationFilter}
          />

          <TextInput
            style={styles.filterInput}
            placeholder="Target University"
            placeholderTextColor="#6B7280"
            value={universityFilter}
            onChangeText={setUniversityFilter}
          />

          <TextInput
            style={styles.filterInput}
            placeholder="Min SAT Score"
            placeholderTextColor="#6B7280"
            value={minSat}
            onChangeText={setMinSat}
            keyboardType="numeric"
          />

          <TextInput
            style={styles.filterInput}
            placeholder="Min GPA"
            placeholderTextColor="#6B7280"
            value={minGpa}
            onChangeText={setMinGpa}
            keyboardType="decimal-pad"
          />
        </View>
      )}

      {/* Results */}
      <ScrollView style={styles.scrollView}>
        {loading ? (
          <View style={styles.centerContent}>
            <ActivityIndicator size="large" color="#3B82F6" />
            <Text style={styles.loadingText}>Searching...</Text>
          </View>
        ) : users.length === 0 ? (
          <View style={styles.centerContent}>
            <Text style={styles.emptyText}>No users found</Text>
            <Text style={styles.emptySubtext}>
              Try adjusting your search or filters
            </Text>
          </View>
        ) : (
          users.map((user) => (
            <UserCard
              key={user.id}
              user={user}
              onFollow={handleFollow}
              onUnfollow={handleUnfollow}
              onMessage={handleMessage}
            />
          ))
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  header: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#ECECEC',
    marginBottom: 16,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  searchInput: {
    flex: 1,
    backgroundColor: '#1E1E1E',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#ECECEC',
  },
  filterButton: {
    width: 44,
    height: 44,
    backgroundColor: '#1E1E1E',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  filterIcon: {
    fontSize: 20,
  },
  clearFiltersButton: {
    alignSelf: 'flex-start',
    marginTop: 8,
    paddingVertical: 4,
  },
  clearFiltersText: {
    fontSize: 12,
    color: '#EF4444',
    fontWeight: '500',
  },
  filtersPanel: {
    padding: 16,
    backgroundColor: '#1A1A1A',
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  filterTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ECECEC',
    marginBottom: 12,
  },
  filterInput: {
    backgroundColor: '#121212',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#ECECEC',
    marginBottom: 8,
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  centerContent: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#8E8E8E',
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8E8E8E',
    marginBottom: 4,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#6B7280',
  },
});
