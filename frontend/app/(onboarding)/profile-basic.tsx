import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { useOnboarding } from '@/components/onboarding/OnboardingContext';

const COUNTRIES = [
  'USA', 'UK', 'Canada', 'Australia', 'Germany', 'Netherlands',
  'China', 'Kazakhstan', 'Russia', 'India', 'Other'
];

interface FormData {
  fullName: string;
  username: string;
  dateOfBirth: string;
  country: string;
  city: string;
  phone: string;
}

export default function ProfileBasicScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const { onboardingData, updateOnboardingData } = useOnboarding();

  const [formData, setFormData] = useState<FormData>({
    fullName: onboardingData.full_name || '',
    username: onboardingData.username || '',
    dateOfBirth: onboardingData.date_of_birth || '',
    country: onboardingData.country || '',
    city: onboardingData.city || '',
    phone: onboardingData.phone || '',
  });

  const [showCountryPicker, setShowCountryPicker] = useState(false);
  const [loading, setLoading] = useState(false);

  const calculateAge = (dob: string): number => {
    if (!dob) return 0;
    const birthDate = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  const handleNext = async () => {
    // Validation
    if (!formData.fullName || formData.fullName.trim().length < 2) {
      Alert.alert('Invalid Name', 'Please enter your full name');
      return;
    }

    if (!formData.username || formData.username.trim().length < 3) {
      Alert.alert('Invalid Username', 'Username must be at least 3 characters');
      return;
    }

    if (!formData.dateOfBirth) {
      Alert.alert('Date Required', 'Please enter your date of birth');
      return;
    }

    const age = calculateAge(formData.dateOfBirth);
    if (age < 13) {
      Alert.alert('Age Requirement', 'You must be at least 13 years old to use this app');
      return;
    }

    if (age > 100) {
      Alert.alert('Invalid Date', 'Please enter a valid date of birth');
      return;
    }

    if (!formData.country) {
      Alert.alert('Country Required', 'Please select your country');
      return;
    }

    if (!formData.city || formData.city.trim().length < 2) {
      Alert.alert('City Required', 'Please enter your city');
      return;
    }

    try {
      setLoading(true);

      // TODO: Check username uniqueness
      // For now, simulate availability check

      // Save onboarding data
      updateOnboardingData({
        full_name: formData.fullName,
        username: formData.username,
        date_of_birth: formData.dateOfBirth,
        country: formData.country,
        city: formData.city,
        phone: formData.phone,
        age: age,
      });

      router.push('/(onboarding)/academic');
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to save profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Progress */}
          <View style={styles.progressContainer}>
            <View style={styles.progressBar}>
              <View style={[styles.progressFill, { width: '30%' }]} />
            </View>
            <Text style={styles.progressText}>Step 4 of 14</Text>
          </View>

          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Basic Information</Text>
            <Text style={styles.subtitle}>Tell us a bit about yourself</Text>
          </View>

          {/* Form */}
          <View style={styles.form}>
            {/* Full Name */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Full Name *</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter your full name"
                value={formData.fullName}
                onChangeText={(text) => setFormData({ ...formData, fullName: text })}
                autoCapitalize="words"
              />
            </View>

            {/* Username */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Username *</Text>
              <TextInput
                style={styles.input}
                placeholder="Choose a unique username"
                value={formData.username}
                onChangeText={(text) => setFormData({ ...formData, username: text.toLowerCase().replace(/\s/g, '') })}
                autoCapitalize="none"
                autoComplete="username"
              />
              <Text style={styles.hint}>This will be visible to other users</Text>
            </View>

            {/* Date of Birth */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Date of Birth *</Text>
              <TextInput
                style={styles.input}
                placeholder="YYYY-MM-DD (e.g., 2005-06-15)"
                value={formData.dateOfBirth}
                onChangeText={(text) => setFormData({ ...formData, dateOfBirth: text })}
                keyboardType="numbers-and-punctuation"
                maxLength={10}
              />
              {formData.dateOfBirth && calculateAge(formData.dateOfBirth) > 0 && (
                <Text style={styles.ageText}>Age: {calculateAge(formData.dateOfBirth)} years old</Text>
              )}
            </View>

            {/* Country */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Country *</Text>
              <TouchableOpacity
                style={styles.picker}
                onPress={() => setShowCountryPicker(true)}
              >
                <Text style={formData.country ? styles.pickerText : styles.pickerPlaceholder}>
                  {formData.country || 'Select your country'}
                </Text>
                <Text style={styles.pickerArrow}>▼</Text>
              </TouchableOpacity>
            </View>

            {/* City */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>City *</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter your city"
                value={formData.city}
                onChangeText={(text) => setFormData({ ...formData, city: text })}
                autoCapitalize="words"
              />
            </View>

            {/* Phone (Optional) */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Phone Number (Optional)</Text>
              <TextInput
                style={styles.input}
                placeholder="+1 (555) 123-4567"
                value={formData.phone}
                onChangeText={(text) => setFormData({ ...formData, phone: text })}
                keyboardType="phone-pad"
                autoComplete="tel"
              />
            </View>
          </View>

          {/* Country Picker Modal */}
          {showCountryPicker && (
            <View style={styles.modalOverlay}>
              <View style={styles.modalContent}>
                <Text style={styles.modalTitle}>Select Country</Text>
                <ScrollView style={styles.countryList}>
                  {COUNTRIES.map((country) => (
                    <TouchableOpacity
                      key={country}
                      style={styles.countryItem}
                      onPress={() => {
                        setFormData({ ...formData, country });
                        setShowCountryPicker(false);
                      }}
                    >
                      <Text style={styles.countryName}>{country}</Text>
                      {formData.country === country && (
                        <Text style={styles.checkmark}>✓</Text>
                      )}
                    </TouchableOpacity>
                  ))}
                </ScrollView>
                <TouchableOpacity
                  style={styles.modalClose}
                  onPress={() => setShowCountryPicker(false)}
                >
                  <Text style={styles.modalCloseText}>Cancel</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          {/* Continue Button */}
          <TouchableOpacity
            style={[styles.continueButton, loading && styles.continueButtonDisabled]}
            onPress={handleNext}
            disabled={loading}
          >
            <Text style={styles.continueButtonText}>
              {loading ? 'Loading...' : 'Continue'}
            </Text>
          </TouchableOpacity>

          {/* Back Button */}
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
          >
            <Text style={styles.backButtonText}>← Back</Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  keyboardView: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 24,
    paddingTop: 20,
    paddingBottom: 24,
  },
  progressContainer: {
    marginBottom: 24,
  },
  progressBar: {
    height: 4,
    backgroundColor: '#E5E7EB',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#6366F1',
  },
  progressText: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 8,
    textAlign: 'center',
  },
  header: {
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
  },
  form: {
    gap: 20,
    marginBottom: 24,
  },
  inputGroup: {
    gap: 8,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  input: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  picker: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  pickerText: {
    fontSize: 16,
    color: '#111827',
  },
  pickerPlaceholder: {
    fontSize: 16,
    color: '#9CA3AF',
  },
  pickerArrow: {
    fontSize: 12,
    color: '#6B7280',
  },
  hint: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  ageText: {
    fontSize: 14,
    color: '#6366F1',
    fontWeight: '500',
  },
  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    width: '90%',
    maxHeight: '70%',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  countryList: {
    maxHeight: 400,
  },
  countryItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  countryName: {
    fontSize: 16,
    color: '#1F2937',
  },
  checkmark: {
    fontSize: 18,
    color: '#6366F1',
    fontWeight: 'bold',
  },
  modalClose: {
    marginTop: 16,
    paddingVertical: 12,
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
  },
  modalCloseText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#6B7280',
  },
  continueButton: {
    backgroundColor: '#6366F1',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  continueButtonDisabled: {
    opacity: 0.6,
  },
  continueButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  backButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  backButtonText: {
    fontSize: 14,
    color: '#6B7280',
  },
});
