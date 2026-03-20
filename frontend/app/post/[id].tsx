/**
 * Post Detail Screen
 *
 * Displays:
 * - Full post content
 * - Author info
 * - Voting
 * - Nested comments
 * - Reply functionality
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  TextInput,
  Alert,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { communityAPI } from '@/services/api';
import { CommentThread, Comment } from '@/components/community/CommentThread';

interface Post {
  id: number;
  title: string;
  content: string;
  flair: string;
  images: string[];
  files: Array<{ url: string; name: string }>;
  author: string;
  author_avatar?: string;
  author_joined_date?: string;
  community: {
    id: number;
    name: string;
    slug: string;
    icon: string;
  };
  score: number;
  upvotes: number;
  downvotes: number;
  comment_count: number;
  view_count: number;
  is_pinned: boolean;
  is_locked: boolean;
  time_since_posted: string;
  user_vote?: 'upvote' | 'downvote' | null;
}

export default function PostDetailScreen() {
  const { id } = useLocalSearchParams();
  const [post, setPost] = useState<Post | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [commentText, setCommentText] = useState('');

  useEffect(() => {
    if (id) {
      loadPost();
      loadComments();
    }
  }, [id]);

  const loadPost = async () => {
    try {
      const response = await communityAPI.getPost(Number(id));
      setPost(response.data);
    } catch (error) {
      console.error('Failed to load post:', error);
      Alert.alert('Error', 'Failed to load post');
    } finally {
      setLoading(false);
    }
  };

  const loadComments = async () => {
    try {
      const response = await communityAPI.getPostComments(Number(id));
      setComments(response.data.results || response.data);
    } catch (error) {
      console.error('Failed to load comments:', error);
    }
  };

  const handleVote = async (voteType: 'upvote' | 'downvote') => {
    if (!post) return;

    try {
      const response = voteType === 'upvote'
        ? await communityAPI.upvotePost(post.id)
        : await communityAPI.downvotePost(post.id);

      setPost(response.data);
    } catch (error) {
      console.error('Failed to vote:', error);
    }
  };

  const handleCommentVote = async (commentId: number, voteType: 'upvote' | 'downvote') => {
    try {
      const response = voteType === 'upvote'
        ? await communityAPI.upvoteComment(commentId)
        : await communityAPI.downvoteComment(commentId);

      // Update comment in list
      const updateComments = (comments: Comment[]): Comment[] => {
        return comments.map(comment => {
          if (comment.id === commentId) {
            return response.data;
          }
          if (comment.replies) {
            return {
              ...comment,
              replies: updateComments(comment.replies),
            };
          }
          return comment;
        });
      };

      setComments(updateComments(comments));
    } catch (error) {
      console.error('Failed to vote on comment:', error);
    }
  };

  const handlePostComment = async () => {
    if (!commentText.trim() || !post) return;

    try {
      await communityAPI.createComment({
        post: post.id,
        content: commentText.trim(),
      });

      setCommentText('');
      loadComments(); // Reload comments to get new one
    } catch (error) {
      console.error('Failed to post comment:', error);
      Alert.alert('Error', 'Failed to post comment');
    }
  };

  const handleReply = async (parentCommentId: number, content: string) => {
    if (!post) return;

    try {
      await communityAPI.createComment({
        post: post.id,
        parent_comment: parentCommentId,
        content,
      });

      loadComments(); // Reload to show new reply
    } catch (error) {
      console.error('Failed to reply:', error);
      Alert.alert('Error', 'Failed to post reply');
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContent}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  if (!post) {
    return (
      <View style={styles.centerContent}>
        <Text style={styles.errorText}>Post not found</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor="#121212" />
      <ScrollView style={styles.scrollView}>
        {/* Community Header */}
        <TouchableOpacity
          style={styles.communityHeader}
          onPress={() => router.push(`/community/${post.community.slug}`)}
        >
          <Text style={styles.communityIcon}>{post.community.icon}</Text>
          <View style={styles.communityInfo}>
            <Text style={styles.communityName}>{post.community.name}</Text>
            <View style={styles.metaRow}>
              <Text style={styles.authorName}>{post.author}</Text>
              <Text style={styles.separator}>•</Text>
              <Text style={styles.timeAgo}>{post.time_since_posted}</Text>
            </View>
          </View>
        </TouchableOpacity>

        {/* Flair & Title */}
        <View style={styles.postHeader}>
          {post.flair && (
            <View style={styles.flairBadge}>
              <Text style={styles.flairText}>{post.flair.toUpperCase()}</Text>
            </View>
          )}
          {post.is_pinned && <Text style={styles.pinnedLabel}>📌 Pinned</Text>}
          <Text style={styles.title}>{post.title}</Text>
        </View>

        {/* Content */}
        <Text style={styles.content}>{post.content}</Text>

        {/* Images (if any) */}
        {post.images && post.images.length > 0 && (
          <View style={styles.imagesContainer}>
            {/* TODO: Render images */}
            <Text style={styles.imagesPlaceholder}>{post.images.length} images</Text>
          </View>
        )}

        {/* Engagement Stats */}
        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <Text style={styles.statIcon}>👁</Text>
            <Text style={styles.statText}>{post.view_count} views</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statIcon}>💬</Text>
            <Text style={styles.statText}>{post.comment_count} comments</Text>
          </View>
        </View>

        {/* Action Bar */}
        <View style={styles.actionBar}>
          <TouchableOpacity
            style={[
              styles.voteButton,
              post.user_vote === 'upvote' && styles.voteButtonActive,
            ]}
            onPress={() => handleVote('upvote')}
          >
            <Text
              style={[
                styles.voteButtonText,
                post.user_vote === 'upvote' && styles.voteButtonTextActive,
              ]}
            >
              ▲ Upvote
            </Text>
          </TouchableOpacity>

          <View style={styles.voteCount}>
            <Text
              style={[
                styles.voteCountText,
                post.user_vote === 'upvote' && styles.voteCountUp,
                post.user_vote === 'downvote' && styles.voteCountDown,
              ]}
            >
              {post.score}
            </Text>
          </View>

          <TouchableOpacity
            style={[
              styles.voteButton,
              post.user_vote === 'downvote' && styles.voteButtonActive,
            ]}
            onPress={() => handleVote('downvote')}
          >
            <Text
              style={[
                styles.voteButtonText,
                post.user_vote === 'downvote' && styles.voteButtonTextActive,
              ]}
            >
              ▼ Downvote
            </Text>
          </TouchableOpacity>
        </View>

        {/* Comment Input */}
        {!post.is_locked && (
          <View style={styles.commentInputSection}>
            <TextInput
              style={styles.commentInput}
              placeholder="What are your thoughts?"
              placeholderTextColor="#6B7280"
              multiline
              value={commentText}
              onChangeText={setCommentText}
            />
            <TouchableOpacity
              style={[
                styles.commentSubmitButton,
                !commentText.trim() && styles.commentSubmitButtonDisabled,
              ]}
              onPress={handlePostComment}
              disabled={!commentText.trim()}
            >
              <Text
                style={[
                  styles.commentSubmitButtonText,
                  !commentText.trim() && styles.commentSubmitButtonTextDisabled,
                ]}
              >
                Comment
              </Text>
            </TouchableOpacity>
          </View>
        )}

        {post.is_locked && (
          <View style={styles.lockedNotice}>
            <Text style={styles.lockedNoticeText}>🔒 Comments are locked</Text>
          </View>
        )}

        {/* Comments */}
        <View style={styles.commentsSection}>
          <Text style={styles.commentsTitle}>
            Comments ({post.comment_count})
          </Text>

          {comments.length === 0 ? (
            <View style={styles.emptyComments}>
              <Text style={styles.emptyText}>No comments yet</Text>
              <Text style={styles.emptySubtext}>
                Be the first to share your thoughts!
              </Text>
            </View>
          ) : (
            <CommentThread
              comments={comments}
              onVote={handleCommentVote}
              onReply={handleReply}
            />
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
  communityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  communityIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  communityInfo: {
    flex: 1,
  },
  communityName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E8E',
    marginBottom: 2,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  authorName: {
    fontSize: 12,
    color: '#8E8E8E',
  },
  separator: {
    fontSize: 12,
    color: '#6B7280',
    marginHorizontal: 4,
  },
  timeAgo: {
    fontSize: 11,
    color: '#6B7280',
  },
  postHeader: {
    padding: 16,
  },
  flairBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#2A2A2A',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 4,
    marginBottom: 8,
  },
  flairText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#8B5CF6',
    letterSpacing: 0.5,
  },
  pinnedLabel: {
    fontSize: 12,
    color: '#10B981',
    fontWeight: '600',
    marginBottom: 8,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#ECECEC',
    lineHeight: 30,
  },
  content: {
    fontSize: 16,
    color: '#ECECEC',
    lineHeight: 24,
    padding: 16,
  },
  imagesContainer: {
    padding: 16,
  },
  imagesPlaceholder: {
    fontSize: 14,
    color: '#8E8E8E',
  },
  statsRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 8,
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
  actionBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  voteButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  voteButtonActive: {
    backgroundColor: '#2A2A2A',
  },
  voteButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E8E',
  },
  voteButtonTextActive: {
    color: '#ECECEC',
  },
  voteCount: {
    marginHorizontal: 16,
  },
  voteCountText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#ECECEC',
  },
  voteCountUp: {
    color: '#FF6B6B',
  },
  voteCountDown: {
    color: '#6B9BD1',
  },
  commentInputSection: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  commentInput: {
    backgroundColor: '#1E1E1E',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#ECECEC',
    minHeight: 80,
    textAlignVertical: 'top',
    marginBottom: 8,
  },
  commentSubmitButton: {
    backgroundColor: '#3B82F6',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  commentSubmitButtonDisabled: {
    backgroundColor: '#2A2A2A',
  },
  commentSubmitButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  commentSubmitButtonTextDisabled: {
    color: '#6B7280',
  },
  lockedNotice: {
    padding: 16,
    backgroundColor: '#2A2A2A',
    alignItems: 'center',
  },
  lockedNoticeText: {
    fontSize: 14,
    color: '#8E8E8E',
  },
  commentsSection: {
    paddingBottom: 16,
  },
  commentsTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ECECEC',
    padding: 16,
    paddingBottom: 8,
  },
  emptyComments: {
    padding: 16,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E8E',
    marginBottom: 4,
  },
  emptySubtext: {
    fontSize: 12,
    color: '#6B7280',
  },
});
