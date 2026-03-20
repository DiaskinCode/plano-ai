import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';

interface ProofStripProps {
  weekFocusMin: number;
  protectedMin: number;
}

export default function ProofStrip({ weekFocusMin, protectedMin }: ProofStripProps) {
  const hours = Math.floor(weekFocusMin / 60);
  const minutes = weekFocusMin % 60;

  return (
    <View style={styles.container}>
      <MaterialCommunityIcons name="chart-line" size={20} color="#5B6AFF" />

      <View style={styles.content}>
        <Text style={styles.text}>
          You invested <Text style={styles.highlight}>{hours}h {minutes}m</Text> this week
        </Text>
        {protectedMin > 0 && (
          <Text style={styles.subtext}>
            {protectedMin} min protected for high-priority work
          </Text>
        )}
      </View>

      <MaterialCommunityIcons name="check-circle" size={20} color="#34C759" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: 'rgba(16, 163, 127, 0.1)',
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(16, 163, 127, 0.2)',
  },
  content: {
    flex: 1,
  },
  text: {
    fontSize: 14,
    color: '#ECECEC',
    fontWeight: '500',
  },
  highlight: {
    fontWeight: 'bold',
    color: '#5B6AFF',
  },
  subtext: {
    fontSize: 12,
    color: '#8E8E8E',
    marginTop: 2,
  },
});
