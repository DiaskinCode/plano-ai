/**
 * UserCard Component
 *
 * Reusable user preview card for:
 * - Search results
 * - Followers/Following lists
 * - Mentions
 * - Recommendations
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
} from 'react-native';
import { router } from 'expo-router';

interface UserCardProps {
  user: {
    id: number;
    username: string;
    avatar_url?: string;
    bio?: string;
    location?: string;
    follower_count: number;
    target_universities?: string[];
    is_following?: boolean;
  };
  onFollow?: (userId: number) => void;
  onUnfollow?: (userId: number) => void;
  onMessage?: (userId: number) => void;
  compact?: boolean;
}

export const UserCard: React.FC<UserCardProps> = ({
  user,
  onFollow,
  onUnfollow,
  onMessage,
  compact = false,
}) => {
  const handlePress = () => {
    router.push(`/user/${user.username}`);
  };

  const handleFollow = () => {
    if (onFollow) {
      onFollow(user.id);
    }
  };

  const handleUnfollow = () => {
    if (onUnfollow) {
      onUnfollow(user.id);
    }
  };

  const handleMessage = () => {
    if (onMessage) {
      onMessage(user.id);
    }
  };

  return (
    <TouchableOpacity style={styles.container} onPress={handlePress} activeOpacity={0.7}>
      {/* Avatar */}
      <View style={styles.avatarContainer}>
        {user.avatar_url ? (
          <Image source={{ uri: user.avatar_url }} style={styles.avatar} />
        ) : (
          <View style={[styles.avatar, styles.avatarPlaceholder]}>
            <Text style={styles.avatarPlaceholderText}>
              {user.username.charAt(0).toUpperCase()}
            </Text>
          </View>
        )}
      </View>

      {/* Content */}
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.username}>{user.username}</Text>
          <View style={styles.statsRow}>
            <Text style={styles.statText}>
              {user.follower_count.toLocaleString()} followers
            </Text>
          </View>
        </View>

        {user.location && !compact && (
          <Text style={styles.location}>📍 {user.location}</Text>
        )}

        {!compact && user.bio && (
          <Text style={styles.bio} numberOfLines={2}>
            {user.bio}
          </Text>
        )}

        {!compact && user.target_universities && user.target_universities.length > 0 && (
          <View style={styles.universitiesRow}>
            {user.target_universities.slice(0, 3).map((uni, index) => (
              <View key={index} style={styles.universityTag}>
                <Text style={styles.universityText}>{uni}</Text>
              </View>
            ))}
          </View>
        )}
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        {user.is_following ? (
          <TouchableOpacity
            style={[styles.followButton, styles.followButtonFollowing]}
            onPress={handleUnfollow}
          >
            <Text style={[styles.followButtonText, styles.followButtonTextFollowing]}>
              Following
            </Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={styles.followButton} onPress={handleFollow}>
            <Text style={styles.followButtonText}>Follow</Text>
          </TouchableOpacity>
        )}

        {onMessage && (
          <TouchableOpacity style={styles.messageButton} onPress={handleMessage}>
            <Text style={styles.messageIcon}>💬</Text>
          </TouchableOpacity>
        )}
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E1E1E',
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
  },
  avatarContainer: {
    marginRight: 12,
  },
  avatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
  },
  avatarPlaceholder: {
    backgroundColor: '#3B82F6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarPlaceholderText: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  content: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  username: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ECECEC',
    marginRight: 12,
  },
  statsRow: {
    flexDirection: 'row',
  },
  statText: {
    fontSize: 12,
    color: '#8E8E8E',
  },
  location: {
    fontSize: 12,
    color: '#8E8E8E',
    marginBottom: 4,
  },
  bio: {
    fontSize: 14,
    color: '#B8B8B8',
    lineHeight: 18,
    marginBottom: 6,
  },
  universitiesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  universityTag: {
    backgroundColor: '#2A2A2A',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    marginRight: 6,
    marginBottom: 4,
  },
  universityText: {
    fontSize: 10,
    color: '#8E8E8E',
  },
  actions: {
    marginLeft: 8,
    alignItems: 'center',
  },
  followButton: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 6,
    marginBottom: 6,
  },
  followButtonFollowing: {
    backgroundColor: '#2A2A2A',
    borderWidth: 1,
    borderColor: '#3E3E3E',
  },
  followButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  followButtonTextFollowing: {
    color: '#8E8E8E',
  },
  messageButton: {
    width: 32,
    height: 32,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#2A2A2A',
    borderRadius: 16,
  },
  messageIcon: {
    fontSize: 14,
  },
});
