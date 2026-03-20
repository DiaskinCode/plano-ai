/**
 * FeaturedMentors Component
 *
 * Horizontal carousel displaying 2-3 featured mentors
 * - Plan-based blur effect for Basic users
 * - "View More" button to navigate to full mentors page
 * - Staggered fade-in animation on load
 */

import React, { useState, useEffect } from "react";
import {
  View,
  StyleSheet,
  TouchableOpacity,
  Text,
  ScrollView,
} from "react-native";
import { useRouter } from "expo-router";
import { MentorCard } from "../mentors/MentorCard";
import { MentorBlur } from "../mentors/MentorBlur";
import { Mentor } from "@/types/mentor";

interface FeaturedMentorsProps {
  mentors: Mentor[];
  userPlan: "basic" | "pro" | "premium";
}

export const FeaturedMentors: React.FC<FeaturedMentorsProps> = ({
  mentors,
  userPlan,
}) => {
  const router = useRouter();
  const [visibleCards, setVisibleCards] = useState<boolean[]>([]);

  useEffect(() => {
    // Staggered fade-in animation
    const delays = mentors.map((_, index) => {
      return setTimeout(() => {
        setVisibleCards((prev) => {
          const newVisible = [...prev];
          newVisible[index] = true;
          return newVisible;
        });
      }, index * 100);
    });

    return () => delays.forEach((timeout) => clearTimeout(timeout));
  }, [mentors]);

  if (!mentors || mentors.length === 0) {
    return null;
  }

  const displayMentors = mentors.slice(0, 3); // Max 3 mentors

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Featured Mentors</Text>
        <TouchableOpacity
          style={styles.viewMoreButton}
          onPress={() => router.push("/mentors" as any)}
        >
          <Text style={styles.viewMoreText}>View More</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
        decelerationRate="fast"
        snapToInterval={136} // Card width (120) + gap (16)
        snapToAlignment="start"
      >
        {displayMentors.map((mentor, index) => {
          const isVisible = visibleCards[index];

          return (
            <View
              key={mentor.id}
              style={[styles.cardWrapper, !isVisible && styles.cardHidden]}
            >
              {userPlan === "basic" ? (
                <MentorBlur
                  userPlan={userPlan}
                  requiredPlan="pro"
                  onUpgradePress={() => {
                    // TODO: Open upgrade modal
                    console.log("Upgrade pressed");
                  }}
                >
                  <MentorCard mentor={mentor} userPlan={userPlan} />
                </MentorBlur>
              ) : (
                <MentorCard
                  mentor={mentor}
                  userPlan={userPlan}
                  onPress={() => router.push(`/mentors/${mentor.id}` as any)}
                />
              )}
            </View>
          );
        })}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#1A1A1A",
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#2A2A2A",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: "700",
    color: "#ECECEC",
  },
  viewMoreButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: "#2A2A2A",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#3E3E3E",
  },
  viewMoreText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#3B82F6",
  },
  scrollContent: {
    flexDirection: "row",
    gap: 16,
  },
  cardWrapper: {
    opacity: 1,
  },
  cardHidden: {
    opacity: 0,
  },
});
