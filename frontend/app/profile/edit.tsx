/**
 * Edit Profile Screen
 *
 * Edit own profile:
 * - Display name, username, bio, location
 * - Upload/change avatar
 * - Academic stats (OPTIONAL)
 * - Add/remove target universities
 * - Privacy settings
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  Image,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { router } from 'expo-router';
import { socialAPI } from '@/services/api';

interface UserProfile {
  id: number;
  username: string;
  email: string;
  avatar_url?: string;
  bio?: string;
  location?: string;
  target_universities?: string[];
  gpa?: number;
  sat_score?: number;
  ielts_score?: number;
  stats_visibility: 'public' | 'followers' | 'private';
  message_privacy: 'everyone' | 'followers' | 'following';
  activity_visibility: 'public' | 'followers' | 'private';
}

export default function EditProfileScreen() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Form fields
  const [bio, setBio] = useState('');
  const [location, setLocation] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');
  const [targetUniInput, setTargetUniInput] = useState('');

  // Academic stats (optional)
  const [gpa, setGpa] = useState('');
  const [satScore, setSatScore] = useState('');
  const [ieltsScore, setIeltsScore] = useState('');

  // Privacy settings
  const [statsVisibility, setStatsVisibility] = useState<'public' | 'followers' | 'private'>('public');
  const [messagePrivacy, setMessagePrivacy] = useState<'everyone' | 'followers' | 'following'>('everyone');
  const [activityVisibility, setActivityVisibility] = useState<'public' | 'followers' | 'private'>('public');

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await socialAPI.getOwnProfile();
      const data = response.data;

      setProfile(data);
      setBio(data.bio || '');
      setLocation(data.location || '');
      setAvatarUrl(data.avatar_url || '');
      setGpa(data.gpa ? String(data.gpa) : '');
      setSatScore(data.sat_score ? String(data.sat_score) : '');
      setIeltsScore(data.ielts_score ? String(data.ielts_score) : '');
      setStatsVisibility(data.stats_visibility);
      setMessagePrivacy(data.message_privacy);
      setActivityVisibility(data.activity_visibility);
    } catch (error) {
      console.error('Failed to load profile:', error);
      Alert.alert('Error', 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!profile) return;

    try {
      setSaving(true);

      const updateData: any = {
        bio,
        location,
        avatar_url: avatarUrl || undefined,
        stats_visibility: statsVisibility,
        message_privacy: messagePrivacy,
        activity_visibility: activityVisibility,
      };

      // Only include academic stats if provided
      if (gpa) updateData.gpa = parseFloat(gpa);
      if (satScore) updateData.sat_score = parseInt(satScore);
      if (ieltsScore) updateData.ielts_score = parseFloat(ieltsScore);

      await socialAPI.updateProfile(profile.id, updateData);

      Alert.alert('Success', 'Profile updated successfully', [
        { text: 'OK', onPress: () => router.back() },
      ]);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to update profile';
      Alert.alert('Error', errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleAddUniversity = () => {
    if (!targetUniInput.trim() || !profile) return;

    const universities = profile.target_universities || [];
    if (universities.includes(targetUniInput)) {
      Alert.alert('Already Added', 'This university is already in your list');
      return;
    }

    if (universities.length >= 10) {
      Alert.alert('Limit Reached', 'You can add up to 10 target universities');
      return;
    }

    setProfile({
      ...profile,
      target_universities: [...universities, targetUniInput],
    });
    setTargetUniInput('');
  };

  const handleRemoveUniversity = (uni: string) => {
    if (!profile) return;

    setProfile({
      ...profile,
      target_universities: (profile.target_universities || []).filter(u => u !== uni),
    });
  };

  if (loading) {
    return (
      <View style={styles.centerContent}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  if (!profile) {
    return (
      <View style={styles.centerContent}>
        <Text style={styles.errorText}>Failed to load profile</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor="#121212" />
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.cancelButton}
          onPress={() => router.back()}
        >
          <Text style={styles.cancelButtonText}>Cancel</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Edit Profile</Text>
        <TouchableOpacity
          style={styles.saveButton}
          onPress={handleSave}
          disabled={saving}
        >
          <Text style={styles.saveButtonText}>
            {saving ? 'Saving...' : 'Save'}
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollView}>
        {/* Avatar Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Avatar</Text>
          <View style={styles.avatarContainer}>
            {avatarUrl ? (
              <Image source={{ uri: avatarUrl }} style={styles.avatar} />
            ) : (
              <View style={[styles.avatar, styles.avatarPlaceholder]}>
                <Text style={styles.avatarPlaceholderText}>
                  {profile.username.charAt(0).toUpperCase()}
                </Text>
              </View>
            )}
          </View>
          <TextInput
            style={styles.input}
            placeholder="Avatar URL"
            placeholderTextColor="#6B7280"
            value={avatarUrl}
            onChangeText={setAvatarUrl}
            autoCapitalize="none"
          />
        </View>

        {/* Basic Info */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Basic Information</Text>

          <Text style={styles.label}>Bio</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            placeholder="Tell us about yourself..."
            placeholderTextColor="#6B7280"
            value={bio}
            onChangeText={setBio}
            multiline
            numberOfLines={4}
            maxLength={500}
          />
          <Text style={styles.charCount}>{bio.length}/500</Text>

          <Text style={styles.label}>Location</Text>
          <TextInput
            style={styles.input}
            placeholder="City, Country"
            placeholderTextColor="#6B7280"
            value={location}
            onChangeText={setLocation}
          />
        </View>

        {/* Target Universities */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Target Universities</Text>

          <View style={styles.universityInputRow}>
            <TextInput
              style={[styles.input, { flex: 1 }]}
              placeholder="Add university..."
              placeholderTextColor="#6B7280"
              value={targetUniInput}
              onChangeText={setTargetUniInput}
              onSubmitEditing={handleAddUniversity}
            />
            <TouchableOpacity
              style={styles.addButton}
              onPress={handleAddUniversity}
            >
              <Text style={styles.addButtonText}>Add</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.universitiesList}>
            {(profile.target_universities || []).map((uni, index) => (
              <View key={index} style={styles.universityTag}>
                <Text style={styles.universityText}>{uni}</Text>
                <TouchableOpacity onPress={() => handleRemoveUniversity(uni)}>
                  <Text style={styles.removeIcon}> ✕</Text>
                </TouchableOpacity>
              </View>
            ))}
          </View>

          {(profile.target_universities || []).length === 0 && (
            <Text style={styles.emptyText}>No universities added yet</Text>
          )}
        </View>

        {/* Academic Stats (Optional) */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Academic Stats</Text>
            <Text style={styles.sectionSubtitle}>(Optional)</Text>
          </View>
          <Text style={styles.sectionNote}>
            Skip if you don't want to share these stats
          </Text>

          <Text style={styles.label}>GPA</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g., 3.8"
            placeholderTextColor="#6B7280"
            value={gpa}
            onChangeText={setGpa}
            keyboardType="decimal-pad"
          />

          <Text style={styles.label}>SAT Score</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g., 1450"
            placeholderTextColor="#6B7280"
            value={satScore}
            onChangeText={setSatScore}
            keyboardType="numeric"
          />

          <Text style={styles.label}>IELTS Score</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g., 7.5"
            placeholderTextColor="#6B7280"
            value={ieltsScore}
            onChangeText={setIeltsScore}
            keyboardType="decimal-pad"
          />
        </View>

        {/* Privacy Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Privacy Settings</Text>

          <Text style={styles.label}>Stats Visibility</Text>
          <View style={styles.optionsRow}>
            {(['public', 'followers', 'private'] as const).map((option) => (
              <TouchableOpacity
                key={option}
                style={[
                  styles.optionButton,
                  statsVisibility === option && styles.optionButtonActive,
                ]}
                onPress={() => setStatsVisibility(option)}
              >
                <Text
                  style={[
                    styles.optionText,
                    statsVisibility === option && styles.optionTextActive,
                  ]}
                >
                  {option.charAt(0).toUpperCase() + option.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.label}>Who Can Message You</Text>
          <View style={styles.optionsRow}>
            {(['everyone', 'followers', 'following'] as const).map((option) => (
              <TouchableOpacity
                key={option}
                style={[
                  styles.optionButton,
                  messagePrivacy === option && styles.optionButtonActive,
                ]}
                onPress={() => setMessagePrivacy(option)}
              >
                <Text
                  style={[
                    styles.optionText,
                    messagePrivacy === option && styles.optionTextActive,
                  ]}
                >
                  {option.charAt(0).toUpperCase() + option.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.label}>Activity Visibility</Text>
          <View style={styles.optionsRow}>
            {(['public', 'followers', 'private'] as const).map((option) => (
              <TouchableOpacity
                key={option}
                style={[
                  styles.optionButton,
                  activityVisibility === option && styles.optionButtonActive,
                ]}
                onPress={() => setActivityVisibility(option)}
              >
                <Text
                  style={[
                    styles.optionText,
                    activityVisibility === option && styles.optionTextActive,
                  ]}
                >
                  {option.charAt(0).toUpperCase() + option.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    fontSize: 16,
    color: '#8E8E8E',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  cancelButton: {
    width: 80,
  },
  cancelButtonText: {
    fontSize: 14,
    color: '#8E8E8E',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ECECEC',
    flex: 1,
    textAlign: 'center',
  },
  saveButton: {
    width: 80,
    alignItems: 'flex-end',
  },
  saveButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#3B82F6',
  },
  scrollView: {
    flex: 1,
  },
  section: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ECECEC',
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginLeft: 8,
  },
  sectionNote: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 16,
    fontStyle: 'italic',
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#B8B8B8',
    marginBottom: 8,
    marginTop: 12,
  },
  input: {
    backgroundColor: '#1E1E1E',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#ECECEC',
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  charCount: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'right',
    marginTop: 4,
  },
  avatarContainer: {
    alignItems: 'center',
    marginBottom: 16,
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
  },
  avatarPlaceholder: {
    backgroundColor: '#3B82F6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarPlaceholderText: {
    fontSize: 40,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  universityInputRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },
  addButton: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    justifyContent: 'center',
  },
  addButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  universitiesList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  universityTag: {
    backgroundColor: '#2A2A2A',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 8,
    flexDirection: 'row',
    alignItems: 'center',
  },
  universityText: {
    fontSize: 14,
    color: '#ECECEC',
  },
  removeIcon: {
    fontSize: 14,
    color: '#EF4444',
  },
  emptyText: {
    fontSize: 14,
    color: '#6B7280',
    fontStyle: 'italic',
  },
  optionsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  optionButton: {
    flex: 1,
    backgroundColor: '#1E1E1E',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2A2A2A',
  },
  optionButtonActive: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  optionText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#8E8E8E',
  },
  optionTextActive: {
    color: '#FFFFFF',
  },
});
