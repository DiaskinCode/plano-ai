import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import i18n from '@/services/i18n';
import { useOnboarding } from '@/components/onboarding/OnboardingContext';

const languages = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
];

export default function LanguageScreen() {
  const router = useRouter();
  const { updateOnboardingData } = useOnboarding();

  const handleLanguageSelect = async (langCode: string) => {
    try {
      // Save language preference
      await AsyncStorage.setItem('userLanguage', langCode);
      await AsyncStorage.setItem('selectedLanguage', langCode);

      // Update i18n
      i18n.changeLanguage(langCode);

      // Update onboarding context
      updateOnboardingData({ selected_language: langCode });

      // Navigate to welcome screen
      router.push('/(onboarding)/welcome');
    } catch (error) {
      console.error('Error saving language:', error);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Logo */}
        <View style={styles.logoContainer}>
          <View style={styles.logo}>
            <Text style={styles.logoText}>P</Text>
          </View>
          <Text style={styles.appName}>PathAI</Text>
        </View>

        {/* Title */}
        <Text style={styles.title}>Select Your Language</Text>
        <Text style={styles.subtitle}>Choose your preferred language to continue</Text>

        {/* Language Options */}
        <View style={styles.languageList}>
          {languages.map((language) => (
            <TouchableOpacity
              key={language.code}
              style={styles.languageCard}
              onPress={() => handleLanguageSelect(language.code)}
              activeOpacity={0.7}
            >
              <Text style={styles.flag}>{language.flag}</Text>
              <Text style={styles.languageName}>{language.name}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Continue Button (Hidden - auto-advance on selection) */}
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
    paddingTop: 60,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 60,
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
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: '#ECECEC',
    textAlign: 'center',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    color: '#8E8E8E',
    textAlign: 'center',
    marginBottom: 48,
  },
  languageList: {
    gap: 16,
  },
  languageCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1A1A1A',
    borderRadius: 16,
    padding: 20,
    borderWidth: 2,
    borderColor: '#2A2A2A',
  },
  flag: {
    fontSize: 40,
    marginRight: 20,
  },
  languageName: {
    fontSize: 20,
    fontWeight: '600',
    color: '#ECECEC',
    flex: 1,
  },
});
