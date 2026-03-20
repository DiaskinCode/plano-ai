/**
 * Mentorship API Service
 *
 * API client for mentorship features
 * Matches the simplified V1 backend API
 */

import AsyncStorage from "@react-native-async-storage/async-storage";
import { calendarService } from "./calendarService";
import {
  Mentor,
  MentorAvailability,
  MentorBooking,
  CreateBookingRequest,
  MentorReviewRequest,
  CreateReviewRequest,
  MentorReviewResponse,
  PlanReviewSubmission,
  EssayReviewSubmission,
  ApplySuggestionsResult,
  PaginatedResponse,
  MentorAvailabilityRule,
  MentorListParams,
  TimeSlot,
} from "../types/mentor";

// Re-export TimeSlot for convenience
export type { TimeSlot };

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || "http://192.168.0.210:8000";

console.log("[mentorship.ts] API_BASE_URL =", API_BASE_URL);

/**
 * Get auth token
 */
async function getAuthToken(): Promise<string | null> {
  return await AsyncStorage.getItem("access_token");
}

/**
 * Set auth token
 */
async function setAuthToken(token: string): Promise<void> {
  await AsyncStorage.setItem("access_token", token);
}

/**
 * Make authenticated API request
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const token = await getAuthToken();

  const url = `${API_BASE_URL}${endpoint}`;
  console.log(`[API] ${options.method || "GET"} ${url}`);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ error: "Unknown error" }));
      console.error(`[API Error] ${url}`, error);
      throw new Error(error.error || error.detail || "API request failed");
    }

    return response.json();
  } catch (error: any) {
    if (error.name === 'AbortError') {
      console.error(`[API Timeout] ${url}`);
      throw new Error("Request timed out. Please check your connection.");
    }
    throw error;
  }
}

/**
 * Get auth headers
 */
function getAuthHeaders(): Record<string, string> {
  // Note: This won't work directly - need to get token from storage first
  // In practice, you'd pass the token or use a different pattern
  return {
    "Content-Type": "application/json",
  };
}

// ==================== MENTOR PUBLIC ENDPOINTS ====================

/**
 * List mentors (public)
 */
export async function listMentors(
  params?: MentorListParams,
): Promise<PaginatedResponse<Mentor>> {
  const queryParams = new URLSearchParams();

  if (params?.featured) queryParams.append("featured", "true");
  if (params?.expertise) queryParams.append("expertise", params.expertise);
  if (params?.min_rating)
    queryParams.append("min_rating", params.min_rating.toString());
  if (params?.search) queryParams.append("search", params.search);
  if (params?.ordering) queryParams.append("ordering", params.ordering);
  if (params?.page) queryParams.append("page", params.page.toString());
  if (params?.page_size)
    queryParams.append("page_size", params.page_size.toString());

  const queryString = queryParams.toString();
  return apiRequest<PaginatedResponse<Mentor>>(
    `/api/mentors/${queryString ? `?${queryString}` : ""}`,
  );
}

/**
 * Get mentor details
 */
export async function getMentor(id: number): Promise<Mentor> {
  return apiRequest<Mentor>(`/api/mentors/${id}/`);
}

/**
 * Get mentor availability
 */
export async function getMentorAvailability(
  id: number,
  startDate: string,
  endDate: string,
  duration: number = 60,
): Promise<MentorAvailability> {
  const queryParams = new URLSearchParams({
    from: startDate,
    to: endDate,
    duration: duration.toString(),
  });

  return apiRequest<MentorAvailability>(
    `/api/mentors/${id}/availability/?${queryParams.toString()}`,
  );
}

/**
 * Book a mentor session
 */
export async function bookSession(
  mentorId: number,
  booking: CreateBookingRequest,
): Promise<MentorBooking> {
  return apiRequest<MentorBooking>(`/api/mentors/${mentorId}/book/`, {
    method: "POST",
    body: JSON.stringify(booking),
  });
}

// ==================== MENTOR SELF-SERVICE ====================

/**
 * Get my mentor profile
 */
export async function getMyMentorProfile(): Promise<Mentor> {
  return apiRequest<Mentor>("/api/mentors/me/");
}

/**
 * Update my mentor profile
 */
