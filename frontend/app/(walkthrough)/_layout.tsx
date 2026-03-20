/**
 * Walkthrough Layout
 *
 * Modal-style layout for new user onboarding
 * Shows 3-4 friendly screens explaining app features
 */

import { Stack } from 'expo-router';

export default function WalkthroughLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        gestureEnabled: true,
        animation: 'slide_from_right',
      }}
    >
      <Stack.Screen name="welcome" options={{ gestureEnabled: false }} />
      <Stack.Screen name="features" />
      <Stack.Screen name="ready" options={{ gestureEnabled: false }} />
    </Stack>
  );
}
