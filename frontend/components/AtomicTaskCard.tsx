import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useState } from 'react';
import { useRouter } from 'expo-router';

interface DefinitionOfDone {
  text: string;
  weight: number;
  completed: boolean;
}

interface AtomicTaskCardProps {
  task: {
    id: number;
    title: string;
    description?: string;
    task_type: 'auto' | 'copilot' | 'manual';
    timebox_minutes: number;
    deliverable_type: string;
    definition_of_done: DefinitionOfDone[];
    progress_percentage: number;
    priority: number;
    status: string;
    scheduled_time?: string;
    external_url?: string;
    blocked_by?: number[];
  };
  onMarkDone: (id: number) => void;
  onSkip: (id: number) => void;
  onLetsGo?: (id: number) => void;
  onToggleDoDItem?: (taskId: number, itemIndex: number) => void;
  onViewDetails?: (id: number) => void;
}

export default function AtomicTaskCard({
  task,
  onMarkDone,
  onSkip,
  onLetsGo,
  onToggleDoDItem,
  onViewDetails
}: AtomicTaskCardProps) {
  const [expanded, setExpanded] = useState(false);
  const router = useRouter();

  const getTaskTypeIcon = (type: string) => {
    switch (type) {
      case 'auto': return 'robot';
      case 'copilot': return 'account-supervisor';
      case 'manual': return 'account';
      default: return 'circle-outline';
    }
  };

  const getTaskTypeColor = (type: string) => {
    switch (type) {
      case 'auto': return '#34C759';
      case 'copilot': return '#007AFF';
      case 'manual': return '#FF9500';
      default: return '#999';
    }
  };

  const getPriorityColor = (priority: number) => {
    switch (priority) {
      case 3: return '#FF3B30';
      case 2: return '#FF9500';
      case 1: return '#34C759';
      default: return '#999';
    }
  };

  const getDeliverableIcon = (type: string) => {
    const icons: { [key: string]: string } = {
      spreadsheet: 'table',
      doc: 'file-document',
      email: 'email',
      recording: 'microphone',
      link: 'link',
      shortlist: 'format-list-bulleted',
      file: 'file',
      note: 'note-text',
      other: 'circle-outline'
    };
    return icons[type] || 'circle-outline';
  };

  const isBlocked = task.blocked_by && task.blocked_by.length > 0;

  return (
    <View style={[styles.card, isBlocked && styles.cardBlocked]}>
      {/* Header Row */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={[styles.priorityDot, { backgroundColor: getPriorityColor(task.priority) }]} />
          <Text style={styles.title} numberOfLines={expanded ? undefined : 2}>
            {task.title}
          </Text>
        </View>

        <TouchableOpacity onPress={() => setExpanded(!expanded)}>
          <MaterialCommunityIcons
            name={expanded ? 'chevron-up' : 'chevron-down'}
            size={20}
            color="#8E8E8E"
          />
        </TouchableOpacity>
      </View>

      {/* Meta Info Row */}
      <View style={styles.metaRow}>
        {/* Task Type Badge */}
        <View style={[styles.badge, { backgroundColor: getTaskTypeColor(task.task_type) + '20' }]}>
          <MaterialCommunityIcons
            name={getTaskTypeIcon(task.task_type)}
            size={12}
            color={getTaskTypeColor(task.task_type)}
          />
          <Text style={[styles.badgeText, { color: getTaskTypeColor(task.task_type) }]}>
            {task.task_type}
          </Text>
        </View>

        {/* Timebox */}
        <View style={styles.badge}>
          <MaterialCommunityIcons name="clock-outline" size={12} color="#8E8E8E" />
          <Text style={styles.badgeText}>{task.timebox_minutes}m</Text>
        </View>

        {/* Deliverable */}
        <View style={styles.badge}>
          <MaterialCommunityIcons
            name={getDeliverableIcon(task.deliverable_type) as any}
            size={12}
            color="#8E8E8E"
          />
          <Text style={styles.badgeText}>{task.deliverable_type}</Text>
        </View>

        {isBlocked && (
          <View style={[styles.badge, styles.blockedBadge]}>
            <MaterialCommunityIcons name="lock" size={12} color="#FF3B30" />
            <Text style={[styles.badgeText, { color: '#FF3B30' }]}>Blocked</Text>
          </View>
        )}
      </View>

      {/* Progress Bar */}
      <View style={styles.progressContainer}>
        <View style={styles.progressBar}>
          <View
            style={[
              styles.progressFill,
              { width: `${task.progress_percentage}%` }
            ]}
          />
        </View>
        <Text style={styles.progressText}>{task.progress_percentage}%</Text>
      </View>

      {/* Expanded Content */}
      {expanded && (
        <View style={styles.expandedContent}>
          {/* Description */}
          {task.description && (
            <Text style={styles.description}>{task.description}</Text>
          )}

          {/* Definition of Done */}
          {task.definition_of_done && task.definition_of_done.length > 0 && (
            <View style={styles.dodSection}>
              <Text style={styles.dodTitle}>Definition of Done</Text>
              {task.definition_of_done.map((item, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.dodItem}
                  onPress={() => onToggleDoDItem?.(task.id, index)}
                >
                  <MaterialCommunityIcons
                    name={item.completed ? 'checkbox-marked' : 'checkbox-blank-outline'}
                    size={20}
                    color={item.completed ? '#34C759' : '#8E8E8E'}
                  />
                  <Text style={[styles.dodText, item.completed && styles.dodTextCompleted]}>
                    {item.text}
                  </Text>
                  <Text style={styles.dodWeight}>{item.weight}%</Text>
                </TouchableOpacity>
              ))}
            </View>
          )}

          {/* External Link */}
          {task.external_url && (
            <TouchableOpacity style={styles.externalLink}>
              <MaterialCommunityIcons name="open-in-new" size={16} color="#007AFF" />
              <Text style={styles.externalLinkText}>View Resource</Text>
            </TouchableOpacity>
          )}

          {/* Ask AI Button */}
          <TouchableOpacity
            style={styles.askAIButtonContainer}
            onPress={() => router.push(`/task/${task.id}`)}
            activeOpacity={0.8}
          >
            <LinearGradient
              colors={['#667eea', '#764ba2', '#f093fb']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.askAIButton}
            >
              <MaterialCommunityIcons name="sparkles" as any size={18} color="#fff" />
              <Text style={styles.askAIButtonText}>Ask AI</Text>
            </LinearGradient>
          </TouchableOpacity>

          {/* Action Buttons */}
          <View style={styles.actions}>
            {task.task_type === 'copilot' && onLetsGo && (
              <TouchableOpacity
                style={[styles.actionButton, styles.letsGoButton]}
                onPress={() => onLetsGo(task.id)}
              >
                <MaterialCommunityIcons name="chat" size={16} color="#fff" />
                <Text style={styles.actionButtonText}>Let's Go</Text>
              </TouchableOpacity>
            )}

            <TouchableOpacity
              style={[styles.actionButton, styles.doneButton]}
              onPress={() => onMarkDone(task.id)}
            >
              <MaterialCommunityIcons name="check" size={16} color="#fff" />
              <Text style={styles.actionButtonText}>Done</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.actionButton, styles.skipButton]}
              onPress={() => onSkip(task.id)}
            >
              <MaterialCommunityIcons name="skip-next" size={16} color="#fff" />
              <Text style={styles.actionButtonText}>Skip</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Compact Actions (when collapsed) */}
      {!expanded && (
        <View style={styles.compactActions}>
          {task.task_type === 'copilot' && onLetsGo && (
            <TouchableOpacity
              style={styles.compactButton}
              onPress={() => onLetsGo(task.id)}
            >
              <MaterialCommunityIcons name="chat" size={16} color="#007AFF" />
            </TouchableOpacity>
          )}

          <TouchableOpacity
            style={styles.compactButton}
            onPress={() => onMarkDone(task.id)}
          >
            <MaterialCommunityIcons name="check" size={16} color="#34C759" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.compactButton}
            onPress={() => onSkip(task.id)}
          >
            <MaterialCommunityIcons name="skip-next" size={16} color="#FF9500" />
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#2A2A2A',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#3E3E3E',
  },
  cardBlocked: {
    opacity: 0.7,
    borderColor: '#FF3B30',
    borderWidth: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  headerLeft: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  priorityDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 6,
  },
  title: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    color: '#ECECEC',
    lineHeight: 22,
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: '#1A1A1A',
  },
  blockedBadge: {
    backgroundColor: '#FF3B3020',
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '500',
    color: '#8E8E8E',
    textTransform: 'capitalize',
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  progressBar: {
    flex: 1,
    height: 6,
    backgroundColor: '#1A1A1A',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#34C759',
    borderRadius: 3,
  },
  progressText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#8E8E8E',
    width: 35,
    textAlign: 'right',
  },
  expandedContent: {
    borderTopWidth: 1,
    borderTopColor: '#3E3E3E',
    paddingTop: 12,
  },
  description: {
    fontSize: 14,
    color: '#ECECEC',
    lineHeight: 20,
    marginBottom: 12,
  },
  dodSection: {
    marginBottom: 12,
  },
  dodTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#ECECEC',
    marginBottom: 8,
  },
  dodItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 6,
  },
  dodText: {
    flex: 1,
    fontSize: 14,
    color: '#ECECEC',
  },
  dodTextCompleted: {
    color: '#8E8E8E',
    textDecorationLine: 'line-through',
  },
  dodWeight: {
    fontSize: 12,
    fontWeight: '500',
    color: '#8E8E8E',
  },
  externalLink: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 8,
    marginBottom: 12,
  },
  externalLinkText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },
  askAIButtonContainer: {
    marginBottom: 12,
  },
  askAIButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 10,
  },
  askAIButtonText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#fff',
    letterSpacing: 0.5,
  },
  actions: {
    flexDirection: 'row',
    gap: 8,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: 10,
    borderRadius: 8,
  },
  letsGoButton: {
    backgroundColor: '#007AFF',
  },
  doneButton: {
    backgroundColor: '#34C759',
  },
  skipButton: {
    backgroundColor: '#FF9500',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
  compactActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 8,
    marginTop: 8,
  },
  compactButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#1A1A1A',
    borderWidth: 1,
    borderColor: '#3E3E3E',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
