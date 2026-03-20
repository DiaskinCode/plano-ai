/**
 * Community Approval Queue (Admin Only)
 *
 * Admin screen to review and approve/reject community creation requests
 * - View all pending requests
 * - Review details
 * - Approve or reject with notes
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  TextInput,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';

// TODO: Replace with actual API call
interface CommunityCreationRequest {
  id: number;
  name: string;
  slug: string;
  description: string;
  community_type: 'region' | 'topic';
  icon: string;
  banner_color: string;
  tags: string[];
  status: 'pending' | 'approved' | 'rejected' | 'changes_requested';
  created_by: string;
  created_at: string;
  admin_notes?: string;
}

type StatusFilter = 'pending' | 'approved' | 'rejected' | 'changes_requested' | 'all';

export default function CommunityApprovalsScreen() {
  const [requests, setRequests] = useState<CommunityCreationRequest[]>([]);
  const [filteredRequests, setFilteredRequests] = useState<CommunityCreationRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('pending');
  const [selectedRequest, setSelectedRequest] = useState<CommunityCreationRequest | null>(null);
  const [adminNotes, setAdminNotes] = useState('');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    loadRequests();
  }, []);

  useEffect(() => {
    filterRequests();
  }, [requests, statusFilter]);

  const loadRequests = async () => {
    try {
      setLoading(true);

      // TODO: Replace with actual API call
      // const response = await communityAPI.getCreationRequests({ status: statusFilter });
      // setRequests(response.data);

      // Mock data for now
      const mockRequests: CommunityCreationRequest[] = [
        {
          id: 1,
          name: 'Stanford Applicants 2025',
          slug: 'stanford-applicants-2025',
          description: 'A community for students applying to Stanford University in 2025. Share tips, experiences, and support each other through the application process.',
          community_type: 'topic',
          icon: '🎓',
          banner_color: '#EF4444',
          tags: ['Stanford', 'College Applications', '2025'],
          status: 'pending',
          created_by: 'john_doe',
          created_at: new Date().toISOString(),
        },
        {
          id: 2,
          name: 'New York City Students',
          slug: 'nyc-students',
          description: 'Connect with high school students in NYC for study groups, college prep, and local events.',
          community_type: 'region',
          icon: '🌆',
          banner_color: '#3B82F6',
          tags: ['NYC', 'High School', 'Study Groups'],
          status: 'pending',
          created_by: 'jane_smith',
          created_at: new Date().toISOString(),
        },
      ];

      setRequests(mockRequests);
    } catch (error) {
      console.error('Failed to load requests:', error);
      Alert.alert('Error', 'Failed to load community requests');
    } finally {
      setLoading(false);
    }
  };

  const filterRequests = () => {
    if (statusFilter === 'all') {
      setFilteredRequests(requests);
    } else {
      setFilteredRequests(requests.filter((req) => req.status === statusFilter));
    }
  };

  const handleApprove = async () => {
    if (!selectedRequest) return;

    setProcessing(true);

    try {
      // TODO: Replace with actual API call
      // await communityAPI.approveCreationRequest(selectedRequest.id, {
      //   admin_notes: adminNotes,
      // });

      // Mock approval
      await new Promise(resolve => setTimeout(resolve, 1000));

      Alert.alert('Approved', `Community "${selectedRequest.name}" has been approved and created.`);

      // Update local state
      setRequests(requests.map((req) =>
        req.id === selectedRequest.id ? { ...req, status: 'approved' as const } : req
      ));

      setSelectedRequest(null);
      setAdminNotes('');
    } catch (error) {
      Alert.alert('Error', 'Failed to approve community');
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!selectedRequest) return;

    if (!adminNotes.trim()) {
      Alert.alert('Notes Required', 'Please provide a reason for rejection');
      return;
    }

    setProcessing(true);

    try {
      // TODO: Replace with actual API call
      // await communityAPI.rejectCreationRequest(selectedRequest.id, {
      //   admin_notes: adminNotes,
      // });

      // Mock rejection
      await new Promise(resolve => setTimeout(resolve, 1000));

      Alert.alert('Rejected', `Community request has been rejected.`);

      // Update local state
      setRequests(requests.map((req) =>
        req.id === selectedRequest.id ? { ...req, status: 'rejected' as const, admin_notes } : req
      ));

      setSelectedRequest(null);
      setAdminNotes('');
    } catch (error) {
      Alert.alert('Error', 'Failed to reject community');
    } finally {
      setProcessing(false);
    }
  };

  const handleRequestChanges = async () => {
    if (!selectedRequest) return;

    if (!adminNotes.trim()) {
      Alert.alert('Notes Required', 'Please specify what changes are needed');
      return;
    }

    setProcessing(true);

    try {
      // TODO: Replace with actual API call
      // await communityAPI.requestChanges(selectedRequest.id, {
      //   admin_notes: adminNotes,
      // });

      // Mock request changes
      await new Promise(resolve => setTimeout(resolve, 1000));

      Alert.alert('Changes Requested', 'User will be notified to make the requested changes.');

      // Update local state
      setRequests(requests.map((req) =>
        req.id === selectedRequest.id
          ? { ...req, status: 'changes_requested' as const, admin_notes }
          : req
      ));

      setSelectedRequest(null);
      setAdminNotes('');
    } catch (error) {
      Alert.alert('Error', 'Failed to request changes');
    } finally {
      setProcessing(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return '#F59E0B';
      case 'approved':
        return '#10B981';
      case 'rejected':
        return '#EF4444';
      case 'changes_requested':
        return '#8B5CF6';
      default:
        return '#6B7280';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'pending':
        return 'Pending';
      case 'approved':
        return 'Approved';
      case 'rejected':
        return 'Rejected';
      case 'changes_requested':
        return 'Changes Requested';
      default:
        return status;
    }
  };

  const renderRequestCard = (request: CommunityCreationRequest) => {
    const isSelected = selectedRequest?.id === request.id;

    return (
      <TouchableOpacity
        key={request.id}
        style={[styles.requestCard, isSelected && styles.requestCardSelected]}
        onPress={() => setSelectedRequest(request)}
      >
        <View style={styles.requestHeader}>
          <View style={[styles.previewIcon, { backgroundColor: request.banner_color }]}>
            <Text style={styles.previewIconText}>{request.icon}</Text>
          </View>

          <View style={styles.requestInfo}>
            <View style={styles.requestTitleRow}>
              <Text style={styles.requestName}>{request.name}</Text>
              <View
                style={[
                  styles.statusBadge,
                  { backgroundColor: getStatusColor(request.status) + '20' },
                ]}
              >
                <Text style={[styles.statusText, { color: getStatusColor(request.status) }]}>
                  {getStatusLabel(request.status)}
                </Text>
              </View>
            </View>

            <Text style={styles.requestMeta}>
              {request.community_type === 'topic' ? '💡' : '🌍'} {request.community_type} • by{' '}
              {request.created_by}
            </Text>

            <Text style={styles.requestDescription} numberOfLines={2}>
              {request.description}
            </Text>

            <View style={styles.tagsContainer}>
              {request.tags.slice(0, 3).map((tag, index) => (
                <View key={index} style={styles.tag}>
                  <Text style={styles.tagText}>{tag}</Text>
                </View>
              ))}
            </View>
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  if (loading) {
    return (
      <View style={styles.centerContent}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={styles.loadingText}>Loading requests...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Community Approvals</Text>
        <Text style={styles.headerSubtitle}>
          {filteredRequests.length} {filteredRequests.length === 1 ? 'request' : 'requests'}
        </Text>
      </View>

      {/* Filter Tabs */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filterScrollView}
        contentContainerStyle={styles.filterContent}
      >
        {(['pending', 'approved', 'rejected', 'changes_requested', 'all'] as StatusFilter[]).map(
          (filter) => (
            <TouchableOpacity
              key={filter}
              style={[
                styles.filterChip,
                statusFilter === filter && styles.filterChipActive,
              ]}
              onPress={() => setStatusFilter(filter)}
            >
              <Text
                style={[
                  styles.filterChipText,
                  statusFilter === filter && styles.filterChipTextActive,
                ]}
              >
                {filter === 'all' ? 'All' : getStatusLabel(filter)}
              </Text>
            </TouchableOpacity>
          )
        )}
      </ScrollView>

      {/* Request List */}
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {filteredRequests.length === 0 ? (
          <View style={styles.emptyState}>
            <MaterialCommunityIcons name="clipboard-check" size={64} color="#3E3E3E" />
            <Text style={styles.emptyStateText}>No requests found</Text>
            <Text style={styles.emptyStateSubtext}>
              {statusFilter === 'all'
                ? 'No community creation requests yet'
                : `No ${getStatusLabel(statusFilter).toLowerCase()} requests`}
            </Text>
          </View>
        ) : (
          <View style={styles.requestsList}>{filteredRequests.map(renderRequestCard)}</View>
        )}
      </ScrollView>

      {/* Action Panel */}
      {selectedRequest && selectedRequest.status === 'pending' && (
        <View style={styles.actionPanel}>
          <View style={styles.actionPanelHeader}>
            <Text style={styles.actionPanelTitle}>Review: {selectedRequest.name}</Text>
            <TouchableOpacity onPress={() => setSelectedRequest(null)}>
              <MaterialCommunityIcons name="close" size={24} color="#8E8E8E" />
            </TouchableOpacity>
          </View>

          <View style={styles.actionPanelContent}>
            <View style={[styles.previewCard, { backgroundColor: selectedRequest.banner_color }]}>
              <Text style={styles.previewCardIcon}>{selectedRequest.icon}</Text>
              <View style={styles.previewCardContent}>
                <Text style={styles.previewCardName}>{selectedRequest.name}</Text>
                <Text style={styles.previewCardSlug}>/{selectedRequest.slug}</Text>
                <Text style={styles.previewCardDesc} numberOfLines={3}>
                  {selectedRequest.description}
                </Text>
                <View style={styles.previewCardTags}>
                  {selectedRequest.tags.map((tag, index) => (
                    <Text key={index} style={styles.previewCardTag}>
                      #{tag}
                    </Text>
                  ))}
                </View>
              </View>
            </View>

            <Text style={styles.notesLabel}>Admin Notes (required for reject/changes)</Text>
            <TextInput
              style={styles.notesInput}
              placeholder="Add notes for the user..."
              placeholderTextColor="#6B7280"
              value={adminNotes}
              onChangeText={setAdminNotes}
              multiline
              numberOfLines={3}
            />

            <View style={styles.actionButtons}>
              <TouchableOpacity
                style={[styles.actionButton, styles.rejectButton]}
                onPress={handleReject}
                disabled={processing}
              >
                <MaterialCommunityIcons name="close" size={20} color="#FFFFFF" />
                <Text style={styles.actionButtonText}>Reject</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.actionButton, styles.changesButton]}
                onPress={handleRequestChanges}
                disabled={processing}
              >
                <MaterialCommunityIcons name="pencil" size={20} color="#FFFFFF" />
                <Text style={styles.actionButtonText}>Request Changes</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.actionButton, styles.approveButton]}
                onPress={handleApprove}
                disabled={processing}
              >
                {processing ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <>
                    <MaterialCommunityIcons name="check" size={20} color="#FFFFFF" />
                    <Text style={styles.actionButtonText}>Approve</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#8E8E8E',
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#ECECEC',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#8E8E8E',
  },
  filterScrollView: {
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  filterContent: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#2A2A2A',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#3E3E3E',
  },
  filterChipActive: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  filterChipText: {
    fontSize: 13,
    color: '#B8B8B8',
    fontWeight: '500',
  },
  filterChipTextActive: {
    color: '#FFFFFF',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#8E8E8E',
    marginTop: 16,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
    textAlign: 'center',
  },
  requestsList: {
    gap: 12,
  },
  requestCard: {
    backgroundColor: '#1E1E1E',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#3E3E3E',
  },
  requestCardSelected: {
    borderColor: '#3B82F6',
    backgroundColor: '#1E1E1E',
  },
  requestHeader: {
    flexDirection: 'row',
    gap: 12,
  },
  previewIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  previewIconText: {
    fontSize: 28,
  },
  requestInfo: {
    flex: 1,
  },
  requestTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  requestName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ECECEC',
    flex: 1,
    marginRight: 8,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  requestMeta: {
    fontSize: 12,
    color: '#8E8E8E',
    marginBottom: 6,
  },
  requestDescription: {
    fontSize: 14,
    color: '#B8B8B8',
    marginBottom: 8,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  tag: {
    backgroundColor: '#2A2A2A',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  tagText: {
    fontSize: 11,
    color: '#8E8E8E',
  },
  actionPanel: {
    backgroundColor: '#1A1A1A',
    borderTopWidth: 1,
    borderTopColor: '#2A2A2A',
    maxHeight: '60%',
  },
  actionPanelHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
  },
  actionPanelTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ECECEC',
  },
  actionPanelContent: {
    padding: 16,
  },
  previewCard: {
    flexDirection: 'row',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  previewCardIcon: {
    fontSize: 40,
    marginRight: 12,
  },
  previewCardContent: {
    flex: 1,
  },
  previewCardName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ECECEC',
    marginBottom: 2,
  },
  previewCardSlug: {
    fontSize: 12,
    color: 'rgba(236, 236, 236, 0.7)',
    marginBottom: 6,
  },
  previewCardDesc: {
    fontSize: 13,
    color: 'rgba(236, 236, 236, 0.8)',
    marginBottom: 8,
  },
  previewCardTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  previewCardTag: {
    fontSize: 11,
    color: 'rgba(236, 236, 236, 0.7)',
  },
  notesLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ECECEC',
    marginBottom: 8,
  },
  notesInput: {
    backgroundColor: '#1E1E1E',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#ECECEC',
    borderWidth: 1,
    borderColor: '#3E3E3E',
    marginBottom: 16,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 8,
    gap: 6,
  },
  rejectButton: {
    backgroundColor: '#EF4444',
  },
  changesButton: {
    backgroundColor: '#8B5CF6',
  },
  approveButton: {
    backgroundColor: '#10B981',
  },
  actionButtonText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
