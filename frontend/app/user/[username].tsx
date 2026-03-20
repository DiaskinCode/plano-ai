/**
 * Public Profile Screen
 *
 * Displays user profile with:
 * - Avatar, name, bio
 * - Academic stats (if public)
 * - Target universities
 * - Social stats (followers, following, posts)
 * - Follow/Message buttons
 * - Communities membership
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Image,
  Alert,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { socialAPI } from '@/services/api';

interface UserProfile {
  id: number;
  username: string;
  email: string;
  avatar_url?: string;
  bio?: string;
  location?: string;
  target_universities?: string[];
  follower_count: number;
  following_count: number;
  post_count: number;
  gpa?: number;
  sat_score?: number;
  ielts_score?: number;
  stats_visibility: 'public' | 'followers' | 'private';
  activity_visibility: 'public' | 'followers' | 'private';
  is_following?: boolean;
  is_followed_by?: boolean;
}

export default function UserProfileScreen() {
  const { username } = useLocalSearchParams();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'posts' | 'communities'>('posts');

  useEffect(() => {
    if (username) {
      loadProfile();
    }
  }, [username]);

  const loadProfile = async () => {
    try {
      // Get user by username - need to search first
      const searchResponse = await socialAPI.searchUsers({ search: username as string });
      const users = searchResponse.data.results || searchResponse.data;

      const foundUser = users.find((u: UserProfile) => u.username === username);
      if (!foundUser) {
        Alert.alert('Not Found', 'User not found');
        router.back();
        return;
      }

      // Get full profile
      const profileResponse = await socialAPI.getProfile(foundUser.id);
      setProfile(profileResponse.data);
    } catch (error) {
      console.error('Failed to load profile:', error);
      Alert.alert('Error', 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleFollow = async () => {
    if (!profile) return;

    try {
      await socialAPI.followUser(profile.username);
      setProfile({
        ...profile,
        is_following: true,
        follower_count: profile.follower_count + 1,
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to follow user';
      Alert.alert('Error', errorMessage);
    }
  };

  const handleUnfollow = async () => {
    if (!profile) return;

    try {
      await socialAPI.unfollowUser(profile.username);
      setProfile({
        ...profile,
        is_following: false,
        follower_count: profile.follower_count - 1,
      });
    } catch (error) {
      console.error('Failed to unfollow:', error);
      Alert.alert('Error', 'Failed to unfollow user');
    }
  };

  const handleMessage = () => {
    if (!profile) return;
    router.push(`/messages/${profile.id}`);
  };

  const canViewStats = () => {
    if (!profile) return false;
    return profile.stats_visibility === 'public';
  };

  if (loading) {
    return (
      <View style={styles.centerContent}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  if (!profile) {
    return (
      <View style={styles.centerContent}>
        <Text style={styles.errorText}>User not found</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor="#121212" />
      <ScrollView style={styles.scrollView}>
        {/* Header */}
        <View style={styles.header}>
          {/* Avatar */}
          <View style={styles.avatarContainer}>
            {profile.avatar_url ? (
              <Image source={{ uri: profile.avatar_url }} style={styles.avatar} />
            ) : (
              <View style={[styles.avatar, styles.avatarPlaceholder]}>
                <Text style={styles.avatarPlaceholderText}>
                  {profile.username ? profile.username.charAt(0).toUpperCase() : '?'}
                </Text>
              </View>
            )}
          </View>

          {/* Username & Name */}
          <Text style={styles.username}>{profile.username || 'Unknown User'}</Text>

          {/* Location */}
          {profile.location && (
            <Text style={styles.location}>📍 {profile.location}</Text>
          )}

          {/* Stats */}
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statCount}>{profile.follower_count.toLocaleString()}</Text>
              <Text style={styles.statLabel}>Followers</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statCount}>{profile.following_count.toLocaleString()}</Text>
              <Text style={styles.statLabel}>Following</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statCount}>{profile.post_count}</Text>
              <Text style={styles.statLabel}>Posts</Text>
            </View>
          </View>

          {/* Action Buttons */}
          <View style={styles.actionsRow}>
            {profile.is_following ? (
              <TouchableOpacity
                style={[styles.actionButton, styles.actionButtonSecondary]}
                onPress={handleUnfollow}
              >
                <Text style={[styles.actionButtonText, styles.actionButtonTextSecondary]}>
                  Following
                </Text>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity style={styles.actionButton} onPress={handleFollow}>
                <Text style={styles.actionButtonText}>Follow</Text>
              </TouchableOpacity>
            )}

            <TouchableOpacity
              style={[styles.actionButton, styles.messageButton]}
              onPress={handleMessage}
            >
              <Text style={styles.messageButtonText}>💬 Message</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Bio */}
        {profile.bio && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>About</Text>
            <Text style={styles.bio}>{profile.bio}</Text>
          </View>
        )}

        {/* Target Universities */}
        {profile.target_universities && profile.target_universities.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Target Universities</Text>
            <View style={styles.universitiesRow}>
              {profile.target_universities.map((uni, index) => (
                <View key={index} style={styles.universityTag}>
                  <Text style={styles.universityText}>🎓 {uni}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Academic Stats (if public) */}
        {canViewStats() && (profile.gpa || profile.sat_score || profile.ielts_score) && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Academic Stats</Text>
            <View style={styles.academicStats}>
              {profile.gpa && (
                <View style={styles.statCard}>
                  <Text style={styles.statCardLabel}>GPA</Text>
                  <Text style={styles.statCardValue}>{profile.gpa}</Text>
                </View>
              )}
              {profile.sat_score && (
                <View style={styles.statCard}>
                  <Text style={styles.statCardLabel}>SAT</Text>
                  <Text style={styles.statCardValue}>{profile.sat_score}</Text>
                </View>
              )}
              {profile.ielts_score && (
                <View style={styles.statCard}>
                  <Text style={styles.statCardLabel}>IELTS</Text>
                  <Text style={styles.statCardValue}>{profile.ielts_score}</Text>
                </View>
              )}
            </View>
          </View>
        )}

        {/* Privacy Notice */}
        {!canViewStats() && (
          <View style={styles.section}>
            <Text style={styles.privacyNotice}>
            🔒 Academic stats are private
            </Text>
          </View>
        )}

        {/* Activity Tabs */}
        <View style={styles.tabContainer}>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'posts' && styles.tabActive]}
            onPress={() => setActiveTab('posts')}
          >
            <Text style={[styles.tabText, activeTab === 'posts' && styles.tabTextActive]}>
              Posts ({profile.post_count})
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'communities' && styles.tabActive]}
            onPress={() => setActiveTab('communities')}
          >
            <Text style={[styles.tabText, activeTab === 'communities' && styles.tabTextActive]}>
              Communities
            </Text>
          </TouchableOpacity>
        </View>

        {/* Tab Content */}
        <View style={styles.tabContent}>
          {activeTab === 'posts' ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateText}>No posts yet</Text>
              <Text style={styles.emptyStateSubtext}>
                Posts will appear here
              </Text>
            </View>
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateText}>No communities yet</Text>
              <Text style={styles.emptyStateSubtext}>
                Communities will appear here
              </Text>
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    fontSize: 16,
    color: '#8E8E8E',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    padding: 20,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  avatarContainer: {
    marginBottom: 16,
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
  },
  avatarPlaceholder: {
    backgroundColor: '#3B82F6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarPlaceholderText: {
    fontSize: 40,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  username: {
    fontSize: 24,
    fontWeight: '700',
    color: '#ECECEC',
    marginBottom: 8,
  },
  location: {
    fontSize: 14,
    color: '#8E8E8E',
    marginBottom: 16,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    marginBottom: 20,
  },
  statItem: {
    alignItems: 'center',
  },
  statCount: {
    fontSize: 20,
    fontWeight: '700',
    color: '#ECECEC',
  },
  statLabel: {
    fontSize: 12,
    color: '#8E8E8E',
    marginTop: 4,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    minWidth: 120,
    alignItems: 'center',
  },
  actionButtonSecondary: {
    backgroundColor: '#2A2A2A',
    borderWidth: 1,
    borderColor: '#3E3E3E',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  actionButtonTextSecondary: {
    color: '#8E8E8E',
  },
  messageButton: {
    backgroundColor: '#2A2A2A',
    paddingHorizontal: 16,
  },
  messageButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ECECEC',
  },
  section: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ECECEC',
    marginBottom: 12,
  },
  bio: {
    fontSize: 16,
    color: '#B8B8B8',
    lineHeight: 22,
  },
  universitiesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  universityTag: {
    backgroundColor: '#2A2A2A',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 8,
  },
  universityText: {
    fontSize: 14,
    color: '#ECECEC',
  },
  academicStats: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  statCard: {
    backgroundColor: '#1E1E1E',
    padding: 16,
    borderRadius: 12,
    marginRight: 12,
    marginBottom: 12,
    minWidth: 100,
    alignItems: 'center',
  },
  statCardLabel: {
    fontSize: 12,
    color: '#8E8E8E',
    marginBottom: 4,
  },
  statCardValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#10B981',
  },
  privacyNotice: {
    fontSize: 14,
    color: '#6B7280',
    fontStyle: 'italic',
    textAlign: 'center',
  },
  tabContainer: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabActive: {
    borderBottomColor: '#3B82F6',
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E8E',
  },
  tabTextActive: {
    color: '#ECECEC',
  },
  tabContent: {
    padding: 20,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyStateText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8E8E8E',
    marginBottom: 4,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#6B7280',
  },
});
