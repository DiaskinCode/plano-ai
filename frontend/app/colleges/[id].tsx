import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import LiquidGlassCard from '@/components/LiquidGlassCard';
import { getTargetUniversities, deleteTargetUniversity } from '@/services/onboardingApi';

interface TargetUniversity {
  id: number;
  university_name: string;
  location: {
    city: string;
    state: string;
    country: string;
  };
  category: string;
  acceptance_rate: number;
  avg_sat?: number;
  avg_act?: number;
  tuition_per_year: number;
  application_deadline: string;
  major: string;
  reasoning: string;
}

export default function CollegeDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const [college, setCollege] = useState<TargetUniversity | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCollegeDetails();
  }, [id]);

  const loadCollegeDetails = async () => {
    try {
      const colleges = await getTargetUniversities();
      const found = colleges.find((c: TargetUniversity) => c.id === parseInt(id as string));
      if (found) {
        setCollege(found);
      } else {
        Alert.alert('Error', 'College not found');
        router.back();
      }
    } catch (error) {
      console.error('Error loading college:', error);
      Alert.alert('Error', 'Failed to load college details');
      router.back();
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = () => {
    Alert.alert(
      'Remove College',
      `Are you sure you want to remove ${college?.university_name} from your list?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            if (college) {
              try {
                await deleteTargetUniversity(college.id);
                Alert.alert('Success', 'College removed from your list');
                router.back();
              } catch (error) {
                Alert.alert('Error', 'Failed to remove college');
              }
            }
          },
        },
      ]
    );
  };

  const getTierColor = (tier: string) => {
    switch (tier.toLowerCase()) {
      case 'reach': return '#FF6B6B';
      case 'target': return '#4ECDC4';
      case 'safety': return '#95E1D3';
      default: return '#CCC';
    }
  };

  const getCountryFlag = (country: string): string => {
    if (country.includes('USA') || country.includes('United States')) return '🇺🇸';
    if (country.includes('UK') || country.includes('United Kingdom')) return '🇬🇧';
    if (country.includes('China')) return '🇨🇳';
    if (country.includes('Italy')) return '🇮🇹';
    if (country.includes('Canada')) return '🇨🇦';
    return '🏳️';
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#5B6AFF" />
          <Text style={styles.loadingText}>Loading college details...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!college) {
    return null;
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <MaterialCommunityIcons name="arrow-left" size={24} color="#fff" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>College Details</Text>
          <View style={styles.headerSpacer} />
        </View>

        {/* College Card */}
        <LiquidGlassCard intensity="high" style={styles.collegeCard}>
          <View style={styles.collegeHeader}>
            <Text style={styles.collegeFlag}>{getCountryFlag(college.location.country)}</Text>
            <View style={styles.collegeInfo}>
              <Text style={styles.collegeName}>{college.university_name}</Text>
              <Text style={styles.location}>
                {college.location.city}, {college.location.state || college.location.country}
              </Text>
            </View>
          </View>
          <View style={[styles.tierBadgeLarge, { backgroundColor: getTierColor(college.category) }]}>
            <Text style={styles.tierTextLarge}>{college.category.toUpperCase()} SCHOOL</Text>
          </View>
        </LiquidGlassCard>

        {/* Stats Section */}
        <LiquidGlassCard intensity="medium" style={styles.statsCard}>
          <Text style={styles.sectionTitle}>Key Statistics</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statItem}>
              <MaterialCommunityIcons name="percent" size={24} color="#5B6AFF" />
              <Text style={styles.statLabel}>Acceptance Rate</Text>
              <Text style={styles.statValue}>{college.acceptance_rate}%</Text>
            </View>
            {college.avg_sat && (
              <View style={styles.statItem}>
                <MaterialCommunityIcons name="school" size={24} color="#5B6AFF" />
                <Text style={styles.statLabel}>Avg SAT</Text>
                <Text style={styles.statValue}>{college.avg_sat}</Text>
              </View>
            )}
            <View style={styles.statItem}>
              <MaterialCommunityIcons name="cash" size={24} color="#5B6AFF" />
              <Text style={styles.statLabel}>Tuition/Year</Text>
              <Text style={styles.statValue}>${college.tuition_per_year?.toLocaleString()}</Text>
            </View>
          </View>
        </LiquidGlassCard>

        {/* Academic Info */}
        <LiquidGlassCard intensity="medium" style={styles.infoCard}>
          <Text style={styles.sectionTitle}>Academic Information</Text>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Major</Text>
            <Text style={styles.infoValue}>{college.major}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Application Deadline</Text>
            <Text style={styles.infoValue}>{college.application_deadline}</Text>
          </View>
        </LiquidGlassCard>

        {/* AI Reasoning */}
        <LiquidGlassCard intensity="low" style={styles.reasoningCard}>
          <View style={styles.reasoningHeader}>
            <MaterialCommunityIcons name="lightbulb-on" size={24} color="#FFD700" />
            <Text style={styles.reasoningTitle}>Why This College?</Text>
          </View>
          <Text style={styles.reasoningText}>{college.reasoning}</Text>
        </LiquidGlassCard>

        {/* Actions */}
        <View style={styles.actions}>
          <TouchableOpacity style={styles.websiteButton}>
            <MaterialCommunityIcons name="web" size={20} color="#fff" />
            <Text style={styles.websiteButtonText}>Visit Website</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.removeButton} onPress={handleRemove}>
            <MaterialCommunityIcons name="delete-outline" size={20} color="#FF6B6B" />
            <Text style={styles.removeButtonText}>Remove from List</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#ccc',
    marginTop: 16,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
    flex: 1,
    textAlign: 'center',
  },
  headerSpacer: {
    width: 40,
  },
  collegeCard: {
    padding: 20,
    marginBottom: 16,
  },
  collegeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    marginBottom: 16,
  },
  collegeFlag: {
    fontSize: 48,
  },
  collegeInfo: {
    flex: 1,
  },
  collegeName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 4,
  },
  location: {
    fontSize: 16,
    color: '#ccc',
  },
  tierBadgeLarge: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  tierTextLarge: {
    fontSize: 14,
    fontWeight: '700',
    color: '#000',
  },
  statsCard: {
    padding: 20,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
    gap: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#ccc',
    textAlign: 'center',
  },
  statValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  infoCard: {
    padding: 20,
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  infoLabel: {
    fontSize: 16,
    color: '#ccc',
  },
  infoValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  reasoningCard: {
    padding: 20,
    marginBottom: 24,
  },
  reasoningHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  reasoningTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
  },
  reasoningText: {
    fontSize: 15,
    color: '#ccc',
    lineHeight: 22,
  },
  actions: {
    gap: 12,
    paddingBottom: 24,
  },
  websiteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#5B6AFF',
    paddingVertical: 14,
    borderRadius: 12,
    gap: 8,
  },
  websiteButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  removeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 107, 107, 0.1)',
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#FF6B6B',
    gap: 8,
  },
  removeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FF6B6B',
  },
});
