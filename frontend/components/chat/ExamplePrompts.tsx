import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import LiquidGlassCard from '@/components/LiquidGlassCard';
import { colors, spacing, typography, borderRadius } from '@/theme';

interface ExamplePromptsProps {
  onSelectPrompt: (prompt: string) => void;
}

const EXAMPLE_PROMPTS = [
  {
    icon: 'book-open-variant' as const,
    text: 'Generate plan to pass IELTS',
    color: colors.primary,
  },
  {
    icon: 'calendar-plus' as const,
    text: 'Create task tomorrow',
    color: colors.success,
  },
  {
    icon: 'bell-ring' as const,
    text: 'Remind me to...',
    color: colors.warning,
  },
  {
    icon: 'calendar-today' as const,
    text: "What's my schedule today?",
    color: colors.info || colors.primary,
  },
];

export function ExamplePrompts({ onSelectPrompt }: ExamplePromptsProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.sectionTitle}>Try these examples:</Text>
      <View style={styles.promptsGrid}>
        {EXAMPLE_PROMPTS.map((prompt, index) => (
          <TouchableOpacity
            key={index}
            style={styles.promptButton}
            onPress={() => onSelectPrompt(prompt.text)}
            activeOpacity={0.7}
          >
            <LiquidGlassCard
              variant="subtle"
              intensity="medium"
              style={styles.promptCard}
            >
              <View style={[styles.iconContainer, { backgroundColor: prompt.color + '20' }]}>
                <MaterialCommunityIcons
                  name={prompt.icon}
                  size={20}
                  color={prompt.color}
                />
              </View>
              <Text style={styles.promptText} numberOfLines={2}>
                {prompt.text}
              </Text>
            </LiquidGlassCard>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: spacing.lg,
    paddingBottom: 120, // Space for the composer
    paddingTop: spacing.md,
  },
  sectionTitle: {
    ...typography.labelMedium,
    color: colors.textSecondary,
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  promptsGrid: {
    gap: spacing.sm,
  },
  promptButton: {
    marginBottom: spacing.sm,
  },
  promptCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
  },
  iconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  promptText: {
    ...typography.bodyMedium,
    color: colors.text,
    flex: 1,
  },
});

export default ExamplePrompts;
