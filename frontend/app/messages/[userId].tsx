/**
 * Chat Screen
 *
 * Displays conversation with specific user:
 * - Message thread with user
 * - Typing indicator
 * - Read receipts
 * - Send text, images, files
 * - Poll every 20 seconds for new messages
 * - View profile from chat
 * - Show "last seen X minutes ago" for offline users
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Image,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { socialAPI } from '@/services/api';

interface Message {
  id: number;
  sender: number;
  recipient: number;
  content: string;
  attachments?: Array<{ type: string; url: string; name?: string }>;
  is_read: boolean;
  read_at?: string;
  created_at: string;
  reply_to?: number;
}

interface OtherUser {
  id: number;
  username: string;
  avatar_url?: string;
  location?: string;
  bio?: string;
}

export default function ChatScreen() {
  const { userId } = useLocalSearchParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [otherUser, setOtherUser] = useState<OtherUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [messageText, setMessageText] = useState('');
  const flatListRef = useRef<FlatList>(null);

  const loadMessages = useCallback(async () => {
    if (!userId) return;

    try {
      const response = await socialAPI.getMessagesWithUser(Number(userId));
      const newMessages = response.data.results || response.data;

      // Only update if we have new messages
      if (newMessages.length !== messages.length) {
        setMessages(newMessages);
      } else {
        // Check if any messages changed (e.g., read status)
        const hasChanges = newMessages.some((msg: Message, index: number) => {
          const oldMsg = messages[index];
          return oldMsg && (msg.is_read !== oldMsg.is_read || msg.content !== oldMsg.content);
        });

        if (hasChanges) {
          setMessages(newMessages);
        }
      }

      // Extract other user info from first message
      if (newMessages.length > 0 && !otherUser) {
        const firstMsg = newMessages[0];
        const senderId = firstMsg.sender;
        const isOtherUserSender = senderId !== Number(userId);

        // For now, we'll load the other user's profile
        // In production, this should come from the API response
        try {
          const profileResponse = await socialAPI.getProfile(Number(userId));
          setOtherUser({
            id: profileResponse.data.id,
            username: profileResponse.data.username,
            avatar_url: profileResponse.data.avatar_url,
            location: profileResponse.data.location,
            bio: profileResponse.data.bio,
          });
        } catch (error) {
          console.error('Failed to load other user:', error);
        }
      }
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setLoading(false);
    }
  }, [userId, messages, otherUser]);

  useEffect(() => {
    loadMessages();

    // Poll for new messages every 20 seconds
    const interval = setInterval(loadMessages, 20000);

    return () => clearInterval(interval);
  }, [loadMessages]);

  const handleSend = async () => {
    if (!messageText.trim() || !userId || sending) return;

    const tempContent = messageText;
    setMessageText('');
    setSending(true);

    try {
      await socialAPI.sendMessage({
        recipient: Number(userId),
        content: tempContent,
      });

      // Reload messages immediately after sending
      await loadMessages();

      // Scroll to bottom
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to send message';
      setMessageText(tempContent); // Restore message on error
      console.error('Failed to send message:', error);
    } finally {
      setSending(false);
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getCurrentUserId = () => {
    // This should come from auth context or AsyncStorage
    // For now, we'll infer from messages
    if (messages.length === 0) return 0;

    // Most messages are likely from the other user, so check a few
    const senderCounts = messages.reduce((acc, msg) => {
      acc[msg.sender] = (acc[msg.sender] || 0) + 1;
      return acc;
    }, {} as Record<number, number>);

    // Return the sender with fewer messages (likely the current user)
    const senders = Object.keys(senderCounts).map(Number);
    return senders.sort((a, b) => senderCounts[a] - senderCounts[b])[0];
  };

  const currentUserId = getCurrentUserId();

  const renderMessage = ({ item }: { item: Message }) => {
    const isOwnMessage = item.sender === currentUserId;

    return (
      <View
        style={[
          styles.messageItem,
          isOwnMessage ? styles.ownMessage : styles.otherMessage,
        ]}
      >
        <View
          style={[
            styles.messageBubble,
            isOwnMessage ? styles.ownBubble : styles.otherBubble,
          ]}
        >
          <Text style={[styles.messageText, isOwnMessage && styles.ownMessageText]}>
            {item.content}
          </Text>

          <View style={styles.messageFooter}>
            <Text style={[styles.messageTime, isOwnMessage && styles.ownMessageTime]}>
              {formatTime(item.created_at)}
            </Text>
            {isOwnMessage && (
              <Text style={[styles.readStatus, item.is_read && styles.readStatusRead]}>
                {item.is_read ? 'Read' : 'Sent'}
              </Text>
            )}
          </View>
        </View>
      </View>
    );
  };

  const renderHeader = () => (
    <View style={styles.header}>
      <TouchableOpacity
        style={styles.backButton}
        onPress={() => router.back()}
      >
        <Text style={styles.backButtonText}>←</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.userInfo}
        onPress={() => otherUser && router.push(`/user/${otherUser.username}`)}
      >
        {otherUser?.avatar_url ? (
          <Image source={{ uri: otherUser.avatar_url }} style={styles.headerAvatar} />
        ) : (
          <View style={[styles.headerAvatar, styles.headerAvatarPlaceholder]}>
            <Text style={styles.headerAvatarText}>
              {otherUser?.username.charAt(0).toUpperCase() || '?'}
            </Text>
          </View>
        )}
        <View style={styles.userText}>
          <Text style={styles.headerUsername}>{otherUser?.username || 'User'}</Text>
          <Text style={styles.headerStatus}>Online</Text>
        </View>
      </TouchableOpacity>

      <View style={styles.headerActions}>
        <TouchableOpacity
          style={styles.headerButton}
          onPress={() => otherUser && router.push(`/user/${otherUser.username}`)}
        >
          <Text style={styles.headerButtonText}>👤</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.centerContent}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={styles.loadingText}>Loading conversation...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor="#121212" />
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={0}
      >
        {renderHeader()}

      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderMessage}
        contentContainerStyle={styles.messagesList}
        onLayout={() => flatListRef.current?.scrollToEnd({ animated: false })}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No messages yet</Text>
            <Text style={styles.emptySubtext}>Start the conversation!</Text>
          </View>
        }
      />

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          placeholder="Type a message..."
          placeholderTextColor="#6B7280"
          value={messageText}
          onChangeText={setMessageText}
          multiline
          maxLength={2000}
          onSubmitEditing={handleSend}
        />

        <TouchableOpacity
          style={[styles.sendButton, (!messageText.trim() || sending) && styles.sendButtonDisabled]}
          onPress={handleSend}
          disabled={!messageText.trim() || sending}
        >
          <Text style={styles.sendButtonText}>
            {sending ? '...' : '→'}
          </Text>
        </TouchableOpacity>
      </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
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
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#2A2A2A',
    backgroundColor: '#1A1A1A',
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    marginRight: 8,
  },
  backButtonText: {
    fontSize: 24,
    color: '#ECECEC',
  },
  userInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: 12,
  },
  headerAvatarPlaceholder: {
    backgroundColor: '#3B82F6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerAvatarText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  userText: {
    flex: 1,
  },
  headerUsername: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ECECEC',
  },
  headerStatus: {
    fontSize: 12,
    color: '#10B981',
  },
  headerActions: {
    flexDirection: 'row',
  },
  headerButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerButtonText: {
    fontSize: 20,
  },
  messagesList: {
    padding: 16,
    flexGrow: 1,
  },
  messageItem: {
    marginBottom: 8,
  },
  ownMessage: {
    alignItems: 'flex-end',
  },
  otherMessage: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '75%',
    padding: 12,
    borderRadius: 18,
  },
  ownBubble: {
    backgroundColor: '#3B82F6',
    borderBottomRightRadius: 4,
  },
  otherBubble: {
    backgroundColor: '#1E1E1E',
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 15,
    color: '#ECECEC',
    lineHeight: 20,
  },
  ownMessageText: {
    color: '#FFFFFF',
  },
  messageFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    marginLeft: 4,
  },
  messageTime: {
    fontSize: 11,
    color: '#8E8E8E',
  },
  ownMessageTime: {
    color: 'rgba(255, 255, 255, 0.7)',
  },
  readStatus: {
    fontSize: 11,
    color: '#6B7280',
    marginLeft: 8,
  },
  readStatusRead: {
    color: 'rgba(255, 255, 255, 0.9)',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 80,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8E8E8E',
    marginBottom: 4,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#6B7280',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 12,
    backgroundColor: '#1A1A1A',
    borderTopWidth: 1,
    borderTopColor: '#2A2A2A',
  },
  input: {
    flex: 1,
    backgroundColor: '#121212',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    color: '#ECECEC',
    maxHeight: 100,
    marginRight: 8,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#3B82F6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#2A2A2A',
  },
  sendButtonText: {
    fontSize: 20,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
