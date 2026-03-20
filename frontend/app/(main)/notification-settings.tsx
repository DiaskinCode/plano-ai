import { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Switch,
  TouchableOpacity,
  Alert,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { notificationsAPI, NotificationPreferences } from '@/services/notifications';
import DateTimePicker from '@react-native-community/datetimepicker';
import { clearAllTaskNotifications } from '@/utils/taskNotifications';

const COLORS = {
  bg: '#1A1A1A',
  surface: '#2A2A2A',
  border: '#3E3E3E',
  text: '#ECECEC',
  textSecondary: '#8E8E8E',
  primary: '#5B6AFF',
  error: '#FF3B30',
};

export default function NotificationSettingsScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Notification preferences state
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    task_reminders_enabled: true,
    deadline_notifications_enabled: true,
    ai_motivation_enabled: true,
    daily_pulse_reminder_enabled: true,
    task_reminder_minutes_before: 15,
    daily_pulse_time: '20:00',
    quiet_hours_enabled: false,
    quiet_hours_start: null,
    quiet_hours_end: null,
  });

  // Date picker visibility
  const [showDailyPulseTimePicker, setShowDailyPulseTimePicker] = useState(false);
  const [showQuietHoursStartPicker, setShowQuietHoursStartPicker] = useState(false);
  const [showQuietHoursEndPicker, setShowQuietHoursEndPicker] = useState(false);

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      const response = await notificationsAPI.getPreferences();
      setPreferences(response.data);
    } catch (error) {
      console.error('Failed to load notification preferences:', error);
      Alert.alert(t('common.error'), t('notifications.settings.loadError'));
    } finally {
      setLoading(false);
    }
  };

  const savePreferences = async (updatedPrefs: Partial<NotificationPreferences>) => {
    try {
      setSaving(true);
      await notificationsAPI.updatePreferences(updatedPrefs);
      setPreferences({ ...preferences, ...updatedPrefs });
    } catch (error) {
      console.error('Failed to save notification preferences:', error);
      Alert.alert(t('common.error'), t('notifications.settings.saveError'));
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = async (key: keyof NotificationPreferences, value: boolean) => {
    const update = { [key]: value };

    // If user is disabling task reminders, clear all local notifications
    if (key === 'task_reminders_enabled' && !value) {
      try {
        await clearAllTaskNotifications();
        console.log('Cleared all local task notifications');
      } catch (error) {
        console.error('Error clearing local notifications:', error);
      }
    }

    savePreferences(update);
  };

  const handleReminderMinutesChange = (minutes: number) => {
    savePreferences({ task_reminder_minutes_before: minutes });
  };

  const sendTestNotification = async () => {
    try {
      await notificationsAPI.sendTest();
      Alert.alert(
        t('notifications.settings.testNotificationSent'),
        t('notifications.settings.testNotificationMessage')
      );
    } catch (error) {
      console.error('Failed to send test notification:', error);
      Alert.alert(t('common.error'), t('notifications.settings.testNotificationError'));
    }
  };

  const parseTime = (timeString: string | null): Date => {
    if (!timeString) return new Date();
    const [hours, minutes] = timeString.split(':').map(Number);
    const date = new Date();
    date.setHours(hours, minutes, 0, 0);
    return date;
  };

  const formatTime = (date: Date): string => {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
  };

  if (loading) {
    return (
      <View style={[styles.container, styles.centerContent]}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <MaterialCommunityIcons name="arrow-left" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('notifications.settings.title')}</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.content}>
        {/* Notification Types */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('notifications.settings.types')}</Text>

          <View style={styles.card}>
            <View style={styles.settingRow}>
              <View style={styles.settingLeft}>
                <MaterialCommunityIcons name="clock-outline" size={24} color={COLORS.primary} />
                <View style={styles.settingText}>
                  <Text style={styles.settingTitle}>{t('notifications.settings.taskReminders')}</Text>
                  <Text style={styles.settingSubtitle}>{t('notifications.settings.taskRemindersDesc')}</Text>
                </View>
              </View>
              <Switch
                value={preferences.task_reminders_enabled}
                onValueChange={(value) => handleToggle('task_reminders_enabled', value)}
                trackColor={{ false: COLORS.border, true: COLORS.primary }}
                thumbColor="#fff"
                disabled={saving}
              />
            </View>
          </View>

          <View style={styles.card}>
            <View style={styles.settingRow}>
              <View style={styles.settingLeft}>
                <MaterialCommunityIcons name="calendar-alert" size={24} color={COLORS.primary} />
                <View style={styles.settingText}>
                  <Text style={styles.settingTitle}>{t('notifications.settings.deadlines')}</Text>
                  <Text style={styles.settingSubtitle}>{t('notifications.settings.deadlinesDesc')}</Text>
                </View>
              </View>
              <Switch
                value={preferences.deadline_notifications_enabled}
                onValueChange={(value) => handleToggle('deadline_notifications_enabled', value)}
                trackColor={{ false: COLORS.border, true: COLORS.primary }}
                thumbColor="#fff"
                disabled={saving}
              />
            </View>
          </View>

          <View style={styles.card}>
            <View style={styles.settingRow}>
              <View style={styles.settingLeft}>
                <MaterialCommunityIcons name="checkbox-marked-circle-outline" size={24} color={COLORS.primary} />
                <View style={styles.settingText}>
                  <Text style={styles.settingTitle}>{t('notifications.settings.dailyPulse')}</Text>
                  <Text style={styles.settingSubtitle}>{t('notifications.settings.dailyPulseDesc')}</Text>
                </View>
              </View>
              <Switch
                value={preferences.daily_pulse_reminder_enabled}
                onValueChange={(value) => handleToggle('daily_pulse_reminder_enabled', value)}
                trackColor={{ false: COLORS.border, true: COLORS.primary }}
                thumbColor="#fff"
                disabled={saving}
              />
            </View>
          </View>

          <View style={styles.card}>
            <View style={styles.settingRow}>
              <View style={styles.settingLeft}>
                <MaterialCommunityIcons name="lightbulb-on-outline" size={24} color={COLORS.primary} />
                <View style={styles.settingText}>
                  <Text style={styles.settingTitle}>{t('notifications.settings.aiMotivation')}</Text>
                  <Text style={styles.settingSubtitle}>{t('notifications.settings.aiMotivationDesc')}</Text>
                </View>
              </View>
              <Switch
                value={preferences.ai_motivation_enabled}
                onValueChange={(value) => handleToggle('ai_motivation_enabled', value)}
                trackColor={{ false: COLORS.border, true: COLORS.primary }}
                thumbColor="#fff"
                disabled={saving}
              />
            </View>
          </View>
        </View>

        {/* Timing Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('notifications.settings.timing')}</Text>

          {/* Task Reminder Minutes */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{t('notifications.settings.reminderTime')}</Text>
            <Text style={styles.cardSubtitle}>{t('notifications.settings.reminderTimeDesc')}</Text>

            <View style={styles.minutesSelector}>
              {[5, 10, 15, 30, 60].map((minutes) => (
                <TouchableOpacity
                  key={minutes}
                  style={[
                    styles.minuteButton,
                    preferences.task_reminder_minutes_before === minutes && styles.minuteButtonActive,
                  ]}
                  onPress={() => handleReminderMinutesChange(minutes)}
                  disabled={saving}
                >
                  <Text
                    style={[
                      styles.minuteButtonText,
                      preferences.task_reminder_minutes_before === minutes && styles.minuteButtonTextActive,
                    ]}
                  >
                    {minutes}m
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Daily Pulse Time */}
          {preferences.daily_pulse_reminder_enabled && (
            <TouchableOpacity
              style={styles.card}
              onPress={() => setShowDailyPulseTimePicker(true)}
            >
              <Text style={styles.cardTitle}>{t('notifications.settings.dailyPulseTime')}</Text>
              <Text style={styles.timeValue}>{preferences.daily_pulse_time}</Text>
            </TouchableOpacity>
          )}

          {showDailyPulseTimePicker && (
            <DateTimePicker
              value={parseTime(preferences.daily_pulse_time)}
              mode="time"
              is24Hour={true}
              display="default"
              onChange={(event, selectedDate) => {
                setShowDailyPulseTimePicker(Platform.OS === 'ios');
                if (selectedDate) {
                  savePreferences({ daily_pulse_time: formatTime(selectedDate) });
                }
              }}
            />
          )}
        </View>

        {/* Quiet Hours */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('notifications.settings.quietHours')}</Text>

          <View style={styles.card}>
            <View style={styles.settingRow}>
              <View style={styles.settingLeft}>
                <MaterialCommunityIcons name="sleep" size={24} color={COLORS.primary} />
                <View style={styles.settingText}>
                  <Text style={styles.settingTitle}>{t('notifications.settings.enableQuietHours')}</Text>
                  <Text style={styles.settingSubtitle}>{t('notifications.settings.quietHoursDesc')}</Text>
                </View>
              </View>
              <Switch
                value={preferences.quiet_hours_enabled}
                onValueChange={(value) => handleToggle('quiet_hours_enabled', value)}
                trackColor={{ false: COLORS.border, true: COLORS.primary }}
                thumbColor="#fff"
                disabled={saving}
              />
            </View>
          </View>

          {preferences.quiet_hours_enabled && (
            <View style={styles.card}>
              <View style={styles.quietHoursRow}>
                <TouchableOpacity
                  style={styles.timeButton}
                  onPress={() => setShowQuietHoursStartPicker(true)}
                >
                  <Text style={styles.timeLabel}>{t('notifications.settings.from')}</Text>
                  <Text style={styles.timeValue}>{preferences.quiet_hours_start || '22:00'}</Text>
                </TouchableOpacity>

                <MaterialCommunityIcons name="arrow-right" size={24} color={COLORS.textSecondary} />

                <TouchableOpacity
                  style={styles.timeButton}
                  onPress={() => setShowQuietHoursEndPicker(true)}
                >
                  <Text style={styles.timeLabel}>{t('notifications.settings.to')}</Text>
                  <Text style={styles.timeValue}>{preferences.quiet_hours_end || '08:00'}</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          {showQuietHoursStartPicker && (
            <DateTimePicker
              value={parseTime(preferences.quiet_hours_start)}
              mode="time"
              is24Hour={true}
              display="default"
              onChange={(event, selectedDate) => {
                setShowQuietHoursStartPicker(Platform.OS === 'ios');
                if (selectedDate) {
                  savePreferences({ quiet_hours_start: formatTime(selectedDate) });
                }
              }}
            />
          )}

          {showQuietHoursEndPicker && (
            <DateTimePicker
              value={parseTime(preferences.quiet_hours_end)}
              mode="time"
              is24Hour={true}
              display="default"
              onChange={(event, selectedDate) => {
                setShowQuietHoursEndPicker(Platform.OS === 'ios');
                if (selectedDate) {
                  savePreferences({ quiet_hours_end: formatTime(selectedDate) });
                }
              }}
            />
          )}
        </View>

        {/* Test Notification Button */}
        <TouchableOpacity style={styles.testButton} onPress={sendTestNotification}>
          <MaterialCommunityIcons name="bell-ring" size={20} color="#fff" />
          <Text style={styles.testButtonText}>{t('notifications.settings.sendTest')}</Text>
        </TouchableOpacity>

        <View style={{ height: 40 }} />
      </ScrollView>

      {/* Saving Indicator */}
      {saving && (
        <View style={styles.savingIndicator}>
          <ActivityIndicator size="small" color="#fff" />
          <Text style={styles.savingText}>{t('common.saving')}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  centerContent: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    paddingTop: 60,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    color: COLORS.text,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 12,
  },
  settingText: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 4,
  },
  settingSubtitle: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 8,
  },
  cardSubtitle: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginBottom: 16,
  },
  minutesSelector: {
    flexDirection: 'row',
    gap: 8,
  },
  minuteButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
  },
  minuteButtonActive: {
    borderColor: COLORS.primary,
    backgroundColor: '#0D2A22',
  },
  minuteButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  minuteButtonTextActive: {
    color: COLORS.primary,
  },
  timeValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.primary,
    marginTop: 8,
  },
  quietHoursRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  timeButton: {
    flex: 1,
    alignItems: 'center',
  },
  timeLabel: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginBottom: 8,
  },
  testButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  testButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  savingIndicator: {
    position: 'absolute',
    bottom: 24,
    left: '50%',
    transform: [{ translateX: -60 }],
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 20,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  savingText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
});
