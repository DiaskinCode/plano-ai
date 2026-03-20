import { useState, useEffect, useRef, useMemo } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Animated,
  Alert,
  Modal,
  Dimensions,
  PanResponder,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { todosAPI } from '@/services/api';
import { useTranslation } from 'react-i18next';

const { width, height } = Dimensions.get('window');

const COLORS = {
  bg: '#1A1A1A',
  surface: '#2A2A2A',
  surfaceHover: '#3A3A3A',
  border: '#3E3E3E',
  text: '#ECECEC',
  textSecondary: '#8E8E8E',
  primary: '#5B6AFF',

  // Task colors
  planTask: '#3B82F6',
  adHocTask: '#10B981',
  opportunityTask: '#F59E0B',
  externalEvent: '#6B7280',
  milestoneAccent: '#EF4444',

  // Energy bands
  energyPeak: 'rgba(16, 163, 127, 0.1)',
  energyLow: 'rgba(107, 114, 128, 0.05)',
};

const HOUR_HEIGHT = 80; // Increased from 60 for more vertical space
const HOURS = Array.from({ length: 24 }, (_, i) => i);

type ViewMode = 'day' | '3day' | 'week';

type CalendarTask = {
  id: number;
  title: string;
  startTime: Date;
  duration: number;
  type: 'plan' | 'adhoc' | 'opportunity' | 'external';
  priority: number;
  locked: boolean;
  milestone?: boolean;
  location?: string;
  status?: string; // pending, done, skipped
};

type DisplacementReason = {
  blockId: number;
  summary: string;
  timestamp: string;
};

type DragPreview = {
  task: CalendarTask;
  newStartTime: Date;
  displacedTasks: Array<{ task: CalendarTask; newStartTime: Date }>;
};

const GRID_MINUTES = 15;
const MAX_DISPLACEMENT_HOPS = 50;

interface CalendarScreenProps {
  selectedDateProp?: Date;
  onDateChange?: (date: Date) => void;
  hideDayPicker?: boolean;
  onOpenFullCalendar?: () => void;
}

