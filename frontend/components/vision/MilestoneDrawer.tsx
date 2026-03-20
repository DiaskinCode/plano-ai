import { View, Text, StyleSheet, TouchableOpacity, Modal, ScrollView, Alert } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';

interface MilestoneDrawerProps {
  visible: boolean;
  milestone: any;
  onClose: () => void;
  onScheduleTasks: () => void;
  onAddBuffer: () => void;
  onMarkRisk: () => void;
}

export default function MilestoneDrawer({
  visible,
  milestone,
  onClose,
  onScheduleTasks,
  onAddBuffer,
  onMarkRisk,
}: MilestoneDrawerProps) {
  if (!milestone) return null;

  const dueDate = new Date(milestone.due);
  const formattedDue = dueDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <TouchableOpacity style={styles.backdrop} onPress={onClose} />

        <View style={styles.drawer}>
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.headerLeft}>
              <Text style={styles.title}>{milestone.name}</Text>
              <View style={styles.progressBar}>
                <View style={[styles.progressFill, { width: `${milestone.percent}%` }]} />
              </View>
              <Text style={styles.progressText}>{milestone.percent}% complete</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <MaterialCommunityIcons name="close" size={24} color="#ECECEC" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            {/* Meta Info */}
            <View style={styles.metaGrid}>
              <View style={styles.metaItem}>
                <Text style={styles.metaLabel}>Due Date</Text>
                <Text style={styles.metaValue}>{formattedDue}</Text>
              </View>
              <View style={styles.metaItem}>
                <Text style={styles.metaLabel}>Buffer</Text>
                <Text style={styles.metaValue}>{milestone.buffer_days} days</Text>
              </View>
              {milestone.risk_flags?.length > 0 && (
                <View style={styles.metaItem}>
                  <Text style={styles.metaLabel}>Risks</Text>
                  <Text style={[styles.metaValue, styles.riskValue]}>{milestone.risk_flags.length}</Text>
                </View>
              )}
            </View>

            {/* Proof of Work */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Proof of Work</Text>
              <View style={styles.statsRow}>
                <View style={styles.statBox}>
                  <MaterialCommunityIcons name="clock-outline" size={24} color="#5B6AFF" />
                  <Text style={styles.statValue}>{milestone.stats?.focus_min || 0} min</Text>
                  <Text style={styles.statLabel}>Focus Time</Text>
                </View>
                <View style={styles.statBox}>
                  <MaterialCommunityIcons name="check-circle-outline" size={24} color="#5B6AFF" />
                  <Text style={styles.statValue}>{milestone.stats?.critical_done || 0} / {milestone.stats?.critical_total || 0}</Text>
                  <Text style={styles.statLabel}>Critical Tasks</Text>
                </View>
                {milestone.proofs?.length > 0 && (
                  <View style={styles.statBox}>
                    <MaterialCommunityIcons name="file-document-outline" size={24} color="#5B6AFF" />
                    <Text style={styles.statValue}>{milestone.proofs.length}</Text>
                    <Text style={styles.statLabel}>Artifacts</Text>
                  </View>
                )}
              </View>
            </View>

            {/* Next Tasks */}
            {milestone.next_tasks?.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Next Tasks</Text>
                {milestone.next_tasks.map((task: any, idx: number) => (
                  <View key={idx} style={styles.taskCard}>
                    <View style={styles.taskLeft}>
                      <MaterialCommunityIcons name="circle-outline" size={20} color="#5B6AFF" />
                      <Text style={styles.taskTitle}>{task.title}</Text>
                    </View>
                    <Text style={styles.taskDuration}>{task.est_min} min</Text>
                  </View>
                ))}

                <TouchableOpacity style={styles.scheduleButton} onPress={onScheduleTasks}>
                  <MaterialCommunityIcons name="calendar-plus" size={20} color="#fff" />
                  <Text style={styles.scheduleButtonText}>Schedule Both for Tomorrow</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Risk Flags */}
            {milestone.risk_flags?.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Risk Flags</Text>
                {milestone.risk_flags.map((risk: any, idx: number) => (
                  <View key={idx} style={styles.riskCard}>
                    <MaterialCommunityIcons name="alert-circle" size={18} color="#FF3B30" />
                    <Text style={styles.riskText}>{risk.note || 'General risk'}</Text>
                  </View>
                ))}
              </View>
            )}

            {/* Actions */}
            <View style={styles.actionsSection}>
              <TouchableOpacity style={styles.actionButton} onPress={onAddBuffer}>
                <MaterialCommunityIcons name="calendar-clock" size={20} color="#5B6AFF" />
                <Text style={styles.actionButtonText}>Add Buffer Week</Text>
              </TouchableOpacity>

              <TouchableOpacity style={[styles.actionButton, styles.actionButtonDanger]} onPress={onMarkRisk}>
                <MaterialCommunityIcons name="alert-octagon" size={20} color="#FF3B30" />
                <Text style={[styles.actionButtonText, styles.actionButtonTextDanger]}>Mark Risk</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
  },
  drawer: {
    backgroundColor: '#2A2A2A',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '85%',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#3E3E3E',
  },
  headerLeft: {
    flex: 1,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ECECEC',
    marginBottom: 12,
  },
  progressBar: {
    height: 6,
    backgroundColor: '#3E3E3E',
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 6,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#5B6AFF',
  },
  progressText: {
    fontSize: 12,
    color: '#8E8E8E',
  },
  closeButton: {
    padding: 4,
  },
  content: {
    padding: 20,
  },
  metaGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  metaItem: {
    flex: 1,
    backgroundColor: '#1A1A1A',
    padding: 12,
    borderRadius: 12,
  },
  metaLabel: {
    fontSize: 11,
    color: '#8E8E8E',
    marginBottom: 4,
    textTransform: 'uppercase',
    fontWeight: '600',
  },
  metaValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ECECEC',
  },
  riskValue: {
    color: '#FF3B30',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ECECEC',
    marginBottom: 12,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  statBox: {
    flex: 1,
    backgroundColor: '#1A1A1A',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ECECEC',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 11,
    color: '#8E8E8E',
    marginTop: 4,
    textAlign: 'center',
  },
  taskCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#1A1A1A',
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
  },
  taskLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  taskTitle: {
    fontSize: 14,
    color: '#ECECEC',
    flex: 1,
  },
  taskDuration: {
    fontSize: 13,
    color: '#8E8E8E',
    fontWeight: '600',
  },
  scheduleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#5B6AFF',
    padding: 14,
    borderRadius: 12,
    marginTop: 8,
  },
  scheduleButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#fff',
  },
  riskCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: 'rgba(255, 59, 48, 0.1)',
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
  },
  riskText: {
    fontSize: 14,
    color: '#FF3B30',
    flex: 1,
  },
  actionsSection: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 20,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#1A1A1A',
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#5B6AFF',
  },
  actionButtonDanger: {
    borderColor: '#FF3B30',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#5B6AFF',
  },
  actionButtonTextDanger: {
    color: '#FF3B30',
  },
});
