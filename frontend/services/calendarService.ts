import * as Calendar from 'expo-calendar';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface MeetingEvent {
  id: number;
  title: string;
  mentorName: string;
  startDate: Date;
  endDate: Date;
  meetingUrl?: string;
  topic?: string;
  location?: string;
  notes?: string;
}

class CalendarService {
  private calendarId: string | null = null;

  /**
   * Initialize calendar service and request permissions
   */
  async initialize(): Promise<boolean> {
    try {
      // Check if platform supports calendar
      if (Platform.OS === 'web') {
        console.warn('Calendar integration not available on web');
        return false;
      }

      // Request calendar permissions
      const { status } = await Calendar.requestCalendarPermissionsAsync();

      if (status !== 'granted') {
        console.warn('Calendar permission not granted');
        return false;
      }

      // Get or create default calendar
      await this.getOrCreateDefaultCalendar();

      return true;
    } catch (error) {
      console.error('Error initializing calendar service:', error);
      return false;
    }
  }

  /**
   * Get or create default calendar for the app
   */
  private async getOrCreateDefaultCalendar(): Promise<string | null> {
    try {
      const calendars = await Calendar.getCalendarsAsync(Calendar.EntityTypes.EVENT);

      // Try to find existing app calendar
      let appCalendar = calendars.find(
        (cal) => cal.title === 'PathAI Mentoring' && cal.sourceType === Calendar.SourceType.LOCAL
      );

      if (appCalendar) {
        this.calendarId = appCalendar.id;
        console.log('Found existing calendar:', appCalendar.id);
        return this.calendarId;
      }

      // Create new calendar
      const newCalendarId = await Calendar.createCalendarAsync({
        title: 'PathAI Mentoring',
        color: '#3B82F6',
        entityType: Calendar.EntityTypes.EVENT,
        sourceId: calendars[0]?.sourceId,
        sourceType: Calendar.SourceType.LOCAL,
        name: 'PathAI Mentoring',
        ownerAccount: 'PathAI',
        accessLevel: Calendar.CalendarAccessLevel.OWNER,
      });

      this.calendarId = newCalendarId;
      console.log('Created new calendar:', newCalendarId);
      await AsyncStorage.setItem('pathai_calendar_id', newCalendarId);

      return newCalendarId;
    } catch (error) {
      console.error('Error getting/creating calendar:', error);
      return null;
    }
  }

  /**
   * Add a mentorship meeting to calendar
   * @param meeting - Meeting details
   * @returns eventId or null if failed
   */
  async addMeetingToCalendar(meeting: MeetingEvent): Promise<string | null> {
    try {
      if (!this.calendarId) {
        await this.initialize();
        if (!this.calendarId) {
          throw new Error('Calendar not initialized');
        }
      }

      // Create event details
      const eventDetails: Calendar.Event = {
        title: meeting.title,
        startDate: meeting.startDate,
        endDate: meeting.endDate,
        location: meeting.meetingUrl || meeting.location || undefined,
        notes: this.createEventNotes(meeting),
        url: meeting.meetingUrl,
      };

      // Create event
      const eventId = await Calendar.createEventAsync(this.calendarId, eventDetails);

      // Store event ID for later cancellation
      await AsyncStorage.setItem(`meeting_calendar_${meeting.id}`, eventId);

      console.log(`Added meeting ${meeting.id} to calendar:`, eventId);
      return eventId;
    } catch (error) {
      console.error(`Error adding meeting ${meeting.id} to calendar:`, error);
      return null;
    }
  }

  /**
   * Create formatted notes for calendar event
   */
  private createEventNotes(meeting: MeetingEvent): string {
    let notes = `Mentor Session with ${meeting.mentorName}\n`;

    if (meeting.topic) {
      notes += `\nTopic: ${meeting.topic}\n`;
    }

    if (meeting.meetingUrl) {
      notes += `\nMeeting Link: ${meeting.meetingUrl}\n`;
    }

    notes += `\n---\nScheduled via PathAI`;

    return notes;
  }

  /**
   * Remove a meeting from calendar
   * @param bookingId - Booking ID
   */
  async removeMeetingFromCalendar(bookingId: number): Promise<boolean> {
    try {
      // Get stored event ID
      const eventId = await AsyncStorage.getItem(`meeting_calendar_${bookingId}`);

      if (!eventId) {
        console.warn(`No calendar event found for booking ${bookingId}`);
        return false;
      }

      if (!this.calendarId) {
        // Try to get calendar ID from storage
        const storedCalendarId = await AsyncStorage.getItem('pathai_calendar_id');
        if (storedCalendarId) {
          this.calendarId = storedCalendarId;
        } else {
          throw new Error('Calendar not initialized');
        }
      }

      // Remove event
      await Calendar.deleteEventAsync(this.calendarId, eventId);

      // Remove from storage
      await AsyncStorage.removeItem(`meeting_calendar_${bookingId}`);

      console.log(`Removed meeting ${bookingId} from calendar`);
      return true;
    } catch (error) {
      console.error(`Error removing meeting ${bookingId} from calendar:`, error);
      return false;
    }
  }

  /**
   * Update a meeting in calendar
   * @param bookingId - Booking ID
   * @param meeting - Updated meeting details
   */
  async updateMeetingInCalendar(bookingId: number, meeting: MeetingEvent): Promise<string | null> {
    try {
      // Remove old event
      await this.removeMeetingFromCalendar(bookingId);

      // Add new event
      return await this.addMeetingToCalendar(meeting);
    } catch (error) {
      console.error(`Error updating meeting ${bookingId} in calendar:`, error);
      return null;
    }
  }

  /**
   * Check if calendar permission is granted
   */
  async checkPermission(): Promise<boolean> {
    try {
      const { status } = await Calendar.getCalendarPermissionsAsync();
      return status === 'granted';
    } catch (error) {
      console.error('Error checking calendar permission:', error);
      return false;
    }
  }

  /**
   * Request calendar permission
   */
  async requestPermission(): Promise<boolean> {
    try {
      const { status } = await Calendar.requestCalendarPermissionsAsync();
      return status === 'granted';
    } catch (error) {
      console.error('Error requesting calendar permission:', error);
      return false;
    }
  }

  /**
   * Get all calendar events for debugging
   */
  async getCalendarEvents(): Promise<Calendar.Event[]> {
    try {
      if (!this.calendarId) {
        await this.initialize();
      }

      if (!this.calendarId) {
        return [];
      }

      const startDate = new Date();
      const endDate = new Date();
      endDate.setMonth(endDate.getMonth() + 1);

      const events = await Calendar.getEventsAsync([this.calendarId], startDate, endDate);
      return events;
    } catch (error) {
      console.error('Error getting calendar events:', error);
      return [];
    }
  }
}

// Export singleton instance
export const calendarService = new CalendarService();

export default calendarService;
