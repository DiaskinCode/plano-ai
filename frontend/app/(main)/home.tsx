import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Modal,
  Dimensions,
  Image,
} from "react-native";
import { useRouter } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as WebBrowser from "expo-web-browser";
import LiquidGlassCard from "@/components/LiquidGlassCard";
import {
  universityProfileAPI,
  universityRecommenderAPI,
} from "@/services/universityRecommenderApi";
import { authAPI, todosAPI, mentorAPI, essaysAPI } from "@/services/api";
import { getMyBookings } from "@/services/mentorship";
import { colors, spacing, borderRadius } from "@/theme";

// Types
interface Task {
  id: number;
  title: string;
  scheduled_date?: string;
  status: string;
  timebox_minutes?: number;
}

interface MentorBooking {
  id: number;
  mentor: number;
  mentor_title?: string;
  mentor_photo_url?: string;
  student: number;
  start_at_utc: string;
  end_at_utc: string;
  duration_minutes: number;
  status: "requested" | "confirmed" | "completed" | "cancelled";
  topic?: string;
  student_notes?: string;
  meeting_url?: string;
}

interface Mentor {
  id: number;
  title: string;
  bio: string;
  photo_url?: string;
  education?: string;
  expertise_areas: string[];
  hourly_rate_credits: number;
  timezone: string;
  meeting_link?: string;
  is_verified: boolean;
  is_active: boolean;
  rating: string | number; // API returns as string
  total_sessions: number;
}

interface Extracurricular {
  id: number;
  title: string;
  category: string;
  hours_per_week: number;
}

interface ShortlistItem {
  id: number;
  university: {
    short_name: string;
    name: string;
    location: string;
    total_cost: number;
    acceptance_rate: number;
  };
}

interface Essay {
  id: number;
  title: string;
  target_university: string;
  essay_type: string;
  progress_percentage: number;
  status: string;
  word_count: number;
  word_count_goal: number;
}

