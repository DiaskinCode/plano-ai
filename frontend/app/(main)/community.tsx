/**
 * Community Tab Screen
 *
 * Displays:
 * - Region communities
 * - Topic communities
 * - Search and filter
 * - User's joined communities
 */

import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  RefreshControl,
  SafeAreaView,
  StatusBar,
  Platform,
} from "react-native";
import { router } from "expo-router";
import { communityAPI } from "@/services/api";
import { QuickActions } from "@/components/community/QuickActions";

interface Community {
  id: number;
  name: string;
  slug: string;
  description: string;
  community_type: "region" | "topic";
  icon: string;
  banner_color: string;
  member_count: number;
  member_count_display: string;
  online_count: number;
  post_count: number;
  is_official: boolean;
  tags: string[];
  is_member?: boolean;
  user_role?: string;
}

export default function CommunityScreen() {
  const [tab, setTab] = useState<"region" | "topic" | "my">("region");
  const [communities, setCommunities] = useState<Community[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadCommunities();
    loadUserPlan();
  }, [tab, searchQuery]);

  const loadUserPlan = async () => {
    try {
      const profile = await communityAPI.getMyCommunities();
      // User plan loaded - mentors available on Pro/Premium
    } catch (error) {
      console.error("Failed to load user plan:", error);
    }
  };

  const loadCommunities = async () => {
    try {
      setLoading(true);

      let response;
      if (tab === "my") {
        response = await communityAPI.getMyCommunities();
      } else {
        response = await communityAPI.getCommunities({
          type: tab,
          search: searchQuery || undefined,
          sort: "popular",
        });
      }

      // Handle both paginated and non-paginated responses
      const data = response?.data;
      if (data && typeof data === "object") {
        const communityList = data.results || data;
        setCommunities(Array.isArray(communityList) ? communityList : []);
      } else {
        setCommunities([]);
      }
    } catch (error) {
      console.error("Failed to load communities:", error);
      setCommunities([]);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadCommunities();
    setRefreshing(false);
  };

  const handleJoinCommunity = async (
    communityId: number,
    isMember: boolean,
  ) => {
    try {
      if (isMember) {
        await communityAPI.leaveCommunity(communityId);
      } else {
        await communityAPI.joinCommunity(communityId);
      }

      // Refresh communities
      loadCommunities();
    } catch (error) {
      console.error("Failed to join/leave community:", error);
    }
  };

  const renderCommunityCard = (community: Community) => {
    const isMember = community.is_member;

    return (
      <TouchableOpacity
        key={community.id}
        style={styles.communityCard}
        onPress={() => router.push(`/community/${community.slug}`)}
      >
        {/* Icon & Banner */}
        <View
          style={[
            styles.cardHeader,
            { backgroundColor: community.banner_color },
          ]}
        >
          <Text style={styles.communityIcon}>{community.icon}</Text>
          {community.is_official && (
            <View style={styles.officialBadge}>
              <Text style={styles.officialBadgeText}>✓ Official</Text>
            </View>
          )}
        </View>

        {/* Content */}
        <View style={styles.cardContent}>
          <Text style={styles.communityName}>{community.name}</Text>
          <Text style={styles.description} numberOfLines={2}>
            {community.description}
          </Text>

          {/* Stats */}
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statIcon}>👥</Text>
              <Text style={styles.statText}>
                {community.member_count_display} members
              </Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statIcon}>🟢</Text>
              <Text style={styles.statText}>
                {community.online_count} online
              </Text>
            </View>
          </View>

          {/* Tags */}
          {community.tags && community.tags.length > 0 && (
            <View style={styles.tagsRow}>
              {community.tags.slice(0, 3).map((tag, index) => (
                <View key={index} style={styles.tag}>
                  <Text style={styles.tagText}>{tag}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Action Button */}
          <TouchableOpacity
            style={[styles.joinButton, isMember && styles.joinButtonJoined]}
            onPress={(e) => {
              e.stopPropagation();
              handleJoinCommunity(community.id, isMember || false);
            }}
          >
            <Text
              style={[
                styles.joinButtonText,
                isMember && styles.joinButtonTextJoined,
              ]}
            >
              {isMember ? "Joined" : "Join"}
            </Text>
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <StatusBar barStyle="light-content" backgroundColor="#121212" />
      {/* Header with Quick Actions */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Community</Text>
        <QuickActions />
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, tab === "region" && styles.tabActive]}
          onPress={() => setTab("region")}
        >
          <Text
            style={[styles.tabText, tab === "region" && styles.tabTextActive]}
          >
            By Region
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, tab === "topic" && styles.tabActive]}
          onPress={() => setTab("topic")}
        >
          <Text
            style={[styles.tabText, tab === "topic" && styles.tabTextActive]}
          >
            By Topic
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, tab === "my" && styles.tabActive]}
          onPress={() => setTab("my")}
        >
          <Text style={[styles.tabText, tab === "my" && styles.tabTextActive]}>
            My Communities
          </Text>
        </TouchableOpacity>
      </View>

      {/* Search */}
      <View style={styles.searchSection}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search communities..."
          placeholderTextColor="#6B7280"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>

      {/* Communities List */}
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {loading ? (
          <View style={styles.centerContent}>
            <ActivityIndicator size="large" color="#3B82F6" />
            <Text style={styles.loadingText}>Loading communities...</Text>
          </View>
        ) : !Array.isArray(communities) || communities.length === 0 ? (
          <View style={styles.centerContent}>
            <Text style={styles.emptyText}>No communities found</Text>
            <Text style={styles.emptySubtext}>
              Try adjusting your search or filters
            </Text>
          </View>
        ) : (
          communities.map((community) => renderCommunityCard(community))
        )}
      </ScrollView>

      {/* FAB - Create Post */}
      <TouchableOpacity
        style={styles.fab}
        onPress={() => {
          // TODO: Open create post modal
          console.log("Create post FAB pressed");
        }}
      >
        <Text style={styles.fabIcon}>+</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#121212",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#2A2A2A",
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: "700",
    color: "#ECECEC",
  },
  tabs: {
    flexDirection: "row",
    paddingHorizontal: 16,
    paddingTop: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#2A2A2A",
  },
  tab: {
    marginRight: 24,
    paddingBottom: 12,
  },
  tabActive: {
    borderBottomWidth: 2,
    borderBottomColor: "#3B82F6",
  },
  tabText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#8E8E8E",
  },
  tabTextActive: {
    color: "#ECECEC",
  },
  searchSection: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#2A2A2A",
  },
  searchInput: {
    backgroundColor: "#1E1E1E",
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: "#ECECEC",
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  centerContent: {
    paddingVertical: 40,
    alignItems: "center",
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: "#8E8E8E",
  },
  emptyText: {
    fontSize: 16,
    fontWeight: "600",
    color: "#8E8E8E",
    marginBottom: 4,
  },
  emptySubtext: {
    fontSize: 14,
    color: "#6B7280",
  },
  communityCard: {
    backgroundColor: "#1E1E1E",
    borderRadius: 12,
    marginBottom: 16,
    overflow: "hidden",
  },
  cardHeader: {
    height: 80,
    justifyContent: "center",
    alignItems: "center",
    position: "relative",
  },
  communityIcon: {
    fontSize: 40,
  },
  officialBadge: {
    position: "absolute",
    top: 8,
    right: 8,
    backgroundColor: "rgba(0, 0, 0, 0.6)",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  officialBadgeText: {
    fontSize: 10,
    fontWeight: "600",
    color: "#10B981",
  },
  cardContent: {
    padding: 12,
  },
  communityName: {
    fontSize: 18,
    fontWeight: "700",
    color: "#ECECEC",
    marginBottom: 6,
  },
  description: {
    fontSize: 14,
    color: "#B8B8B8",
    marginBottom: 12,
    lineHeight: 20,
  },
  statsRow: {
    flexDirection: "row",
    marginBottom: 12,
  },
  statItem: {
    flexDirection: "row",
    alignItems: "center",
    marginRight: 16,
  },
  statIcon: {
    fontSize: 14,
    marginRight: 4,
  },
  statText: {
    fontSize: 12,
    color: "#8E8E8E",
  },
  tagsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginBottom: 12,
  },
  tag: {
    backgroundColor: "#2A2A2A",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    marginRight: 6,
    marginBottom: 6,
  },
  tagText: {
    fontSize: 11,
    color: "#8E8E8E",
  },
  joinButton: {
    backgroundColor: "#3B82F6",
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: "center",
  },
  joinButtonJoined: {
    backgroundColor: "#2A2A2A",
    borderWidth: 1,
    borderColor: "#3E3E3E",
  },
  joinButtonText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#FFFFFF",
  },
  joinButtonTextJoined: {
    color: "#8E8E8E",
  },
  fab: {
    position: "absolute",
    bottom: 24,
    right: 24,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: "#3B82F6",
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  fabIcon: {
    fontSize: 28,
    color: "#FFFFFF",
    fontWeight: "300",
  },
});
