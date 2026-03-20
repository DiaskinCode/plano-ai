/**
 * CommentThread Component
 *
 * Displays nested comments with:
 * - Threading (indentation for replies)
 * - Author info
 * - Vote buttons
 * - Reply functionality
 * - Collapse/expand
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
} from 'react-native';

interface CommentThreadProps {
  comments: Comment[];
  onVote?: (commentId: number, voteType: 'upvote' | 'downvote') => void;
  onReply?: (commentId: number, content: string) => void;
  depth?: number;
}

export interface Comment {
  id: number;
  content: string;
  author: string;
  author_avatar?: string;
  score: number;
  upvotes: number;
  downvotes: number;
  time_since_posted: string;
  user_vote?: 'upvote' | 'downvote' | null;
  reply_count: number;
  is_edited?: boolean;
  replies?: Comment[];
}

export const CommentThread: React.FC<CommentThreadProps> = ({
  comments,
  onVote,
  onReply,
  depth = 0,
}) => {
  const [expandedReplies, setExpandedReplies] = useState<Set<number>>(new Set());
  const [replyingTo, setReplyingTo] = useState<number | null>(null);
  const [replyText, setReplyText] = useState('');

  const toggleReplies = (commentId: number) => {
    const newExpanded = new Set(expandedReplies);
    if (newExpanded.has(commentId)) {
      newExpanded.delete(commentId);
    } else {
      newExpanded.add(commentId);
    }
    setExpandedReplies(newExpanded);
  };

  const handleReply = (commentId: number) => {
    if (replyText.trim() && onReply) {
      onReply(commentId, replyText.trim());
      setReplyText('');
      setReplyingTo(null);
    }
  };

  const maxDepth = 5;

  return (
    <View style={styles.container}>
      {comments.map((comment) => (
        <View
          key={comment.id}
          style={[styles.commentWrapper, { marginLeft: depth * 12 }]}
        >
          <View style={styles.comment}>
            {/* Vote Section */}
            <View style={styles.voteSection}>
              <TouchableOpacity
                style={[
                  styles.voteButton,
                  comment.user_vote === 'upvote' && styles.voteButtonActive,
                ]}
                onPress={() => onVote?.(comment.id, 'upvote')}
              >
                <Text
                  style={[
                    styles.voteIcon,
                    comment.user_vote === 'upvote' && styles.voteIconActive,
                  ]}
                >
                  ▲
                </Text>
              </TouchableOpacity>

              <Text
                style={[
                  styles.voteCount,
                  comment.user_vote === 'upvote' && styles.voteCountUp,
                  comment.user_vote === 'downvote' && styles.voteCountDown,
                ]}
              >
                {comment.score}
              </Text>

              <TouchableOpacity
                style={[
                  styles.voteButton,
                  comment.user_vote === 'downvote' && styles.voteButtonActive,
                ]}
                onPress={() => onVote?.(comment.id, 'downvote')}
              >
                <Text
                  style={[
                    styles.voteIcon,
                    comment.user_vote === 'downvote' && styles.voteIconActive,
                  ]}
                >
                  ▼
                </Text>
              </TouchableOpacity>
            </View>

            {/* Content Section */}
            <View style={styles.contentSection}>
              {/* Author & Time */}
              <View style={styles.metaRow}>
                <View style={styles.avatar} />
                <Text style={styles.authorName}>{comment.author}</Text>
                <Text style={styles.separator}>•</Text>
                <Text style={styles.timeAgo}>{comment.time_since_posted}</Text>
                {comment.is_edited && (
                  <Text style={styles.editedLabel}>(edited)</Text>
                )}
              </View>

              {/* Content */}
              <Text style={styles.content}>{comment.content}</Text>

              {/* Actions */}
              <View style={styles.actionsRow}>
                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={() => setReplyingTo(replyingTo === comment.id ? null : comment.id)}
                >
                  <Text style={styles.actionText}>Reply</Text>
                </TouchableOpacity>

                {comment.reply_count > 0 && depth < maxDepth && (
                  <TouchableOpacity
                    style={styles.actionButton}
                    onPress={() => toggleReplies(comment.id)}
                  >
                    <Text style={styles.actionText}>
                      {expandedReplies.has(comment.id) ? '− Hide' : `+ ${comment.reply_count} replies`}
                    </Text>
                  </TouchableOpacity>
                )}
              </View>

              {/* Reply Input */}
              {replyingTo === comment.id && (
                <View style={styles.replySection}>
                  <TextInput
                    style={styles.replyInput}
                    placeholder="Write a reply..."
                    placeholderTextColor="#6B7280"
                    multiline
                    value={replyText}
                    onChangeText={setReplyText}
                  />
                  <View style={styles.replyActions}>
                    <TouchableOpacity
                      style={styles.replyButtonCancel}
                      onPress={() => {
                        setReplyingTo(null);
                        setReplyText('');
                      }}
                    >
                      <Text style={styles.replyButtonText}>Cancel</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[
                        styles.replyButtonSubmit,
                        !replyText.trim() && styles.replyButtonDisabled,
                      ]}
                      onPress={() => handleReply(comment.id)}
                      disabled={!replyText.trim()}
                    >
                      <Text
                        style={[
                          styles.replyButtonText,
                          styles.replyButtonTextSubmit,
                        ]}
                      >
                        Reply
                      </Text>
                    </TouchableOpacity>
                  </View>
                </View>
              )}
            </View>
          </View>

          {/* Nested Replies */}
          {comment.replies && comment.replies.length > 0 && expandedReplies.has(comment.id) && (
            <CommentThread
              comments={comment.replies}
              onVote={onVote}
              onReply={onReply}
              depth={depth + 1}
            />
          )}
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 12,
  },
  commentWrapper: {
    marginBottom: 12,
  },
  comment: {
    flexDirection: 'row',
  },
  voteSection: {
    width: 40,
    alignItems: 'center',
    marginRight: 8,
  },
  voteButton: {
    width: 28,
    height: 28,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 14,
  },
  voteButtonActive: {
    backgroundColor: '#3E3E3E',
  },
  voteIcon: {
    fontSize: 14,
    color: '#8E8E8E',
  },
  voteIconActive: {
    color: '#ECECEC',
  },
  voteCount: {
    fontSize: 12,
    fontWeight: '600',
    color: '#ECECEC',
    marginVertical: 2,
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
    marginBottom: 4,
  },
  avatar: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#3E3E3E',
    marginRight: 6,
  },
  authorName: {
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
  timeAgo: {
    fontSize: 11,
    color: '#6B7280',
  },
  editedLabel: {
    fontSize: 10,
    color: '#6B7280',
    fontStyle: 'italic',
    marginLeft: 4,
  },
  content: {
    fontSize: 14,
    color: '#ECECEC',
    lineHeight: 20,
    marginBottom: 6,
  },
  actionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  actionButton: {
    marginRight: 16,
  },
  actionText: {
    fontSize: 12,
    color: '#8E8E8E',
    fontWeight: '500',
  },
  replySection: {
    marginTop: 8,
    backgroundColor: '#2A2A2A',
    borderRadius: 8,
    padding: 8,
  },
  replyInput: {
    backgroundColor: '#1E1E1E',
    borderRadius: 6,
    padding: 10,
    color: '#ECECEC',
    fontSize: 14,
    minHeight: 60,
    textAlignVertical: 'top',
    marginBottom: 8,
  },
  replyActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  replyButtonCancel: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
  },
  replyButtonSubmit: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  replyButtonDisabled: {
    opacity: 0.5,
  },
  replyButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E8E',
  },
  replyButtonTextSubmit: {
    color: '#FFFFFF',
  },
});