export default function NewHomeScreen() {
  const router = useRouter();
  const [userName, setUserName] = useState("");
  const [loading, setLoading] = useState(true);

  // Data
  const [upcomingTasks, setUpcomingTasks] = useState<Task[]>([]);
  const [upcomingMeeting, setUpcomingMeeting] = useState<MentorBooking | null>(null);
  const [mentors, setMentors] = useState<Mentor[]>([]);
  const [extracurriculars, setExtracurriculars] = useState<Extracurricular[]>(
    [],
  );
  const [hasProfile, setHasProfile] = useState(false);
  const [shortlist, setShortlist] = useState<ShortlistItem[]>([]);
  const [essays, setEssays] = useState<Essay[]>([]);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [featuredUniversities, setFeaturedUniversities] = useState<any[]>([]);

  // Helper function to get essay type icon
  const getEssayTypeIcon = (type: string): string => {
    const icons: { [key: string]: string } = {
      personal_statement: "📝",
      why_college: "🎓",
      why_major: "🔬",
      leadership: "👥",
      challenge: "💪",
      activity: "🎯",
      community: "🤝",
      achievement: "🏆",
      creative: "🎨",
      supplemental: "✍️",
    };
    return icons[type] || "📄";
  };

  const getStatusColor = (status: string): string => {
    const statusColors: { [key: string]: string } = {
      brainstorming: "#6B7280",
      outlining: "#3B82F6",
      drafting: "#F59E0B",
      reviewing: "#8B5CF6",
      polishing: "#10B981",
      completed: "#06B6D4",
    };
    return statusColors[status] || "#6B7280";
  };

  // Calculate profile completeness - all sections independent
  const profileCompleteness = (() => {
    const items = [
      {
        name: "University Profile",
        completed: hasProfile,
        weight: 25,
        route: "/university-profile/wizard",
      },
      {
        name: "Extracurriculars",
        completed: extracurriculars.length > 0,
        weight: 25,
        route: "/university-profile/activities",
      },
      {
        name: "University Shortlist",
        completed: shortlist.length > 0,
        weight: 25,
        route: "/university-recommender/results",
      },
      {
        name: "Admissions Plan",
        completed: upcomingTasks.length > 0,
        weight: 25,
        route: "/(main)/todos",
      },
    ];

    const completedSections = items.filter((item) => item.completed).length;
    const score = completedSections * 25;

    return { score, items };
  })();

  useEffect(() => {
    checkWalkthroughStatus();
    loadAllData();
  }, []);

  const checkWalkthroughStatus = async () => {
    try {
      const walkthroughCompleted = await AsyncStorage.getItem(
        "walkthrough_completed",
      );
      if (!walkthroughCompleted) {
        // First time user - show walkthrough
        router.replace("/(walkthrough)/welcome");
      }
    } catch (error) {
      console.error("Error checking walkthrough status:", error);
    }
  };

  const loadAllData = async () => {
    try {
      // Load user profile
      const profileResponse = await authAPI.getProfile();
      setUserName(
        profileResponse.data.first_name ||
          profileResponse.data.username ||
          "Student",
      );

      // Load upcoming tasks (next 3)
      try {
        console.log("Fetching tasks...");
        const tasksResponse = await todosAPI.list();
        console.log("=== TASKS API RESPONSE ===");
        console.log("Type:", typeof tasksResponse);
        console.log("Keys:", Object.keys(tasksResponse || {}));

        // Axios wraps responses in a `data` property
        let tasks = [];
        if (
          tasksResponse?.data?.results &&
          Array.isArray(tasksResponse.data.results)
        ) {
          console.log(
            "✓ Response has data.results array, length:",
            tasksResponse.data.results.length,
          );
          tasks = tasksResponse.data.results;
        } else if (
          tasksResponse?.results &&
          Array.isArray(tasksResponse.results)
        ) {
          console.log("✓ Response has results array (no .data wrapper)");
          tasks = tasksResponse.results;
        } else if (Array.isArray(tasksResponse)) {
          console.log("✓ Response is direct array");
          tasks = tasksResponse;
        } else {
          console.warn("✗ Response format not recognized");
          console.warn(
            "Full response:",
            JSON.stringify(tasksResponse, null, 2),
          );
        }

        console.log("Processed tasks count:", tasks.length);
        if (tasks.length > 0) {
          console.log("First task:", tasks[0]);
          console.log(
            "Task statuses:",
            tasks.map((t: Task) => `${t.title} (${t.status})`),
          );
        }

        // Get all tasks (no status filter) and take first 3
        const upcomingTasks = tasks.slice(0, 3);

        console.log("Final upcoming tasks:", upcomingTasks);
        setUpcomingTasks(upcomingTasks);
      } catch (error) {
        console.error("=== ERROR LOADING TASKS ===");
        console.error("Error:", error);
        console.error(
          "Message:",
          error instanceof Error ? error.message : "Unknown error",
        );
        setUpcomingTasks([]);
      }

      // Load mentors
      try {
        const mentorsResponse = await mentorAPI.getMentors({ page_size: 3 });
        setMentors(mentorsResponse.data.results || []);
      } catch (error) {
        console.error("Error loading mentors:", error);
        setMentors([]);
      }

      // Load upcoming meetings
      try {
        const bookings = await getMyBookings();
        console.log("Loaded bookings:", bookings);

        // Filter for confirmed upcoming meetings
        const now = new Date();
        const upcoming = bookings
          .filter((b) => b.status === "confirmed" && new Date(b.start_at_utc) > now)
          .sort((a, b) => new Date(a.start_at_utc).getTime() - new Date(b.start_at_utc).getTime())[0];

        console.log("Next upcoming meeting:", upcoming);
        setUpcomingMeeting(upcoming || null);
      } catch (error) {
        console.error("Error loading bookings:", error);
        setUpcomingMeeting(null);
      }

      // Load extracurriculars
      try {
        const activitiesResponse =
          await universityProfileAPI.getExtracurriculars();
        console.log("Activities response:", activitiesResponse.data);
        // API returns paginated data with results array
        const activities =
          activitiesResponse.data.results || activitiesResponse.data || [];
        setExtracurriculars(activities);
      } catch (error) {
        console.error("Error loading activities:", error);
      }

      // Check if user has a university profile
      let userHasProfile = false;
      try {
        const profileResponse = await universityProfileAPI.getProfile();
        if (
          profileResponse.data &&
          !profileResponse.data.error &&
          profileResponse.data.gpa
        ) {
          userHasProfile = true;
          setHasProfile(true);
        } else {
          setHasProfile(false);
        }
      } catch (error) {
        console.log("No university profile:", error);
        setHasProfile(false);
      }

      // Load featured universities (always load for showcase when no shortlist)
      try {
        const featuredResponse = await universityRecommenderAPI.getFeatured();
        console.log("=== FEATURED UNIVERSITIES ===");
        console.log("Response:", featuredResponse.data);
        console.log("Length:", featuredResponse.data?.length);
        setFeaturedUniversities(featuredResponse.data || []);
      } catch (error) {
        console.log("No featured universities:", error);
      }

      // Load shortlist
      try {
        const shortlistResponse = await universityRecommenderAPI.getShortlist();
        setShortlist(shortlistResponse.data || []);
      } catch (error) {
        console.log("No shortlist:", error);
        setShortlist([]);
      }

      // Load essays
      try {
        const essaysResponse = await essaysAPI.getProjects();
        const essayData =
          essaysResponse.data.projects || essaysResponse.data || [];
        setEssays(essayData);
      } catch (error) {
        console.log("No essays:", error);
        setEssays([]);
      }
    } catch (error) {
      console.error("Error loading data:", error);
    } finally {
      setLoading(false);
    }
  };

  // Helper function to format meeting date
  const formatMeetingDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === now.toDateString()) {
      return "Today";
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return "Tomorrow";
    } else {
      return date.toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
      });
    }
  };

  // Helper function to format meeting time
  const formatMeetingTime = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  };

  // Countdown Timer Component
  const CountdownTimer = ({ targetDate }: { targetDate: string }) => {
    const [timeLeft, setTimeLeft] = useState<{ hours: number; minutes: number } | null>(null);

    useEffect(() => {
      const calculateTimeLeft = () => {
        const now = new Date();
        const target = new Date(targetDate);
        const diff = target.getTime() - now.getTime();

        if (diff <= 0) {
          setTimeLeft({ hours: 0, minutes: 0 });
          return;
        }

        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        setTimeLeft({ hours, minutes });
      };

      calculateTimeLeft();
      const interval = setInterval(calculateTimeLeft, 60000); // Update every minute

      return () => clearInterval(interval);
    }, [targetDate]);

    if (!timeLeft || (timeLeft.hours === 0 && timeLeft.minutes === 0)) return null;

    return (
      <View style={countdownStyles.container}>
        <MaterialCommunityIcons name="timer" size={16} color={colors.primary} />
        <Text style={countdownStyles.text}>
          Starts in {timeLeft.hours > 0 && `${timeLeft.hours}h `}
          {timeLeft.minutes}m
        </Text>
      </View>
    );
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

  // Debug logging
  console.log("=== RENDER STATE ===");
  console.log("hasProfile:", hasProfile);
  console.log("featuredUniversities.length:", featuredUniversities.length);
  console.log("featuredUniversities:", featuredUniversities);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>Hi, {userName}!</Text>
            <Text style={styles.subGreeting}>Let's get started</Text>
          </View>

          {/* Circular Progress Button */}
          <TouchableOpacity
            onPress={() => setShowProgressModal(true)}
            style={styles.progressButton}
          >
            <View style={styles.circularProgress}>
              <View
                style={[
                  styles.progressCircle,
                  {
                    borderColor:
                      profileCompleteness.score >= 100 ? "#4ADE80" : "#5B6AFF",
                  },
                ]}
              >
                <Text style={styles.progressText}>
                  {profileCompleteness.score}%
                </Text>
              </View>
            </View>
          </TouchableOpacity>
        </View>

        {/* Progress Modal */}
        <Modal
          visible={showProgressModal}
          transparent
          animationType="fade"
          onRequestClose={() => setShowProgressModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Profile Progress</Text>
                <TouchableOpacity onPress={() => setShowProgressModal(false)}>
                  <MaterialCommunityIcons name="close" size={28} color="#fff" />
                </TouchableOpacity>
              </View>

              <View style={styles.progressOverview}>
                <View
                  style={[
                    styles.circularProgressLarge,
                    {
                      borderColor:
                        profileCompleteness.score >= 100
                          ? "#4ADE80"
                          : "#5B6AFF",
                    },
                  ]}
                >
                  <Text style={styles.progressTextLarge}>
                    {profileCompleteness.score}%
                  </Text>
                  <Text style={styles.progressSubtext}>Complete</Text>
                </View>
              </View>

              <View style={styles.progressList}>
                {profileCompleteness.items.map((item, index) => (
                  <TouchableOpacity
                    key={index}
                    style={styles.progressItem}
                    onPress={() => {
                      setShowProgressModal(false);
                      router.push(item.route);
                    }}
                  >
                    <View style={styles.progressItemLeft}>
                      <MaterialCommunityIcons
                        name={
                          item.completed ? "check-circle" : "circle-outline"
                        }
                        size={24}
                        color={item.completed ? "#4ADE80" : "#666"}
                      />
                      <View style={styles.progressItemInfo}>
                        <Text style={styles.progressItemName}>{item.name}</Text>
                        <Text style={styles.progressItemWeight}>
                          {item.weight}% of profile
                        </Text>
                      </View>
                    </View>
                    {!item.completed && (
                      <MaterialCommunityIcons
                        name="chevron-right"
                        size={24}
                        color="#5B6AFF"
                      />
                    )}
                  </TouchableOpacity>
                ))}
              </View>

              {profileCompleteness.score < 100 && (
                <View style={styles.modalTip}>
                  <MaterialCommunityIcons
                    name="lightbulb"
                    size={20}
                    color="#FBBF24"
                  />
                  <Text style={styles.modalTipText}>
                    Complete sections in any order to build your full profile
                  </Text>
                </View>
              )}
            </View>
          </View>
        </Modal>

        {/* Upcoming Meeting Card - PRIORITY #1 */}
        {upcomingMeeting && (
          <LiquidGlassCard
            intensity="high"
            style={styles.upcomingMeetingCard}
            onPress={async () => {
              if (upcomingMeeting.meeting_url) {
                await WebBrowser.openBrowserAsync(upcomingMeeting.meeting_url);
              }
            }}
          >
            <View style={styles.meetingHeader}>
              <View style={styles.meetingIconContainer}>
                <MaterialCommunityIcons
                  name="video"
                  size={32}
                  color={colors.primary}
                />
              </View>
              <View style={styles.meetingHeaderContent}>
                <Text style={styles.meetingTitle}>Upcoming Session</Text>
                <Text style={styles.meetingMentor}>
                  {upcomingMeeting.mentor_title || "Mentor Session"}
                </Text>
              </View>
              <View style={styles.joinButtonContainer}>
                <View style={styles.joinButton}>
                  <MaterialCommunityIcons name="login" size={20} color="#fff" />
                  <Text style={styles.joinButtonText}>Join</Text>
                </View>
              </View>
            </View>

            <View style={styles.meetingDetails}>
              <View style={styles.meetingDetailRow}>
                <MaterialCommunityIcons
                  name="calendar"
                  size={18}
                  color="#999"
                />
                <Text style={styles.meetingDetailText}>
                  {formatMeetingDate(upcomingMeeting.start_at_utc)}
                </Text>
              </View>
              <View style={styles.meetingDetailRow}>
                <MaterialCommunityIcons name="clock" size={18} color="#999" />
                <Text style={styles.meetingDetailText}>
                  {formatMeetingTime(upcomingMeeting.start_at_utc)} ({upcomingMeeting.duration_minutes} min)
                </Text>
              </View>
              {upcomingMeeting.topic && (
                <View style={styles.meetingTopicBadge}>
                  <Text style={styles.meetingTopicText}>{upcomingMeeting.topic}</Text>
                </View>
              )}
            </View>

            {/* Countdown Timer */}
            <CountdownTimer targetDate={upcomingMeeting.start_at_utc} />
          </LiquidGlassCard>
        )}

        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>
              {hasProfile ? "Your Colleges" : "Explore Colleges"}
            </Text>
            {(hasProfile && shortlist.length > 0) ||
            featuredUniversities.length > 0 ? (
              <TouchableOpacity
                onPress={() => router.push("/university-recommender/results")}
              >
                <Text style={styles.seeAllText}>Show more</Text>
              </TouchableOpacity>
            ) : null}
          </View>
          {hasProfile && shortlist.length > 0 ? (
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              style={styles.horizontalScroll}
            >
              {shortlist.map((item) => (
                <ShortlistCard
                  key={item.id}
                  item={item}
                  onPress={() =>
                    router.push(
                      `/university-profile/${item.university.short_name}`,
                    )
                  }
                />
              ))}
            </ScrollView>
          ) : featuredUniversities.length > 0 ? (
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              style={styles.horizontalScroll}
            >
              {featuredUniversities.map((uni) => (
                <FeaturedUniversityCard
                  key={uni.id}
                  university={uni}
                  onPress={() =>
                    router.push(`/university-profile/${uni.short_name}`)
                  }
                />
              ))}
            </ScrollView>
          ) : hasProfile ? (
            <View style={styles.collegeActions}>
              <EmptyStateCard
                icon="school-outline"
                title="View Your Recommendations"
                description="See your Match, Safety, and Reach universities"
                buttonText="Review Chances"
                onPress={() => router.push("/university-recommender/results")}
              />
              <TouchableOpacity
                style={styles.editProfileButtonSmall}
                onPress={() => router.push("/university-profile/wizard")}
              >
                <MaterialCommunityIcons
                  name="pencil"
                  size={14}
                  color="#5B6AFF"
                />
                <Text style={styles.editProfileTextSmall}>Edit Profile</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <EmptyStateCard
              icon="school-outline"
              title="Explore Universities"
              description="Create your profile to get personalized recommendations"
              buttonText="Create Your Profile"
              onPress={() => router.push("/university-profile/wizard")}
            />
          )}

        {/* Create University Profile CTA - at bottom of section */}
        {!hasProfile && (
          <LiquidGlassCard intensity="medium" style={styles.createProfileListItem}>
            <View style={styles.createProfileListItemContent}>
              <Text style={styles.createProfileListTitle}>Create University Profile</Text>
              <TouchableOpacity
                style={styles.createProfileListButton}
                onPress={() => router.push("/university-profile/wizard")}
              >
                <Text style={styles.createProfileListButtonText}>Create</Text>
              </TouchableOpacity>
            </View>
          </LiquidGlassCard>
        )}
        </View>

        {/* AI Assistant - UPDATED & MOVED TO 3RD POSITION */}
        <LiquidGlassCard intensity="high" style={styles.aiCard}>
          <View style={styles.aiContent}>
            <View style={styles.aiLeft}>
              <View style={styles.aiIconContainer}>
                <MaterialCommunityIcons
                  name="robot"
                  size={28}
                  color="#5B6AFF"
                />
              </View>
              <View style={styles.aiTextContainer}>
                <Text style={styles.aiTitle}>
                  Not sure which colleges to pick?
                </Text>
                <Text style={styles.aiSubtitle}>
                  Ask AI for personalized recommendations
                </Text>
              </View>
            </View>
            <TouchableOpacity
              style={styles.aiAction}
              onPress={() => router.push("/(main)/chat")}
            >
              <MaterialCommunityIcons
                name="arrow-right"
                size={20}
                color="#5B6AFF"
              />
            </TouchableOpacity>
          </View>
        </LiquidGlassCard>

        {/* Your Mentors */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Your Mentors</Text>
            <TouchableOpacity onPress={() => router.push("/(main)/mentors")}>
              <Text style={styles.seeAllText}>
                {mentors.length > 0 ? "See All" : "Find"}
              </Text>
            </TouchableOpacity>
          </View>
          {mentors.length > 0 ? (
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              style={styles.horizontalScroll}
            >
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
              onPress={() => router.push("/(main)/mentors")}
            />
          )}
        </View>

        {/* Your Activities */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Your Activities</Text>
            <TouchableOpacity
              onPress={() => router.push("/university-profile/activities")}
            >
              <Text style={styles.seeAllText}>
                {extracurriculars.length > 0 ? "See All" : "Add"}
              </Text>
            </TouchableOpacity>
          </View>
          {extracurriculars.length > 0 ? (
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              style={styles.horizontalScroll}
            >
              {extracurriculars.slice(0, 3).map((activity) => (
                <ActivityCard
                  key={activity.id}
                  activity={activity}
                  onPress={() => router.push("/university-profile/activities")}
                />
              ))}
            </ScrollView>
          ) : (
            <EmptyStateCard
              icon="trophy-outline"
              title="No activities yet"
              description="Track your extracurriculars"
              buttonText="Add Activities"
              onPress={() => router.push("/university-profile/activities")}
            />
          )}
        </View>

        {/* Your Essays */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Your Essays</Text>
            <TouchableOpacity onPress={() => router.push("/(main)/essays")}>
              <Text style={styles.seeAllText}>See All</Text>
            </TouchableOpacity>
          </View>

          {essays.length === 0 ? (
            <EmptyStateCard
              icon="file-document-edit-outline"
              title="Start Your College Essays"
              description="Get AI-powered help writing compelling essays"
              buttonText="Start Writing"
              onPress={() => router.push("/(main)/essays")}
            />
          ) : (
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              style={styles.horizontalScroll}
            >
              {essays.slice(0, 3).map((essay) => (
                <LiquidGlassCard
                  key={essay.id}
                  style={styles.miniCard}
                  onPress={() => router.push(`/essay/${essay.id}`)}
                >
                  <View style={styles.essayIconContainer}>
                    <Text style={styles.essayIcon}>
                      {getEssayTypeIcon(essay.essay_type)}
                    </Text>
                  </View>
                  <Text style={styles.miniCardTitle} numberOfLines={1}>
                    {essay.title}
                  </Text>
                  <Text style={styles.miniCardSubtitle} numberOfLines={1}>
                    {essay.target_university}
                  </Text>

                  {/* Progress Bar */}
                  <View style={styles.miniProgressContainer}>
                    <View style={styles.miniProgressBackground}>
                      <View
                        style={[
                          styles.miniProgressFill,
                          { width: `${essay.progress_percentage}%` },
                        ]}
                      />
                    </View>
                    <Text style={styles.miniProgressText}>
                      {essay.progress_percentage}%
                    </Text>
                  </View>

                  {/* Status Badge */}
                  <View
                    style={[
                      styles.miniStatusBadge,
                      { backgroundColor: getStatusColor(essay.status) },
                    ]}
                  >
                    <Text style={styles.miniStatusText}>{essay.status}</Text>
                  </View>
                </LiquidGlassCard>
              ))}

              {/* Add More Button */}
              <TouchableOpacity
                style={[styles.miniCard, styles.addMoreCard]}
                onPress={() => router.push("/(main)/essays")}
                activeOpacity={0.7}
              >
                <MaterialCommunityIcons
                  name="plus"
                  size={32}
                  color={colors.primary}
                />
                <Text style={styles.addMoreText}>New Essay</Text>
              </TouchableOpacity>
            </ScrollView>
          )}
        </View>

        {/* Bottom Spacing */}
        <View style={styles.bottomSpacing} />
      </ScrollView>
    </SafeAreaView>
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
          <MaterialCommunityIcons
            name="account-tie"
            size={40}
            color="#5B6AFF"
          />
        </View>
        <Text style={styles.miniCardTitle} numberOfLines={1}>
          {mentor.title}
        </Text>
        <View style={styles.mentorRating}>
          <MaterialCommunityIcons name="star" size={12} color="#FFD700" />
          <Text style={styles.mentorRatingText}>
            {parseFloat(mentor.rating).toFixed(1)}
          </Text>
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
    <LiquidGlassCard
      onPress={onPress}
      intensity="light"
      style={styles.activityCard}
    >
      <View style={styles.activityHeader}>
        <MaterialCommunityIcons name="trophy" size={20} color="#FFD700" />
        <Text style={styles.activityTitle}>{activity.title}</Text>
      </View>
      <Text style={styles.activitySubtitle}>
        {activity.category} • {activity.hours_per_week}h/week
      </Text>
    </LiquidGlassCard>
  );
}

// Shortlist Card Component
interface ShortlistCardProps {
  item: ShortlistItem;
  onPress: () => void;
}

function ShortlistCard({ item, onPress }: ShortlistCardProps) {
  const hasCampusPhoto =
    item.university.campus_photo_url && item.university.campus_photo_url.length > 0;

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
      <View style={styles.featuredCard}>
        {/* Campus Photo or Logo placeholder */}
        {hasCampusPhoto ? (
          <View style={styles.featuredImageContainer}>
            <Image
              source={{ uri: item.university.campus_photo_url }}
              style={styles.featuredImage}
              resizeMode="cover"
            />
            {/* Logo overlay */}
            {item.university.logo_url && item.university.logo_url.length > 0 ? (
              <Image
                source={{ uri: item.university.logo_url }}
                style={styles.featuredLogo}
              />
            ) : (
              <View style={styles.featuredLogoPlaceholder}>
                <MaterialCommunityIcons
                  name="school"
                  size={28}
                  color="#5B6AFF"
                />
              </View>
            )}
          </View>
        ) : (
          // No campus photo - show large logo centered
          <View style={styles.featuredNoPhotoContainer}>
            {item.university.logo_url && item.university.logo_url.length > 0 ? (
              <Image
                source={{ uri: item.university.logo_url }}
                style={styles.featuredLargeLogo}
                resizeMode="contain"
              />
            ) : (
              <View style={styles.featuredLargeLogoPlaceholder}>
                <MaterialCommunityIcons
                  name="school"
                  size={48}
                  color="#5B6AFF"
                />
                <Text style={styles.featuredPlaceholderText}>
                  {item.university.name.split(" ").slice(0, 2).join(" ")}
                </Text>
              </View>
            )}
          </View>
        )}

        {/* Info */}
        <View
          style={
            hasCampusPhoto ? styles.featuredInfo : styles.featuredInfoNoPhoto
          }
        >
          <Text style={styles.featuredName} numberOfLines={2}>
            {item.university.name}
          </Text>
          <Text style={styles.featuredLocation}>{item.university.location}</Text>

          {/* Stats */}
          <View style={styles.featuredStats}>
            <View style={styles.featuredStat}>
              <MaterialCommunityIcons
                name="percent"
                size={14}
                color="#5B6AFF"
              />
              <Text style={styles.featuredStatText}>
                {item.university.acceptance_rate}%
              </Text>
            </View>
            <View style={styles.featuredStat}>
              <MaterialCommunityIcons name="cash" size={14} color="#5B6AFF" />
              <Text style={styles.featuredStatText}>
                ${(item.university.total_cost / 1000).toFixed(0)}k/yr
              </Text>
            </View>
            {item.university.need_blind && (
              <View style={styles.featuredStat}>
                <MaterialCommunityIcons
                  name="shield-checkmark"
                  size={14}
                  color="#4ADE80"
                />
              </View>
            )}
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

// Featured University Card Component
interface FeaturedUniversityCardProps {
  university: {
    id: number;
    short_name: string;
    name: string;
    location: string;
    campus_photo_url: string;
    logo_url?: string;
    acceptance_rate: number;
    total_cost: number;
    need_blind?: boolean;
    international_aid?: boolean;
  };
  onPress: () => void;
}

function FeaturedUniversityCard({
  university,
  onPress,
}: FeaturedUniversityCardProps) {
  const hasCampusPhoto =
    university.campus_photo_url && university.campus_photo_url.length > 0;

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
      <View style={styles.featuredCard}>
        {/* Campus Photo or Logo placeholder */}
        {hasCampusPhoto ? (
          <View style={styles.featuredImageContainer}>
            <Image
              source={{ uri: university.campus_photo_url }}
              style={styles.featuredImage}
              resizeMode="cover"
            />
            {/* Logo overlay */}
            {university.logo_url && university.logo_url.length > 0 ? (
              <Image
                source={{ uri: university.logo_url }}
                style={styles.featuredLogo}
              />
            ) : (
              <View style={styles.featuredLogoPlaceholder}>
                <MaterialCommunityIcons
                  name="school"
                  size={28}
                  color="#5B6AFF"
                />
              </View>
            )}
          </View>
        ) : (
          // No campus photo - show large logo centered
          <View style={styles.featuredNoPhotoContainer}>
            {university.logo_url && university.logo_url.length > 0 ? (
              <Image
                source={{ uri: university.logo_url }}
                style={styles.featuredLargeLogo}
                resizeMode="contain"
              />
            ) : (
              <View style={styles.featuredLargeLogoPlaceholder}>
                <MaterialCommunityIcons
                  name="school"
                  size={48}
                  color="#5B6AFF"
                />
                <Text style={styles.featuredPlaceholderText}>
                  {university.name.split(" ").slice(0, 2).join(" ")}
                </Text>
              </View>
            )}
          </View>
        )}

        {/* Info */}
        <View
          style={
            hasCampusPhoto ? styles.featuredInfo : styles.featuredInfoNoPhoto
          }
        >
          <Text style={styles.featuredName} numberOfLines={2}>
            {university.name}
          </Text>
          <Text style={styles.featuredLocation}>{university.location}</Text>

          {/* Stats */}
          <View style={styles.featuredStats}>
            <View style={styles.featuredStat}>
              <MaterialCommunityIcons
                name="percent"
                size={14}
                color="#5B6AFF"
              />
              <Text style={styles.featuredStatText}>
                {university.acceptance_rate}%
              </Text>
            </View>
            <View style={styles.featuredStat}>
              <MaterialCommunityIcons name="cash" size={14} color="#5B6AFF" />
              <Text style={styles.featuredStatText}>
                ${(university.total_cost / 1000).toFixed(0)}k/yr
              </Text>
            </View>
            {university.need_blind && (
              <View style={styles.featuredStat}>
                <MaterialCommunityIcons
                  name="shield-checkmark"
                  size={14}
                  color="#4ADE80"
                />
              </View>
            )}
            {university.international_aid && (
              <View style={styles.featuredStat}>
                <MaterialCommunityIcons
                  name="globe"
                  size={14}
                  color="#3B82F6"
                />
              </View>
            )}
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

// Task Card Mini Component
interface TaskCardMiniProps {
  task: Task;
  onPress: () => void;
}

function TaskCardMini({ task, onPress }: TaskCardMiniProps) {
  const isCompleted = task.status === "done";
  const iconColor = isCompleted ? "#4ADE80" : "#5B6AFF";
  const iconName = isCompleted
    ? "check-circle"
    : "checkbox-blank-circle-outline";

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
      <LiquidGlassCard intensity="medium" style={styles.miniCard}>
        <View style={styles.taskContentRow}>
          <MaterialCommunityIcons
            name={iconName as any}
            size={16}
            color={iconColor}
          />
          <View style={styles.taskTextContainer}>
            <Text style={styles.miniCardTitle} numberOfLines={2}>
              {task.title}
            </Text>
            {task.scheduled_date && (
              <Text style={styles.miniCardSubtitle}>
                {new Date(task.scheduled_date).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                })}
              </Text>
            )}
          </View>
        </View>
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

function EmptyStateCard({
  icon,
  title,
  description,
  buttonText,
  onPress,
}: EmptyStateCardProps) {
  return (
    <LiquidGlassCard intensity="light" style={styles.emptyCard}>
      <MaterialCommunityIcons name={icon as any} size={48} color="#666" />
      <Text style={styles.emptyTitle}>{title}</Text>
      <Text style={styles.emptyDescription}>{description}</Text>
      <TouchableOpacity style={styles.emptyButton} onPress={onPress}>
        <Text style={styles.emptyButtonText}>{buttonText}</Text>
      </TouchableOpacity>
    </LiquidGlassCard>
  );
}

const countdownStyles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: spacing.sm,
    gap: spacing.xs,
  },
  text: {
    fontSize: 14,
    color: colors.primary,
    fontWeight: "600",
  },
});

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#000000",
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  loadingText: {
    fontSize: 16,
    color: "#ccc",
    marginTop: 16,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 10,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 24,
  },
  greeting: {
    fontSize: 32,
    fontWeight: "700",
    color: "#fff",
  },
  subGreeting: {
    fontSize: 18,
    color: "#ccc",
    marginTop: 4,
  },
  progressButton: {
    padding: 8,
  },
  circularProgress: {
    alignItems: "center",
    justifyContent: "center",
  },
  progressCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    borderWidth: 4,
    backgroundColor: "rgba(91, 106, 255, 0.1)",
    alignItems: "center",
    justifyContent: "center",
  },
  progressText: {
    fontSize: 16,
    fontWeight: "700",
    color: "#fff",
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.7)",
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  modalContent: {
    backgroundColor: "#1A1A2E",
    borderRadius: 20,
    padding: 24,
    width: "100%",
    maxWidth: 400,
    maxHeight: Dimensions.get("window").height * 0.7,
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 24,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: "700",
    color: "#fff",
  },
  progressOverview: {
    alignItems: "center",
    marginBottom: 24,
  },
  circularProgressLarge: {
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 6,
    backgroundColor: "rgba(91, 106, 255, 0.1)",
    alignItems: "center",
    justifyContent: "center",
  },
  progressTextLarge: {
    fontSize: 32,
    fontWeight: "700",
    color: "#fff",
  },
  progressSubtext: {
    fontSize: 14,
    color: "#ccc",
    marginTop: 4,
  },
  progressList: {
    gap: 16,
    marginBottom: 20,
  },
  progressItem: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    padding: 16,
    borderRadius: 12,
  },
  progressItemLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    flex: 1,
  },
  progressItemInfo: {
    flex: 1,
  },
  progressItemName: {
    fontSize: 16,
    fontWeight: "600",
    color: "#fff",
    marginBottom: 4,
  },
  progressItemWeight: {
    fontSize: 13,
    color: "#999",
  },
  modalTip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    backgroundColor: "rgba(251, 191, 36, 0.1)",
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "rgba(251, 191, 36, 0.3)",
  },
  modalTipText: {
    flex: 1,
    fontSize: 13,
    color: "#FBBF24",
    lineHeight: 18,
  },
  sectionCard: {
    marginBottom: 24,
  },
  // New AI Card Styles - Clean Commercial Design
  aiCard: {
    marginBottom: 20,
    backgroundColor: "rgba(91, 106, 255, 0.08)",
    borderWidth: 1,
    borderColor: "rgba(91, 106, 255, 0.2)",
  },
  aiContent: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 16,
  },
  aiLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    flex: 1,
  },
  aiIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: "rgba(91, 106, 255, 0.15)",
    alignItems: "center",
    justifyContent: "center",
  },
  aiTextContainer: {
    flex: 1,
  },
  aiTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#fff",
    marginBottom: 2,
  },
  aiSubtitle: {
    fontSize: 13,
    color: "#999",
  },
  aiAction: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "rgba(91, 106, 255, 0.15)",
    alignItems: "center",
    justifyContent: "center",
  },
  section: {
    marginBottom: 24,
    width: "100%",
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "700",
    color: "#fff",
  },
  seeAllText: {
    fontSize: 14,
    color: "#5B6AFF",
    fontWeight: "600",
  },
  headerButtons: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  reviewChancesButton: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(91, 106, 255, 0.15)",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    gap: 6,
  },
  reviewChancesButtonText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#5B6AFF",
  },
  horizontalScroll: {
    marginLeft: 0,
    marginRight: -16,
    marginTop: 8,
  },
  miniCard: {
    width: 300,
    padding: 16,
    borderRadius: 12,
  },
  miniCardTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#fff",
    marginBottom: 4,
  },
  miniCardSubtitle: {
    fontSize: 11,
    color: "#ccc",
    marginTop: 4,
  },
  taskContentRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
    width: "100%",
  },
  taskTextContainer: {
    flex: 1,
  },
  mentorAvatar: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: "rgba(91, 106, 255, 0.1)",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 8,
  },
  mentorRating: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    marginTop: 4,
  },
  mentorRatingText: {
    fontSize: 12,
    color: "#FFD700",
    fontWeight: "600",
  },
  activityCard: {
    width: 280,
    padding: 16,
    marginRight: -12,
  },
  activityHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    marginBottom: 8,
  },
  activityTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#fff",
    flex: 1,
  },
  activitySubtitle: {
    fontSize: 13,
    color: "#ccc",
  },
  emptyCard: {
    padding: 0,
    width: "100%",
    alignItems: "center",
  },
  emptyText: {
    fontSize: 16,
    color: "#ccc",
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#fff",
    marginTop: 16,
    marginBottom: 8,
  },
  emptyDescription: {
    fontSize: 14,
    color: "#ccc",
    textAlign: "left",
    marginBottom: 16,
  },
  emptyButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: "#5B6AFF",
    paddingHorizontal: 24,
    paddingVertical: 10,
    borderRadius: 10,
  },
  emptyButtonText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#fff",
    textAlign: "center",
  },
  emptySuggestions: {
    gap: 8,
    marginTop: 16,
  },
  emptySuggestion: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: "rgba(91, 106, 255, 0.1)",
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "rgba(91, 106, 255, 0.3)",
  },
  emptySuggestionText: {
    fontSize: 13,
    color: "#5B6AFF",
    fontWeight: "600",
  },
  placeholderCard: {
    padding: 32,
    alignItems: "center",
    width: "100%",
  },
  placeholderText: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
  },
  universityCardHeader: {
    alignItems: "center",
    gap: 8,
  },
  universityCardInfo: {
    flex: 1,
    alignItems: "center",
  },
  universityCardCost: {
    fontSize: 13,
    fontWeight: "600",
    color: "#5B6AFF",
    marginTop: 4,
  },
  collegeActions: {
    gap: 16,
    width: "100%",
    alignItems: "center",
  },
  editProfileButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(91, 106, 255, 0.15)",
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 10,
    gap: 8,
    borderWidth: 1,
    borderColor: "#5B6AFF",
  },
  editProfileButtonText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#5B6AFF",
  },
  bottomSpacing: {
    height: 100,
  },

  // Essay-specific styles
  essayIconContainer: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: "rgba(91, 106, 255, 0.1)",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 8,
  },
  essayIcon: {
    fontSize: 28,
  },
  miniProgressContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 8,
  },
  miniProgressBackground: {
    flex: 1,
    height: 4,
    backgroundColor: "rgba(0, 0, 0, 0.05)",
    borderRadius: 2,
    marginRight: 8,
  },
  miniProgressFill: {
    height: "100%",
    backgroundColor: "#5B6AFF",
    borderRadius: 2,
  },
  miniProgressText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#5B6AFF",
  },
  miniStatusBadge: {
    position: "absolute",
    top: 8,
    right: 8,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  miniStatusText: {
    fontSize: 10,
    fontWeight: "600",
    color: "#fff",
  },
  addMoreCard: {
    borderStyle: "dashed",
    borderColor: "#5B6AFF",
  },
  addMoreText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#5B6AFF",
    marginTop: 4,
  },

  // Featured University Card styles
  featuredCard: {
    width: 280,
    minHeight: 300,
    borderRadius: 16,
    overflow: "hidden",
    marginRight: 12,
    backgroundColor: "rgba(255, 255, 255, 0.05)",
  },
  featuredImageContainer: {
    width: "100%",
    height: 180,
    position: "relative",
  },
  featuredImage: {
    width: "100%",
    height: "100%",
  },
  featuredLogo: {
    position: "absolute",
    bottom: -30,
    left: 16,
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: "#fff",
    borderWidth: 3,
    borderColor: "rgba(0, 0, 0, 0.5)",
  },
  featuredLogoPlaceholder: {
    position: "absolute",
    bottom: -30,
    left: 16,
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: "rgba(91, 106, 255, 0.1)",
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 3,
    borderColor: "rgba(0, 0, 0, 0.5)",
  },
  featuredNoPhotoContainer: {
    width: "100%",
    height: 180,
    backgroundColor: "rgba(91, 106, 255, 0.05)",
    justifyContent: "center",
    alignItems: "center",
  },
  featuredLargeLogo: {
    width: 80,
    height: 80,
  },
  featuredLargeLogoPlaceholder: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: "rgba(91, 106, 255, 0.1)",
    justifyContent: "center",
    alignItems: "center",
  },
  featuredPlaceholderText: {
    fontSize: 11,
    color: "#5B6AFF",
    fontWeight: "600",
    marginTop: 4,
    textAlign: "center",
  },
  featuredInfo: {
    padding: 16,
    paddingTop: 36,
  },
  featuredInfoNoPhoto: {
    padding: 16,
    paddingTop: 16,
  },
  featuredName: {
    fontSize: 16,
    fontWeight: "700",
    color: "#fff",
    marginBottom: 4,
  },
  featuredLocation: {
    fontSize: 13,
    color: "#999",
    marginBottom: 12,
  },
  featuredStats: {
    flexDirection: "row",
    gap: 12,
  },
  featuredStat: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  featuredStatText: {
    fontSize: 13,
    color: "#5B6AFF",
    fontWeight: "600",
  },

  // Smaller edit profile button
  editProfileButtonSmall: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(91, 106, 255, 0.1)",
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
    gap: 6,
    borderWidth: 1,
    borderColor: "#5B6AFF",
    alignSelf: "center",
  },
  editProfileTextSmall: {
    fontSize: 13,
    fontWeight: "600",
    color: "#5B6AFF",
  },

  // Create University Profile - minimal list item styles (full width)
  createProfileListItem: {
    minWidth: "110%",
    padding: 16,
    marginLeft:'-5%',
    marginTop: 0,
  },
  createProfileListItemContent: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  createProfileListTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#fff",
    flex: 1,
  },
  createProfileListButton: {
    backgroundColor: "#5B6AFF",
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 10,
  },
  createProfileListButtonText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#fff",
  },

  // Upcoming Meeting Card Styles
  upcomingMeetingCard: {
    marginBottom: spacing.lg,
    padding: spacing.lg,
    borderWidth: 2,
    borderColor: colors.primary + "40",
    backgroundColor: colors.primary + "08",
  },
  meetingHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.md,
  },
  meetingIconContainer: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary + "20",
    alignItems: "center",
    justifyContent: "center",
    marginRight: spacing.md,
  },
  meetingHeaderContent: {
    flex: 1,
  },
  meetingTitle: {
    fontSize: 20,
    fontWeight: "700",
    color: "#fff",
    marginBottom: 2,
  },
  meetingMentor: {
    fontSize: 15,
    color: "#999",
  },
  joinButtonContainer: {
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  joinButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderRadius: 12,
    backgroundColor: colors.primary,
  },
  joinButtonText: {
    fontSize: 15,
    fontWeight: "700",
    color: "#fff",
  },
  meetingDetails: {
    gap: spacing.xs,
  },
  meetingDetailRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  meetingDetailText: {
    fontSize: 15,
    color: "#fff",
  },
  meetingTopicBadge: {
    alignSelf: "flex-start",
    marginTop: spacing.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    backgroundColor: "rgba(91, 106, 255, 0.15)",
    borderRadius: 8,
  },
  meetingTopicText: {
    fontSize: 13,
    color: "#999",
    fontWeight: "600",
  },
});
