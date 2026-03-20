import { Tabs, useRouter } from "expo-router";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { useTranslation } from "react-i18next";
import { useEffect, useState } from "react";
import { Platform, StyleSheet, View } from "react-native";
import { BlurView } from "expo-blur";
import AsyncStorage from "@react-native-async-storage/async-storage";
import notificationService from "@/services/notifications";
import { timezoneService } from "@/utils/timezone";
import { authAPI, todosAPI } from "@/services/api";
import type { Notification, NotificationResponse } from "expo-notifications";
import { syncTaskNotifications } from "@/utils/taskNotifications";
import { colors, spacing } from "@/theme";

export default function MainLayout() {
  const { t } = useTranslation();
  const router = useRouter();
  const [isGuest, setIsGuest] = useState(false);

  useEffect(() => {
    // Check if user is in guest mode
    const checkGuestMode = async () => {
      const guestMode = await AsyncStorage.getItem("isGuest");
      setIsGuest(guestMode === "true");
    };
    checkGuestMode();
  }, []);

  useEffect(() => {
    // Initialize services when user enters main app (authenticated)
    const initializeServices = async () => {
      // Skip initialization for guest users
      const guestMode = await AsyncStorage.getItem("isGuest");
      if (guestMode === "true") {
        return;
      }

      // 1. Sync timezone with backend
      try {
        const deviceTimezone = timezoneService.getDeviceTimezone();
        console.log("Device timezone detected:", deviceTimezone);

        await authAPI.updateTimezone(deviceTimezone);
        await timezoneService.saveTimezone(deviceTimezone);
        console.log("Timezone synced with backend:", deviceTimezone);
      } catch (error) {
        console.error("Error syncing timezone:", error);
      }

      // 2. Initialize notification service
      try {
        console.log("Initializing push notifications...");

        const success = await notificationService.initialize(
          // Handler for notifications received while app is open
          (notification: Notification) => {
            console.log("Notification received in foreground:", notification);
            // You can show a custom in-app notification UI here if needed
          },
          // Handler for user tapping on notifications
          (response: NotificationResponse) => {
            console.log("User interacted with notification:", response);

            const data = response.notification.request.content.data;

            // Navigate based on notification type
            if (data.type === "task_reminder" || data.type === "deadline") {
              if (data.task_id) {
                // Navigate to todos screen
                router.push("/todos");
              }
            } else if (data.type === "daily_pulse") {
              // Navigate to analytics/daily pulse
              router.push("/analytics");
            } else if (data.type === "ai_motivation") {
              // Navigate to home/chat
              router.push("/home");
            }
          },
        );

        if (success) {
          console.log("Push notifications initialized successfully");

          // Sync local notifications with today's and upcoming tasks
          try {
            const synced = await syncTaskNotifications(async () => {
              // Fetch upcoming tasks (today and future)
              const response = await todosAPI.list(undefined, "ready");
              return response;
            });
            console.log(`Synced ${synced} task notifications on app start`);
          } catch (syncError) {
            console.error("Error syncing task notifications:", syncError);
          }
        } else {
          console.warn("Failed to initialize push notifications");
        }
      } catch (error) {
        console.error("Error initializing notifications:", error);
      }
    };

    initializeServices();

    // Cleanup listeners on unmount
    return () => {
      notificationService.removeNotificationListeners();
    };
  }, [router]);

  return (
    <>
      <Tabs
        screenOptions={{
          headerShown: false,
          tabBarStyle: {
            position: "absolute",
            backgroundColor: "transparent",
            borderTopWidth: 0,
            elevation: 50,
            zIndex: 50,
            height: Platform.OS === "ios" ? 60 : 55,
            maxHeight: 60,
            paddingBottom: Platform.OS === "ios" ? 8 : 5,
            paddingTop: 5,
          },
          tabBarBackground: () => (
            <View style={StyleSheet.absoluteFill}>
              {/* Liquid Glass progressive blur */}
              <BlurView
                intensity={100}
                tint="dark"
                style={[
                  StyleSheet.absoluteFill,
                  { backgroundColor: "rgba(0, 0, 0, 0.8)" },
                ]}
              />
              {/* Top glass border with subtle shimmer */}
              <View
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  right: 0,
                  height: 1,
                  backgroundColor: "rgba(255, 255, 255, 0.12)",
                  shadowColor: colors.primary,
                  shadowOpacity: 0.1,
                  shadowRadius: 2,
                  shadowOffset: { width: 0, height: -1 },
                }}
              />
            </View>
          ),
          tabBarActiveTintColor: colors.primary,
          tabBarInactiveTintColor: colors.textSecondary,
          tabBarLabelStyle: {
            fontSize: 9,
            fontWeight: "600",
            marginTop: 2,
            marginBottom: 0,
          },
          tabBarIconStyle: {
            marginBottom: 0,
            marginTop: 0,
          },
        }}
      >
        <Tabs.Screen
          name="demo"
          options={{
            href: isGuest ? "/demo" : null,
            title: "Preview",
            tabBarIcon: ({ color, size }) => (
              <MaterialCommunityIcons
                name="eye-outline"
                size={size}
                color={color}
              />
            ),
          }}
        />
        <Tabs.Screen
          name="home"
          options={{
            title: "Home",
            tabBarIcon: ({ color, size }) => (
              <MaterialCommunityIcons name="home" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="chat"
          options={{
            href: null,
          }}
        />
        <Tabs.Screen
          name="index"
          options={{
            href: null,
          }}
        />
        <Tabs.Screen
          name="todos"
          options={{
            title: t("navigation.tasks"),
            tabBarIcon: ({ color, size }) => (
              <MaterialCommunityIcons
                name="check-circle"
                size={size}
                color={color}
              />
            ),
          }}
        />
        <Tabs.Screen
          name="calendar"
          options={{
            href: null, // Hidden - merged into todos
          }}
        />
        <Tabs.Screen
          name="vision"
          options={{
            href: null, // Hidden - replaced by goals
          }}
        />
        <Tabs.Screen
          name="goals"
          options={{
            href: null, // Hide from bottom tab - now integrated into Tasks screen
          }}
        />
        <Tabs.Screen
          name="community"
          options={{
            href: isGuest ? null : "/community",
            title: t("navigation.community"),
            tabBarIcon: ({ color, size }) => (
              <MaterialCommunityIcons
                name="account-group"
                size={size}
                color={color}
              />
            ),
          }}
        />
        <Tabs.Screen
          name="mentors/index"
          options={{
            href: isGuest ? null : "/mentors",
            title: "Find Mentor",
            tabBarIcon: ({ color, size }) => (
              <MaterialCommunityIcons
                name="account-search"
                size={size}
                color={color}
              />
            ),
          }}
        />
        <Tabs.Screen
          name="mentors/[id]"
          options={{
            href: null,
          }}
        />
        <Tabs.Screen
          name="mentorship-bookings"
          options={{
            href: null,
          }}
        />
        <Tabs.Screen
          name="mentor-dashboard"
          options={{
            href: null, // Hide from tab bar - accessible from mentor profile
          }}
        />
        <Tabs.Screen
          name="essays"
          options={{
            href: null, // Hide from tab bar - accessible from Home
          }}
        />
        <Tabs.Screen
          name="mentor-profile"
          options={{
            href: null, // Hide from tab bar - accessible from Profile
          }}
        />
        <Tabs.Screen
          name="profile"
          options={{
            href: isGuest ? null : "/profile",
            title: t("navigation.profile"),
            tabBarIcon: ({ color, size }) => (
              <MaterialCommunityIcons
                name="account"
                size={size}
                color={color}
              />
            ),
          }}
        />
        <Tabs.Screen
          name="profile-info"
          options={{
            href: null, // Hide from tab bar
          }}
        />
        <Tabs.Screen
          name="analytics"
          options={{
            href: null, // Hide from tab bar
          }}
        />
        <Tabs.Screen
          name="weekly-review"
          options={{
            href: null, // Hide from tab bar
          }}
        />
        <Tabs.Screen
          name="notification-settings"
          options={{
            href: null, // Hide from tab bar
          }}
        />
        <Tabs.Screen
          name="performance"
          options={{
            href: null, // Hide from tab bar - access from analytics
          }}
        />
        <Tabs.Screen
          name="search"
          options={{
            href: null, // Hide from tab bar - not a bottom tab
          }}
        />
        <Tabs.Screen
          name="messages"
          options={{
            href: null, // Hide from tab bar - not a bottom tab
          }}
        />
        <Tabs.Screen
          name="community-approvals"
          options={{
            href: null, // Hide from bottom tab - admin only, accessible from Profile
          }}
        />
      </Tabs>
    </>
  );
}
