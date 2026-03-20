import * as Localization from 'expo-localization';
import AsyncStorage from '@react-native-async-storage/async-storage';

/**
 * Timezone utility service for detecting and managing user timezone
 */
class TimezoneService {
  private timezone: string | null = null;

  /**
   * Get the device's current timezone
   * Returns IANA timezone string (e.g., "Asia/Almaty", "America/New_York")
   */
  getDeviceTimezone(): string {
    try {
      // Method 1: Use JavaScript Intl API (most reliable cross-platform)
      const detectedTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      if (detectedTz) {
        console.log('Detected timezone from Intl.DateTimeFormat:', detectedTz);
        this.timezone = detectedTz;
        return detectedTz;
      }

      // Method 2: Try expo-localization getCalendars as fallback
      const tz = Localization.getCalendars()[0]?.timeZone;
      if (tz && tz !== 'UTC') {
        console.log('Detected timezone from getCalendars:', tz);
        this.timezone = tz;
        return tz;
      }

      // Fallback to UTC if all methods fail
      console.warn('Failed to detect timezone, using UTC as fallback');
      return 'UTC';
    } catch (error) {
      console.error('Error detecting timezone:', error);
      return 'UTC';
    }
  }

  /**
   * Get current timezone (cached or freshly detected)
   */
  getCurrentTimezone(): string {
    if (this.timezone) {
      return this.timezone;
    }
    return this.getDeviceTimezone();
  }

  /**
   * Save timezone to local storage
   */
  async saveTimezone(timezone: string): Promise<void> {
    try {
      await AsyncStorage.setItem('user_timezone', timezone);
      this.timezone = timezone;
    } catch (error) {
      console.error('Error saving timezone:', error);
    }
  }

  /**
   * Load timezone from local storage
   */
  async loadTimezone(): Promise<string | null> {
    try {
      const tz = await AsyncStorage.getItem('user_timezone');
      if (tz) {
        this.timezone = tz;
      }
      return tz;
    } catch (error) {
      console.error('Error loading timezone:', error);
      return null;
    }
  }

  /**
   * Initialize timezone - try to load from storage, fallback to device detection
   */
  async initialize(): Promise<string> {
    const stored = await this.loadTimezone();
    if (stored) {
      return stored;
    }

    const detected = this.getDeviceTimezone();
    await this.saveTimezone(detected);
    return detected;
  }

  /**
   * Get timezone offset in minutes from UTC
   * Positive values are east of UTC, negative are west
   */
  getTimezoneOffset(): number {
    const now = new Date();
    // JavaScript getTimezoneOffset returns negative for UTC+
    // We reverse it to match standard convention
    return -now.getTimezoneOffset();
  }

  /**
   * Format timezone for display (e.g., "GMT+6", "GMT-5")
   */
  getTimezoneDisplay(): string {
    const offset = this.getTimezoneOffset();
    const hours = Math.floor(Math.abs(offset) / 60);
    const minutes = Math.abs(offset) % 60;

    const sign = offset >= 0 ? '+' : '-';
    const minutesStr = minutes > 0 ? `:${minutes.toString().padStart(2, '0')}` : '';

    return `GMT${sign}${hours}${minutesStr}`;
  }
}

// Export singleton instance
export const timezoneService = new TimezoneService();

export default timezoneService;
