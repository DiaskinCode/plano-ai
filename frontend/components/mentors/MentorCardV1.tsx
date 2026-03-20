/**
 * MentorCard Component
 *
 * Updated for simplified V1 API
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Mentor } from '@/types/mentor';

interface MentorCardProps {
  mentor: Mentor;
  userPlan?: 'basic' | 'pro' | 'premium';
}

export function MentorCard({ mentor, userPlan = 'basic' }: MentorCardProps) {
  const router = useRouter();

  const isAccessible = userPlan === 'pro' || userPlan === 'premium';

  const handlePress = () => {
    if (!isAccessible) {
      // Show upgrade modal
      return;
    }
    router.push(`/mentor/${mentor.id}`);
  };

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={handlePress}
      activeOpacity={0.7}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.profileInfo}>
          {mentor.photo_url ? (
            <Image source={{ uri: mentor.photo_url }} style={styles.avatar} />
          ) : (
            <View style={[styles.avatar, styles.avatarPlaceholder]}>
              <MaterialCommunityIcons name="account" size={32} color="#999" />
            </View>
          )}
          <View style={styles.textContainer}>
            <Text style={styles.title}>{mentor.title}</Text>
            <View style={styles.statsRow}>
              <View style={styles.ratingContainer}>
                <MaterialCommunityIcons name="star" size={16} color="#FFD700" />
                <Text style={styles.rating}>{mentor.rating.toFixed(1)}</Text>
                <Text style={styles.reviewCount}>({mentor.total_sessions})</Text>
              </View>
              <Text style={styles.timezone}>{mentor.timezone}</Text>
            </View>
          </View>
        </View>
        {mentor.is_verified && (
          <View style={styles.verifiedBadge}>
            <MaterialCommunityIcons name="check-decagram" size={16} color="#4CAF50" />
          </View>
        )}
      </View>

      {/* Bio */}
      <Text style={styles.bio} numberOfLines={2}>
        {mentor.bio}
      </Text>

      {/* Expertise Areas */}
      <View style={styles.expertiseContainer}>
        {mentor.expertise_areas.slice(0, 3).map((area, index) => (
          <View key={index} style={styles.expertiseChip}>
            <Text style={styles.expertiseText}>{area}</Text>
          </View>
        ))}
        {mentor.expertise_areas.length > 3 && (
          <Text style={styles.moreText}>+{mentor.expertise_areas.length - 3}</Text>
        )}
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        <View style={styles.priceContainer}>
          <MaterialCommunityIcons name="clock-outline" size={16} color="#666" />
          <Text style={styles.price}>{mentor.hourly_rate_credits} credits/hr</Text>
        </View>
        <View style={styles.availabilityContainer}>
          <View style={[styles.dot, { backgroundColor: '#4CAF50' }]} />
          <Text style={styles.availabilityText}>Available</Text>
        </View>
      </View>

      {/* Lock overlay for basic users */}
      {!isAccessible && <View style={styles.lockOverlay} />}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  profileInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    marginRight: 12,
  },
  avatarPlaceholder: {
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  textContainer: {
    flex: 1,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 12,
  },
  rating: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginLeft: 4,
  },
  reviewCount: {
    fontSize: 12,
    color: '#999',
    marginLeft: 4,
  },
  timezone: {
    fontSize: 12,
    color: '#999',
  },
  verifiedBadge: {
    padding: 4,
  },
  bio: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 12,
  },
  expertiseContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 12,
  },
  expertiseChip: {
    backgroundColor: '#f0f7ff',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 6,
    marginBottom: 6,
  },
  expertiseText: {
    fontSize: 12,
    color: '#0066cc',
    fontWeight: '500',
  },
  moreText: {
    fontSize: 12,
    color: '#999',
    marginLeft: 6,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    paddingTop: 12,
  },
  priceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  price: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginLeft: 6,
  },
  availabilityContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  availabilityText: {
    fontSize: 12,
    color: '#4CAF50',
    fontWeight: '500',
  },
  lockOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 12,
  },
});
