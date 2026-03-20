import React, { useState } from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  ScrollView,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { taskSplitterAPI } from '@/services/api';

interface SubTask {
  id: number;
  title: string;
  scheduled_date: string;
  timebox_minutes: number;
  sequence_order: number;
}

interface TaskSplitButtonProps {
  taskId: number;
  taskTitle: string;
  onSplitComplete?: () => void;
}

export default function TaskSplitButton({
  taskId,
  taskTitle,
  onSplitComplete,
}: TaskSplitButtonProps) {
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [subtasks, setSubtasks] = useState<SubTask[]>([]);
  const [splitComplete, setSplitComplete] = useState(false);

  const handleSplitTask = async () => {
    try {
      setLoading(true);
      const response = await taskSplitterAPI.splitTask(taskId);
      const data = response.data;

      setSubtasks(data.subtasks || []);
      setSplitComplete(true);
    } catch (error) {
      console.error('Failed to split task:', error);
      Alert.alert('Error', 'Failed to split task. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setShowModal(false);
    setSplitComplete(false);
    setSubtasks([]);

    if (splitComplete && onSplitComplete) {
      onSplitComplete();
    }
  };

  return (
    <>
      <TouchableOpacity
        style={styles.splitButton}
        onPress={() => setShowModal(true)}
      >
        <MaterialCommunityIcons name="scissors-cutting" size={18} color="#007AFF" />
        <Text style={styles.splitButtonText}>Split Task</Text>
      </TouchableOpacity>

      <Modal
        visible={showModal}
        animationType="slide"
        transparent={true}
        onRequestClose={handleClose}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <View style={styles.modalHeader}>
              <MaterialCommunityIcons name="scissors-cutting" size={24} color="#007AFF" />
              <Text style={styles.modalTitle}>Split Task</Text>
              <TouchableOpacity onPress={handleClose}>
                <MaterialCommunityIcons name="close" size={24} color="#8E8E93" />
              </TouchableOpacity>
            </View>

            <ScrollView
              style={styles.modalContent}
              contentContainerStyle={{ paddingBottom: 40 }}
              showsVerticalScrollIndicator={false}
            >
              {!splitComplete ? (
                <>
                  <Text style={styles.taskTitle}>{taskTitle}</Text>
                  <Text style={styles.description}>
                    Split this task into smaller, manageable sub-tasks using AI.
                    This will help you make progress on overwhelming tasks.
                  </Text>

                  <TouchableOpacity
                    style={[styles.actionButton, loading && styles.actionButtonDisabled]}
                    onPress={handleSplitTask}
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <ActivityIndicator size="small" color="#FFFFFF" />
                        <Text style={styles.actionButtonText}>Splitting...</Text>
                      </>
                    ) : (
                      <>
                        <MaterialCommunityIcons name="auto-fix" size={20} color="#FFFFFF" />
                        <Text style={styles.actionButtonText}>Split with AI</Text>
                      </>
                    )}
                  </TouchableOpacity>
                </>
              ) : (
                <>
                  <View style={styles.successHeader}>
                    <MaterialCommunityIcons name="check-circle" size={32} color="#34C759" />
                    <Text style={styles.successTitle}>Task Split Successfully!</Text>
                  </View>
                  <Text style={styles.successDescription}>
                    Created {subtasks.length} sub-tasks. Original task has been paused.
                  </Text>

                  <View style={styles.subtasksList}>
                    {subtasks.map((subtask, index) => (
                      <View key={subtask.id} style={styles.subtaskItem}>
                        <View style={styles.subtaskNumber}>
                          <Text style={styles.subtaskNumberText}>{index + 1}</Text>
                        </View>
                        <View style={styles.subtaskContent}>
                          <Text style={styles.subtaskTitle}>{subtask.title}</Text>
                          <View style={styles.subtaskMeta}>
                            <MaterialCommunityIcons name="clock-outline" size={14} color="#8E8E93" />
                            <Text style={styles.subtaskMetaText}>
                              {subtask.timebox_minutes} min
                            </Text>
                            <MaterialCommunityIcons name="calendar" size={14} color="#8E8E93" style={{ marginLeft: 12 }} />
                            <Text style={styles.subtaskMetaText}>
                              {new Date(subtask.scheduled_date).toLocaleDateString()}
                            </Text>
                          </View>
                        </View>
                      </View>
                    ))}
                  </View>

                  <TouchableOpacity
                    style={styles.doneButton}
                    onPress={handleClose}
                  >
                    <Text style={styles.doneButtonText}>Done</Text>
                  </TouchableOpacity>
                </>
              )}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  splitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: '#F2F2F7',
    borderRadius: 8,
    gap: 6,
  },
  splitButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContainer: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    height: 600,
    overflow: 'hidden',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
    gap: 12,
  },
  modalTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: '700',
    color: '#000000',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  taskTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 12,
  },
  description: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
    marginBottom: 24,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    backgroundColor: '#007AFF',
    borderRadius: 12,
    gap: 8,
  },
  actionButtonDisabled: {
    backgroundColor: '#8E8E93',
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  successHeader: {
    alignItems: 'center',
    marginBottom: 16,
  },
  successTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#000000',
    marginTop: 12,
  },
  successDescription: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    marginBottom: 24,
  },
  subtasksList: {
    gap: 12,
    marginBottom: 24,
  },
  subtaskItem: {
    flexDirection: 'row',
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
    padding: 16,
    gap: 12,
  },
  subtaskNumber: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#007AFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  subtaskNumberText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  subtaskContent: {
    flex: 1,
  },
  subtaskTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 8,
  },
  subtaskMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  subtaskMetaText: {
    fontSize: 12,
    color: '#8E8E93',
  },
  doneButton: {
    paddingVertical: 16,
    backgroundColor: '#34C759',
    borderRadius: 12,
    alignItems: 'center',
  },
  doneButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
