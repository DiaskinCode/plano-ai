import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';

const COLORS = {
  bg: '#000000',
  text: '#ECECEC',
  textSecondary: '#8E8E8E',
  primary: '#5B6AFF',
};

export default function Slide1Screen() {
  const router = useRouter();
  const { t } = useTranslation();

  const handleNext = () => {
    router.push('/(intro)/slide2');
  };

  const handleSkip = () => {
    router.replace('/(auth)/login');
  };

  return (
    <View style={styles.container}>
      {/* Background Gradient */}
      <LinearGradient
        colors={['rgba(102, 126, 234, 0.3)', 'rgba(118, 75, 162, 0.2)', 'transparent']}
        style={styles.backgroundGradient}
      />

      {/* Skip Button */}
      <TouchableOpacity style={styles.skipButton} onPress={handleSkip}>
        <Text style={styles.skipText}>{t('intro.skip')}</Text>
      </TouchableOpacity>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.content}>
        {/* Icon */}
        <View style={styles.iconContainer}>
          <LinearGradient
            colors={['#667eea', '#764ba2']}
            style={styles.iconGradient}
          >
            <MaterialCommunityIcons name="robot" size={64} color="#fff" />
          </LinearGradient>
        </View>

        {/* Title & Description */}
        <Text style={styles.title}>{t('intro.slide1.title')}</Text>
        <Text style={styles.description}>{t('intro.slide1.description')}</Text>

        {/* Illustration/Feature Highlights */}
        <View style={styles.features}>
          <View style={styles.featureItem}>
            <MaterialCommunityIcons name="chat-outline" size={24} color={COLORS.primary} />
            <Text style={styles.featureText}>{t('intro.slide1.feature1')}</Text>
          </View>
          <View style={styles.featureItem}>
            <MaterialCommunityIcons name="target" size={24} color={COLORS.primary} />
            <Text style={styles.featureText}>{t('intro.slide1.feature2')}</Text>
          </View>
          <View style={styles.featureItem}>
            <MaterialCommunityIcons name="calendar-check" size={24} color={COLORS.primary} />
            <Text style={styles.featureText}>{t('intro.slide1.feature3')}</Text>
          </View>
        </View>

        {/* Progress Dots */}
        <View style={styles.progressDots}>
          <View style={[styles.dot, styles.dotActive]} />
          <View style={styles.dot} />
          <View style={styles.dot} />
          <View style={styles.dot} />
        </View>

        {/* Next Button */}
        <TouchableOpacity style={styles.nextButton} onPress={handleNext}>
          <LinearGradient
            colors={['#5B6AFF', '#0D8A6B']}
            style={styles.nextGradient}
          >
            <Text style={styles.nextText}>{t('intro.next')}</Text>
            <MaterialCommunityIcons name="arrow-right" size={24} color="#fff" />
          </LinearGradient>
        </TouchableOpacity>
        </View>
      </ScrollView>
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
    width: 500,
    height: 500,
    borderRadius: 250,
    top: -150,
    alignSelf: 'center',
  },
  skipButton: {
    position: 'absolute',
    top: 60,
    right: 24,
    zIndex: 10,
  },
  skipText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  scrollContent: {
    flexGrow: 1,
  },
  content: {
    flex: 1,
    paddingTop: 120,
    paddingHorizontal: 24,
    paddingBottom: 40,
    alignItems: 'center',
  },
  iconContainer: {
    marginBottom: 48,
  },
  iconGradient: {
    width: 140,
    height: 140,
    borderRadius: 70,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#667eea',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.4,
    shadowRadius: 20,
    elevation: 12,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: 16,
  },
  description: {
    fontSize: 16,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 48,
    paddingHorizontal: 16,
  },
  features: {
    width: '100%',
    gap: 16,
    marginBottom: 48,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(16, 163, 127, 0.2)',
  },
  featureText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  progressDots: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 32,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
  dotActive: {
    backgroundColor: COLORS.primary,
    width: 24,
  },
  nextButton: {
    width: '100%',
    borderRadius: 16,
    overflow: 'hidden',
  },
  nextGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 18,
    gap: 12,
  },
  nextText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
  },
});
