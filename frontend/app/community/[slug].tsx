/**
 * Community Detail Screen
 *
 * Displays:
 * - Community info (members, description, rules)
 * - Posts in the community
 * - Sort options (hot, new, top)
 * - Filter by flair
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Modal,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { communityAPI } from '@/services/api';
import { PostCard } from '@/components/community/PostCard';

interface Community {
  id: number;
  name: string;
  slug: string;
  description: string;
  community_type: 'region' | 'topic';
  icon: string;
  banner_color: string;
  rules: string[];
  member_count: number;
  online_count: number;
  post_count: number;
  is_official: boolean;
  tags: string[];
  is_member?: boolean;
  user_role?: string;
}

interface Post {
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
}

const SORT_OPTIONS = [
  { key: 'hot', label: '🔥 Hot' },
  { key: 'new', label: '✨ New' },
  { key: 'top', label: '🏆 Top' },
];

const FLAIR_OPTIONS = [
  { key: '', label: 'All' },
  { key: 'success', label: '✅ Success' },
  { key: 'question', label: '❓ Question' },
  { key: 'advice', label: '💡 Advice' },
  { key: 'essay', label: '📝 Essay' },
  { key: 'news', label: '📰 News' },
  { key: 'resource', label: '📚 Resource' },
  { key: 'discussion', label: '💬 Discussion' },
  { key: 'rant', label: '😤 Rant' },
];

export default function CommunityDetailScreen() {
  const { slug } = useLocalSearchParams();
  const [community, setCommunity] = useState<Community | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [sort, setSort] = useState('hot');
  const [flair, setFlair] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showSortMenu, setShowSortMenu] = useState(false);
  const [showFlairMenu, setShowFlairMenu] = useState(false);

  useEffect(() => {
    if (slug) {
      loadCommunity();
      loadPosts();
    }
  }, [slug, sort, flair]);

  const loadCommunity = async () => {
    try {
      // Get community by slug (need to search for it)
      const response = await communityAPI.getCommunities({ search: slug as string });
      const communities = response.data.results || response.data;
      const found = communities.find((c: Community) => c.slug === slug);
      if (found) {
        setCommunity(found);
      }
    } catch (error) {
      console.error('Failed to load community:', error);
    }
  };

  const loadPosts = async () => {
    if (!community) return;

    try {
      setLoading(true);
      const response = await communityAPI.getCommunityPosts(community.id, {
        sort: sort as any,
        flair: flair || undefined,
      });
      setPosts(response.data.results || response.data);
    } catch (error) {
      console.error('Failed to load posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadCommunity();
    await loadPosts();
    setRefreshing(false);
  };

  const handleVote = async (postId: number, voteType: 'upvote' | 'downvote') => {
    try {
      const response = voteType === 'upvote'
        ? await communityAPI.upvotePost(postId)
        : await communityAPI.downvotePost(postId);

      // Update post in list
      setPosts(posts.map(post =>
        post.id === postId ? response.data : post
      ));
    } catch (error) {
      console.error('Failed to vote:', error);
    }
  };

  const handleJoinLeave = async () => {
    if (!community) return;

    try {
      if (community.is_member) {
        await communityAPI.leaveCommunity(community.id);
      } else {
        await communityAPI.joinCommunity(community.id);
      }

      // Reload community
      loadCommunity();
    } catch (error) {
      console.error('Failed to join/leave:', error);
    }
  };

  if (!community) {
    return (
      <View style={styles.centerContent}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  const isMember = community.is_member;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor="#121212" />
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Banner */}
        <View style={[styles.banner, { backgroundColor: community.banner_color }]}>
          <Text style={styles.bannerIcon}>{community.icon}</Text>
          {community.is_official && (
            <View style={styles.officialBadge}>
              <Text style={styles.officialBadgeText}>✓ Official Community</Text>
            </View>
          )}
        </View>

        {/* Info */}
        <View style={styles.infoSection}>
          <Text style={styles.communityName}>{community.name}</Text>

          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statIcon}>👥</Text>
              <Text style={styles.statText}>{community.member_count.toLocaleString()}</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statIcon}>🟢</Text>
              <Text style={styles.statText}>{community.online_count} online</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statIcon}>📝</Text>
              <Text style={styles.statText}>{community.post_count} posts</Text>
            </View>
          </View>

          <Text style={styles.description}>{community.description}</Text>

          {/* Join Button */}
          {!isMember && (
            <TouchableOpacity
              style={styles.joinButton}
              onPress={handleJoinLeave}
            >
              <Text style={styles.joinButtonText}>Join Community</Text>
            </TouchableOpacity>
          )}

          {isMember && (
            <View style={styles.memberInfo}>
              <Text style={styles.memberInfoText}>
                ✓ You're a member{community.user_role ? ` (${community.user_role})` : ''}
              </Text>
              <TouchableOpacity onPress={handleJoinLeave}>
                <Text style={styles.leaveButtonText}>Leave</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Rules */}
        {community.rules.length > 0 && (
          <View style={styles.rulesSection}>
            <Text style={styles.rulesTitle}>Rules</Text>
            {community.rules.map((rule, index) => (
              <View key={index} style={styles.ruleItem}>
                <Text style={styles.ruleNumber}>{index + 1}.</Text>
                <Text style={styles.ruleText}>{rule}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Tags */}
        {community.tags.length > 0 && (
          <View style={styles.tagsSection}>
            {community.tags.map((tag, index) => (
              <View key={index} style={styles.tag}>
                <Text style={styles.tagText}>{tag}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Sort & Filter */}
        <View style={styles.filtersRow}>
          <TouchableOpacity
            style={styles.filterButton}
            onPress={() => setShowSortMenu(true)}
          >
            <Text style={styles.filterButtonText}>
              {SORT_OPTIONS.find(s => s.key === sort)?.label}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.filterButton}
            onPress={() => setShowFlairMenu(true)}
          >
            <Text style={styles.filterButtonText}>
              {FLAIR_OPTIONS.find(f => f.key === flair)?.label}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Posts */}
        <View style={styles.postsSection}>
          {loading ? (
            <View style={styles.centerContent}>
              <ActivityIndicator size="large" color="#3B82F6" />
            </View>
          ) : posts.length === 0 ? (
            <View style={styles.centerContent}>
              <Text style={styles.emptyText}>No posts yet</Text>
              <Text style={styles.emptySubtext}>
                Be the first to post in {community.name}!
              </Text>
            </View>
          ) : (
            posts.map((post) => (
              <PostCard key={post.id} post={post} onVote={handleVote} />
            ))
          )}
        </View>
      </ScrollView>

      {/* Sort Menu Modal */}
      <Modal
        visible={showSortMenu}
        transparent
        animationType="slide"
        onRequestClose={() => setShowSortMenu(false)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setShowSortMenu(false)}
        >
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Sort by</Text>
            {SORT_OPTIONS.map((option) => (
              <TouchableOpacity
                key={option.key}
                style={styles.modalOption}
                onPress={() => {
                  setSort(option.key);
                  setShowSortMenu(false);
                }}
              >
                <Text
                  style={[
                    styles.modalOptionText,
                    sort === option.key && styles.modalOptionTextActive,
                  ]}
                >
                  {option.label}
                </Text>
                {sort === option.key && (
                  <Text style={styles.modalCheck}>✓</Text>
                )}
              </TouchableOpacity>
            ))}
          </View>
        </TouchableOpacity>
      </Modal>

      {/* Flair Menu Modal */}
      <Modal
        visible={showFlairMenu}
        transparent
        animationType="slide"
        onRequestClose={() => setShowFlairMenu(false)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setShowFlairMenu(false)}
        >
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Filter by flair</Text>
            {FLAIR_OPTIONS.map((option) => (
              <TouchableOpacity
                key={option.key}
                style={styles.modalOption}
                onPress={() => {
                  setFlair(option.key);
                  setShowFlairMenu(false);
                }}
              >
                <Text
                  style={[
                    styles.modalOptionText,
                    flair === option.key && styles.modalOptionTextActive,
                  ]}
                >
                  {option.label}
                </Text>
                {flair === option.key && (
                  <Text style={styles.modalCheck}>✓</Text>
                )}
              </TouchableOpacity>
            ))}
          </View>
        </TouchableOpacity>
      </Modal>
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
  scrollView: {
    flex: 1,
  },
  banner: {
    height: 120,
    justifyContent: 'center',
    alignItems: 'center',
  },
  bannerIcon: {
    fontSize: 48,
  },
  officialBadge: {
    position: 'absolute',
    bottom: 8,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  officialBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#10B981',
  },
  infoSection: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  communityName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#ECECEC',
    marginBottom: 12,
  },
  statsRow: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
  },
  statIcon: {
    fontSize: 16,
    marginRight: 4,
  },
  statText: {
    fontSize: 14,
    color: '#8E8E8E',
  },
  description: {
    fontSize: 14,
    color: '#B8B8B8',
    lineHeight: 20,
    marginBottom: 12,
  },
  joinButton: {
    backgroundColor: '#3B82F6',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  joinButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  memberInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#2A2A2A',
    padding: 12,
    borderRadius: 8,
  },
  memberInfoText: {
    fontSize: 14,
    color: '#10B981',
  },
  leaveButtonText: {
    fontSize: 14,
    color: '#EF4444',
    fontWeight: '600',
  },
  rulesSection: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  rulesTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ECECEC',
    marginBottom: 12,
  },
  ruleItem: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  ruleNumber: {
    fontSize: 14,
    color: '#8E8E8E',
    marginRight: 8,
  },
  ruleText: {
    flex: 1,
    fontSize: 14,
    color: '#B8B8B8',
    lineHeight: 20,
  },
  tagsSection: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  tag: {
    backgroundColor: '#2A2A2A',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 8,
  },
  tagText: {
    fontSize: 12,
    color: '#8E8E8E',
  },
  filtersRow: {
    flexDirection: 'row',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  filterButton: {
    backgroundColor: '#2A2A2A',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    marginRight: 8,
  },
  filterButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ECECEC',
  },
  postsSection: {
    paddingBottom: 16,
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
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1E1E1E',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 20,
    paddingBottom: 40,
    paddingHorizontal: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ECECEC',
    marginBottom: 16,
  },
  modalOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  modalOptionText: {
    fontSize: 16,
    color: '#ECECEC',
  },
  modalOptionTextActive: {
    color: '#3B82F6',
    fontWeight: '600',
  },
  modalCheck: {
    fontSize: 18,
    color: '#3B82F6',
  },
});