export default function CalendarScreen({ selectedDateProp, onDateChange, hideDayPicker = false, onOpenFullCalendar }: CalendarScreenProps = {}) {
  const { t } = useTranslation();
  const [selectedDate, setSelectedDate] = useState(selectedDateProp || new Date());
  const [viewMode, setViewMode] = useState<ViewMode>('day');
  const [tasks, setTasks] = useState<CalendarTask[]>([]);
  const [unscheduledTasks, setUnscheduledTasks] = useState<any[]>([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [currentTask, setCurrentTask] = useState<CalendarTask | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [quickInput, setQuickInput] = useState('');
  const [timeBudget, setTimeBudget] = useState({ used: 360, total: 480 }); // minutes
  const [energyPeak, setEnergyPeak] = useState({ start: 9, end: 12 });
  const [undoStack, setUndoStack] = useState<any[]>([]);
  const [lastAction, setLastAction] = useState<string | null>(null);
  const [selectedTask, setSelectedTask] = useState<CalendarTask | null>(null);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [draggingTask, setDraggingTask] = useState<CalendarTask | null>(null);
  const [dragPreview, setDragPreview] = useState<DragPreview | null>(null);
  const [displacementReasons, setDisplacementReasons] = useState<DisplacementReason[]>([]);
  const [resizingTask, setResizingTask] = useState<number | null>(null);
  const [showResizeHandles, setShowResizeHandles] = useState<number | null>(null);
  const [resizeMode, setResizeMode] = useState<'top' | 'bottom' | null>(null);
  const [initialDuration, setInitialDuration] = useState(0);
  const [initialStartTime, setInitialStartTime] = useState<Date | null>(null);
  const longPressTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [showFullCalendar, setShowFullCalendar] = useState(false);
  const [calendarMonth, setCalendarMonth] = useState(new Date());

  const drawerAnim = useRef(new Animated.Value(width)).current;
  const scrollViewRef = useRef<ScrollView>(null);
  const dayScrollRef = useRef<ScrollView>(null);
  const taskAnimations = useRef<Map<number, Animated.ValueXY>>(new Map()).current;

  // Swipe gesture refs
  const swipeStartX = useRef(0);
  const swipeAnim = useRef(new Animated.Value(0)).current;
  const [isSwipingDay, setIsSwipingDay] = useState(false);

  useEffect(() => {
    loadTasks();
    loadUnscheduledTasks();
    // Scroll to 8 AM on mount
    setTimeout(() => {
      scrollViewRef.current?.scrollTo({ y: 8 * HOUR_HEIGHT, animated: true });
    }, 100);
  }, [selectedDate]);

  // Generate days for horizontal picker (current month)
  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const days = [];

    for (let i = 1; i <= daysInMonth; i++) {
      days.push(new Date(year, month, i));
    }
    return days;
  };

  const daysInCurrentMonth = getDaysInMonth(selectedDate);

  // Get visible days - обновляется при смене selectedDate
  const visibleDays = useMemo(() => {
    const days = [];
    const baseTime = selectedDate.getTime();
    const oneDayMs = 24 * 60 * 60 * 1000;

    for (let i = -14; i <= 14; i++) { // 29 дней - можно свайпать много раз
      const day = new Date(baseTime + (i * oneDayMs));
      days.push(day);
    }
    return days;
  }, [selectedDate]);

  const selectDay = (day: Date) => {
    setSelectedDate(day);
    if (onDateChange) {
      onDateChange(day);
    }
    setShowFullCalendar(false);
  };

  const changeDayByOffset = (offset: number) => {
    const newDate = new Date(selectedDate);
    newDate.setDate(newDate.getDate() + offset);
    selectDay(newDate);
  };

  // Swipe PanResponder for day navigation с анимацией
  const swipePanResponder = useMemo(() =>
    PanResponder.create({
      onStartShouldSetPanResponder: () => false,
      onMoveShouldSetPanResponder: (evt, gestureState) => {
        // Активировать только если горизонтальный свайп и не драг задачи
        return !draggingTask && Math.abs(gestureState.dx) > 20 && Math.abs(gestureState.dy) < 30;
      },
      onPanResponderGrant: (evt) => {
        swipeStartX.current = evt.nativeEvent.pageX;
        swipeAnim.setValue(0);
        setIsSwipingDay(true);
      },
      onPanResponderMove: (evt, gestureState) => {
        // Двигаем контент вместе с пальцем
        swipeAnim.setValue(gestureState.dx);
      },
      onPanResponderRelease: (evt, gestureState) => {
        if (Math.abs(gestureState.dx) > 50) {
          // Достаточный свайп - меняем день с анимацией
          const toValue = gestureState.dx > 0 ? width : -width;
          const direction = gestureState.dx > 0 ? -1 : 1;

          Animated.timing(swipeAnim, {
            toValue,
            duration: 250,
            useNativeDriver: true,
          }).start(() => {
            // Меняем день
            const newDate = new Date(selectedDate);
            newDate.setDate(newDate.getDate() + direction);

            // Сбрасываем анимацию и состояние
            swipeAnim.setValue(0);
            setIsSwipingDay(false);

            // Обновляем дату
            selectDay(newDate);
          });
        } else {
          // Недостаточный свайп - возвращаем назад
          Animated.spring(swipeAnim, {
            toValue: 0,
            useNativeDriver: true,
            tension: 65,
            friction: 10,
          }).start(() => {
            setIsSwipingDay(false);
          });
        }
      },
      onPanResponderTerminate: () => {
        Animated.spring(swipeAnim, {
          toValue: 0,
          useNativeDriver: true,
        }).start(() => {
          setIsSwipingDay(false);
        });
      },
    }), [draggingTask, selectedDate]
  );

  // Sync with prop if provided
  useEffect(() => {
    if (selectedDateProp) {
      setSelectedDate(selectedDateProp);
    }
  }, [selectedDateProp]);

  const loadTasks = async () => {
    try {
      // Determine filter based on selected date
      const today = new Date();
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);

      const selectedDateStr = selectedDate.toISOString().split('T')[0];
      const todayStr = today.toISOString().split('T')[0];
      const tomorrowStr = tomorrow.toISOString().split('T')[0];

      let filter = 'upcoming';
      if (selectedDateStr === todayStr) {
        filter = 'today';
      } else if (selectedDateStr === tomorrowStr) {
        filter = 'tomorrow';
      }

      const response = await todosAPI.getTodos(filter);
      const apiTasks = response.data.results || response.data || [];

      // Convert API tasks to calendar format
      // Filter by scheduled_date (show tasks even without scheduled_time)
      const calendarTasks: CalendarTask[] = apiTasks
        .filter((task: any) => task.scheduled_date === selectedDateStr)
        .map((task: any) => {
          let taskDate: Date;

          if (task.scheduled_time) {
            // Task has a specific time
            const [hours, minutes] = task.scheduled_time.split(':').map(Number);
            taskDate = new Date(selectedDate);
            taskDate.setHours(hours, minutes, 0, 0);
          } else {
            // Task without time - place at 9 AM by default
            taskDate = new Date(selectedDate);
            taskDate.setHours(9, 0, 0, 0);
          }

          return {
            id: task.id,
            title: task.title,
            startTime: taskDate,
            duration: task.estimated_duration_minutes || 60,
            type: task.source === 'integrated' ? 'adhoc' : 'plan',
            priority: task.priority || 2,
            locked: false,
            milestone: task.milestone_critical || false,
            status: task.status || 'pending',
          };
        });

      setTasks(calendarTasks);
    } catch (error) {
      console.error('Failed to load tasks:', error);
      setTasks([]);
    }
  };

  const loadUnscheduledTasks = async () => {
    try {
      const response = await todosAPI.getTodos('today');
      const apiTasks = response.data.results || response.data || [];

      const today = new Date().toISOString().split('T')[0];

      // Filter tasks without scheduled_date (truly unscheduled)
      // Don't include tasks that have a date but no time - those appear in calendar
      const unscheduled = apiTasks.filter((task: any) =>
        !task.scheduled_date || (task.scheduled_date !== today && !task.scheduled_time)
      );
      setUnscheduledTasks(unscheduled);
    } catch (error) {
      console.error('Failed to load unscheduled tasks:', error);
      setUnscheduledTasks([]);
    }
  };

  const toggleDrawer = () => {
    const toValue = drawerOpen ? width : 0;
    Animated.spring(drawerAnim, {
      toValue,
      useNativeDriver: true,
      tension: 50,
      friction: 8,
    }).start();
    setDrawerOpen(!drawerOpen);
  };

  const parseNaturalLanguage = (input: string) => {
    // Simple parser for "doc 15:00 Gangnam" format
    const timeMatch = input.match(/(\d{1,2}):(\d{2})/);
    const parts = input.split(' ');

    const task: Partial<CalendarTask> = {
      title: parts[0],
      type: 'adhoc',
      duration: 30,
      priority: 2,
      locked: false,
    };

    if (timeMatch) {
      const hour = parseInt(timeMatch[1]);
      const minute = parseInt(timeMatch[2]);
      task.startTime = new Date(selectedDate.setHours(hour, minute));
    }

    const locationIndex = parts.findIndex(p => p.match(/^[A-Z]/));
    if (locationIndex > 0) {
      task.location = parts.slice(locationIndex).join(' ');
    }

    return task;
  };

  const addQuickTask = async () => {
    if (!quickInput.trim()) return;

    const parsed = parseNaturalLanguage(quickInput);
    const autoPlaced = findBestSlot(parsed as CalendarTask);

    try {
      const startTime = autoPlaced.startTime || new Date();
      const timeStr = `${startTime.getHours().toString().padStart(2, '0')}:${startTime.getMinutes().toString().padStart(2, '0')}`;

      const response = await todosAPI.create({
        title: parsed.title,
        scheduled_date: selectedDate.toISOString().split('T')[0],
        scheduled_time: timeStr,
        estimated_duration_minutes: parsed.duration || 30,
        priority: parsed.priority || 2,
        source: 'integrated',
      });

      // Add to local state
      const newCalendarTask: CalendarTask = {
        id: response.data.id,
        title: parsed.title || 'Untitled',
        startTime: autoPlaced.startTime || new Date(),
        duration: parsed.duration || 30,
        type: 'adhoc',
        priority: parsed.priority || 2,
        locked: false,
      };

      setTasks([...tasks, newCalendarTask]);
      setQuickInput('');

      if (autoPlaced.moved && autoPlaced.reason) {
        setLastAction(autoPlaced.reason);
        setTimeout(() => setLastAction(null), 3000);
      }
    } catch (error) {
      console.error('Failed to create task:', error);
      Alert.alert('Error', 'Failed to create task');
    }
  };

  const findBestSlot = (task: CalendarTask) => {
    // Find free slots that match duration
    const freeSlots = [];
    for (let hour = 0; hour < 24; hour++) {
      for (let minute = 0; minute < 60; minute += 15) {
        const slotStart = new Date(selectedDate.setHours(hour, minute));
        const slotEnd = new Date(slotStart.getTime() + task.duration * 60000);

        const hasConflict = tasks.some(t => {
          const taskEnd = new Date(t.startTime.getTime() + t.duration * 60000);
          return (
            (slotStart >= t.startTime && slotStart < taskEnd) ||
            (slotEnd > t.startTime && slotEnd <= taskEnd)
          );
        });

        if (!hasConflict) {
          // Check if in energy peak
          const inEnergyPeak = hour >= energyPeak.start && hour < energyPeak.end;
          freeSlots.push({
            startTime: slotStart,
            score: inEnergyPeak ? 10 : 5,
            reason: inEnergyPeak
              ? 'Placed in morning. You finish more tasks before 12:00.'
              : 'Best available slot for this duration.',
          });
        }
      }
    }

    // Return best slot
    if (freeSlots.length > 0) {
      const best = freeSlots.sort((a, b) => b.score - a.score)[0];
      return {
        startTime: best.startTime,
        moved: true,
        reason: best.reason,
      };
    }

    return {
      startTime: new Date(selectedDate.setHours(9, 0)),
      moved: false,
      reason: null,
    };
  };

  const moveTask = async (taskId: number, newStartTime: Date) => {
    const taskIndex = tasks.findIndex(t => t.id === taskId);
    if (taskIndex === -1) return;

    const task = tasks[taskIndex];
    if (task.locked) {
      Alert.alert('Locked', 'This task cannot be moved.');
      return;
    }

    // Check for conflicts
    const taskEnd = new Date(newStartTime.getTime() + task.duration * 60000);
    const conflicts = tasks.filter(t => {
      if (t.id === taskId) return false;
      const tEnd = new Date(t.startTime.getTime() + t.duration * 60000);
      return (
        (newStartTime >= t.startTime && newStartTime < tEnd) ||
        (taskEnd > t.startTime && taskEnd <= tEnd)
      );
    });

    if (conflicts.length > 0) {
      Alert.alert(
        'Time clash',
        `Keep ${task.title} or move ${conflicts[0].title}?`,
        [
          { text: 'Cancel', style: 'cancel' },
          { text: `Keep ${task.title}`, onPress: async () => {
            await updateTaskTime(task, newStartTime);
          }}
        ]
      );
      return;
    }

    await updateTaskTime(task, newStartTime);
  };

  const updateTaskTime = async (task: CalendarTask, newStartTime: Date) => {
    try {
      const timeStr = `${newStartTime.getHours().toString().padStart(2, '0')}:${newStartTime.getMinutes().toString().padStart(2, '0')}`;

      await todosAPI.update(task.id, {
        scheduled_time: timeStr,
      });

      // Update local state
      const taskIndex = tasks.findIndex(t => t.id === task.id);
      const newTasks = [...tasks];
      newTasks[taskIndex] = { ...task, startTime: newStartTime };
      setTasks(newTasks);
      setLastAction(`Moved "${task.title}". Reason saved.`);
      setTimeout(() => setLastAction(null), 3000);
    } catch (error) {
      console.error('Failed to update task:', error);
      Alert.alert('Error', 'Failed to update task time');
    }
  };

  const updateTaskDuration = async (taskId: number, newDuration: number) => {
    try {
      await todosAPI.update(taskId, {
        estimated_duration_minutes: newDuration,
      });

      setLastAction(`Duration updated to ${newDuration} minutes`);
      setTimeout(() => setLastAction(null), 3000);
    } catch (error) {
      console.error('Failed to update task duration:', error);
      Alert.alert('Error', 'Failed to update task duration');
    }
  };

  const splitTask = (taskId: number) => {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;

    const halfDuration = Math.floor(task.duration / 2);
    const newTask: CalendarTask = {
      ...task,
      id: Date.now(),
      duration: halfDuration,
      startTime: new Date(task.startTime.getTime() + halfDuration * 60000 + 15 * 60000),
    };

    const updatedTask = { ...task, duration: halfDuration };
    setTasks([...tasks.filter(t => t.id !== taskId), updatedTask, newTask]);
    setLastAction(`Split into 2 x ${halfDuration}m blocks.`);
    setTimeout(() => setLastAction(null), 3000);
  };

  const snoozeTask = (taskId: number, minutes: number) => {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;

    const newStartTime = new Date(task.startTime.getTime() + minutes * 60000);
    moveTask(taskId, newStartTime);
  };

  // Snap time to grid (15-minute increments)
  const snapToGrid = (time: Date): Date => {
    const snapped = new Date(time);
    const minutes = snapped.getMinutes();
    const roundedMinutes = Math.floor(minutes / GRID_MINUTES) * GRID_MINUTES;
    snapped.setMinutes(roundedMinutes, 0, 0);
    return snapped;
  };

  // Check if a time range is free (no conflicts)
  const isFree = (start: Date, end: Date, excludeTaskIds: number[] = []): boolean => {
    return !tasks.some(t => {
      if (excludeTaskIds.includes(t.id)) return false;
      const taskEnd = new Date(t.startTime.getTime() + t.duration * 60000);
      return (start < taskEnd && end > t.startTime);
    });
  };

  // Find overlapping tasks in a time range
  const findOverlaps = (start: Date, end: Date, excludeTaskIds: number[] = []): CalendarTask[] => {
    return tasks.filter(t => {
      if (excludeTaskIds.includes(t.id)) return false;
      const taskEnd = new Date(t.startTime.getTime() + t.duration * 60000);
      return (start < taskEnd && end > t.startTime);
    });
  };

  // Find next contiguous free slot (for displacement)
  const findNextContiguousFreeSlot = (duration: number, earliestStart: Date, excludeTaskIds: number[] = []): Date | null => {
    const gridStart = snapToGrid(earliestStart);
    const dayEnd = new Date(selectedDate);
    dayEnd.setHours(23, 45, 0, 0); // End at 23:45

    for (let offset = 0; offset < 24 * 60; offset += GRID_MINUTES) {
      const slotStart = new Date(gridStart.getTime() + offset * 60000);
      if (slotStart > dayEnd) break;

      const slotEnd = new Date(slotStart.getTime() + duration * 60000);
      if (isFree(slotStart, slotEnd, excludeTaskIds)) {
        return slotStart;
      }
    }

    return null;
  };

  // Main displacement algorithm with cascade
  const tryPlaceWithDisplacement = (
    task: CalendarTask,
    desiredStart: Date,
    workingTasks: CalendarTask[],
    reasons: DisplacementReason[],
    hops = 0
  ): { success: boolean; updatedTasks: CalendarTask[]; reasons: DisplacementReason[] } => {
    if (hops > MAX_DISPLACEMENT_HOPS) {
      return { success: false, updatedTasks: workingTasks, reasons };
    }

    const desiredEnd = new Date(desiredStart.getTime() + task.duration * 60000);
    const overlaps = findOverlaps(desiredStart, desiredEnd, [task.id]);

    // No overlaps - place directly
    if (overlaps.length === 0) {
      const updated = workingTasks.map(t =>
        t.id === task.id ? { ...task, startTime: desiredStart } : t
      );
      reasons.push({
        blockId: task.id,
        summary: `Placed at ${desiredStart.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`,
        timestamp: new Date().toISOString(),
      });
      return { success: true, updatedTasks: updated, reasons };
    }

    // Check if any overlap is locked - cannot displace
    const hasLockedConflict = overlaps.some(t => t.locked);
    if (hasLockedConflict) {
      // Try to find nearest free slot at or after desired start
      const fallbackSlot = findNextContiguousFreeSlot(task.duration, desiredStart, [task.id]);
      if (!fallbackSlot) {
        return { success: false, updatedTasks: workingTasks, reasons };
      }

      const updated = workingTasks.map(t =>
        t.id === task.id ? { ...task, startTime: fallbackSlot } : t
      );
      const lockedTask = overlaps.find(t => t.locked);
      reasons.push({
        blockId: task.id,
        summary: `Conflict with locked '${lockedTask?.title}'. Placed at ${fallbackSlot.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`,
        timestamp: new Date().toISOString(),
      });
      return { success: true, updatedTasks: updated, reasons };
    }

    // Displace movable overlapping tasks (sorted by start time)
    let mutatedTasks = [...workingTasks];
    const sortedOverlaps = [...overlaps].sort((a, b) =>
      a.startTime.getTime() - b.startTime.getTime()
    );

    for (const overlap of sortedOverlaps) {
      // Find next free slot for the displaced task
      const nextSlot = findNextContiguousFreeSlot(
        overlap.duration,
        desiredEnd,
        [overlap.id, task.id]
      );

      if (!nextSlot) {
        return { success: false, updatedTasks: workingTasks, reasons };
      }

      // Move the overlapping task
      mutatedTasks = mutatedTasks.map(t =>
        t.id === overlap.id ? { ...t, startTime: nextSlot } : t
      );

      reasons.push({
        blockId: overlap.id,
        summary: `Moved to ${nextSlot.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })} due to placement of '${task.title}'`,
        timestamp: new Date().toISOString(),
      });

      // Check if this creates new overlaps (cascade)
      const newEnd = new Date(nextSlot.getTime() + overlap.duration * 60000);
      const newOverlaps = mutatedTasks.filter(t => {
        if (t.id === overlap.id || t.id === task.id) return false;
        const tEnd = new Date(t.startTime.getTime() + t.duration * 60000);
        return (nextSlot < tEnd && newEnd > t.startTime);
      });

      if (newOverlaps.length > 0) {
        // Recursively displace the newly overlapped tasks
        const cascadeResult = tryPlaceWithDisplacement(
          overlap,
          nextSlot,
          mutatedTasks,
          reasons,
          hops + 1
        );
        if (!cascadeResult.success) {
          return { success: false, updatedTasks: workingTasks, reasons };
        }
        mutatedTasks = cascadeResult.updatedTasks;
      }
    }

    // Place the original task
    mutatedTasks = mutatedTasks.map(t =>
      t.id === task.id ? { ...task, startTime: desiredStart } : t
    );

    reasons.push({
      blockId: task.id,
      summary: `Placed at ${desiredStart.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })} after displacing ${sortedOverlaps.length} task(s)`,
      timestamp: new Date().toISOString(),
    });

    return { success: true, updatedTasks: mutatedTasks, reasons };
  };

  // Handle task drop with displacement
  const handleTaskDrop = async (taskId: number, pointerTime: Date) => {
    const task = tasks.find(t => t.id === taskId);
    if (!task || task.locked) return;

    const desiredStart = snapToGrid(pointerTime);
    const reasons: DisplacementReason[] = [];

    const result = tryPlaceWithDisplacement(task, desiredStart, tasks, reasons);

    if (!result.success) {
      Alert.alert(
        'No Space Available',
        'Day is full. Try splitting tasks or move to tomorrow.',
        [{ text: 'OK' }]
      );
      return;
    }

    // Animate and update tasks
    setTasks(result.updatedTasks);
    setDisplacementReasons(reasons);

    // Update all moved tasks in backend
    try {
      const updates = result.updatedTasks
        .filter(t => {
          const original = tasks.find(orig => orig.id === t.id);
          return original && original.startTime.getTime() !== t.startTime.getTime();
        })
        .map(t => {
          const timeStr = `${t.startTime.getHours().toString().padStart(2, '0')}:${t.startTime.getMinutes().toString().padStart(2, '0')}`;
          return todosAPI.update(t.id, { scheduled_time: timeStr });
        });

      await Promise.all(updates);

      // Show summary toast
      const movedTasks = reasons.filter(r => r.blockId !== taskId);
      if (movedTasks.length > 0) {
        const summary = movedTasks.map(r => `${tasks.find(t => t.id === r.blockId)?.title}`).join(', ');
        setLastAction(`Moved ${summary} to accommodate drop`);
        setTimeout(() => setLastAction(null), 3000);
      }
    } catch (error) {
      console.error('Failed to update tasks:', error);
      Alert.alert('Error', 'Failed to update some tasks');
    }
  };

  const toggleLock = (taskId: number) => {
    const newTasks = tasks.map(t =>
      t.id === taskId ? { ...t, locked: !t.locked } : t
    );
    setTasks(newTasks);
  };

  const markTaskDone = async (taskId: number) => {
    try {
      await todosAPI.markDone(taskId);
      // Remove from calendar
      setTasks(tasks.filter(t => t.id !== taskId));
      setLastAction('Task marked as done!');
      setTimeout(() => setLastAction(null), 3000);
      Alert.alert('Success', 'Task marked as done!');
    } catch (error) {
      console.error('Failed to mark task as done:', error);
      Alert.alert('Error', 'Failed to mark task as done');
    }
  };

  const skipTask = async (taskId: number) => {
    try {
      await todosAPI.skipTodo(taskId, 'Skipped from calendar');
      // Remove from calendar
      setTasks(tasks.filter(t => t.id !== taskId));
      setLastAction('Task skipped');
      setTimeout(() => setLastAction(null), 3000);
      Alert.alert('Success', 'Task skipped');
    } catch (error) {
      console.error('Failed to skip task:', error);
      Alert.alert('Error', 'Failed to skip task');
    }
  };

  const getTaskColor = (task: CalendarTask) => {
    // If task is done, return greyed out color
    if (task.status === 'done') {
      return '#4A4A4A'; // Dark grey for completed tasks
    }

    switch (task.type) {
      case 'external': return COLORS.externalEvent;
      case 'plan': return COLORS.planTask;
      case 'adhoc': return COLORS.adHocTask;
      case 'opportunity': return COLORS.opportunityTask;
      default: return COLORS.planTask;
    }
  };

  const renderTimeline = () => {
    // Simpler non-overlapping layout: just stack tasks side by side if they overlap
    interface TaskWithPosition {
      task: CalendarTask;
      topOffset: number;
      taskHeight: number;
      column: number;
    }

    const tasksWithColumns: TaskWithPosition[] = [];

    // Sort tasks by start time
    const sortedTasks = [...tasks].sort((a, b) => {
      const aTime = a.startTime.getTime();
      const bTime = b.startTime.getTime();
      return aTime - bTime;
    });

    sortedTasks.forEach((task) => {
      const topOffset =
        task.startTime.getHours() * HOUR_HEIGHT +
        (task.startTime.getMinutes() / 60) * HOUR_HEIGHT;
      const taskHeight = (task.duration / 60) * HOUR_HEIGHT;
      const endOffset = topOffset + taskHeight;

      // Find all tasks that overlap with this one
      const overlapping = tasksWithColumns.filter(t => {
        const tEnd = t.topOffset + t.taskHeight;
        return (topOffset < tEnd && endOffset > t.topOffset);
      });

      // Assign to the first free column
      let column = 0;
      const usedColumns = new Set(overlapping.map(t => t.column));
      while (usedColumns.has(column)) {
        column++;
      }

      tasksWithColumns.push({
        task,
        topOffset,
        taskHeight,
        column,
      });
    });

    return (
      <View style={styles.timeline}>
        {HOURS.map((hour) => (
          <View key={hour} style={styles.hourRow}>
            <View style={styles.hourLabel}>
              <Text style={styles.hourText}>
                {hour.toString().padStart(2, '0')}:00
              </Text>
            </View>
            <View style={styles.hourLine}>
              {/* Energy band shading */}
              {hour >= energyPeak.start && hour < energyPeak.end && (
                <View style={styles.energyBand} />
              )}
            </View>
          </View>
        ))}

        {/* Render tasks */}
        {tasksWithColumns.map(({ task, topOffset, taskHeight, column }) => {
          // Calculate max columns needed at this task's time
          const maxCol = Math.max(
            column,
            ...tasksWithColumns
              .filter(t => {
                const tEnd = t.topOffset + t.taskHeight;
                return (topOffset < tEnd && (topOffset + taskHeight) > t.topOffset);
              })
              .map(t => t.column)
          );
          const totalColumns = maxCol + 1;

          const availableWidth = width - 90;
          const columnWidth = availableWidth / totalColumns;
          const leftOffset = 70 + (column * columnWidth);

          const isDragging = draggingTask?.id === task.id;
          const isResizing = resizingTask === task.id;
          const showHandles = showResizeHandles === task.id;

          // Create pan responder for drag (move task)
          const panResponder = PanResponder.create({
            onStartShouldSetPanResponder: () => !task.locked && !showHandles,
            onStartShouldSetPanResponderCapture: () => false,
            onMoveShouldSetPanResponder: (_, gestureState) => {
              return !showHandles && Math.abs(gestureState.dy) > 5;
            },
            onMoveShouldSetPanResponderCapture: () => false,
            onPanResponderGrant: () => {
              // Start long-press timer to show resize handles
              longPressTimer.current = setTimeout(() => {
                setShowResizeHandles(task.id);
                setLastAction('Drag handles to resize');
              }, 500);

              setDraggingTask(task);
              // Initialize animation for this task if not exists
              if (!taskAnimations.has(task.id)) {
                taskAnimations.set(task.id, new Animated.ValueXY());
              }
            },
            onPanResponderMove: (_, gestureState) => {
              // Clear long press timer if user moves significantly
              if (Math.abs(gestureState.dy) > 5 && longPressTimer.current) {
                clearTimeout(longPressTimer.current);
                longPressTimer.current = null;
              }

              const anim = taskAnimations.get(task.id);
              if (anim) {
                // Normal drag mode - move task
                anim.setValue({ x: 0, y: gestureState.dy });
              }
            },
            onPanResponderRelease: (_, gestureState) => {
              // Clear long-press timer
              if (longPressTimer.current) {
                clearTimeout(longPressTimer.current);
                longPressTimer.current = null;
              }

              const anim = taskAnimations.get(task.id);
              if (anim) {
                // Only process if dragged significantly
                if (Math.abs(gestureState.dy) > 5) {
                  // Calculate new time based on drag distance
                  const draggedMinutes = (gestureState.dy / HOUR_HEIGHT) * 60;
                  const newTime = new Date(task.startTime.getTime() + draggedMinutes * 60000);

                  // Animate back to position
                  Animated.spring(anim, {
                    toValue: { x: 0, y: 0 },
                    useNativeDriver: true,
                  }).start();

                  // Handle drop
                  handleTaskDrop(task.id, newTime);
                } else {
                  // Small movement - just a tap, reset animation and open modal
                  Animated.spring(anim, {
                    toValue: { x: 0, y: 0 },
                    useNativeDriver: true,
                  }).start();

                  // Open task modal on tap
                  setSelectedTask(task);
                  setShowTaskModal(true);
                }
              }
              setDraggingTask(null);
            },
            onPanResponderTerminate: () => {
              // Clear long-press timer
              if (longPressTimer.current) {
                clearTimeout(longPressTimer.current);
                longPressTimer.current = null;
              }

              const anim = taskAnimations.get(task.id);
              if (anim) {
                Animated.spring(anim, {
                  toValue: { x: 0, y: 0 },
                  useNativeDriver: true,
                }).start();
              }
              setDraggingTask(null);
            },
          });

          // Create pan responder for resize handles
          const createHandlePanResponder = (handleType: 'top' | 'bottom') => PanResponder.create({
            onStartShouldSetPanResponder: () => true,
            onStartShouldSetPanResponderCapture: () => true,
            onMoveShouldSetPanResponder: () => true,
            onMoveShouldSetPanResponderCapture: () => true,
            onPanResponderTerminationRequest: () => false,
            onPanResponderGrant: () => {
              setResizingTask(task.id);
              setResizeMode(handleType);
              setInitialDuration(task.duration);
              setInitialStartTime(task.startTime);
            },
            onPanResponderMove: (_, gestureState) => {
              if (handleType === 'bottom') {
                // Dragging bottom handle - change duration only
                const deltaMinutes = Math.round((gestureState.dy / HOUR_HEIGHT) * 60 / 15) * 15;
                const newDuration = Math.max(15, initialDuration + deltaMinutes);

                const updatedTasks = tasks.map(t =>
                  t.id === task.id ? { ...t, duration: newDuration } : t
                );
                setTasks(updatedTasks);
              } else {
                // Dragging top handle - change start time and duration
                const deltaMinutes = Math.round((gestureState.dy / HOUR_HEIGHT) * 60 / 15) * 15;
                const newStartTime = new Date((initialStartTime || task.startTime).getTime() + deltaMinutes * 60000);
                const newDuration = Math.max(15, initialDuration - deltaMinutes);

                const updatedTasks = tasks.map(t =>
                  t.id === task.id ? { ...t, startTime: newStartTime, duration: newDuration } : t
                );
                setTasks(updatedTasks);
              }
            },
            onPanResponderRelease: () => {
              // Save changes
              const currentTask = tasks.find(t => t.id === task.id);
              if (currentTask) {
                updateTaskDuration(task.id, currentTask.duration);
                if (handleType === 'top') {
                  updateTaskTime(currentTask, currentTask.startTime);
                }
              }
              setResizingTask(null);
              setResizeMode(null);
              setShowResizeHandles(null);
              setLastAction(null);
            },
            onPanResponderTerminate: () => {
              setResizingTask(null);
              setResizeMode(null);
            },
          });

          const taskAnim = taskAnimations.get(task.id);

          return (
            <Animated.View
              key={task.id}
              {...panResponder.panHandlers}
              style={[
                styles.taskBlock,
                {
                  top: topOffset,
                  height: Math.max(taskHeight - 2, 30),
                  left: leftOffset,
                  width: columnWidth - 6,
                  backgroundColor: getTaskColor(task),
                  borderLeftWidth: task.milestone ? 4 : 0,
                  borderLeftColor: COLORS.milestoneAccent,
                  opacity: isDragging || isResizing ? 0.8 : 1,
                  zIndex: isDragging || isResizing ? 1000 : 1,
                  transform: taskAnim && !isResizing ? taskAnim.getTranslateTransform() : [],
                  shadowOpacity: isResizing ? 0.3 : 0.1,
                  shadowRadius: isResizing ? 8 : 4,
                },
              ]}
            >
              <TouchableOpacity
                onPress={() => {
                  if (!draggingTask) {
                    if (showHandles) {
                      // Dismiss handles if they're showing
                      setShowResizeHandles(null);
                    } else {
                      setSelectedTask(task);
                      setShowTaskModal(true);
                    }
                  }
                }}
                style={{ flex: 1 }}
              >
              <View style={styles.taskHeader}>
                <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
                  {task.status === 'done' && (
                    <MaterialCommunityIcons name="check-circle" size={14} color="#34C759" style={{ marginRight: 4 }} />
                  )}
                  <Text
                    style={[
                      styles.taskTitle,
                      task.status === 'done' && { textDecorationLine: 'line-through', opacity: 0.6 }
                    ]}
                    numberOfLines={1}
                  >
                    {task.title}
                  </Text>
                </View>
                <View style={styles.taskHeaderRight}>
                  {task.locked && (
                    <MaterialCommunityIcons name="lock" size={12} color="#fff" style={{ marginRight: 4 }} />
                  )}
                  <MaterialCommunityIcons name="chevron-right" size={14} color="rgba(255,255,255,0.6)" />
                </View>
              </View>
              <Text style={styles.taskMeta} numberOfLines={1}>
                {task.duration}m {task.location ? `• ${task.location}` : ''}
              </Text>
              {taskHeight > 40 && (
                <View style={styles.taskTypeChip}>
                  <Text style={styles.taskTypeText}>
                    {task.type === 'plan' ? 'Plan' : task.type === 'adhoc' ? 'Ad hoc' : task.type === 'opportunity' ? 'Opportunity' : ''}
                  </Text>
                </View>
              )}
              </TouchableOpacity>

              {/* Resize Handles - show on long press */}
              {showHandles && (
                <>
                  {/* Top Handle */}
                  <View
                    {...createHandlePanResponder('top').panHandlers}
                    style={styles.resizeHandle}
                  >
                    <View style={styles.resizeHandleDot} />
                    <View style={styles.resizeHandleDot} />
                    <View style={styles.resizeHandleDot} />
                  </View>

                  {/* Bottom Handle */}
                  <View
                    {...createHandlePanResponder('bottom').panHandlers}
                    style={[styles.resizeHandle, styles.resizeHandleBottom]}
                  >
                    <View style={styles.resizeHandleDot} />
                    <View style={styles.resizeHandleDot} />
                    <View style={styles.resizeHandleDot} />
                  </View>
                </>
              )}
            </Animated.View>
          );
        })}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Top Bar - минималистичный с только слайдером дней */}
      <View style={styles.topBar}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.daysScrollContent}
        >
          {/* Vertical container for rows */}
          <View style={{ flexDirection: 'column' }}>
            {/* Week Days Row */}
            <View style={styles.weekDaysRow}>
              {visibleDays.map((day, index) => {
                const dayNames = t('calendar.dayNames', { returnObjects: true }) as string[];
                const dayOfWeek = day.getDay(); // 0=Sunday, 1=Monday, etc.
                return (
                  <View key={`weekday-${index}`} style={styles.weekDayCell}>
                    <Text style={styles.weekDayText}>{dayNames[dayOfWeek]}</Text>
                  </View>
                );
              })}
            </View>

            {/* Days Numbers Row */}
            <View style={styles.daysNumbersRow}>
              {visibleDays.map((day) => {
                const isSelected = day.toDateString() === selectedDate.toDateString();
                const isToday = day.toDateString() === new Date().toDateString();
                return (
                  <TouchableOpacity
                    key={day.toISOString()}
                    style={[
                      styles.dayNumberButton,
                      isSelected && styles.dayNumberButtonSelected,
                    ]}
                    onPress={() => selectDay(day)}
                  >
                    <Text style={[
                      styles.dayNumberText,
                      isSelected && styles.dayNumberTextSelected,
                    ]}>
                      {day.getDate()}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>
        </ScrollView>
      </View>

      {/* Action Toast */}
      {lastAction && (
        <View style={styles.actionToast}>
          <Text style={styles.actionToastText}>{lastAction}</Text>
        </View>
      )}

      {/* Main Content */}
      <View style={styles.mainContent} {...swipePanResponder.panHandlers}>
        <Animated.View
          style={{
            flex: 1,
            transform: [{ translateX: swipeAnim }],
          }}
        >
          <ScrollView
            ref={scrollViewRef}
            style={styles.scrollView}
            showsVerticalScrollIndicator={true}
            scrollEnabled={!draggingTask && !isSwipingDay && resizingTask === null}
          >
            {renderTimeline()}
          </ScrollView>
        </Animated.View>

        {/* Right Drawer */}
        <Animated.View
          style={[
            styles.rightDrawer,
            {
              transform: [{ translateX: drawerAnim }],
            },
          ]}
        >
          <View style={styles.drawerHeader}>
            <Text style={styles.drawerTitle}>Today's Tasks</Text>
          </View>

          <View style={styles.quickAdd}>
            <TextInput
              style={styles.quickInput}
              placeholder="doc 15:00 Gangnam"
              placeholderTextColor={COLORS.textSecondary}
              value={quickInput}
              onChangeText={setQuickInput}
              onSubmitEditing={addQuickTask}
            />
            <TouchableOpacity style={styles.quickAddButton} onPress={addQuickTask}>
              <MaterialCommunityIcons name="plus" size={20} color="#fff" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.unscheduledList}>
            {unscheduledTasks.map((task) => (
              <TouchableOpacity
                key={task.id}
                style={styles.unscheduledTask}
              >
                <View style={styles.unscheduledTaskHeader}>
                  <Text style={styles.unscheduledTaskTitle}>{task.title}</Text>
                  <View style={[
                    styles.priorityDot,
                    { backgroundColor: task.priority === 3 ? COLORS.milestoneAccent : task.priority === 2 ? COLORS.opportunityTask : COLORS.textSecondary }
                  ]} />
                </View>
                <Text style={styles.unscheduledTaskMeta}>
                  {task.estimated_duration_minutes || 30}m
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </Animated.View>
      </View>

      {/* Bottom Mini Player */}
      {currentTask && (
        <View style={styles.miniPlayer}>
          <View style={styles.miniPlayerContent}>
            <View style={styles.miniPlayerInfo}>
              <Text style={styles.miniPlayerTitle}>{currentTask.title}</Text>
              <Text style={styles.miniPlayerTime}>
                {Math.floor(timeRemaining / 60)}:{(timeRemaining % 60).toString().padStart(2, '0')} remaining
              </Text>
            </View>

            <View style={styles.miniPlayerControls}>
              <TouchableOpacity
                style={styles.miniPlayerButton}
                onPress={() => Alert.alert('Chunk', 'Split into shorter tasks')}
              >
                <MaterialCommunityIcons name="timer-sand" size={20} color={COLORS.text} />
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.playButton}
                onPress={() => setIsPlaying(!isPlaying)}
              >
                <MaterialCommunityIcons
                  name={isPlaying ? 'pause' : 'play'}
                  size={24}
                  color="#fff"
                />
              </TouchableOpacity>
            </View>
          </View>
        </View>
      )}

      {/* Task Detail Modal */}
      <Modal
        visible={showTaskModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowTaskModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.taskDetailModal}>
            <View style={styles.taskDetailHeader}>
              <Text style={styles.taskDetailTitle}>{selectedTask?.title}</Text>
              <TouchableOpacity onPress={() => setShowTaskModal(false)}>
                <MaterialCommunityIcons name="close" size={24} color={COLORS.text} />
              </TouchableOpacity>
            </View>

            <View style={styles.taskDetailInfo}>
              <View style={styles.taskDetailRow}>
                <MaterialCommunityIcons name="clock-outline" size={20} color={COLORS.textSecondary} />
                <Text style={styles.taskDetailText}>
                  {selectedTask?.startTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })} • {selectedTask?.duration}min
                </Text>
              </View>

              {selectedTask?.location && (
                <View style={styles.taskDetailRow}>
                  <MaterialCommunityIcons name="map-marker" size={20} color={COLORS.textSecondary} />
                  <Text style={styles.taskDetailText}>{selectedTask.location}</Text>
                </View>
              )}

              <View style={styles.taskDetailRow}>
                <MaterialCommunityIcons name="flag" size={20} color={COLORS.textSecondary} />
                <Text style={styles.taskDetailText}>
                  Priority: {selectedTask?.priority === 3 ? 'High' : selectedTask?.priority === 2 ? 'Medium' : 'Low'}
                </Text>
              </View>

              <View style={styles.taskDetailRow}>
                <MaterialCommunityIcons name="tag" size={20} color={COLORS.textSecondary} />
                <Text style={styles.taskDetailText}>
                  Type: {selectedTask?.type === 'plan' ? 'Plan' : selectedTask?.type === 'adhoc' ? 'Ad hoc' : selectedTask?.type === 'opportunity' ? 'Opportunity' : 'External'}
                </Text>
              </View>
            </View>

            <View style={styles.taskDetailActions}>
              <TouchableOpacity
                style={styles.taskActionButton}
                onPress={() => {
                  if (selectedTask) splitTask(selectedTask.id);
                  setShowTaskModal(false);
                }}
              >
                <MaterialCommunityIcons name="call-split" size={20} color={COLORS.text} />
                <Text style={styles.taskActionText}>Split</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.taskActionButton}
                onPress={() => {
                  if (selectedTask) snoozeTask(selectedTask.id, 15);
                  setShowTaskModal(false);
                }}
              >
                <MaterialCommunityIcons name="clock-plus-outline" size={20} color={COLORS.text} />
                <Text style={styles.taskActionText}>Snooze 15m</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.taskActionButton}
                onPress={() => {
                  if (selectedTask) snoozeTask(selectedTask.id, 30);
                  setShowTaskModal(false);
                }}
              >
                <MaterialCommunityIcons name="clock-plus-outline" size={20} color={COLORS.text} />
                <Text style={styles.taskActionText}>Snooze 30m</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.taskActionButton}
                onPress={() => {
                  if (selectedTask) toggleLock(selectedTask.id);
                  setShowTaskModal(false);
                }}
              >
                <MaterialCommunityIcons
                  name={selectedTask?.locked ? "lock-open" : "lock"}
                  size={20}
                  color={COLORS.text}
                />
                <Text style={styles.taskActionText}>
                  {selectedTask?.locked ? 'Unlock' : 'Lock'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.taskActionButton, styles.doneButton]}
                onPress={() => {
                  if (selectedTask) {
                    markTaskDone(selectedTask.id);
                    setShowTaskModal(false);
                  }
                }}
              >
                <MaterialCommunityIcons name="check-circle" size={20} color="#fff" />
                <Text style={[styles.taskActionText, styles.doneButtonText]}>Done</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.taskActionButton, styles.skipButton]}
                onPress={() => {
                  if (selectedTask) {
                    skipTask(selectedTask.id);
                    setShowTaskModal(false);
                  }
                }}
              >
                <MaterialCommunityIcons name="skip-next" size={20} color="#fff" />
                <Text style={[styles.taskActionText, styles.skipButtonText]}>Skip</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Full Calendar Modal */}
      <Modal
        visible={showFullCalendar}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowFullCalendar(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.fullCalendarModal}>
            <View style={styles.fullCalendarHeader}>
              <TouchableOpacity
                onPress={() => {
                  const newMonth = new Date(calendarMonth);
                  newMonth.setMonth(newMonth.getMonth() - 1);
                  setCalendarMonth(newMonth);
                }}
              >
                <MaterialCommunityIcons name="chevron-left" size={28} color={COLORS.text} />
              </TouchableOpacity>
              <Text style={styles.fullCalendarTitle}>
                {calendarMonth.toLocaleString('default', { month: 'long', year: 'numeric' })}
              </Text>
              <TouchableOpacity
                onPress={() => {
                  const newMonth = new Date(calendarMonth);
                  newMonth.setMonth(newMonth.getMonth() + 1);
                  setCalendarMonth(newMonth);
                }}
              >
                <MaterialCommunityIcons name="chevron-right" size={28} color={COLORS.text} />
              </TouchableOpacity>
            </View>

            <View style={styles.calendarGrid}>
              {getDaysInMonth(calendarMonth).map((day) => {
                const isSelected = day.toDateString() === selectedDate.toDateString();
                const isToday = day.toDateString() === new Date().toDateString();
                return (
                  <TouchableOpacity
                    key={day.toISOString()}
                    style={[
                      styles.calendarDay,
                      isSelected && styles.calendarDaySelected,
                      isToday && styles.calendarDayToday,
                    ]}
                    onPress={() => {
                      selectDay(day);
                      setCalendarMonth(day);
                    }}
                  >
                    <Text
                      style={[
                        styles.calendarDayText,
                        isSelected && styles.calendarDayTextSelected,
                        isToday && !isSelected && styles.calendarDayTextToday,
                      ]}
                    >
                      {day.getDate()}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>

            <TouchableOpacity
              style={styles.closeCalendarButton}
              onPress={() => setShowFullCalendar(false)}
            >
              <Text style={styles.closeCalendarText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  dayPickerContainer: {
    backgroundColor: COLORS.surface,
    paddingTop: 60,
    paddingBottom: 8,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  dayPickerRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dayPickerContent: {
    paddingRight: 8,
  },
  dayButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.bg,
    borderWidth: 1,
    borderColor: COLORS.border,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 4,
  },
  dayButtonSelected: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  dayButtonToday: {
    borderColor: COLORS.primary,
    borderWidth: 2,
  },
  dayButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  dayButtonTextSelected: {
    color: '#fff',
  },
  calendarExpandButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.bg,
    borderWidth: 1,
    borderColor: COLORS.border,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 4,
  },
  topBar: {
    paddingTop: 12,
    paddingBottom: 12,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  daysScrollContent: {
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  weekDaysRow: {
    flexDirection: 'row',
    marginBottom: 6,
    gap: 10,
  },
  weekDayCell: {
    width: 32,
    alignItems: 'center',
  },
  weekDayText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.text,
  },
  daysNumbersRow: {
    flexDirection: 'row',
    gap: 10,
  },
  dayNumberButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  dayNumberButtonSelected: {
    backgroundColor: COLORS.primary,
  },
  dayNumberText: {
    fontSize: 16,
    fontWeight: '500',
    color: COLORS.textSecondary,
  },
  dayNumberTextSelected: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  todayButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: COLORS.primary,
    borderRadius: 6,
    marginRight: 10,
  },
  todayButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  dateText: {
    color: COLORS.text,
    fontSize: 14,
    fontWeight: '600',
  },
  // Inline week days in topBar
  inlineWeekDays: {
    marginLeft: 8,
  },
  weekDaysInlineRow: {
    flexDirection: 'row',
    marginBottom: 4,
  },
  weekDayInlineCell: {
    width: 32,
    alignItems: 'center',
    marginRight: 4,
  },
  weekDayInlineText: {
    fontSize: 10,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  daysButtonsRow: {
    flexDirection: 'row',
  },
  inlineDayButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.bg,
    borderWidth: 1,
    borderColor: COLORS.border,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 4,
  },
  inlineDayButtonSelected: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  inlineDayButtonToday: {
    borderColor: COLORS.primary,
    borderWidth: 2,
  },
  inlineDayButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  inlineDayButtonTextSelected: {
    color: '#fff',
  },
  calendarIconButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.bg,
    borderWidth: 1,
    borderColor: COLORS.border,
    justifyContent: 'center',
    alignItems: 'center',
  },
  drawerToggleButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.bg,
    borderWidth: 1,
    borderColor: COLORS.border,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 'auto',
  },
  viewToggle: {
    flexDirection: 'row',
    backgroundColor: COLORS.bg,
    borderRadius: 6,
    padding: 2,
  },
  viewToggleButton: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 4,
    minWidth: 28,
    alignItems: 'center',
    marginHorizontal: 1,
  },
  viewToggleButtonActive: {
    backgroundColor: COLORS.primary,
  },
  viewToggleText: {
    color: COLORS.textSecondary,
    fontSize: 11,
    fontWeight: '600',
  },
  viewToggleTextActive: {
    color: '#fff',
  },
  timeBudget: {
    gap: 4,
  },
  timeBudgetLabel: {
    fontSize: 10,
    color: COLORS.textSecondary,
  },
  timeBudgetBar: {
    width: 100,
    height: 4,
    backgroundColor: COLORS.border,
    borderRadius: 2,
    overflow: 'hidden',
  },
  timeBudgetFill: {
    height: '100%',
    borderRadius: 2,
  },
  timeBudgetText: {
    fontSize: 10,
    color: COLORS.text,
  },
  energyChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: COLORS.bg,
    borderRadius: 12,
  },
  energyChipText: {
    fontSize: 11,
    color: COLORS.text,
  },
  drawerToggle: {
    padding: 4,
  },
  actionToast: {
    position: 'absolute',
    top: 120,
    left: '50%',
    transform: [{ translateX: -150 }],
    width: 300,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.primary,
    borderRadius: 8,
    padding: 12,
    zIndex: 1000,
  },
  actionToastText: {
    color: COLORS.text,
    fontSize: 13,
    textAlign: 'center',
  },
  mainContent: {
    flex: 1,
    flexDirection: 'row',
  },
  scrollView: {
    flex: 1,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
    gap: 16,
  },
  emptyStateText: {
    color: COLORS.textSecondary,
    fontSize: 14,
    textAlign: 'center',
    maxWidth: 250,
  },
  timeline: {
    position: 'relative',
    paddingBottom: 100,
  },
  hourRow: {
    flexDirection: 'row',
    height: HOUR_HEIGHT,
  },
  hourLabel: {
    width: 60,
    paddingRight: 8,
    paddingTop: 4,
    alignItems: 'flex-end',
  },
  hourText: {
    fontSize: 11,
    color: COLORS.textSecondary,
  },
  hourLine: {
    flex: 1,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    position: 'relative',
  },
  energyBand: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: COLORS.energyPeak,
  },
  taskBlock: {
    position: 'absolute',
    borderRadius: 8,
    padding: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  taskHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  taskTitle: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
    flex: 1,
  },
  taskMeta: {
    color: 'rgba(255,255,255,0.8)',
    fontSize: 11,
    marginBottom: 4,
  },
  taskTypeChip: {
    alignSelf: 'flex-start',
    paddingHorizontal: 6,
    paddingVertical: 2,
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 4,
  },
  taskTypeText: {
    color: '#fff',
    fontSize: 9,
    fontWeight: '600',
  },
  rightDrawer: {
    position: 'absolute',
    top: 0,
    right: 0,
    bottom: 0,
    width: width * 0.7,
    backgroundColor: COLORS.surface,
    borderLeftWidth: 1,
    borderLeftColor: COLORS.border,
  },
  drawerHeader: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  drawerTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  quickAdd: {
    flexDirection: 'row',
    padding: 12,
    gap: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  quickInput: {
    flex: 1,
    backgroundColor: COLORS.bg,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    color: COLORS.text,
    fontSize: 13,
  },
  quickAddButton: {
    width: 40,
    height: 40,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  unscheduledList: {
    flex: 1,
  },
  unscheduledTask: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  unscheduledTaskHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  unscheduledTaskTitle: {
    color: COLORS.text,
    fontSize: 13,
    fontWeight: '500',
    flex: 1,
  },
  priorityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  unscheduledTaskMeta: {
    color: COLORS.textSecondary,
    fontSize: 11,
  },
  miniPlayer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    paddingBottom: 80, // Space for tab bar
  },
  miniPlayerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 12,
  },
  miniPlayerInfo: {
    flex: 1,
  },
  miniPlayerTitle: {
    color: COLORS.text,
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  miniPlayerTime: {
    color: COLORS.textSecondary,
    fontSize: 12,
  },
  miniPlayerControls: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  miniPlayerButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: COLORS.bg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  playButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  taskHeaderRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  taskDetailModal: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 400,
  },
  taskDetailHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  taskDetailTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
    flex: 1,
    marginRight: 12,
  },
  taskDetailInfo: {
    marginBottom: 20,
  },
  taskDetailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  taskDetailText: {
    fontSize: 15,
    color: COLORS.text,
    marginLeft: 12,
  },
  taskDetailActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -6,
  },
  taskActionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.bg,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    margin: 6,
    minWidth: '45%',
  },
  taskActionText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
    marginLeft: 8,
  },
  doneButton: {
    backgroundColor: '#34C759',
    borderColor: '#34C759',
  },
  doneButtonText: {
    color: '#fff',
  },
  skipButton: {
    backgroundColor: '#FF9500',
    borderColor: '#FF9500',
  },
  skipButtonText: {
    color: '#fff',
  },
  fullCalendarModal: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 20,
    padding: 24,
    width: '90%',
    maxHeight: '80%',
  },
  fullCalendarHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  fullCalendarTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  calendarGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  calendarDay: {
    width: '13%',
    aspectRatio: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
    borderRadius: 8,
    backgroundColor: COLORS.bg,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  calendarDaySelected: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  calendarDayToday: {
    borderColor: COLORS.primary,
    borderWidth: 2,
  },
  calendarDayText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  calendarDayTextSelected: {
    color: '#fff',
  },
  calendarDayTextToday: {
    color: COLORS.primary,
  },
  closeCalendarButton: {
    backgroundColor: COLORS.bg,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
  closeCalendarText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  resizeHandle: {
    position: 'absolute',
    top: -12,
    left: 0,
    right: 0,
    height: 24,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 4,
    zIndex: 1001,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    borderRadius: 12,
  },
  resizeHandleBottom: {
    top: undefined,
    bottom: -12,
  },
  resizeHandleDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
  },
});
