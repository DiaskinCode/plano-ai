import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ActivityIndicator, ScrollView } from 'react-native';
import { useRouter, Link } from 'expo-router';
import { useTranslation } from 'react-i18next';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authAPI } from '@/services/api';
import analytics from '@/services/analytics';

const COLORS = {
  bg: '#000000',
  surface: '#1A1A1A',
  border: '#2A2A2A',
  text: '#ECECEC',
  textSecondary: '#8E8E8E',
  primary: '#5B6AFF',
  error: '#EF4444',
};

export default function LoginScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    setLoading(true);
    try {
      const response = await authAPI.login({ email, password });
      const { user, tokens } = response.data;

      await AsyncStorage.setItem('access_token', tokens.access);
      await AsyncStorage.setItem('refresh_token', tokens.refresh);
      await AsyncStorage.setItem('user', JSON.stringify(user));

      analytics.trackUserLoggedIn(user.id.toString(), email);
      await AsyncStorage.setItem('onboarding_completed', 'true');

      router.replace('/(main)/home');
    } catch (error: any) {
      Alert.alert('Login Failed', error.response?.data?.error || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleGuestMode = async () => {
    await AsyncStorage.setItem('isGuest', 'true');
    await AsyncStorage.setItem('onboarding_completed', 'true');
    router.replace('/(main)/demo');
  };

  return (
    <View style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="interactive"
        bounces={false}
      >
        <Text style={styles.title}>{t('auth.welcomeBack')}</Text>
        <Text style={styles.subtitle}>{t('auth.welcomeBackSubtitle')}</Text>

        <View style={styles.formContainer}>
          {/* Email Input - NO WRAPPER */}
          <TextInput
            style={styles.input}
            placeholder="Email"
            placeholderTextColor={COLORS.textSecondary}
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            returnKeyType="next"
            blurOnSubmit={true}
            onSubmitEditing={() => console.log('Email submitted')}
          />

          {/* Password Input - NO WRAPPER */}
          <TextInput
            style={styles.input}
            placeholder="Password"
            placeholderTextColor={COLORS.textSecondary}
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            autoCapitalize="none"
            returnKeyType="done"
            blurOnSubmit={true}
            onSubmitEditing={handleLogin}
          />

          <TouchableOpacity
            style={styles.loginButton}
            onPress={handleLogin}
            disabled={loading}
            activeOpacity={0.7}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.loginButtonText}>{t('auth.signIn')}</Text>
            )}
          </TouchableOpacity>

          <View style={styles.registerContainer}>
            <Text style={styles.registerText}>{t('auth.noAccount')} </Text>
            <Link href="/(auth)/register" asChild>
              <TouchableOpacity>
                <Text style={styles.registerLink}>{t('auth.registerLink')}</Text>
              </TouchableOpacity>
            </Link>
          </View>

          <TouchableOpacity
            style={styles.guestButton}
            onPress={handleGuestMode}
            activeOpacity={0.7}
          >
            <Text style={styles.guestButtonText}>Continue as Guest</Text>
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
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    paddingVertical: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 32,
  },
  formContainer: {
    width: '100%',
  },
  input: {
    width: '100%',
    height: 56,
    backgroundColor: 'rgba(26, 26, 26, 0.8)',
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 16,
    marginBottom: 16,
    color: COLORS.text,
    fontSize: 16,
    zIndex: 1,
  },
  loginButton: {
    borderRadius: 16,
    backgroundColor: '#5B6AFF',
    marginTop: 24,
    paddingVertical: 18,
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  loginButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  registerContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 24,
  },
  registerText: {
    color: COLORS.textSecondary,
    fontSize: 14,
  },
  registerLink: {
    color: COLORS.primary,
    fontSize: 14,
    fontWeight: '600',
  },
  guestButton: {
    marginTop: 16,
    paddingVertical: 16,
    alignItems: 'center',
  },
  guestButtonText: {
    color: COLORS.primary,
    fontSize: 16,
    fontWeight: '600',
  },
});
