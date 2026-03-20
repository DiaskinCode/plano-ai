/**
 * Community Creation Modal
 *
 * Allows users to create a new community
 * - Requires admin approval
 * - Form validation
 * - Status tracking
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';

type CommunityType = 'region' | 'topic';
type BannerColor = '#3B82F6' | '#8B5CF6' | '#EC4899' | '#F59E0B' | '#10B981' | '#EF4444';

const COMMUNITY_TYPES = [
  { id: 'region', label: 'Region', icon: '🌍', description: 'Connect with people in your area' },
  { id: 'topic', label: 'Topic', icon: '💡', description: 'Discuss shared interests' },
];

const BANNER_COLORS: BannerColor[] = [
  '#3B82F6', // Blue
  '#8B5CF6', // Purple
  '#EC4899', // Pink
  '#F59E0B', // Orange
  '#10B981', // Green
  '#EF4444', // Red
];

const ICONS = ['🎓', '💻', '📚', '🔬', '🎨', '🎵', '⚽', '💼', '🌱', '🚀'];

interface CreateCommunityForm {
  name: string;
  slug: string;
  description: string;
  community_type: CommunityType;
  icon: string;
  banner_color: BannerColor;
  tags: string;
}

export default function CreateCommunityModal() {
  const router = useRouter();

  const [form, setForm] = useState<CreateCommunityForm>({
    name: '',
    slug: '',
    description: '',
    community_type: 'topic',
    icon: ICONS[0],
    banner_color: '#3B82F6',
    tags: '',
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof CreateCommunityForm, string>>>({});

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof CreateCommunityForm, string>> = {};

    if (!form.name.trim()) {
      newErrors.name = 'Community name is required';
    } else if (form.name.length < 3) {
      newErrors.name = 'Name must be at least 3 characters';
    } else if (form.name.length > 50) {
      newErrors.name = 'Name must be less than 50 characters';
    }

    if (!form.description.trim()) {
      newErrors.description = 'Description is required';
    } else if (form.description.length < 20) {
      newErrors.description = 'Description must be at least 20 characters';
    } else if (form.description.length > 500) {
      newErrors.description = 'Description must be less than 500 characters';
    }

    if (!form.tags.trim()) {
      newErrors.tags = 'At least one tag is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  };

  const handleNameChange = (text: string) => {
    setForm({ ...form, name: text, slug: generateSlug(text) });
    if (errors.name) setErrors({ ...errors, name: undefined });
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      // TODO: Call API to submit community creation request
      // await communityAPI.createCreationRequest({
      //   name: form.name,
      //   slug: form.slug,
      //   description: form.description,
      //   community_type: form.community_type,
      //   icon: form.icon,
      //   banner_color: form.banner_color,
      //   tags: form.tags.split(',').map(t => t.trim()),
      // });

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      Alert.alert(
        'Community Submitted!',
        'Your community request has been submitted for admin approval. You will receive a notification once it is reviewed.',
        [
          { text: 'OK', onPress: () => router.back() },
        ]
      );
    } catch (error: any) {
      Alert.alert(
        'Submission Failed',
        error.response?.data?.detail || 'Failed to submit community request'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor="#121212" />
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.cancelButton} onPress={() => router.back()}>
          <MaterialCommunityIcons name="close" size={24} color="#8E8E8E" />
        </TouchableOpacity>

        <Text style={styles.headerTitle}>Create Community</Text>

        <TouchableOpacity
          style={[styles.submitButton, loading && styles.submitButtonDisabled]}
          onPress={handleSubmit}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Text style={styles.submitButtonText}>Submit</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Form */}
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Notice */}
        <View style={styles.noticeBox}>
          <MaterialCommunityIcons name="information" size={20} color="#3B82F6" />
          <Text style={styles.noticeText}>
            Your community will be reviewed by our team before appearing publicly.
          </Text>
        </View>

        {/* Community Type */}
        <View style={styles.section}>
          <Text style={styles.label}>Community Type</Text>
          <View style={styles.typeContainer}>
            {COMMUNITY_TYPES.map((type) => (
              <TouchableOpacity
                key={type.id}
                style={[
                  styles.typeCard,
                  form.community_type === type.id && styles.typeCardSelected,
                ]}
                onPress={() => setForm({ ...form, community_type: type.id as CommunityType })}
              >
                <Text style={styles.typeIcon}>{type.icon}</Text>
                <Text style={styles.typeLabel}>{type.label}</Text>
                <Text style={styles.typeDescription}>{type.description}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Name */}
        <View style={styles.section}>
          <Text style={styles.label}>Community Name</Text>
          <TextInput
            style={[styles.input, errors.name && styles.inputError]}
            placeholder="e.g., Stanford Applicants 2025"
            placeholderTextColor="#6B7280"
            value={form.name}
            onChangeText={handleNameChange}
            maxLength={50}
          />
          {errors.name && <Text style={styles.errorText}>{errors.name}</Text>}
          <Text style={styles.characterCount}>{form.name.length}/50</Text>
        </View>

        {/* Slug (Read-only) */}
        <View style={styles.section}>
          <Text style={styles.label}>URL Slug</Text>
          <View style={styles.slugContainer}>
            <Text style={styles.slugPrefix}>pathai.app/community/</Text>
            <Text style={styles.slugValue}>{form.slug || 'your-community'}</Text>
          </View>
        </View>

        {/* Description */}
        <View style={styles.section}>
          <Text style={styles.label}>Description</Text>
          <TextInput
            style={[styles.textArea, errors.description && styles.inputError]}
            placeholder="Describe what your community is about and who should join..."
            placeholderTextColor="#6B7280"
            value={form.description}
            onChangeText={(text) => {
              setForm({ ...form, description: text });
              if (errors.description) setErrors({ ...errors, description: undefined });
            }}
            multiline
            numberOfLines={4}
            maxLength={500}
          />
          {errors.description && <Text style={styles.errorText}>{errors.description}</Text>}
          <Text style={styles.characterCount}>{form.description.length}/500</Text>
        </View>

        {/* Icon Selection */}
        <View style={styles.section}>
          <Text style={styles.label}>Community Icon</Text>
          <View style={styles.iconGrid}>
            {ICONS.map((icon) => (
              <TouchableOpacity
                key={icon}
                style={[
                  styles.iconOption,
                  form.icon === icon && styles.iconOptionSelected,
                ]}
                onPress={() => setForm({ ...form, icon })}
              >
                <Text style={styles.iconOptionText}>{icon}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Banner Color */}
        <View style={styles.section}>
          <Text style={styles.label}>Banner Color</Text>
          <View style={styles.colorContainer}>
            {BANNER_COLORS.map((color) => (
              <TouchableOpacity
                key={color}
                style={[
                  styles.colorOption,
                  { backgroundColor: color },
                  form.banner_color === color && styles.colorOptionSelected,
                ]}
                onPress={() => setForm({ ...form, banner_color: color })}
              >
                {form.banner_color === color && (
                  <MaterialCommunityIcons name="check" size={20} color="#FFFFFF" />
                )}
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Tags */}
        <View style={styles.section}>
          <Text style={styles.label}>Tags</Text>
          <Text style={styles.helperText}>
            Add up to 5 tags separated by commas
          </Text>
          <TextInput
            style={[styles.input, errors.tags && styles.inputError]}
            placeholder="e.g., SAT, College Essays, Applications"
            placeholderTextColor="#6B7280"
            value={form.tags}
            onChangeText={(text) => {
              setForm({ ...form, tags: text });
              if (errors.tags) setErrors({ ...errors, tags: undefined });
            }}
          />
          {errors.tags && <Text style={styles.errorText}>{errors.tags}</Text>}
        </View>

        {/* Preview */}
        <View style={styles.section}>
          <Text style={styles.label}>Preview</Text>
          <View style={[styles.previewCard, { backgroundColor: form.banner_color }]}>
            <Text style={styles.previewIcon}>{form.icon}</Text>
            <View style={styles.previewContent}>
              <Text style={styles.previewName}>{form.name || 'Community Name'}</Text>
              <Text style={styles.previewDescription} numberOfLines={2}>
                {form.description || 'Community description...'}
              </Text>
            </View>
          </View>
        </View>

        {/* Submit Button */}
        <TouchableOpacity
          style={[styles.submitButtonLarge, loading && styles.submitButtonLargeDisabled]}
          onPress={handleSubmit}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Text style={styles.submitButtonLargeText}>Submit for Approval</Text>
          )}
        </TouchableOpacity>

        <View style={styles.bottomSpacer} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  cancelButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ECECEC',
  },
  submitButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#3B82F6',
    borderRadius: 8,
  },
  submitButtonDisabled: {
    backgroundColor: '#3E3E3E',
  },
  submitButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  noticeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    padding: 12,
    borderRadius: 8,
    marginBottom: 24,
    gap: 8,
  },
  noticeText: {
    flex: 1,
    fontSize: 13,
    color: '#3B82F6',
    lineHeight: 18,
  },
  section: {
    marginBottom: 24,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ECECEC',
    marginBottom: 8,
  },
  helperText: {
    fontSize: 13,
    color: '#8E8E8E',
    marginBottom: 8,
  },
  typeContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  typeCard: {
    flex: 1,
    backgroundColor: '#1E1E1E',
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: '#3E3E3E',
    alignItems: 'center',
  },
  typeCardSelected: {
    borderColor: '#3B82F6',
    backgroundColor: '#1E1E1E',
  },
  typeIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  typeLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ECECEC',
    marginBottom: 4,
  },
  typeDescription: {
    fontSize: 11,
    color: '#8E8E8E',
    textAlign: 'center',
  },
  input: {
    backgroundColor: '#1E1E1E',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#ECECEC',
    borderWidth: 1,
    borderColor: '#3E3E3E',
  },
  inputError: {
    borderColor: '#EF4444',
  },
  errorText: {
    fontSize: 12,
    color: '#EF4444',
    marginTop: 4,
  },
  characterCount: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4,
    textAlign: 'right',
  },
  slugContainer: {
    flexDirection: 'row',
    backgroundColor: '#1E1E1E',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#3E3E3E',
  },
  slugPrefix: {
    fontSize: 13,
    color: '#8E8E8E',
  },
  slugValue: {
    fontSize: 13,
    color: '#3B82F6',
  },
  textArea: {
    backgroundColor: '#1E1E1E',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#ECECEC',
    borderWidth: 1,
    borderColor: '#3E3E3E',
    minHeight: 100,
    textAlignVertical: 'top',
  },
  iconGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  iconOption: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#1E1E1E',
    borderWidth: 2,
    borderColor: '#3E3E3E',
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconOptionSelected: {
    borderColor: '#3B82F6',
    backgroundColor: '#1E1E1E',
  },
  iconOptionText: {
    fontSize: 24,
  },
  colorContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  colorOption: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: 'transparent',
  },
  colorOptionSelected: {
    borderColor: '#FFFFFF',
  },
  previewCard: {
    flexDirection: 'row',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    gap: 12,
  },
  previewIcon: {
    fontSize: 40,
  },
  previewContent: {
    flex: 1,
  },
  previewName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ECECEC',
    marginBottom: 4,
  },
  previewDescription: {
    fontSize: 14,
    color: 'rgba(236, 236, 236, 0.7)',
  },
  submitButtonLarge: {
    backgroundColor: '#3B82F6',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  submitButtonLargeDisabled: {
    backgroundColor: '#3E3E3E',
  },
  submitButtonLargeText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  bottomSpacer: {
    height: 40,
  },
});
