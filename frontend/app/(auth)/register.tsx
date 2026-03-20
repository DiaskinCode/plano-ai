import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { useRouter, Link } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authAPI } from '@/services/api';
import { timezoneService } from '@/utils/timezone';
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

export default function RegisterScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showPassword2, setShowPassword2] = useState(false);

  const handleGuestMode = async () => {
    // Set guest mode flag
    await AsyncStorage.setItem('isGuest', 'true');
    await AsyncStorage.setItem('onboarding_completed', 'true');

    // Navigate to demo screen
    router.replace('/(main)/demo');
  };

  const handleRegister = async () => {
    if (!email || !username || !password || !password2) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    if (password !== password2) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      // Detect user's timezone
      const timezone = timezoneService.getDeviceTimezone();
      console.log('Detected timezone:', timezone);

      const response = await authAPI.register({ email, username, password, password2, timezone });
      const { user, tokens } = response.data;

      // Save tokens and user
      await AsyncStorage.setItem('access_token', tokens.access);
      await AsyncStorage.setItem('refresh_token', tokens.refresh);
      await AsyncStorage.setItem('user', JSON.stringify(user));
      await AsyncStorage.setItem('onboarding_completed', 'true');

      // Track registration event
      analytics.trackUserRegistered(user.id.toString(), email, username);

      // Save timezone locally
      await timezoneService.saveTimezone(timezone);

      // Navigate straight to home (skip onboarding wizard)
      router.replace('/(main)/home');
    } catch (error: any) {
      // Handle validation errors
      const errorData = error.response?.data;
      let errorMessage = 'Please try again';

      if (errorData) {
        if (errorData.email) {
          errorMessage = errorData.email[0];
        } else if (errorData.username) {
          errorMessage = errorData.username[0];
        } else if (errorData.password) {
          errorMessage = errorData.password[0];
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        }
      }

      Alert.alert('Registration Failed', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Background Gradients */}
      <LinearGradient
        colors={['rgba(16, 163, 127, 0.3)', 'rgba(16, 163, 127, 0.1)', 'transparent']}
        style={styles.backgroundGradientTop}
        pointerEvents="none"
      />
      <LinearGradient
        colors={['transparent', 'rgba(102, 126, 234, 0.1)', 'rgba(118, 75, 162, 0.2)']}
        style={styles.backgroundGradientBottom}
        pointerEvents="none"
      />

      <View style={styles.content}>
          {/* Logo/Icon Section */}
          <View style={styles.logoContainer}>
            <LinearGradient
              colors={['#5B6AFF', '#0D8A6B']}
              style={styles.logoGradient}
            >
              <MaterialCommunityIcons name="account-plus" size={48} color="#fff" />
            </LinearGradient>
          </View>

          {/* Title Section */}
          <Text style={styles.title}>{t('auth.joinPlano')}</Text>
          <Text style={styles.subtitle}>{t('auth.startJourney')}</Text>

          {/* Form Section */}
          <View style={styles.formContainer}>
            {/* Email Input - Simplified */}
            <View style={styles.inputWrapper}>
              <MaterialCommunityIcons name="email-outline" size={20} color={COLORS.textSecondary} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder={t('auth.emailPlaceholder')}
                placeholderTextColor={COLORS.textSecondary}
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            {/* Username Input - Simplified */}
            <View style={styles.inputWrapper}>
              <MaterialCommunityIcons name="account-outline" size={20} color={COLORS.textSecondary} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder={t('auth.usernamePlaceholder')}
                placeholderTextColor={COLORS.textSecondary}
                value={username}
                onChangeText={setUsername}
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            {/* Password Input - Simplified */}
            <View style={styles.inputWrapper}>
              <MaterialCommunityIcons name="lock-outline" size={20} color={COLORS.textSecondary} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder={t('auth.passwordPlaceholder')}
                placeholderTextColor={COLORS.textSecondary}
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPassword}
                autoCapitalize="none"
              />
              <TouchableOpacity onPress={() => setShowPassword(!showPassword)} style={styles.eyeIcon}>
                <MaterialCommunityIcons
                  name={showPassword ? "eye-off-outline" : "eye-outline"}
                  size={20}
                  color={COLORS.textSecondary}
                />
              </TouchableOpacity>
            </View>

            {/* Confirm Password Input - Simplified */}
            <View style={styles.inputWrapper}>
              <MaterialCommunityIcons name="lock-check-outline" size={20} color={COLORS.textSecondary} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder={t('auth.confirmPasswordPlaceholder')}
                placeholderTextColor={COLORS.textSecondary}
                value={password2}
                onChangeText={setPassword2}
                secureTextEntry={!showPassword2}
                autoCapitalize="none"
              />
              <TouchableOpacity onPress={() => setShowPassword2(!showPassword2)} style={styles.eyeIcon}>
                <MaterialCommunityIcons
                  name={showPassword2 ? "eye-off-outline" : "eye-outline"}
                  size={20}
                  color={COLORS.textSecondary}
                />
              </TouchableOpacity>
            </View>

            {/* Register Button */}
            <TouchableOpacity
              style={styles.registerButton}
              onPress={handleRegister}
              disabled={loading}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#5B6AFF', '#0D8A6B']}
                style={styles.registerGradient}
              >
                {loading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <>
                    <Text style={styles.registerButtonText}>{t('auth.signUp')}</Text>
                    <MaterialCommunityIcons name="arrow-right" size={24} color="#fff" />
                  </>
                )}
              </LinearGradient>
            </TouchableOpacity>

            {/* Login Link */}
            <View style={styles.loginContainer}>
              <Text style={styles.loginText}>{t('auth.haveAccount')} </Text>
              <Link href="/(auth)/login" asChild>
                <TouchableOpacity>
                  <Text style={styles.loginLink}>{t('auth.loginLink')}</Text>
                </TouchableOpacity>
              </Link>
            </View>

            {/* Divider */}
            <View style={styles.dividerContainer}>
              <View style={styles.divider} />
              <Text style={styles.dividerText}>or</Text>
              <View style={styles.divider} />
            </View>

            {/* Guest Mode Button */}
            <TouchableOpacity
              style={styles.guestButton}
              onPress={handleGuestMode}
              activeOpacity={0.7}
            >
              <MaterialCommunityIcons name="account-outline" size={20} color={COLORS.primary} />
              <View style={styles.guestButtonContent}>
                <Text style={styles.guestButtonText}>Continue as Guest</Text>
                <Text style={styles.guestButtonSubtext}>Explore with limited features</Text>
              </View>
              <MaterialCommunityIcons name="arrow-right" size={20} color={COLORS.textSecondary} />
            </TouchableOpacity>
          </View>
        </View>
      </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  backgroundGradientTop: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 300,
  },
  backgroundGradientBottom: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 300,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    paddingVertical: 40,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  logoGradient: {
    width: 96,
    height: 96,
    borderRadius: 48,
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
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 40,
  },
  formContainer: {
    gap: 16,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(26, 26, 26, 0.8)',
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 16,
    paddingHorizontal: 16,
    paddingVertical: 16,
    marginBottom: 16,
  },
  inputIcon: {
    marginRight: 12,
  },
  eyeIcon: {
    padding: 4,
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
    padding: 0,
    margin: 0,
  },
  registerButton: {
    borderRadius: 16,
    overflow: 'hidden',
    marginTop: 16,
    shadowColor: '#5B6AFF',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  registerGradient: {
    paddingVertical: 18,
    paddingHorizontal: 24,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  registerButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  loginContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 24,
  },
  loginText: {
    color: COLORS.textSecondary,
    fontSize: 15,
  },
  loginLink: {
    color: COLORS.primary,
    fontSize: 15,
    fontWeight: '600',
  },
  dividerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 24,
  },
  divider: {
    flex: 1,
    height: 1,
    backgroundColor: COLORS.border,
  },
  dividerText: {
    color: COLORS.textSecondary,
    fontSize: 14,
    marginHorizontal: 12,
  },
  guestButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    backgroundColor: 'rgba(26, 26, 26, 0.6)',
    gap: 12,
  },
  guestButtonContent: {
    flex: 1,
  },
  guestButtonText: {
    color: COLORS.primary,
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  guestButtonSubtext: {
    color: COLORS.textSecondary,
    fontSize: 13,
  },
});
