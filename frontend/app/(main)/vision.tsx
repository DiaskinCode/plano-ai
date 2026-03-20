import { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Alert,
  TextInput,
} from 'react-native';
import { visionAPI } from '@/services/api';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import IslandRoadmap from '@/components/vision/IslandRoadmap';
import MilestoneDrawer from '@/components/vision/MilestoneDrawer';
import ProofStrip from '@/components/vision/ProofStrip';
import LiquidGlassCard from '@/components/LiquidGlassCard';

export default function VisionScreen() {
  const [visionData, setVisionData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedMilestone, setSelectedMilestone] = useState<any>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);

  useEffect(() => {
    loadVisionData();
  }, []);

  const loadVisionData = async () => {
    try {
      setLoading(true);
      const response = await visionAPI.getVisionAnalytics();
      setVisionData(response.data);
    } catch (error: any) {
      console.error('Failed to load vision analytics:', error);
      if (error.response?.status === 404) {
        // No vision found, show empty state
        setVisionData(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleMilestonePress = (milestone: any) => {
    setSelectedMilestone(milestone);
    setDrawerVisible(true);
  };

  const handleScheduleTasks = async () => {
    if (!selectedMilestone) return;

    try {
      await visionAPI.scheduleTasksForMilestone(selectedMilestone.id);
      Alert.alert('Success', 'Tasks scheduled for tomorrow at 9:30 AM');
      setDrawerVisible(false);
      loadVisionData();
    } catch (error) {
      console.error('Failed to schedule tasks:', error);
      Alert.alert('Error', 'Failed to schedule tasks');
    }
  };

  const handleAddBuffer = async () => {
    if (!selectedMilestone) return;

    Alert.alert(
      'Add Buffer Days',
      'How many days would you like to add?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: '7 days',
          onPress: async () => {
            try {
              await visionAPI.addMilestoneBuffer(selectedMilestone.id, 7);
              Alert.alert('Success', 'Added 7 days of buffer');
              setDrawerVisible(false);
              loadVisionData();
            } catch (error) {
              console.error('Failed to add buffer:', error);
              Alert.alert('Error', 'Failed to add buffer');
            }
          },
        },
        {
          text: '14 days',
          onPress: async () => {
            try {
              await visionAPI.addMilestoneBuffer(selectedMilestone.id, 14);
              Alert.alert('Success', 'Added 14 days of buffer');
              setDrawerVisible(false);
              loadVisionData();
            } catch (error) {
              console.error('Failed to add buffer:', error);
              Alert.alert('Error', 'Failed to add buffer');
            }
          },
        },
      ]
    );
  };

  const handleMarkRisk = async () => {
    if (!selectedMilestone) return;

    Alert.prompt(
      'Mark Risk',
      'What is the risk?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Mark',
          onPress: async (note) => {
            try {
              await visionAPI.markMilestoneRisk(selectedMilestone.id, note || 'General risk');
              Alert.alert('Success', 'Risk flag added');
              setDrawerVisible(false);
              loadVisionData();
            } catch (error) {
              console.error('Failed to mark risk:', error);
              Alert.alert('Error', 'Failed to mark risk');
            }
          },
        },
      ],
      'plain-text'
    );
  };

  const handlePrimaryAction = () => {
    const current = visionData?.milestones?.find((m: any) =>
      ['in_progress', 'next'].includes(m.state)
    );
    if (current) {
      handleMilestonePress(current);
    }
  };

  if (!visionData && !loading) {
    return (
      <View style={styles.container}>
        <View style={styles.emptyContainer}>
          <MaterialCommunityIcons name="target" size={64} color="#3E3E3E" />
          <Text style={styles.emptyText}>No vision created yet</Text>
          <Text style={styles.emptySubtext}>
            Complete onboarding to generate your success vision
          </Text>
        </View>
      </View>
    );
  }

  // Filter milestones based on search query
  const filteredMilestones = visionData?.milestones?.filter((m: any) =>
    m.name.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  return (
    <View style={styles.container}>
      {/* Header with Logo and Search */}
      <View style={styles.header}>
        <Text style={styles.logo}>Plano</Text>
        <TouchableOpacity
          style={styles.searchButton}
          onPress={() => setShowSearch(!showSearch)}
        >
          <MaterialCommunityIcons name="magnify" size={24} color="#ECECEC" />
        </TouchableOpacity>
      </View>

      {/* Search Input */}
      {showSearch && (
        <View style={styles.searchWrapper}>
          <LiquidGlassCard style={styles.searchContainer} intensity="heavy">
            <MaterialCommunityIcons name="magnify" size={20} color="#8E8E8E" />
            <TextInput
              style={styles.searchInput}
              placeholder="Search weeks or milestones..."
              placeholderTextColor="#8E8E8E"
              value={searchQuery}
              onChangeText={setSearchQuery}
              autoFocus
            />
            {searchQuery.length > 0 && (
              <TouchableOpacity onPress={() => setSearchQuery('')}>
                <MaterialCommunityIcons name="close-circle" size={20} color="#8E8E8E" />
              </TouchableOpacity>
            )}
          </LiquidGlassCard>
        </View>
      )}

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={loadVisionData} />}
        showsVerticalScrollIndicator={false}
        ref={(ref) => {
          // Scroll to bottom on mount to show current position
          if (ref && visionData) {
            setTimeout(() => {
              ref.scrollToEnd({ animated: false });
            }, 100);
          }
        }}
      >
        {visionData && (
          <>
            {/* Island Roadmap */}
            <View style={styles.roadmapSection}>
              <IslandRoadmap
                milestones={searchQuery ? filteredMilestones : visionData.milestones || []}
                onMilestonePress={handleMilestonePress}
              />
            </View>

            {/* Progress Proof Strip */}
            <ProofStrip
              weekFocusMin={visionData.effort_summary?.week_focus_min || 0}
              protectedMin={visionData.effort_summary?.protected_min || 0}
            />
          </>
        )}
      </ScrollView>

      {/* Action Bar */}
      {visionData?.action_cta && (
        <View style={styles.actionBar}>
          <LiquidGlassCard
            onPress={handlePrimaryAction}
            variant="elevated"
            intensity="heavy"
            style={styles.primaryButtonCard}
          >
            <View style={styles.primaryButtonContent}>
              <MaterialCommunityIcons name="calendar-clock" size={20} color="#fff" />
              <Text style={styles.primaryButtonText} numberOfLines={1}>
                {visionData.action_cta}
              </Text>
            </View>
          </LiquidGlassCard>
        </View>
      )}

      {/* Milestone Detail Drawer */}
      <MilestoneDrawer
        visible={drawerVisible}
        milestone={selectedMilestone}
        onClose={() => setDrawerVisible(false)}
        onScheduleTasks={handleScheduleTasks}
        onAddBuffer={handleAddBuffer}
        onMarkRisk={handleMarkRisk}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#131313',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 16,
    backgroundColor: '#131313',
  },
  logo: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ECECEC',
  },
  searchButton: {
    padding: 8,
  },
  searchWrapper: {
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    color: '#ECECEC',
  },
  content: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  roadmapSection: {
    padding: 16,
    paddingTop: 8,
  },
  actionBar: {
    padding: 16,
    paddingBottom: 24,
    backgroundColor: 'transparent',
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
  },
  primaryButtonCard: {
    borderRadius: 12,
  },
  primaryButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    padding: 16,
  },
  primaryButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#fff',
    flex: 1,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#8E8E8E',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
});