export async function updateMyMentorProfile(
  data: Partial<Mentor>,
): Promise<Mentor> {
  return apiRequest<Mentor>("/api/mentors/me/", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Get my availability rules
 */
export async function getMyAvailabilityRules(): Promise<
  MentorAvailabilityRule[]
> {
  return apiRequest<MentorAvailabilityRule[]>("/api/mentors/me/availability/");
}

/**
 * Create availability rule
 */
export async function createAvailabilityRule(
  rule: Omit<MentorAvailabilityRule, "id" | "mentor">,
): Promise<MentorAvailabilityRule> {
  return apiRequest<MentorAvailabilityRule>("/api/mentors/me/availability/", {
    method: "POST",
    body: JSON.stringify(rule),
  });
}

/**
 * Delete availability rule
 */
export async function deleteAvailabilityRule(id: number): Promise<void> {
  await apiRequest<void>(`/api/mentors/me/availability/${id}/`, {
    method: "DELETE",
  });
}

// ==================== BOOKINGS ====================

/**
 * Get my bookings
 */
export async function getMyBookings(): Promise<MentorBooking[]> {
  return apiRequest<MentorBooking[]>("/api/mentorship/bookings/");
}

/**
 * Confirm booking (mentor only)
 */
export async function confirmBooking(
  bookingId: number,
): Promise<MentorBooking> {
  const booking = await apiRequest<MentorBooking>(
    `/api/mentorship/bookings/${bookingId}/confirm/`,
    {
      method: "POST",
    },
  );

  // Add to calendar after confirmation
  try {
    await calendarService.addMeetingToCalendar({
      id: booking.id,
      title: `Mentor Session: ${booking.mentor_title || "Mentor"}`,
      mentorName: booking.mentor_title || "Mentor",
      startDate: new Date(booking.start_at_utc),
      endDate: new Date(booking.end_at_utc),
      meetingUrl: booking.meeting_url,
      topic: booking.topic,
      notes: booking.student_notes,
    });
    console.log(`Added booking ${booking.id} to calendar`);
  } catch (error) {
    console.error(`Failed to add booking ${booking.id} to calendar:`, error);
    // Don't throw - calendar sync is optional
  }

  return booking;
}

/**
 * Cancel booking
 */
export async function cancelBooking(bookingId: number): Promise<MentorBooking> {
  const booking = await apiRequest<MentorBooking>(
    `/api/mentorship/bookings/${bookingId}/cancel/`,
    {
      method: "POST",
    },
  );

  // Remove from calendar after cancellation
  try {
    await calendarService.removeMeetingFromCalendar(bookingId);
    console.log(`Removed booking ${bookingId} from calendar`);
  } catch (error) {
    console.error(`Failed to remove booking ${bookingId} from calendar:`, error);
    // Don't throw - calendar sync is optional
  }

  return booking;
}

/**
 * Complete booking (mentor only)
 */
export async function completeBooking(
  bookingId: number,
  mentorSummary: string,
  actionItems: any[] = [],
): Promise<MentorBooking> {
  return apiRequest<MentorBooking>(
    `/api/mentorship/bookings/${bookingId}/complete/`,
    {
      method: "POST",
      body: JSON.stringify({
        mentor_summary: mentorSummary,
        action_items: actionItems,
      }),
    },
  );
}

/**
 * Submit booking rating (student only)
 */
export async function rateBooking(
  bookingId: number,
  rating: number,
  reviewText?: string,
): Promise<MentorBooking> {
  return apiRequest<MentorBooking>(
    `/api/mentorship/bookings/${bookingId}/rate/`,
    {
      method: "POST",
      body: JSON.stringify({
        rating,
        review_text: reviewText,
      }),
    },
  );
}

// ==================== REVIEWS ====================

/**
 * Create review request (plan or essay)
 */
export async function createReviewRequest(
  request: CreateReviewRequest,
): Promise<MentorReviewRequest> {
  return apiRequest<MentorReviewRequest>("/api/mentorship/reviews/request/", {
    method: "POST",
    body: JSON.stringify({
      mentor_id: request.mentor_id,
      request_type: request.request_type,
      goal_spec_id: request.goal_spec_id,
      essay_project_id: request.essay_project_id,
      questions: request.questions,
      price_credits: request.price_credits || 0,
    }),
  });
}

/**
 * Get my review requests
 */
export async function getMyReviews(): Promise<MentorReviewRequest[]> {
  return apiRequest<MentorReviewRequest[]>("/api/mentorship/reviews/");
}

/**
 * Get review request details
 */
export async function getReviewRequest(
  id: number,
): Promise<MentorReviewRequest> {
  return apiRequest<MentorReviewRequest>(`/api/mentorship/reviews/${id}/`);
}

/**
 * Submit plan review response (mentor only)
 */
export async function submitPlanReview(
  reviewId: number,
  review: PlanReviewSubmission,
): Promise<MentorReviewResponse> {
  return apiRequest<MentorReviewResponse>(
    `/api/mentorship/reviews/${reviewId}/submit/`,
    {
      method: "POST",
      body: JSON.stringify(review),
    },
  );
}

/**
 * Submit essay review response (mentor only)
 */
export async function submitEssayReview(
  reviewId: number,
  review: EssayReviewSubmission,
): Promise<MentorReviewResponse> {
  return apiRequest<MentorReviewResponse>(
    `/api/mentorship/reviews/${reviewId}/submit/`,
    {
      method: "POST",
      body: JSON.stringify(review),
    },
  );
}

/**
 * Apply mentor suggestions (student only)
 */
export async function applyReviewSuggestions(
  reviewId: number,
): Promise<ApplySuggestionsResult> {
  return apiRequest<ApplySuggestionsResult>(
    `/api/mentorship/reviews/${reviewId}/apply/`,
    {
      method: "POST",
    },
  );
}

// ==================== HELPER FUNCTIONS ====================

/**
 * Format time slot for display
 */
export function formatTimeSlot(
  slot: {
    start_at_utc: string;
    duration_minutes: number;
  },
  timezone: string = "UTC",
): string {
  const startDate = new Date(slot.start_at_utc);
  const endDate = new Date(startDate.getTime() + slot.duration_minutes * 60000);

  const formatter = new Intl.DateTimeFormat("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "numeric",
    timeZone: timezone,
  });

  return formatter.format(startDate);
}

/**
 * Get day name from day_of_week
 */
export function getDayName(dayOfWeek: number): string {
  const days = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
  ];
  return days[dayOfWeek];
}

/**
 * Convert minutes to time string
 */
export function minutesToTime(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours}:${mins.toString().padStart(2, "0")}`;
}

/**
 * Convert time string to minutes
 */
export function timeToMinutes(time: string): number {
  const [hours, minutes] = time.split(":").map(Number);
  return hours * 60 + minutes;
}
