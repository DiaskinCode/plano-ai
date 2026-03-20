import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Animated,
  Dimensions,
} from 'react-native';
import { BlurView } from 'expo-blur';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LiquidGlassButton } from '../LiquidGlassButton';
import { LiquidGlassCard } from '../LiquidGlassCard';
import { colors, spacing, borderRadius, typography } from '@/theme';

const { width } = Dimensions.get('window');
const SIDEBAR_WIDTH = width * 0.75;

interface Conversation {
  id: number;
  title: string;
  message_count: number;
}

interface ChatSidebarProps {
  isOpen: boolean;
  sidebarAnim: Animated.Value;
  conversations: Conversation[];
  currentConversationId?: number;
  onClose: () => void;
  onNewChat: () => void;
  onSelectConversation: (id: number) => void;
  onDeleteConversation: (id: number) => void;
  t: (key: string) => string;
}

/**
 * Chat sidebar component for conversation management.
 * Features:
 * - Animated slide-in from left
 * - Blur backdrop
 * - Conversation list with delete actions
 */
export function ChatSidebar({
  isOpen,
  sidebarAnim,
  conversations,
  currentConversationId,
  onClose,
  onNewChat,
  onSelectConversation,
  onDeleteConversation,
  t,
}: ChatSidebarProps) {
  return (
    <>
      {/* Backdrop with blur */}
      {isOpen && (
        <TouchableOpacity
          style={styles.backdrop}
          activeOpacity={1}
          onPress={onClose}
        >
          <BlurView intensity={30} tint="dark" style={StyleSheet.absoluteFill} />
        </TouchableOpacity>
      )}

      {/* Sidebar with Liquid Glass design */}
      <Animated.View
        style={[
          styles.sidebar,
          {
            transform: [{ translateX: sidebarAnim }],
          },
        ]}
      >
        {/* Header */}
        <BlurView intensity={50} tint="dark" style={styles.headerBlur}>
          <View style={styles.header}>
            <TouchableOpacity style={styles.newChatButton} onPress={onNewChat}>
              <MaterialCommunityIcons
                name="pencil"
                size={18}
                color={colors.bg}
                style={{ marginRight: 8 }}
              />
              <Text style={styles.newChatText}>{t('home.newChat')}</Text>
            </TouchableOpacity>

            <LiquidGlassButton
              icon="close"
              onPress={onClose}
              variant="ghost"
              size={32}
              iconSize={24}
            />
          </View>
        </BlurView>

        {/* Conversations list with Liquid Glass cards */}
        <ScrollView style={styles.list} showsVerticalScrollIndicator={false}>
          {conversations.map((conv) => (
            <View key={conv.id} style={styles.conversationItem}>
              <LiquidGlassCard
                onPress={() => onSelectConversation(conv.id)}
                variant={currentConversationId === conv.id ? 'elevated' : 'subtle'}
                style={styles.conversationCard}
              >
                <View style={styles.conversationContent}>
                  <View style={styles.conversationHeader}>
                    <MaterialCommunityIcons
                      name="message-text"
                      size={16}
                      color={colors.text}
                    />
                    <Text style={styles.conversationTitle} numberOfLines={1}>
                      {conv.title}
                    </Text>
                  </View>
                  <Text style={styles.conversationMeta}>
                    {conv.message_count} {t('home.messages')}
                  </Text>
                </View>
              </LiquidGlassCard>

              <LiquidGlassButton
                icon="delete"
                onPress={() => onDeleteConversation(conv.id)}
                variant="ghost"
                size={40}
                iconSize={20}
                color={colors.danger}
              />
            </View>
          ))}
        </ScrollView>
      </Animated.View>
    </>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    zIndex: 1,
  },
  sidebar: {
    position: 'absolute',
    top: 0,
    left: 0,
    bottom: 0,
    width: SIDEBAR_WIDTH,
    backgroundColor: colors.bg,
    borderRightWidth: 1,
    borderRightColor: colors.liquidGlass.borderMedium,
    zIndex: 2,
  },
  headerBlur: {
    borderBottomWidth: 1,
    borderBottomColor: colors.liquidGlass.borderLight,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingTop: 60,
    paddingBottom: spacing.md,
    backgroundColor: colors.liquidGlass.overlayLight,
  },
  newChatButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.text,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 2,
    borderRadius: borderRadius.md,
  },
  newChatText: {
    ...typography.labelLarge,
    color: colors.bg,
  },
  list: {
    flex: 1,
    paddingHorizontal: spacing.sm,
    paddingTop: spacing.sm,
  },
  conversationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    marginBottom: spacing.xs,
  },
  conversationCard: {
    flex: 1,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  conversationContent: {
    flex: 1,
  },
  conversationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: 4,
  },
  conversationTitle: {
    ...typography.labelMedium,
    color: colors.text,
    flex: 1,
  },
  conversationMeta: {
    ...typography.caption,
    color: colors.textSecondary,
  },
});

export default ChatSidebar;
