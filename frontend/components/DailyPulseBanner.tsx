import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { BlurView } from 'expo-blur';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { analyticsAPI } from '@/services/api';

interface DailyPulseBannerProps {
  onPress?: (brief: any) => void;
  onSentToChat?: () => void;
}

export default function DailyPulseBanner({ onPress, onSentToChat }: DailyPulseBannerProps) {
  const [loading, setLoading] = useState(true);
  const [briefData, setBriefData] = useState<any>(null);
  const [dismissed, setDismissed] = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    loadDailyPulse();
  }, []);

  const loadDailyPulse = async () => {
    try {
      setLoading(true);

      // Check if user dismissed it today
      const today = new Date().toISOString().split('T')[0];
      const dismissedDate = await AsyncStorage.getItem('daily_pulse_dismissed');
      if (dismissedDate === today) {
        setDismissed(true);
        setLoading(false);
        return;
      }

      // Get today's Daily Pulse
      const response = await analyticsAPI.getDailyPulse();
      console.log('Daily Pulse API Response:', response.data);
      if (response.data) {
        setBriefData(response.data);
      }
    } catch (error: any) {
      console.error('Failed to load daily pulse:', error);
      console.error('Error details:', error.response?.data);

      if (error.response?.status === 404) {
        // No brief for today, generate one
        console.log('No brief found, generating new one...');
        try {
          const genResponse = await analyticsAPI.generateDailyPulse();
          console.log('Generate response:', genResponse.data);
          const response = await analyticsAPI.getDailyPulse();
          console.log('Fetched generated brief:', response.data);
          if (response.data) {
            setBriefData(response.data);
          }
        } catch (genError: any) {
          console.error('Failed to generate daily pulse:', genError);
          console.error('Generation error details:', genError.response?.data);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = async () => {
    const today = new Date().toISOString().split('T')[0];
    await AsyncStorage.setItem('daily_pulse_dismissed', today);
    setDismissed(true);

    // Mark as shown in app
    try {
      await analyticsAPI.markDailyPulseShown('app');
    } catch (error) {
      console.error('Failed to mark as shown:', error);
    }
  };

  const handlePress = async () => {
    if (!briefData) return;

    if (onPress) {
      onPress(briefData);
      return;
    }

    // Send to chat
    setSending(true);
    try {
      await analyticsAPI.sendDailyPulseToChat();
      Alert.alert('Success', 'Daily Pulse sent to chat!');
      if (onSentToChat) {
        onSentToChat();
      }
    } catch (error: any) {
      console.error('Failed to send to chat:', error);
      Alert.alert('Error', 'Failed to send Daily Pulse to chat');
    } finally {
      setSending(false);
    }
  };

  // Don't show if dismissed or no data
  if (dismissed || (!loading && !briefData)) {
    return null;
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <LinearGradient
          colors={['rgba(59, 130, 246, 0.15)', 'rgba(59, 130, 246, 0.05)']}
          style={styles.gradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <BlurView intensity={20} tint="dark" style={styles.blur}>
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color="#3B82F6" />
              <Text style={styles.loadingText}>Loading your daily pulse...</Text>
            </View>
          </BlurView>
        </LinearGradient>
      </View>
    );
  }

  const {
    greeting_message = 'Good morning!',
    top_priorities = [],
    workload_percentage = 0,
    workload_status = 'optimal',
    warnings = []
  } = briefData || {};

  // Get workload emoji
  const getWorkloadEmoji = () => {
    switch (workload_status) {
      case 'light': return '😌';
      case 'optimal': return '⚡';
      case 'heavy': return '💪';
      case 'overloaded': return '⚠️';
      default: return '📊';
    }
  };

  // Get workload color
  const getWorkloadColor = () => {
    switch (workload_status) {
      case 'light': return '#34C759';
      case 'optimal': return '#5B6AFF';
      case 'heavy': return '#FF9500';
      case 'overloaded': return '#EF4444';
      default: return '#8E8E8E';
    }
  };

  // Extract greeting text (remove emojis)
  const getGreetingText = () => {
    if (!greeting_message) return 'Good morning!';
    return greeting_message.split(/[🌙🌅☀️⏰]/)[0].trim() || greeting_message;
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity
        onPress={handlePress}
        activeOpacity={0.9}
        disabled={sending}
      >
        <LinearGradient
          colors={['rgba(59, 130, 246, 0.2)', 'rgba(59, 130, 246, 0.1)', 'rgba(59, 130, 246, 0.05)']}
          style={styles.gradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <BlurView intensity={30} tint="dark" style={styles.blur}>
            {/* Dismiss Button */}
            <TouchableOpacity
              style={styles.dismissButton}
              onPress={handleDismiss}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            >
              <MaterialCommunityIcons name="close" size={18} color="#8E8E8E" />
            </TouchableOpacity>

            {/* Header with Greeting */}
            <View style={styles.header}>
              <MaterialCommunityIcons name="white-balance-sunny" size={24} color="#3B82F6" />
              <Text style={styles.greeting} numberOfLines={1}>
                {getGreetingText()}
              </Text>
            </View>

            {/* Stats Row */}
            <View style={styles.statsRow}>
              {/* Priorities */}
              <View style={styles.statItem}>
                <View style={styles.statIconContainer}>
                  <MaterialCommunityIcons name="target" size={20} color="#3B82F6" />
                </View>
                <Text style={styles.statValue}>{Array.isArray(top_priorities) ? top_priorities.length : 0}</Text>
                <Text style={styles.statLabel}>Priorities</Text>
              </View>

              {/* Divider */}
              <View style={styles.divider} />

              {/* Workload */}
              <View style={styles.statItem}>
                <View style={styles.statIconContainer}>
                  <Text style={styles.workloadEmoji}>{getWorkloadEmoji()}</Text>
                </View>
                <Text style={[styles.statValue, { color: getWorkloadColor() }]}>
                  {workload_percentage || 0}%
                </Text>
                <Text style={styles.statLabel}>Workload</Text>
              </View>

              {/* Divider */}
              <View style={styles.divider} />

              {/* Warnings */}
              <View style={styles.statItem}>
                <View style={styles.statIconContainer}>
                  <MaterialCommunityIcons
                    name={Array.isArray(warnings) && warnings.length > 0 ? "alert-circle" : "check-circle"}
                    size={20}
                    color={Array.isArray(warnings) && warnings.length > 0 ? "#FF9500" : "#34C759"}
                  />
                </View>
                <Text style={styles.statValue}>{Array.isArray(warnings) ? warnings.length : 0}</Text>
                <Text style={styles.statLabel}>Reminders</Text>
              </View>
            </View>

            {/* Footer */}
            <View style={styles.footer}>
              <View style={styles.tapHint}>
                <MaterialCommunityIcons name="chat-outline" size={14} color="#3B82F6" />
                <Text style={styles.tapHintText}>
                  {sending ? 'Sending to chat...' : 'Tap to view in chat'}
                </Text>
              </View>
            </View>
          </BlurView>
        </LinearGradient>
      </TouchableOpacity>

      {/* Glow Effect */}
      <View style={styles.glowTop} />
      <View style={styles.glowBottom} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    margin: 16,
    marginTop: 8,
    marginBottom: 8,
    borderRadius: 20,
    overflow: 'hidden',
    position: 'relative',
  },
  gradient: {
    borderRadius: 20,
    padding: 1,
  },
  blur: {
    borderRadius: 20,
    padding: 16,
    paddingTop: 20,
    borderWidth: 1,
    borderColor: 'rgba(59, 130, 246, 0.2)',
    backgroundColor: 'rgba(26, 26, 26, 0.6)',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    paddingVertical: 16,
  },
  loadingText: {
    fontSize: 14,
    color: '#8E8E8E',
  },
  dismissButton: {
    position: 'absolute',
    top: 12,
    right: 12,
    zIndex: 10,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    width: 24,
    height: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  greeting: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ECECEC',
    flex: 1,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    marginBottom: 12,
  },
  statItem: {
    alignItems: 'center',
    flex: 1,
  },
  statIconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 6,
  },
  workloadEmoji: {
    fontSize: 20,
  },
  statValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ECECEC',
    marginBottom: 2,
  },
  statLabel: {
    fontSize: 10,
    color: '#8E8E8E',
    fontWeight: '500',
  },
  divider: {
    width: 1,
    height: 36,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
  },
  tapHint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(59, 130, 246, 0.2)',
  },
  tapHintText: {
    fontSize: 11,
    color: '#3B82F6',
    fontWeight: '600',
  },
  glowTop: {
    position: 'absolute',
    top: -50,
    left: '20%',
    right: '20%',
    height: 100,
    backgroundColor: 'rgba(59, 130, 246, 0.3)',
    borderRadius: 100,
    opacity: 0.5,
  },
  glowBottom: {
    position: 'absolute',
    bottom: -50,
    left: '30%',
    right: '30%',
    height: 100,
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    borderRadius: 100,
    opacity: 0.3,
  },
});
