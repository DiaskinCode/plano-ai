/**
 * Booking Confirmation Screen (V1)
 *
 * Confirm and book a mentor session
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
  Alert,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { getMentor, bookSession } from '@/services/mentorship';
import { Mentor } from '@/types/mentor';

export default function MentorBookScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{
    mentorId: string;
    startAt: string;
    duration: string;
  }>();

  const mentorId = parseInt(params.mentorId);
  const startAt = params.startAt;
  const duration = parseInt(params.duration);

  const [mentor, setMentor] = useState<Mentor | null>(null);
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState(false);
  const [notes, setNotes] = useState('');
  const [topic, setTopic] = useState('Essay Review');

  const topicOptions = [
    'Essay Review',
    'Plan Validation',
    'Interview Prep',
    'Career Guidance',
    'Other',
  ];

  useEffect(() => {
    loadMentor();
  }, [mentorId]);

  const loadMentor = async () => {
    try {
      setLoading(true);
      const data = await getMentor(mentorId);
      setMentor(data);
    } catch (error) {
      console.error('Error loading mentor:', error);
      Alert.alert('Error', 'Failed to load mentor information');
    } finally {
      setLoading(false);
    }
  };

  const handleBook = async () => {
    if (!mentor) return;

    try {
      setBooking(true);

      await bookSession(mentorId, {
        start_at: startAt,
        duration_minutes: duration,
        notes: notes.trim(),
        topic: topic,
      });

      Alert.alert(
        'Booking Requested!',
        'Your session has been requested. You will receive a confirmation once the mentor accepts.',
        [
          {
            text: 'OK',
            onPress: () => router.back(),
          },
        ]
      );
    } catch (error: any) {
      Alert.alert('Booking Failed', error.message || 'Failed to book session');
    } finally {
      setBooking(false);
    }
  };

  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      timeZone: mentor?.timezone || 'UTC',
    });
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#0066cc" />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <MaterialCommunityIcons name="arrow-left" size={24} color="#1a1a1a" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Book Session</Text>
        </View>

        {/* Mentor Info */}
        {mentor && (
          <View style={styles.section}>
            <View style={styles.mentorInfo}>
              <Text style={styles.mentorName}>{mentor.title}</Text>
              <View style={styles.mentorStats}>
                <View style={styles.stat}>
                  <MaterialCommunityIcons name="star" size={16} color="#FFD700" />
                  <Text style={styles.statText}>{mentor.rating.toFixed(1)}</Text>
                </View>
                <View style={styles.stat}>
                  <MaterialCommunityIcons name="clock-outline" size={16} color="#0066cc" />
                  <Text style={styles.statText}>{mentor.total_sessions} sessions</Text>
                </View>
              </View>
            </View>
          </View>
        )}

        {/* Session Details */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Session Details</Text>

          <View style={styles.detailRow}>
            <MaterialCommunityIcons name="calendar" size={20} color="#0066cc" />
            <Text style={styles.detailText}>{formatDateTime(startAt)}</Text>
          </View>

          <View style={styles.detailRow}>
            <MaterialCommunityIcons name="clock-outline" size={20} color="#0066cc" />
            <Text style={styles.detailText}>{duration} minutes</Text>
          </View>

          <View style={styles.detailRow}>
            <MaterialCommunityIcons name="earth" size={20} color="#0066cc" />
            <Text style={styles.detailText}>Timezone: {mentor?.timezone}</Text>
          </View>
        </View>

        {/* Session Topic */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Session Topic</Text>
          <View style={styles.topicContainer}>
            {topicOptions.map((option) => (
              <TouchableOpacity
                key={option}
                style={[styles.topicChip, topic === option && styles.topicChipActive]}
                onPress={() => setTopic(option)}
              >
                <Text
                  style={[styles.topicChipText, topic === option && styles.topicChipTextActive]}
                >
                  {option}
                </Text>
                {topic === option && (
                  <MaterialCommunityIcons name="check" size={16} color="#fff" />
                )}
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Notes */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notes (Optional)</Text>
          <Text style={styles.sectionSubtitle}>
            Let your mentor know what you'd like to discuss
          </Text>
          <TextInput
            style={styles.notesInput}
            placeholder="E.g., I need help with my Stanford essay structure..."
            value={notes}
            onChangeText={setNotes}
            multiline
            numberOfLines={4}
            textAlignVertical="top"
          />
        </View>

        {/* Pricing */}
        {mentor && (
          <View style={styles.section}>
            <View style={styles.pricingContainer}>
              <View>
                <Text style={styles.pricingLabel}>Session Rate</Text>
                <Text style={styles.pricingPrice}>{mentor.hourly_rate_credits} credits</Text>
              </View>
              <View style={styles.totalContainer}>
                <Text style={styles.totalLabel}>Total</Text>
                <Text style={styles.totalPrice}>
                  {Math.round(mentor.hourly_rate_credits * (duration / 60))} credits
                </Text>
              </View>
            </View>
          </View>
        )}

        {/* Book Button */}
        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={[styles.bookButton, booking && styles.bookButtonDisabled]}
            onPress={handleBook}
            disabled={booking}
          >
            {booking ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.bookButtonText}>Request Booking</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Info */}
        <View style={styles.infoContainer}>
          <MaterialCommunityIcons name="information" size={16} color="#999" />
          <Text style={styles.infoText}>
            Your mentor will receive this request and can confirm within 24 hours.
            You'll be notified once confirmed.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  backButton: {
    marginRight: 16,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  section: {
    backgroundColor: '#fff',
    marginTop: 12,
    padding: 20,
  },
  mentorInfo: {
    marginBottom: 8,
  },
  mentorName: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  mentorStats: {
    flexDirection: 'row',
  },
  stat: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
  },
  statText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginLeft: 4,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 12,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#999',
    marginBottom: 8,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  detailText: {
    fontSize: 16,
    color: '#333',
    marginLeft: 12,
  },
  topicContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  topicChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    marginRight: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  topicChipActive: {
    backgroundColor: '#0066cc',
    borderColor: '#0066cc',
  },
  topicChipText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
    marginRight: 4,
  },
  topicChipTextActive: {
    color: '#fff',
  },
  notesInput: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#1a1a1a',
    borderWidth: 1,
    borderColor: '#e0e0e0',
    minHeight: 100,
  },
  pricingContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  pricingLabel: {
    fontSize: 14,
    color: '#999',
  },
  pricingPrice: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  totalContainer: {
    alignItems: 'flex-end',
  },
  totalLabel: {
    fontSize: 12,
    color: '#999',
  },
  totalPrice: {
    fontSize: 20,
    fontWeight: '700',
    color: '#0066cc',
  },
  buttonContainer: {
    padding: 20,
    paddingTop: 0,
  },
  bookButton: {
    backgroundColor: '#0066cc',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  bookButtonDisabled: {
    backgroundColor: '#ccc',
  },
  bookButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#fff',
  },
  infoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#fff',
    marginTop: 0,
  },
  infoText: {
    fontSize: 12,
    color: '#999',
    marginLeft: 8,
    flex: 1,
  },
});
