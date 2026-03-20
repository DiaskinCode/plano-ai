/**
 * Walkthrough Features Screen
 *
 * Highlights three main features with swipeable cards
 */

import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Image,
  StatusBar,
  Dimensions,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width } = Dimensions.get('window');

interface Feature {
  id: string;
  icon: string;
  title: string;
  description: string;
  action: string;
  route: string;
}

const FEATURES: Feature[] = [
  {
    id: 'university',
    icon: 'school',
    title: 'Build Your University Profile',
    description: 'Add your GPA, test scores, and intended major to get personalized university recommendations with AI-powered insights.',
    action: 'Build Profile',
    route: '/university-profile/wizard',
  },
  {
    id: 'extracurriculars',
    icon: 'trophy',
    title: 'Showcase Your Achievements',
    description: 'Add your activities, leadership, projects - even startups! This helps us find universities that value your unique talents.',
    action: 'Add Activities',
    route: '/university-profile/activities',
  },
  {
    id: 'mentors',
    icon: 'people',
    title: 'Get Expert Guidance',
    description: 'Connect with mentors who\'ve been through the process. Get personalized advice on your college applications.',
    action: 'Browse Mentors',
    route: '/(main)/mentors',
  },
];

export default function FeaturesScreen() {
  const router = useRouter();
  const [currentIndex, setCurrentIndex] = useState(0);
  const scrollViewRef = useRef<ScrollView>(null);

  const feature = FEATURES[currentIndex];
  const isLastScreen = currentIndex === FEATURES.length - 1;

  const handleNext = () => {
    if (isLastScreen) {
      router.push('/(walkthrough)/ready');
    } else {
      const nextIndex = currentIndex + 1;
      setCurrentIndex(nextIndex);
      // Scroll to next slide
      scrollViewRef.current?.scrollTo({ x: nextIndex * width, animated: true });
    }
  };

  const handleBack = () => {
    const prevIndex = currentIndex - 1;
    setCurrentIndex(prevIndex);
    scrollViewRef.current?.scrollTo({ x: prevIndex * width, animated: true });
  };

  const handleSkip = async () => {
    await AsyncStorage.setItem('walkthrough_completed', 'true');
    router.replace('/(main)/home');
  };

  const handleAction = async () => {
    await AsyncStorage.setItem('walkthrough_completed', 'true');
    router.replace(feature.route);
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Background */}
      <LinearGradient
        colors={['#0F0F23', '#1A1A3E', '#5B6AFF']}
        style={styles.background}
      />

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={handleSkip}>
          <Text style={styles.skipText}>Skip</Text>
        </TouchableOpacity>
        <View style={styles.pagination}>
          {FEATURES.map((_, index) => (
            <View
              key={index}
              style={[
                styles.dot,
                index === currentIndex && styles.dotActive,
              ]}
            />
          ))}
        </View>
        <View style={styles.skipPlaceholder} />
      </View>

      {/* Content */}
      <ScrollView
        ref={scrollViewRef}
        style={styles.content}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={(event) => {
          const offsetX = event.nativeEvent.contentOffset.x;
          const newIndex = Math.round(offsetX / width);
          setCurrentIndex(newIndex);
        }}
      >
        {FEATURES.map((item, index) => (
          <View key={item.id} style={styles.slide}>
            <View style={styles.card}>
              {/* Icon */}
              <LinearGradient
                colors={['#5B6AFF', '#7B8FFF']}
                style={styles.iconContainer}
              >
                <Ionicons name={item.icon as any} size={80} color="#fff" />
              </LinearGradient>

              {/* Text */}
              <Text style={styles.title}>{item.title}</Text>
              <Text style={styles.description}>{item.description}</Text>

              {/* Action Buttons */}
              <View style={styles.buttons}>
                <TouchableOpacity
                  style={[styles.button, styles.primaryButton]}
                  onPress={handleAction}
                >
                  <Ionicons name="play" size={20} color="#fff" />
                  <Text style={styles.buttonText}>{item.action}</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        ))}
      </ScrollView>

      {/* Navigation */}
      <View style={styles.footer}>
        {currentIndex > 0 && (
          <TouchableOpacity
            style={styles.backButton}
            onPress={handleBack}
          >
            <Ionicons name="arrow-back" size={24} color="#fff" />
          </TouchableOpacity>
        )}

        <TouchableOpacity
          style={styles.nextButton}
          onPress={handleNext}
        >
          <Text style={styles.nextButtonText}>
            {isLastScreen ? 'Finish' : 'Next'}
          </Text>
          <Ionicons
            name={isLastScreen ? 'checkmark' : 'arrow-forward'}
            size={24}
            color="#fff"
          />
        </TouchableOpacity>
      </View>
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingVertical: 16,
  },
  skipText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#999',
  },
  skipPlaceholder: {
    width: 50,
  },
  pagination: {
    flexDirection: 'row',
    gap: 8,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
  },
  dotActive: {
    backgroundColor: '#5B6AFF',
    width: 24,
  },
  content: {
    flex: 1,
  },
  slide: {
    width,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  card: {
    width: '100%',
    alignItems: 'center',
  },
  iconContainer: {
    width: 160,
    height: 160,
    borderRadius: 80,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 40,
    shadowColor: '#5B6AFF',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 16,
    textAlign: 'center',
  },
  description: {
    fontSize: 16,
    color: '#ccc',
    textAlign: 'center',
    marginBottom: 40,
    paddingHorizontal: 20,
    lineHeight: 24,
  },
  buttons: {
    width: '100%',
    gap: 16,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 16,
    gap: 12,
  },
  primaryButton: {
    backgroundColor: '#5B6AFF',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#fff',
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingVertical: 24,
  },
  backButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  nextButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#5B6AFF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 16,
  },
  nextButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#fff',
  },
});
