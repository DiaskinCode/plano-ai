/**
 * Walkthrough Ready Screen
 *
 * Final screen - users are ready to start using the app
 */

import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  StatusBar,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function ReadyScreen() {
  const router = useRouter();

  useEffect(() => {
    // Mark walkthrough as completed
    AsyncStorage.setItem('walkthrough_completed', 'true');
  }, []);

  const handleGoToDashboard = () => {
    router.replace('/(main)/home');
  };

  const handleCompleteProfile = () => {
    router.replace('/university-profile/wizard');
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Background Gradient */}
      <LinearGradient
        colors={['#0F0F23', '#1A1A3E', '#5B6AFF']}
        style={styles.background}
      />

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Success Icon */}
        <View style={styles.iconContainer}>
          <LinearGradient
            colors={['#4ADE80', '#22C55E']}
            style={styles.successIcon}
          >
            <Ionicons name="checkmark" size={80} color="#fff" />
          </LinearGradient>
        </View>

        {/* Title */}
        <Text style={styles.title}>You're All Set!</Text>
        <Text style={styles.subtitle}>
          Start exploring your personalized college application journey
        </Text>

        {/* Features Summary */}
        <View style={styles.featuresSummary}>
          <View style={styles.featureRow}>
            <View style={styles.featureIcon}>
              <Ionicons name="school" size={28} color="#5B6AFF" />
            </View>
            <View style={styles.featureText}>
              <Text style={styles.featureTitle}>University Recommendations</Text>
              <Text style={styles.featureDesc}>AI-powered matches based on your profile</Text>
            </View>
          </View>

          <View style={styles.featureRow}>
            <View style={styles.featureIcon}>
              <Ionicons name="calendar" size={28} color="#5B6AFF" />
            </View>
            <View style={styles.featureText}>
              <Text style={styles.featureTitle}>Smart Planning</Text>
              <Text style={styles.featureDesc}>Organized tasks & deadlines</Text>
            </View>
          </View>

          <View style={styles.featureRow}>
            <View style={styles.featureIcon}>
              <Ionicons name="people" size={28} color="#5B6AFF" />
            </View>
            <View style={styles.featureText}>
              <Text style={styles.featureTitle}>Expert Mentors</Text>
              <Text style={styles.featureDesc}>Guidance from those who've been there</Text>
            </View>
          </View>
        </View>

        {/* CTA Buttons */}
        <View style={styles.buttons}>
          <TouchableOpacity
            style={[styles.button, styles.primaryButton]}
            onPress={handleGoToDashboard}
          >
            <Ionicons name="home" size={24} color="#fff" />
            <Text style={styles.buttonText}>Go to Dashboard</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.secondaryButton]}
            onPress={handleCompleteProfile}
          >
            <Ionicons name="create" size={24} color="#5B6AFF" />
            <Text style={[styles.buttonText, styles.secondaryButtonText]}>
              Complete Profile Now
            </Text>
          </TouchableOpacity>
        </View>

        {/* Tip */}
        <View style={styles.tipBox}>
          <Ionicons name="bulb" size={20} color="#FBBF24" />
          <Text style={styles.tipText}>
            You can always complete your profile later from the home screen
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F0F23',
  },
  background: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 24,
    justifyContent: 'center',
  },
  iconContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  successIcon: {
    width: 120,
    height: 120,
    borderRadius: 60,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#4ADE80',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 18,
    color: '#ccc',
    textAlign: 'center',
    marginBottom: 48,
    paddingHorizontal: 20,
  },
  featuresSummary: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 24,
    marginBottom: 40,
    gap: 24,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  featureIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(91, 106, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  featureText: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 4,
  },
  featureDesc: {
    fontSize: 14,
    color: '#999',
    lineHeight: 20,
  },
  buttons: {
    gap: 16,
    marginBottom: 24,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    borderRadius: 16,
    gap: 12,
  },
  primaryButton: {
    backgroundColor: '#5B6AFF',
    shadowColor: '#5B6AFF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  secondaryButton: {
    backgroundColor: 'rgba(91, 106, 255, 0.15)',
    borderWidth: 2,
    borderColor: '#5B6AFF',
  },
  buttonText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
  },
  secondaryButtonText: {
    color: '#5B6AFF',
  },
  tipBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: 'rgba(251, 191, 36, 0.1)',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(251, 191, 36, 0.3)',
  },
  tipText: {
    flex: 1,
    fontSize: 14,
    color: '#FBBF24',
    lineHeight: 20,
  },
});
