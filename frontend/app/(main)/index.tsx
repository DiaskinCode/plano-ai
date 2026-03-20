import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import LiquidGlassCard from '@/components/LiquidGlassCard';
import { universityProfileAPI } from '@/services/universityRecommenderApi';
import { authAPI, todosAPI, mentorAPI } from '@/services/api';

// Types
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
  tuition_per_year: number;
}

interface Task {
  id: number;
  title: string;
  scheduled_date?: string;
  status: string;
  timebox_minutes?: number;
}

interface Mentor {
  id: number;
  name: string;
  profile_photo?: string;
  expertise_areas: string[];
  rating: number;
}

interface Extracurricular {
  id: number;
  title: string;
  category: string;
  hours_per_week: number;
}

export default function NewHomeScreen() {
  const router = useRouter();
  const [userName, setUserName] = useState('');
  const [loading, setLoading] = useState(true);

  // Data
  const [universities, setUniversities] = useState<TargetUniversity[]>([]);
  const [upcomingTasks, setUpcomingTasks] = useState<Task[]>([]);
  const [mentors, setMentors] = useState<Mentor[]>([]);
  const [extracurriculars, setExtracurriculars] = useState<Extracurricular[]>([]);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    try {
      // Load user profile
      const profileResponse = await authAPI.getProfile();
      setUserName(profileResponse.data.first_name || profileResponse.data.username || 'Student');

      // Load upcoming tasks (next 3)
      try {
        console.log('Fetching tasks...');
        const tasksResponse = await todosAPI.list();
        console.log('Tasks response:', tasksResponse);

        let tasks = [];
        if (Array.isArray(tasksResponse)) {
          tasks = tasksResponse;
        } else if (tasksResponse.results && Array.isArray(tasksResponse.results)) {
          tasks = tasksResponse.results;
        } else if (tasksResponse.data && Array.isArray(tasksResponse.data)) {
          tasks = tasksResponse.data;
        }

        console.log('Processed tasks:', tasks);

        // Filter for ready/pending tasks and get first 3
        const upcomingTasks = tasks
          .filter((task: Task) => task.status === 'ready' || task.status === 'pending')
          .slice(0, 3);

        console.log('Upcoming tasks:', upcomingTasks);
        setUpcomingTasks(upcomingTasks);
      } catch (error) {
        console.error('Error loading tasks:', error);
        setUpcomingTasks([]);
      }

      // Load mentors
      try {
        const mentorsResponse = await mentorAPI.getMentors({ page_size: 3 });
        setMentors(mentorsResponse.data.results || []);
      } catch (error) {
        console.error('Error loading mentors:', error);
        setMentors([]);
      }

      // Load extracurriculars
      try {
        const activitiesResponse = await universityProfileAPI.getExtracurriculars();
        setExtracurriculars(activitiesResponse.data || []);
      } catch (error) {
        console.error('Error loading activities:', error);
        setExtracurriculars([]);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#5B6AFF" />
          <Text style={styles.loadingText}>Loading your dashboard...</Text>
        </View>
      </SafeAreaView>
    );
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
          <Text style={styles.greeting}>Hi, {userName}!</Text>
          <Text style={styles.subGreeting}>Let's get started</Text>
        </View>

        {/* AI Assistant */}
        <LiquidGlassCard intensity="high" style={styles.sectionCard}>
          <View style={styles.aiSection}>
            <View style={styles.aiHeader}>
              <MaterialCommunityIcons name="robot" size={32} color="#5B6AFF" />
              <View style={styles.aiHeaderText}>
                <Text style={styles.aiTitle}>AI Assistant</Text>
                <Text style={styles.aiSubtitle}>Get personalized guidance</Text>
              </View>
            </View>
            <TouchableOpacity
              style={styles.aiButton}
              onPress={() => router.push('/(main)/chat')}
            >
              <Text style={styles.aiButtonText}>Try It</Text>
              <MaterialCommunityIcons name="arrow-right" size={18} color="#fff" />
            </TouchableOpacity>
          </View>
        </LiquidGlassCard>

        {/* Upcoming Plans */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Upcoming Plans</Text>
            <TouchableOpacity onPress={() => router.push('/(main)/todos')}>
              <Text style={styles.seeAllText}>See All</Text>
            </TouchableOpacity>
          </View>
          {upcomingTasks.length > 0 ? (
            upcomingTasks.map((task) => (
              <LiquidGlassCard key={task.id} intensity="low" style={styles.taskCard}>
                <View style={styles.taskHeader}>
                  <MaterialCommunityIcons name="checkbox-blank-circle-outline" size={20} color="#5B6AFF" />
                  <Text style={styles.taskTitle}>{task.title}</Text>
                </View>
                {task.scheduled_date && (
                  <Text style={styles.taskDate}>
                    {new Date(task.scheduled_date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                  </Text>
                )}
              </LiquidGlassCard>
            ))
          ) : (
            <LiquidGlassCard intensity="low" style={styles.emptyCard}>
              <Text style={styles.emptyText}>No upcoming tasks</Text>
            </LiquidGlassCard>
          )}
        </View>

        {/* Your Colleges */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Your Colleges</Text>
            <TouchableOpacity onPress={() => {
              if (universities.length > 0) {
                router.push('/university-recommender/results');
              } else {
                router.push('/university-profile/wizard');
              }
            }}>
              <Text style={styles.seeAllText}>
                {universities.length > 0 ? 'See Recommendations' : 'Find Universities'}
              </Text>
            </TouchableOpacity>
          </View>
          {universities.length > 0 ? (
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.horizontalScroll}>
              {universities.slice(0, 5).map((college) => (
                <CollegeCardMini
                  key={college.id}
                  college={college}
                  onPress={() => router.push(`/colleges/${college.id}`)}
                />
              ))}
            </ScrollView>
          ) : (
            <EmptyStateCard
              icon="school-outline"
              title="No colleges yet"
              description="Get personalized university recommendations"
              buttonText="Create Your Profile"
              onPress={() => router.push('/university-profile/wizard')}
            />
          )}
        </View>

        {/* Your Mentors */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Your Mentors</Text>
            <TouchableOpacity onPress={() => router.push('/(main)/mentors')}>
              <Text style={styles.seeAllText}>
                {mentors.length > 0 ? 'See All' : 'Find'}
              </Text>
            </TouchableOpacity>
          </View>
          {mentors.length > 0 ? (
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.horizontalScroll}>
              {mentors.map((mentor) => (
                <MentorCard
                  key={mentor.id}
                  mentor={mentor}
                  onPress={() => router.push(`/mentors/${mentor.id}`)}
                />
              ))}
            </ScrollView>
          ) : (
            <EmptyStateCard
              icon="account-tie"
              title="No mentors yet"
              description="Connect with experts"
              buttonText="Find Mentors"
              onPress={() => router.push('/(main)/mentors')}
            />
          )}
        </View>

        {/* Your Activities */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Your Activities</Text>
            <TouchableOpacity onPress={() => router.push('/university-profile/activities')}>
              <Text style={styles.seeAllText}>
                {extracurriculars.length > 0 ? 'See All' : 'Add'}
              </Text>
            </TouchableOpacity>
          </View>
          {extracurriculars.length > 0 ? (
            extracurriculars.slice(0, 3).map((activity) => (
              <ActivityCard
                key={activity.id}
                activity={activity}
                onPress={() => router.push('/university-profile/activities')}
              />
            ))
          ) : (
            <EmptyStateCard
              icon="trophy-outline"
              title="No activities yet"
              description="Track your extracurriculars"
              buttonText="Add Activities"
              onPress={() => router.push('/university-profile/activities')}
            />
          )}
        </View>

        {/* Your Essays */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Your Essays</Text>
            <TouchableOpacity onPress={() => router.push('/(main)/todos')}>
              <Text style={styles.seeAllText}>See All</Text>
            </TouchableOpacity>
          </View>
          <EmptyStateCard
            icon="file-document-outline"
            title="Essays coming soon"
            description="Track your college essays"
            buttonText="View Tasks"
            onPress={() => router.push('/(main)/todos')}
          />
        </View>

        {/* Bottom Spacing */}
        <View style={styles.bottomSpacing} />
      </ScrollView>
    </SafeAreaView>
  );
}

// Mini College Card Component
interface CollegeCardMiniProps {
  college: TargetUniversity;
  onPress: () => void;
}

function CollegeCardMini({ college, onPress }: CollegeCardMiniProps) {
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
    if (country.includes('Canada')) return '🇨🇦';
    return '🏳️';
  };

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
      <LiquidGlassCard intensity="medium" style={styles.miniCard}>
        <Text style={styles.miniCardFlag}>{getCountryFlag(college.location.country)}</Text>
        <Text style={styles.miniCardTitle} numberOfLines={2}>
          {college.university_name}
        </Text>
        <View style={[styles.miniCardBadge, { backgroundColor: getTierColor(college.category) }]}>
          <Text style={styles.miniCardBadgeText}>{college.category.toUpperCase()}</Text>
        </View>
      </LiquidGlassCard>
    </TouchableOpacity>
  );
}

// Mentor Card Component
interface MentorCardProps {
  mentor: Mentor;
  onPress: () => void;
}

function MentorCard({ mentor, onPress }: MentorCardProps) {
  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
      <LiquidGlassCard intensity="medium" style={styles.miniCard}>
        <View style={styles.mentorAvatar}>
          <MaterialCommunityIcons name="account-tie" size={40} color="#5B6AFF" />
        </View>
        <Text style={styles.miniCardTitle} numberOfLines={1}>{mentor.name}</Text>
        <View style={styles.mentorRating}>
          <MaterialCommunityIcons name="star" size={12} color="#FFD700" />
          <Text style={styles.mentorRatingText}>{mentor.rating.toFixed(1)}</Text>
        </View>
      </LiquidGlassCard>
    </TouchableOpacity>
  );
}

// Activity Card Component
interface ActivityCardProps {
  activity: Extracurricular;
  onPress: () => void;
}

function ActivityCard({ activity, onPress }: ActivityCardProps) {
  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
      <LiquidGlassCard intensity="low" style={styles.activityCard}>
        <View style={styles.activityHeader}>
          <MaterialCommunityIcons name="trophy" size={20} color="#FFD700" />
          <Text style={styles.activityTitle}>{activity.title}</Text>
        </View>
        <Text style={styles.activitySubtitle}>
          {activity.category} • {activity.hours_per_week}h/week
        </Text>
      </LiquidGlassCard>
    </TouchableOpacity>
  );
}

// Empty State Card Component
interface EmptyStateCardProps {
  icon: string;
  title: string;
  description: string;
  buttonText: string;
  onPress: () => void;
}

function EmptyStateCard({ icon, title, description, buttonText, onPress }: EmptyStateCardProps) {
  return (
    <LiquidGlassCard intensity="low" style={styles.emptyCard}>
      <MaterialCommunityIcons name={icon as any} size={48} color="#666" />
      <Text style={styles.emptyTitle}>{title}</Text>
      <Text style={styles.emptyDescription}>{description}</Text>
      <TouchableOpacity style={styles.emptyButton} onPress={onPress}>
        <Text style={styles.emptyButtonText}>{buttonText}</Text>
      </TouchableOpacity>
    </LiquidGlassCard>
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
    marginBottom: 24,
  },
  greeting: {
    fontSize: 32,
    fontWeight: '700',
    color: '#fff',
  },
  subGreeting: {
    fontSize: 18,
    color: '#ccc',
    marginTop: 4,
  },
  sectionCard: {
    marginBottom: 24,
  },
  aiSection: {
    padding: 20,
  },
  aiHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  aiHeaderText: {
    flex: 1,
  },
  aiTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
  },
  aiSubtitle: {
    fontSize: 14,
    color: '#ccc',
    marginTop: 2,
  },
  aiButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#5B6AFF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
    gap: 8,
  },
  aiButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
  },
  seeAllText: {
    fontSize: 14,
    color: '#5B6AFF',
    fontWeight: '600',
  },
  horizontalScroll: {
    marginHorizontal: -16,
    paddingHorizontal: 16,
  },
  taskCard: {
    padding: 16,
    marginBottom: 8,
  },
  taskHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  taskTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    flex: 1,
  },
  taskDate: {
    fontSize: 13,
    color: '#ccc',
  },
  miniCard: {
    width: 140,
    padding: 12,
    marginRight: 12,
    alignItems: 'center',
  },
  miniCardFlag: {
    fontSize: 32,
    marginBottom: 8,
  },
  miniCardTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 8,
    minHeight: 36,
  },
  miniCardBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  miniCardBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#000',
  },
  mentorAvatar: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(91, 106, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  mentorRating: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 4,
  },
  mentorRatingText: {
    fontSize: 12,
    color: '#FFD700',
    fontWeight: '600',
  },
  activityCard: {
    padding: 16,
    marginBottom: 8,
  },
  activityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  activityTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    flex: 1,
  },
  activitySubtitle: {
    fontSize: 13,
    color: '#ccc',
  },
  emptyCard: {
    padding: 32,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#ccc',
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyDescription: {
    fontSize: 14,
    color: '#ccc',
    textAlign: 'center',
    marginBottom: 16,
  },
  emptyButton: {
    backgroundColor: '#5B6AFF',
    paddingHorizontal: 24,
    paddingVertical: 10,
    borderRadius: 10,
  },
  emptyButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
  bottomSpacing: {
    height: 100,
  },
});
