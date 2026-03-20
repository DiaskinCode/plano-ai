import { useEffect } from 'react';
import { View, Text, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authAPI } from '@/services/api';

export default function Index() {
  const router = useRouter();

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      console.log('🔍 [AUTH CHECK] Starting auth check...');

      // Check if intro has been completed
      const introCompleted = await AsyncStorage.getItem('intro_completed');
      console.log('🔍 [INTRO CHECK] Intro completed:', introCompleted);

      if (!introCompleted) {
        console.log('🔍 [INTRO CHECK] Intro not completed, redirecting to language selector');
        router.replace('/(intro)/language');
        return;
      }

      const token = await AsyncStorage.getItem('access_token');
      console.log('🔍 [AUTH CHECK] Token found:', token ? 'YES' : 'NO');

      if (!token) {
        console.log('🔍 [AUTH CHECK] No token, redirecting to login');
        router.replace('/(auth)/login');
        return;
      }

      // User is authenticated - go straight to home
      console.log('🔍 [AUTH CHECK] ✅ User authenticated, navigating to HOME');
      router.replace('/(main)/home');
    } catch (error) {
      console.error('🔍 [AUTH CHECK] ❌ Auth check error:', error);
      router.replace('/(auth)/login');
    }
  };

  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#000' }}>
      <ActivityIndicator size="large" color="#5B6AFF" />
      <Text style={{ marginTop: 16, color: '#fff' }}>Loading...</Text>
    </View>
  );
}
