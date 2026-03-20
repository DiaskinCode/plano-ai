/**
 * My Bookings Screen (V1)
 *
 * View and manage mentor session bookings
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  SafeAreaView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { getMyBookings, cancelBooking, confirmBooking } from '@/services/mentorship';
import { MentorBooking } from '@/types/mentor';

type TabType = 'upcoming' | 'completed' | 'cancelled';

export default function MyBookingsScreen() {
  const router = useRouter();
  const [bookings, setBookings] = useState<MentorBooking[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('upcoming');
  const [isMentor, setIsMentor] = useState(false);

  useEffect(() => {
    loadBookings();
    checkIfMentor();
  }, []);

  const checkIfMentor = async () => {
    // TODO: Check if current user is a mentor
    setIsMentor(false);
  };

  const loadBookings = async () => {
    try {
      setLoading(true);
      const data = await getMyBookings();
      setBookings(data);
    } catch (error) {
      console.error('Error loading bookings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (bookingId: number) => {
    // TODO: Show confirmation dialog
    try {
      await cancelBooking(bookingId);
      loadBookings();
    } catch (error) {
      console.error('Error cancelling booking:', error);
    }
  };

  const handleConfirm = async (bookingId: number) => {
    try {
      await confirmBooking(bookingId);
      loadBookings();
    } catch (error) {
      console.error('Error confirming booking:', error);
    }
  };

  const getFilteredBookings = () => {
    return bookings.filter((booking) => {
      if (activeTab === 'upcoming') return booking.status === 'confirmed' || booking.status === 'requested';
      if (activeTab === 'completed') return booking.status === 'completed';
      if (activeTab === 'cancelled') return booking.status === 'cancelled';
      return false;
    });
  };

  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed': return '#4CAF50';
      case 'requested': return '#FFA726';
      case 'completed': return '#2196F3';
      case 'cancelled': return '#F44336';
      default: return '#999';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'confirmed': return 'Confirmed';
      case 'requested': return 'Pending';
      case 'completed': return 'Completed';
      case 'cancelled': return 'Cancelled';
      default: return status;
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <MaterialCommunityIcons name="arrow-left" size={24} color="#1a1a1a" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>My Sessions</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* Tabs */}
      <View style={styles.tabsContainer}>
        {(['upcoming', 'completed', 'cancelled'] as TabType[]).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.tabActive]}
            onPress={() => setActiveTab(tab)}
          >
            <Text
              style={[styles.tabText, activeTab === tab && styles.tabTextActive]}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#0066cc" />
        </View>
      ) : (
        <ScrollView style={styles.content}>
          {getFilteredBookings().length === 0 ? (
            <View style={styles.emptyContainer}>
              <MaterialCommunityIcons name="calendar-blank" size={64} color="#ccc" />
              <Text style={styles.emptyTitle}>No {activeTab} sessions</Text>
            </View>
          ) : (
            getFilteredBookings().map((booking) => (
              <View key={booking.id} style={styles.bookingCard}>
                {/* Header */}
                <View style={styles.bookingHeader}>
                  <View style={styles.bookingTitle}>
                    <Text style={styles.mentorTitle}>{booking.mentor_title}</Text>
                    <Text style={styles.topic}>
                      {booking.topic || 'Session'}
                    </Text>
                  </View>
                  <View
                    style={[
                      styles.statusBadge,
                      { backgroundColor: getStatusColor(booking.status) },
                    ]}
                  >
                    <Text style={styles.statusText}>{getStatusText(booking.status)}</Text>
                  </View>
                </View>

                {/* Time */}
                <View style={styles.bookingSection}>
                  <MaterialCommunityIcons name="calendar" size={18} color="#0066cc" />
                  <Text style={styles.bookingTime}>{formatDateTime(booking.start_at_utc)}</Text>
                </View>

                {/* Duration */}
                <View style={styles.bookingSection}>
                  <MaterialCommunityIcons name="clock-outline" size={18} color="#0066cc" />
                  <Text style={styles.bookingTime}>{booking.duration_minutes} minutes</Text>
                </View>

                {/* Meeting URL */}
                {booking.meeting_url && booking.status === 'confirmed' && (
                  <View style={styles.bookingSection}>
                    <MaterialCommunityIcons name="video" size={18} color="#0066cc" />
                    <Text style={styles.meetingLink} numberOfLines={1}>
                      {booking.meeting_url}
                    </Text>
                  </View>
                )}

                {/* Notes */}
                {booking.student_notes && (
                  <View style={styles.notesSection}>
                    <Text style={styles.notesLabel}>Notes:</Text>
                    <Text style={styles.notesText}>{booking.student_notes}</Text>
                  </View>
                )}

                {/* Actions */}
                {activeTab === 'upcoming' && (
                  <View style={styles.actionsContainer}>
                    {booking.status === 'requested' && isMentor && (
                      <TouchableOpacity
                        style={[styles.actionButton, styles.confirmButton]}
                        onPress={() => handleConfirm(booking.id)}
                      >
                        <Text style={styles.actionButtonText}>Confirm</Text>
                      </TouchableOpacity>
                    )}
                    <TouchableOpacity
                      style={[styles.actionButton, styles.cancelButton]}
                      onPress={() => handleCancel(booking.id)}
                    >
                      <Text style={styles.actionButtonText}>Cancel</Text>
                    </TouchableOpacity>
                  </View>
                )}

                {/* Post-session info */}
                {booking.status === 'completed' && booking.mentor_summary && (
                  <View style={styles.summarySection}>
                    <Text style={styles.summaryLabel}>Session Summary:</Text>
                    <Text style={styles.summaryText}>{booking.mentor_summary}</Text>
                  </View>
                )}
              </View>
            ))
          )}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  tabsContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  tab: {
    marginRight: 24,
    paddingVertical: 8,
  },
  tabActive: {
    borderBottomWidth: 2,
    borderBottomColor: '#0066cc',
  },
  tabText: {
    fontSize: 14,
    color: '#999',
    fontWeight: '500',
  },
  tabTextActive: {
    color: '#0066cc',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 80,
  },
  emptyTitle: {
    fontSize: 16,
    color: '#999',
    marginTop: 16,
  },
  bookingCard: {
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
  bookingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  bookingTitle: {
    flex: 1,
  },
  mentorTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  topic: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  bookingSection: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  bookingTime: {
    fontSize: 14,
    color: '#333',
    marginLeft: 8,
  },
  meetingLink: {
    fontSize: 12,
    color: '#0066cc',
    marginLeft: 8,
    flex: 1,
  },
  notesSection: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
    marginBottom: 12,
  },
  notesLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    marginBottom: 4,
  },
  notesText: {
    fontSize: 14,
    color: '#333',
  },
  summarySection: {
    backgroundColor: '#f0f7ff',
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
  },
  summaryLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#0066cc',
    marginBottom: 4,
  },
  summaryText: {
    fontSize: 14,
    color: '#333',
  },
  actionsContainer: {
    flexDirection: 'row',
    marginTop: 12,
    gap: 8,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  confirmButton: {
    backgroundColor: '#4CAF50',
  },
  cancelButton: {
    backgroundColor: '#f0f0f0',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
});
