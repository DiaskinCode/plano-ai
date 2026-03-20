/**
 * PostCard Component
 *
 * Displays a post preview card with:
 * - Author info (avatar, username)
 * - Community name and icon
 * - Flair badge
 * - Title and content preview
 * - Engagement stats (votes, comments)
 * - Time since posted
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

interface PostCardProps {
  post: {
    id: number;
    title: string;
    content: string;
    flair: string;
    author: string;
    author_avatar?: string;
    community_name: string;
    community_icon: string;
    score: number;
    upvotes: number;
    downvotes: number;
    comment_count: number;
    time_since_posted: string;
    user_vote?: 'upvote' | 'downvote' | null;
    is_pinned?: boolean;
  };
  onVote?: (postId: number, voteType: 'upvote' | 'downvote') => void;
}

const FLAIR_COLORS: Record<string, string> = {
  success: '#10B981',
  question: '#3B82F6',
  advice: '#8B5CF6',
  essay: '#F59E0B',
  news: '#EF4444',
  resource: '#06B6D4',
  discussion: '#6366F1',
  rant: '#EC4899',
};

export const PostCard: React.FC<PostCardProps> = ({ post, onVote }) => {
  const handlePress = () => {
    router.push(`/post/${post.id}`);
  };

  const handleVote = (voteType: 'upvote' | 'downvote') => {
    if (onVote) {
      onVote(post.id, voteType);
    }
  };

  const flairColor = FLAIR_COLORS[post.flair] || '#6B7280';

  return (
    <TouchableOpacity style={styles.container} onPress={handlePress}>
      {/* Vote Section */}
      <View style={styles.voteSection}>
        <TouchableOpacity
          style={[
            styles.voteButton,
            post.user_vote === 'upvote' && styles.voteButtonActive,
          ]}
          onPress={() => handleVote('upvote')}
        >
          <Text
            style={[
              styles.voteIcon,
              post.user_vote === 'upvote' && styles.voteIconActive,
            ]}
          >
            ▲
          </Text>
        </TouchableOpacity>

        <Text
          style={[
            styles.voteCount,
            post.user_vote === 'upvote' && styles.voteCountUp,
            post.user_vote === 'downvote' && styles.voteCountDown,
          ]}
        >
          {post.score}
        </Text>

        <TouchableOpacity
          style={[
            styles.voteButton,
            post.user_vote === 'downvote' && styles.voteButtonActive,
          ]}
          onPress={() => handleVote('downvote')}
        >
          <Text
            style={[
              styles.voteIcon,
              post.user_vote === 'downvote' && styles.voteIconActive,
            ]}
          >
            ▼
          </Text>
        </TouchableOpacity>
      </View>

      {/* Content Section */}
      <View style={styles.contentSection}>
        {/* Community & Author */}
        <View style={styles.metaRow}>
          <Text style={styles.communityIcon}>{post.community_icon}</Text>
          <Text style={styles.communityName}>{post.community_name}</Text>
          <Text style={styles.separator}>•</Text>
          <Text style={styles.authorName}>{post.author}</Text>
          <Text style={styles.separator}>•</Text>
          <Text style={styles.timeAgo}>{post.time_since_posted}</Text>
        </View>

        {/* Title */}
        {post.is_pinned && (
          <Text style={styles.pinnedLabel}>📌 Pinned</Text>
        )}
        <Text style={styles.title} numberOfLines={2}>
          {post.title}
        </Text>

        {/* Flair Badge */}
        {post.flair && (
          <View style={[styles.flairBadge, { borderColor: flairColor }]}>
            <Text style={[styles.flairText, { color: flairColor }]}>
              {post.flair.toUpperCase()}
            </Text>
          </View>
        )}

        {/* Content Preview */}
        <Text style={styles.content} numberOfLines={3}>
          {post.content}
        </Text>

        {/* Engagement Stats */}
        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <Text style={styles.statIcon}>💬</Text>
            <Text style={styles.statText}>{post.comment_count} comments</Text>
          </View>

          <View style={styles.statItem}>
            <Text style={styles.statIcon}>👁</Text>
            <Text style={styles.statText}>Share</Text>
          </View>

          <View style={styles.statItem}>
            <Text style={styles.statIcon}>🔖</Text>
            <Text style={styles.statText}>Save</Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: '#1E1E1E',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  voteSection: {
    width: 50,
    alignItems: 'center',
    marginRight: 12,
  },
  voteButton: {
    width: 36,
    height: 36,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 18,
  },
  voteButtonActive: {
    backgroundColor: '#3E3E3E',
  },
  voteIcon: {
    fontSize: 18,
    color: '#8E8E8E',
  },
  voteIconActive: {
    color: '#ECECEC',
  },
  voteCount: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ECECEC',
    marginVertical: 4,
  },
  voteCountUp: {
    color: '#FF6B6B',
  },
  voteCountDown: {
    color: '#6B9BD1',
  },
  contentSection: {
    flex: 1,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  communityIcon: {
    fontSize: 14,
    marginRight: 4,
  },
  communityName: {
    fontSize: 12,
    fontWeight: '600',
    color: '#8E8E8E',
    marginRight: 4,
  },
  separator: {
    fontSize: 12,
    color: '#6B7280',
    marginHorizontal: 4,
  },
  authorName: {
    fontSize: 12,
    color: '#8E8E8E',
  },
  timeAgo: {
    fontSize: 11,
    color: '#6B7280',
  },
  pinnedLabel: {
    fontSize: 11,
    color: '#10B981',
    fontWeight: '600',
    marginBottom: 4,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ECECEC',
    marginBottom: 6,
    lineHeight: 22,
  },
  flairBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    borderWidth: 1,
    marginBottom: 6,
  },
  flairText: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  content: {
    fontSize: 14,
    color: '#B8B8B8',
    lineHeight: 20,
    marginBottom: 8,
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
  },
  statIcon: {
    fontSize: 14,
    marginRight: 4,
  },
  statText: {
    fontSize: 12,
    color: '#8E8E8E',
  },
});
