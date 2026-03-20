/**
 * Mentor Types
 *
 * Type definitions for mentor-related features
 * Matches the simplified V1 backend API
 */

/**
 * Verification status types
 */
export type VerificationStatus = "pending" | "approved" | "rejected" | "suspended";

/**
 * Mentor profile interface
 */
export interface Mentor {
  id: number;
  user_id?: number;
  title: string; // e.g., "Dr. Sarah Chen"
  bio: string;
  photo_url?: string;
  education?: string;
  expertise_areas: string[]; // e.g., ["Essay Writing", "Ivy League"]
  hourly_rate_credits: number; // Platform credits
  timezone: string; // e.g., "America/New_York"
  meeting_link?: string; // Google Meet/Zoom link

  // Verification fields
  verification_status: VerificationStatus;
  verification_video_url?: string;
  verification_submitted_at?: string;
  verification_reviewed_at?: string;
  verification_notes?: string;
  flag_count?: number;
  flagged_at?: string;

  // Legacy (kept for backward compatibility)
  is_verified: boolean;
  is_active: boolean;
  rating: number; // 0-5 average rating
  total_sessions: number; // Total sessions conducted
  created_at: string;
}

/**
 * Availability rule (recurring weekly)
 */
export interface MentorAvailabilityRule {
  id: number;
  mentor: number; // Mentor ID
  day_of_week: number; // 0-6 (Monday-Sunday)
  day_name?: string; // "Monday", "Tuesday", etc.
  start_minute: number; // Minutes from midnight (e.g., 840 = 14:00)
  end_minute: number; // Minutes from midnight (e.g., 960 = 16:00)
  is_active: boolean;
}

/**
 * Generated time slot for booking
 */
export interface TimeSlot {
  start_at_utc: string; // ISO 8601 datetime string
  end_at_utc: string; // ISO 8601 datetime string
  duration_minutes: number; // 15, 30, 45, or 60
}

/**
 * Availability response
 */
export interface MentorAvailability {
  mentor_timezone: string;
  slots: TimeSlot[];
}

/**
 * Mentor booking
 */
export interface MentorBooking {
  id: number;
  mentor: number; // Mentor ID
  mentor_title?: string; // Denormalized for convenience
  student: number; // User ID
  student_email?: string; // Denormalized for convenience
  start_at_utc: string;
  end_at_utc: string;
  duration_minutes: number; // 15, 30, 45, or 60
  status: "requested" | "confirmed" | "completed" | "cancelled";
  topic?: string; // "Essay Review", "Plan Validation"
  student_notes?: string;
  meeting_url?: string;
  mentor_summary?: string; // Filled by mentor after session
  action_items?: any[]; // Filled by mentor after session
  rating?: number; // 1-5 (filled by student after session)
  review_text?: string; // Filled by student after session

  // Flagging fields
  is_flagged?: boolean;
  flag_reason?: string;
  flagged_at?: string;

  created_at: string;
  confirmed_at?: string;
  completed_at?: string;
}

/**
 * Create booking request
 */
export interface CreateBookingRequest {
  start_at: string; // ISO 8601 datetime string (UTC)
  duration_minutes: number; // 15, 30, 45, or 60
  notes?: string;
  topic?: string;
}

/**
 * Review request (unified for plans and essays)
 */
export interface MentorReviewRequest {
  id: number;
  mentor: number; // Mentor ID
  mentor_title?: string;
  student: number; // User ID
  student_email?: string;
  request_type: "plan" | "essay";
  goal_spec?: number; // GoalSpec ID (for plan reviews)
  essay_project?: number; // EssayProject ID (for essay reviews)
  status: "pending" | "in_review" | "done";
  student_questions?: string;
  price_credits: number;
  created_at: string;
  responded_at?: string;
}

/**
 * Create review request
 */
export interface CreateReviewRequest {
  mentor_id: number;
  request_type: "plan" | "essay";
  goal_spec_id?: number; // Required for plan reviews
  essay_project_id?: number; // Required for essay reviews
  questions?: string;
  price_credits?: number;
}

/**
 * Plan review submission (human-friendly)
 */
export interface PlanReviewSubmission {
  overall_comment: string;
  verdict: "approved" | "approved_with_changes" | "rejected";
  top_risks?: string[];
  next_steps?: string[];
  suggestions?: PlanSuggestion[];
}

/**
 * Plan suggestion types
 */
export type PlanSuggestion =
  | {
      task_id: number;
      type: "change_deadline";
      new_due_date: string; // YYYY-MM-DD
      note?: string;
    }
  | {
      type: "add_task";
      title: string;
      due_date: string; // YYYY-MM-DD
      note?: string;
    };

/**
 * Essay review submission (human-friendly)
 */
export interface EssayReviewSubmission {
  overall_comment: string;
  strengths?: string[];
  improvements?: string[];
  rewrite_suggestions?: RewriteSuggestion[];
  scores?: {
    content?: number; // 1-10
    structure?: number; // 1-10
    voice?: number; // 1-10
  };
}

/**
 * Rewrite suggestion for essay
 */
export interface RewriteSuggestion {
  section: string; // e.g., "conclusion", "intro"
  note: string;
}

/**
 * Review response
 */
export interface MentorReviewResponse {
  id: number;
  request: number; // ReviewRequest ID
  mentor_title?: string;
  overall_comment: string;
  payload_json: any; // Structured feedback (differs by type)
  created_at: string;
}

/**
 * Apply suggestions result
 */
export interface ApplySuggestionsResult {
  applied: AppliedChange[];
  errors: string[];
  total_applied: number;
  total_errors: number;
}

/**
 * Applied change summary
 */
export type AppliedChange =
  | {
      type: "edit_task";
      task_id: number;
      task_title: string;
      old_values: Record<string, any>;
      new_values: Record<string, any>;
      note?: string;
    }
  | {
      type: "add_task";
      task_id: number;
      task_title: string;
      note?: string;
    };

/**
 * Mentor list query parameters
 */
export interface MentorListParams {
  featured?: boolean;
  expertise?: string;
  min_rating?: number;
  search?: string;
  ordering?: "rating" | "sessions" | "price_asc" | "price_desc";
  page?: number;
  page_size?: number;
}

/**
 * Paginated response
 */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
