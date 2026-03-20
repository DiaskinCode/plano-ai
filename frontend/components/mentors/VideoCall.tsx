/**
 * Video Call Component (V1)
 *
 * Simple video call integration using meeting links
 * V1: Opens meeting URL (Google Meet, Zoom, etc.) in browser/app
 * V2: Integrate Twilio/Agora for in-app video
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  SafeAreaView,
  Linking,
  Alert,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { WebView } from 'react-native-webview';

interface VideoCallProps {
  visible: boolean;
  meetingUrl?: string;
  meetingTitle?: string;
  onClose: () => void;
}

export function VideoCallModal({ visible, meetingUrl, meetingTitle, onClose }: VideoCallProps) {
  const handleJoinCall = async () => {
    if (!meetingUrl) {
      Alert.alert('Error', 'No meeting link available');
      return;
    }

    try {
      const supported = await Linking.canOpenURL(meetingUrl);
      if (supported) {
        await Linking.openURL(meetingUrl);
      } else {
        Alert.alert('Error', 'Cannot open meeting link');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to open meeting link');
    }
  };

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="fullScreen">
      <SafeAreaView style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <MaterialCommunityIcons name="close" size={24} color="#1a1a1a" />
          </TouchableOpacity>
          <View style={styles.titleContainer}>
            <Text style={styles.title}>{meetingTitle || 'Video Call'}</Text>
            <Text style={styles.subtitle}>Session in progress</Text>
          </View>
          <View style={{ width: 24 }} />
        </View>

        {/* Video Container */}
        <View style={styles.videoContainer}>
          {meetingUrl ? (
            <WebView
              source={{ uri: meetingUrl }}
              style={styles.webview}
              javaScriptEnabled={true}
              domStorageEnabled={true}
              startInLoadingState={true}
              scalesPageToFit={true}
            />
          ) : (
            <View style={styles.placeholderContainer}>
              <MaterialCommunityIcons name="video-off" size={64} color="#ccc" />
              <Text style={styles.placeholderTitle}>Waiting for host...</Text>
              <Text style={styles.placeholderText}>
                The meeting link will appear when your mentor joins
              </Text>
            </View>
          )}
        </View>

        {/* Controls */}
        <View style={styles.controls}>
          {meetingUrl && (
            <TouchableOpacity style={styles.joinButton} onPress={handleJoinCall}>
              <MaterialCommunityIcons name="open-in-new" size={20} color="#fff" />
              <Text style={styles.joinButtonText}>Open in Browser</Text>
            </TouchableOpacity>
          )}

          <TouchableOpacity
            style={[styles.controlButton, styles.muteButton]}
            onPress={() => {
              // TODO: Implement mute
            }}
          >
            <MaterialCommunityIcons name="microphone" size={24} color="#fff" />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.controlButton, styles.videoButton]}
            onPress={() => {
              // TODO: Implement video toggle
            }}
          >
            <MaterialCommunityIcons name="video" size={24} color="#fff" />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.controlButton, styles.endButton]}
            onPress={onClose}
          >
            <MaterialCommunityIcons name="phone-hangup" size={24} color="#fff" />
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    </Modal>
  );
}

/**
 * Video Call Button Component
 *
 * Shows in booking cards to join active sessions
 */
interface VideoCallButtonProps {
  meetingUrl?: string;
  status?: string;
  onPress?: () => void;
}

export function VideoCallButton({ meetingUrl, status, onPress }: VideoCallButtonProps) {
  const isCallActive = status === 'confirmed' || status === 'in_progress';

  if (!isCallActive || !meetingUrl) {
    return null;
  }

  return (
    <TouchableOpacity
      style={styles.callButton}
      onPress={() => {
        if (onPress) {
          onPress();
        } else {
          Linking.openURL(meetingUrl);
        }
      }}
    >
      <MaterialCommunityIcons name="video" size={18} color="#fff" />
      <Text style={styles.callButtonText}>Join Call</Text>
    </TouchableOpacity>
  );
}

/**
 * Upcoming Session Banner
 *
 * Shows in home screen when session is starting soon
 */
interface SessionBannerProps {
  mentorName: string;
  startTime: string;
  meetingUrl?: string;
  onPress?: () => void;
}

export function UpcomingSessionBanner({ mentorName, startTime, meetingUrl, onPress }: SessionBannerProps) {
  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 0) return 'Now';
    if (diffMins < 60) return `in ${diffMins} min`;

    const hours = Math.floor(diffMins / 60);
    return `in ${hours}h ${diffMins % 60} min`;
  };

  return (
    <TouchableOpacity style={styles.banner} onPress={onPress}>
      <View style={styles.bannerIcon}>
        <MaterialCommunityIcons name="video-outline" size={24} color="#fff" />
      </View>
      <View style={styles.bannerContent}>
        <Text style={styles.bannerTitle}>Session with {mentorName}</Text>
        <Text style={styles.bannerSubtitle}>Starting {formatTime(startTime)}</Text>
      </View>
      <View style={styles.bannerAction}>
        <MaterialCommunityIcons name="chevron-right" size={24} color="#fff" />
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
  },
  closeButton: {
    padding: 4,
  },
  titleContainer: {
    flex: 1,
    alignItems: 'center',
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  subtitle: {
    fontSize: 12,
    color: '#666',
  },
  videoContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  webview: {
    flex: 1,
  },
  placeholderContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
  },
  placeholderTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginTop: 16,
  },
  placeholderText: {
    fontSize: 14,
    color: '#999',
    marginTop: 8,
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    backgroundColor: '#1a1a1a',
    paddingVertical: 20,
    paddingHorizontal: 40,
  },
  joinButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0066cc',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 24,
  },
  joinButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 8,
  },
  controlButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  muteButton: {
    backgroundColor: '#333',
  },
  videoButton: {
    backgroundColor: '#333',
  },
  endButton: {
    backgroundColor: '#F44336',
  },
  callButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#4CAF50',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  callButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
  },
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0066cc',
    marginHorizontal: 20,
    marginTop: 12,
    padding: 12,
    borderRadius: 12,
  },
  bannerIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  bannerContent: {
    flex: 1,
  },
  bannerTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
  bannerSubtitle: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    marginTop: 2,
  },
  bannerAction: {
    padding: 4,
  },
});
