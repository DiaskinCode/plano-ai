/**
 * List View Component
 *
 * Displays tasks in a vertical list grouped by date
 * Shows category indicators and task details
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { todosAPI } from '@/services/api';
import { type TaskCategory } from '@/services/taskCategoriesApi';
import { format } from 'date-fns';

interface ListViewProps {
  selectedDate: Date;
  onTaskPress?: (taskId: number) => void;
  categories?: TaskCategory[];
  categoryFilter?: number | null;
}

interface TaskData {
  id: number;
  title: string;
  description: string;
  scheduled_date: string;
  scheduled_time?: string;
  category?: TaskCategory;
  status: string;
  priority: number;
  estimated_duration_minutes?: number;
}

interface GroupedTasks {
  [date: string]: TaskData[];
}

export function ListView({
  selectedDate,
  onTaskPress,
  categories,
  categoryFilter,
}: ListViewProps) {
  const [tasks, setTasks] = useState<TaskData[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTasks();
  }, [selectedDate, categoryFilter]);

  const loadTasks = async () => {
    try {
      setLoading(true);

      // Get date range (next 30 days from selected date)
      const startDate = selectedDate.toISOString().split('T')[0];
      const endDate = new Date(selectedDate);
      endDate.setDate(endDate.getDate() + 30);
      const endDateStr = endDate.toISOString().split('T')[0];

      // Fetch tasks with category filter if set
      const params: any = {
        start_date: startDate,
        end_date: endDateStr,
      };

      if (categoryFilter) {
        params.category = categoryFilter;
      }

      const response = await todosAPI.getTasks(params);
      setTasks(response || []);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const groupTasksByDate = (tasks: TaskData[]): GroupedTasks => {
    return tasks.reduce((groups: GroupedTasks, task) => {
      const date = task.scheduled_date;
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(task);
      return groups;
    }, {});
  };

  const getCategoryForTask = (task: TaskData): TaskCategory | undefined => {
    if (!task.category || !categories) return undefined;
    return categories.find(c => c.id === task.category.id);
  };

  const formatDateHeader = (dateStr: string): string => {
    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (dateStr === today.toISOString().split('T')[0]) {
      return 'Today';
    } else if (dateStr === tomorrow.toISOString().split('T')[0]) {
      return 'Tomorrow';
    } else {
      return format(date, 'EEEE, MMM d');
    }
  };

  const getPriorityColor = (priority: number): string => {
    if (priority === 3) return '#EF4444'; // High - Red
    if (priority === 2) return '#F59E0B'; // Medium - Orange
    return '#6B7280'; // Low - Gray
  };

  const getStatusIcon = (status: string): string => {
    if (status === 'done') return 'checkmark-circle';
    if (status === 'in_progress') return 'time';
    if (status === 'skipped') return 'close-circle';
    return 'radio-button-off';
  };

  const groupedTasks = groupTasksByDate(tasks);
  const sortedDates = Object.keys(groupedTasks).sort();

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#5B6AFF" />
        <Text style={styles.loadingText}>Loading tasks...</Text>
      </View>
    );
  }

  if (tasks.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Ionicons name="calendar-outline" size={64} color="#3E3E3E" />
        <Text style={styles.emptyTitle}>No Tasks Found</Text>
        <Text style={styles.emptyText}>
          {categoryFilter
            ? 'No tasks in this category for the selected period'
            : 'No tasks scheduled for the next 30 days'}
        </Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {sortedDates.map((dateStr) => {
        const dayTasks = groupedTasks[dateStr];

        return (
          <View key={dateStr} style={styles.dateGroup}>
            <View style={styles.dateHeader}>
              <Text style={styles.dateHeaderText}>{formatDateHeader(dateStr)}</Text>
              <View style={styles.taskCount}>
                <Text style={styles.taskCountText}>{dayTasks.length}</Text>
              </View>
            </View>

            {dayTasks.map((task) => {
              const category = getCategoryForTask(task);
              const priorityColor = getPriorityColor(task.priority);

              return (
                <TouchableOpacity
                  key={task.id}
                  style={styles.taskCard}
                  onPress={() => onTaskPress?.(task.id)}
                  activeOpacity={0.7}
                >
                  <View style={styles.taskLeft}>
                    {/* Priority indicator */}
                    <View style={[styles.priorityBar, { backgroundColor: priorityColor }]} />

                    {/* Category icon */}
                    {category && (
                      <View style={styles.categoryIcon}>
                        <Text style={styles.categoryEmoji}>{category.icon}</Text>
                      </View>
                    )}

                    <View style={styles.taskContent}>
                      <View style={styles.taskHeader}>
                        <Text style={styles.taskTitle} numberOfLines={2}>
                          {task.title}
                        </Text>
                        <Ionicons
                          name={getStatusIcon(task.status) as any}
                          size={20}
                          color={
                            task.status === 'done'
                              ? '#10B981'
                              : task.status === 'skipped'
                              ? '#EF4444'
                              : '#6B7280'
                          }
                        />
                      </View>

                      {task.description && (
                        <Text style={styles.taskDescription} numberOfLines={2}>
                          {task.description}
                        </Text>
                      )}

                      <View style={styles.taskMeta}>
                        {task.scheduled_time && (
                          <View style={styles.metaItem}>
                            <Ionicons name="time-outline" size={14} color="#8E8E8E" />
                            <Text style={styles.metaText}>{task.scheduled_time}</Text>
                          </View>
                        )}
                        {task.estimated_duration_minutes && (
                          <View style={styles.metaItem}>
                            <Ionicons name="hourglass-outline" size={14} color="#8E8E8E" />
                            <Text style={styles.metaText}>
                              {task.estimated_duration_minutes}m
                            </Text>
                          </View>
                        )}
                        {category && (
                          <View
                            style={[
                              styles.categoryBadge,
                              { backgroundColor: category.color + '20' },
                            ]}
                          >
                            <Text style={[styles.categoryBadgeText, { color: category.color }]}>
                              {category.name}
                            </Text>
                          </View>
                        )}
                      </View>
                    </View>
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1A1A1A',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 16,
    color: '#8E8E8E',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
    paddingHorizontal: 32,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#ECECEC',
  },
  emptyText: {
    fontSize: 14,
    color: '#8E8E8E',
    textAlign: 'center',
  },
  dateGroup: {
    marginBottom: 8,
  },
  dateHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#2A2A2A',
    borderBottomWidth: 1,
    borderBottomColor: '#3E3E3E',
  },
  dateHeaderText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#ECECEC',
  },
  taskCount: {
    backgroundColor: '#5B6AFF',
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  taskCountText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  taskCard: {
    flexDirection: 'row',
    backgroundColor: '#2A2A2A',
    marginHorizontal: 16,
    marginTop: 8,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#3E3E3E',
  },
  taskLeft: {
    flexDirection: 'row',
    flex: 1,
    gap: 12,
  },
  priorityBar: {
    width: 4,
    borderRadius: 2,
  },
  categoryIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#3E3E3E',
    alignItems: 'center',
    justifyContent: 'center',
  },
  categoryEmoji: {
    fontSize: 20,
  },
  taskContent: {
    flex: 1,
    gap: 6,
  },
  taskHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 8,
  },
  taskTitle: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    color: '#ECECEC',
  },
  taskDescription: {
    fontSize: 14,
    color: '#8E8E8E',
    lineHeight: 20,
  },
  taskMeta: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: 12,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaText: {
    fontSize: 12,
    color: '#8E8E8E',
  },
  categoryBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  categoryBadgeText: {
    fontSize: 12,
    fontWeight: '600',
  },
});
