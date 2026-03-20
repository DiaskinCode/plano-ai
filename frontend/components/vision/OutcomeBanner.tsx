import { View, Text, StyleSheet } from 'react-native';

interface OutcomeBannerProps {
  title: string;
  eta: string;
  confidence: number;
  atPaceEta: string;
}

export default function OutcomeBanner({ title, eta, confidence, atPaceEta }: OutcomeBannerProps) {
  const etaDate = new Date(eta);
  const atPaceDate = new Date(atPaceEta);
  const formattedEta = etaDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

  // Calculate if on track
  const daysDiff = Math.ceil((atPaceDate.getTime() - etaDate.getTime()) / (1000 * 60 * 60 * 24));
  const onTrack = daysDiff <= 0;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title}</Text>

      <View style={styles.metaRow}>
        <View style={styles.etaChip}>
          <Text style={styles.etaLabel}>ETA</Text>
          <Text style={styles.etaValue}>{formattedEta}</Text>
        </View>

        <View style={[styles.confidenceChip, { backgroundColor: confidence >= 70 ? '#34C759' : confidence >= 50 ? '#FF9500' : '#FF3B30' }]}>
          <Text style={styles.confidenceValue}>{Math.round(confidence)}%</Text>
        </View>
      </View>

      {onTrack ? (
        <Text style={styles.meaningText}>You're on track to finish by {formattedEta}</Text>
      ) : (
        <Text style={styles.meaningTextWarning}>
          At this pace, you'll finish by {atPaceDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} ({Math.abs(daysDiff)} days {daysDiff > 0 ? 'late' : 'early'})
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#5B6AFF',
    padding: 20,
    paddingTop: 60,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
  },
  metaRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  etaChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  etaLabel: {
    fontSize: 12,
    color: '#fff',
    fontWeight: '600',
  },
  etaValue: {
    fontSize: 14,
    color: '#fff',
    fontWeight: 'bold',
  },
  confidenceChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  confidenceValue: {
    fontSize: 14,
    color: '#fff',
    fontWeight: 'bold',
  },
  meaningText: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.9,
    fontStyle: 'italic',
  },
  meaningTextWarning: {
    fontSize: 14,
    color: '#FFD700',
    fontWeight: '500',
  },
});
