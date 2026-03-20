import { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import AsyncStorage from '@react-native-async-storage/async-storage';

const COLORS = {
  bg: '#000000',
  surface: '#1A1A1A',
  border: '#2A2A2A',
  text: '#ECECEC',
  textSecondary: '#8E8E8E',
  primary: '#5B6AFF',
};

export default function LanguageScreen() {
  const router = useRouter();
  const { i18n } = useTranslation();
  const [selectedLanguage, setSelectedLanguage] = useState(i18n.language);

  const handleContinue = async () => {
    // Save language preference
    await i18n.changeLanguage(selectedLanguage);
    await AsyncStorage.setItem('language', selectedLanguage);

    // Navigate to first slide
    router.push('/(intro)/slide1');
  };

  const languages = [
    {
      code: 'en',
      name: 'English',
      flag: '🇬🇧',
      nativeName: 'English',
    },
    {
      code: 'ru',
      name: 'Russian',
      flag: '🇷🇺',
      nativeName: 'Русский',
    },
  ];

  return (
    <View style={styles.container}>
      {/* Background Gradient */}
      <LinearGradient
        colors={['rgba(16, 163, 127, 0.2)', 'rgba(16, 163, 127, 0.05)', 'transparent']}
        style={styles.backgroundGradient}
      />

      <View style={styles.content}>
        {/* Logo/Icon */}
        <View style={styles.iconContainer}>
          <LinearGradient
            colors={['#5B6AFF', '#0D8A6B']}
            style={styles.iconGradient}
          >
            <MaterialCommunityIcons name="translate" size={48} color="#fff" />
          </LinearGradient>
        </View>

        {/* Title */}
        <Text style={styles.title}>
          {selectedLanguage === 'ru' ? 'Выберите язык' : 'Choose Your Language'}
        </Text>
        <Text style={styles.subtitle}>
          {selectedLanguage === 'ru' ? 'Выберите предпочитаемый язык' : 'Select your preferred language'}
        </Text>

        {/* Language Options */}
        <View style={styles.languageList}>
          {languages.map((lang) => (
            <TouchableOpacity
              key={lang.code}
              style={[
                styles.languageOption,
                selectedLanguage === lang.code && styles.languageOptionActive,
              ]}
              onPress={() => setSelectedLanguage(lang.code)}
            >
              <View style={styles.languageContent}>
                <Text style={styles.flagIcon}>{lang.flag}</Text>
                <View style={styles.languageText}>
                  <Text style={styles.languageName}>{lang.nativeName}</Text>
                  <Text style={styles.languageNameEn}>{lang.name}</Text>
                </View>
              </View>
              {selectedLanguage === lang.code && (
                <MaterialCommunityIcons name="check-circle" size={24} color={COLORS.primary} />
              )}
            </TouchableOpacity>
          ))}
        </View>

        {/* Continue Button */}
        <TouchableOpacity style={styles.continueButton} onPress={handleContinue}>
          <LinearGradient
            colors={['#5B6AFF', '#0D8A6B']}
            style={styles.continueGradient}
          >
            <Text style={styles.continueText}>
              {selectedLanguage === 'ru' ? 'Продолжить' : 'Continue'}
            </Text>
            <MaterialCommunityIcons name="arrow-right" size={24} color="#fff" />
          </LinearGradient>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  backgroundGradient: {
    position: 'absolute',
    width: 400,
    height: 400,
    borderRadius: 200,
    top: -100,
    left: '50%',
    marginLeft: -200,
  },
  content: {
    flex: 1,
    paddingTop: 100,
    paddingHorizontal: 24,
    paddingBottom: 40,
  },
  iconContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  iconGradient: {
    width: 100,
    height: 100,
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#5B6AFF',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 48,
    lineHeight: 24,
  },
  languageList: {
    gap: 16,
    marginBottom: 32,
  },
  languageOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 20,
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: COLORS.border,
  },
  languageOptionActive: {
    borderColor: COLORS.primary,
    backgroundColor: 'rgba(16, 163, 127, 0.1)',
  },
  languageContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  flagIcon: {
    fontSize: 36,
  },
  languageText: {
    gap: 4,
  },
  languageName: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
  },
  languageNameEn: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  continueButton: {
    marginTop: 'auto',
    borderRadius: 16,
    overflow: 'hidden',
  },
  continueGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 18,
    gap: 12,
  },
  continueText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
  },
});
