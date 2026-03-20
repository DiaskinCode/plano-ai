/**
 * Followers/Following List Screen
 *
 * Displays:
 * - List of followers (people who follow this user)
 * - List of following (people this user follows)
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
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

export default function FollowersFollowingScreen() {
  const { username, type } = useLocalSearchParams();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUsers();
  }, [username, type]);

  const loadUsers = async () => {
    try {
      setLoading(true);

      // First, get the user ID from username
      const searchResponse = await socialAPI.searchUsers({ search: username as string });
      const foundUsers = searchResponse.data.results || searchResponse.data;
      const foundUser = foundUsers.find((u: User) => u.username === username);

      if (!foundUser) {
        setLoading(false);
        return;
      }

      // Get followers or following list
      const response = type === 'followers'
        ? await socialAPI.getFollowers(foundUser.id)
        : await socialAPI.getFollowing(foundUser.id);

      setUsers(response.data.results || response.data);
    } catch (error) {
      console.error('Failed to load users:', error);
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

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Text style={styles.backButtonText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>
          {type === 'followers' ? 'Followers' : 'Following'}
        </Text>
        <View style={styles.placeholder} />
      </View>

      {/* Content */}
      {loading ? (
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color="#3B82F6" />
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      ) : users.length === 0 ? (
        <View style={styles.centerContent}>
          <Text style={styles.emptyText}>
            {type === 'followers' ? 'No followers yet' : 'Not following anyone'}
          </Text>
        </View>
      ) : (
        <ScrollView style={styles.scrollView}>
          {users.map((user) => (
            <UserCard
              key={user.id}
              user={user}
              onFollow={handleFollow}
              onUnfollow={handleUnfollow}
              onMessage={handleMessage}
            />
          ))}
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  backButton: {
    width: 80,
  },
  backButtonText: {
    fontSize: 14,
    color: '#3B82F6',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ECECEC',
    flex: 1,
    textAlign: 'center',
  },
  placeholder: {
    width: 80,
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
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
  },
});
