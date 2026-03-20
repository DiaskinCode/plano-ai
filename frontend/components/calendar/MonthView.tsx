/**
 * Month View Component
 *
 * Displays a full month calendar grid with task indicators
 * Shows dots for tasks per day with category colors
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { todosAPI } from '@/services/api';
import { type TaskCategory } from '@/services/taskCategoriesApi';

const { width } = Dimensions.get('window');

interface MonthViewProps {
  selectedDate: Date;
  onDateSelect: (date: Date) => void;
  categories?: TaskCategory[];
}

interface TaskData {
  id: number;
  title: string;
  scheduled_date: string;
  category?: TaskCategory;
  status: string;
}

export function MonthView({ selectedDate, onDateSelect, categories }: MonthViewProps) {
  const [currentMonth, setCurrentMonth] = useState(new Date(selectedDate));
  const [tasks, setTasks] = useState<TaskData[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTasksForMonth();
  }, [currentMonth]);

  const loadTasksForMonth = async () => {
    try {
      setLoading(true);
      const year = currentMonth.getFullYear();
      const month = currentMonth.getMonth();

      // Get first and last day of month
      const firstDay = new Date(year, month, 1);
      const lastDay = new Date(year, month + 1, 0);

      // Format dates for API
      const startDate = firstDay.toISOString().split('T')[0];
      const endDate = lastDay.toISOString().split('T')[0];

      // Load tasks for this month (you'll need to add this endpoint)
      const response = await todosAPI.getTasks({
        start_date: startDate,
        end_date: endDate,
      });

      setTasks(response || []);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);

    const days = [];
    const startPadding = firstDay.getDay(); // 0 = Sunday

    // Add padding for days before month starts
    for (let i = 0; i < startPadding; i++) {
      days.push(null);
    }

    // Add actual days
    for (let i = 1; i <= lastDay.getDate(); i++) {
      days.push(new Date(year, month, i));
    }

    return days;
  };

  const getTasksForDay = (day: Date) => {
    const dayStr = day.toISOString().split('T')[0];
    return tasks.filter(task => task.scheduled_date === dayStr);
  };

  const goToPrevMonth = () => {
    const newDate = new Date(currentMonth);
    newDate.setMonth(newDate.getMonth() - 1);
    setCurrentMonth(newDate);
  };

  const goToNextMonth = () => {
    const newDate = new Date(currentMonth);
    newDate.setMonth(newDate.getMonth() + 1);
    setCurrentMonth(newDate);
  };

  const isSameDay = (date1: Date, date2: Date) => {
    return (
      date1.getFullYear() === date2.getFullYear() &&
      date1.getMonth() === date2.getMonth() &&
      date1.getDate() === date2.getDate()
    );
  };

  const isToday = (date: Date) => {
    const today = new Date();
    return isSameDay(date, today);
  };

  const days = getDaysInMonth(currentMonth);
  const weekDays = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  return (
    <View style={styles.container}>
      {/* Month Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={goToPrevMonth} style={styles.navButton}>
          <Ionicons name="chevron-back" size={24} color="#5B6AFF" />
        </TouchableOpacity>

        <Text style={styles.monthTitle}>
          {monthNames[currentMonth.getMonth()]} {currentMonth.getFullYear()}
        </Text>

        <TouchableOpacity onPress={goToNextMonth} style={styles.navButton}>
          <Ionicons name="chevron-forward" size={24} color="#5B6AFF" />
        </TouchableOpacity>
      </View>

      {/* Week Day Headers */}
      <View style={styles.weekDays}>
        {weekDays.map((day, index) => (
          <View key={index} style={styles.weekDayCell}>
            <Text style={styles.weekDayText}>{day}</Text>
          </View>
        ))}
      </View>

      {/* Calendar Grid */}
      <ScrollView style={styles.gridContainer}>
        <View style={styles.calendarGrid}>
          {days.map((day, index) => {
            if (!day) {
              return <View key={index} style={styles.dayCell} />;
            }

            const dayTasks = getTasksForDay(day);
            const isSelected = isSameDay(day, selectedDate);
            const isTodayDate = isToday(day);

            return (
              <TouchableOpacity
                key={index}
                style={[
                  styles.dayCell,
                  isSelected && styles.selectedDay,
                  isTodayDate && styles.today,
                ]}
                onPress={() => onDateSelect(day)}
              >
                <Text
                  style={[
                    styles.dayNumber,
                    (isSelected || isTodayDate) && styles.selectedDayNumber,
                  ]}
                >
                  {day.getDate()}
                </Text>

                {/* Task indicators */}
                {dayTasks.length > 0 && (
                  <View style={styles.taskDots}>
                    {dayTasks.slice(0, 3).map((task, i) => {
                      const category = categories?.find(c => c.id === task.category?.id);
                      const color = category?.color || '#5B6AFF';
                      return (
                        <View
                          key={i}
                          style={[
                            styles.taskDot,
                            { backgroundColor: color },
                          ]}
                        />
                      );
                    })}
                    {dayTasks.length > 3 && (
                      <Text style={styles.moreText}>+{dayTasks.length - 3}</Text>
                    )}
                  </View>
                )}
              </TouchableOpacity>
            );
          })}
        </View>
      </ScrollView>
    </View>
  );
}

const CELL_SIZE = (width - 32) / 7;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1A1A1A',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#3E3E3E',
  },
  navButton: {
    padding: 8,
  },
  monthTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ECECEC',
  },
  weekDays: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#3E3E3E',
  },
  weekDayCell: {
    width: CELL_SIZE,
    paddingVertical: 8,
    alignItems: 'center',
  },
  weekDayText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#8E8E8E',
  },
  gridContainer: {
    flex: 1,
  },
  calendarGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
  },
  dayCell: {
    width: CELL_SIZE,
    height: CELL_SIZE,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2A2A2A',
    borderRadius: 8,
    margin: 1,
  },
  selectedDay: {
    backgroundColor: '#5B6AFF30',
    borderColor: '#5B6AFF',
  },
  today: {
    borderColor: '#5B6AFF',
    borderWidth: 2,
  },
  dayNumber: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ECECEC',
  },
  selectedDayNumber: {
    color: '#5B6AFF',
  },
  taskDots: {
    flexDirection: 'row',
    marginTop: 4,
    gap: 2,
  },
  taskDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
  },
  moreText: {
    fontSize: 10,
    color: '#8E8E8E',
    marginLeft: 2,
  },
});
