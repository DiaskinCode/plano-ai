import React, { useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useTranslation } from 'react-i18next';
import { useOnboarding } from '@/components/onboarding/OnboardingContext';

export default function WelcomeScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const { updateOnboardingData } = useOnboarding();

  useEffect(() => {
    // Mark welcome step as viewed
    updateOnboardingData({ welcome_viewed: true });
  }, []);

  const handleGetStarted = () => {
    // New users go to registration
    router.push('/(auth)/register');
  };

  const handleAlreadyHaveAccount = () => {
    // Existing users go to login
    router.push('/(auth)/login');
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Logo and Brand */}
        <View style={styles.header}>
          <View style={styles.logo}>
            <Text style={styles.logoText}>P</Text>
          </View>
          <Text style={styles.appName}>PathAI</Text>
          <Text style={styles.tagline}>{t('onboarding.welcome.tagline', 'Your AI-Powered College Application Coach')}</Text>
        </View>

        {/* Main Content */}
        <View style={styles.mainContent}>
          <Text style={styles.title}>{t('onboarding.welcome.title', 'Welcome to PathAI')}</Text>
          <Text style={styles.subtitle}>
            {t('onboarding.welcome.subtitle', 'Get personalized guidance for your college application journey in just 5 minutes')}
          </Text>

          {/* Features */}
          <View style={styles.features}>
            <View style={styles.feature}>
              <View style={styles.featureIcon}>
                <Text style={styles.featureEmoji}>🎯</Text>
              </View>
              <View style={styles.featureText}>
                <Text style={styles.featureTitle}>{t('onboarding.welcome.features.smart.title', 'Smart Planning')}</Text>
                <Text style={styles.featureDesc}>
                  {t('onboarding.welcome.features.smart.desc', 'AI-generated personalized plans')}
                </Text>
              </View>
            </View>

            <View style={styles.feature}>
              <View style={styles.featureIcon}>
                <Text style={styles.featureEmoji}>📚</Text>
              </View>
              <View style={styles.featureText}>
                <Text style={styles.featureTitle}>{t('onboarding.welcome.features.tasks.title', '200+ Tasks')}</Text>
                <Text style={styles.featureDesc}>
                  {t('onboarding.welcome.features.tasks.desc', 'Step-by-step application guidance')}
                </Text>
              </View>
            </View>

            <View style={styles.feature}>
              <View style={styles.featureIcon}>
                <Text style={styles.featureEmoji}>👥</Text>
              </View>
              <View style={styles.featureText}>
                <Text style={styles.featureTitle}>{t('onboarding.welcome.features.community.title', 'Community')}</Text>
                <Text style={styles.featureDesc}>
                  {t('onboarding.welcome.features.community.desc', 'Connect with applicants worldwide')}
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* Buttons */}
        <View style={styles.footer}>
          <TouchableOpacity style={styles.primaryButton} onPress={handleGetStarted}>
            <Text style={styles.primaryButtonText}>{t('onboarding.welcome.getStarted', 'Get Started')}</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.secondaryButton} onPress={handleAlreadyHaveAccount}>
            <Text style={styles.secondaryButtonText}>
              {t('onboarding.welcome.alreadyHaveAccount', 'Already have an account? Sign In')}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 40,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logo: {
    width: 80,
    height: 80,
    borderRadius: 20,
    backgroundColor: '#5B6AFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  logoText: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  appName: {
    fontSize: 28,
    fontWeight: '700',
    color: '#ECECEC',
    marginBottom: 8,
  },
  tagline: {
    fontSize: 14,
    color: '#8E8E8E',
    textAlign: 'center',
  },
  mainContent: {
    flex: 1,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: '#ECECEC',
    textAlign: 'center',
    marginBottom: 16,
  },
  subtitle: {
    fontSize: 16,
    color: '#8E8E8E',
    textAlign: 'center',
    marginBottom: 40,
    lineHeight: 24,
  },
  features: {
    gap: 24,
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 16,
  },
  featureIcon: {
    width: 56,
    height: 56,
    borderRadius: 14,
    backgroundColor: '#1A1A1A',
    alignItems: 'center',
    justifyContent: 'center',
  },
  featureEmoji: {
    fontSize: 28,
  },
  featureText: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ECECEC',
    marginBottom: 4,
  },
  featureDesc: {
    fontSize: 14,
    color: '#8E8E8E',
    lineHeight: 20,
  },
  footer: {
    gap: 12,
    paddingBottom: 24,
  },
  primaryButton: {
    backgroundColor: '#5B6AFF',
    borderRadius: 16,
    paddingVertical: 18,
    alignItems: 'center',
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  secondaryButton: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  secondaryButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#5B6AFF',
  },
});
