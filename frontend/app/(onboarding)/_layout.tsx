import { Stack } from 'expo-router';
import { OnboardingProvider } from '@/components/onboarding/OnboardingContext';

function OnboardingStack() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        animation: 'slide_from_right',
      }}
      initialRouteName="language"
    >
      <Stack.Screen
        name="language"
        options={{
          gestureEnabled: false,
        }}
      />
      <Stack.Screen
        name="welcome"
        options={{
          gestureEnabled: true,
        }}
      />
      <Stack.Screen
        name="auth"
        options={{
          gestureEnabled: true,
        }}
      />
      <Stack.Screen
        name="profile-basic"
        options={{
          gestureEnabled: true,
        }}
      />
      <Stack.Screen
        name="academic"
        options={{
          gestureEnabled: true,
        }}
      />
      <Stack.Screen
        name="test-scores"
        options={{
          gestureEnabled: true,
        }}
      />
      <Stack.Screen
        name="extracurriculars"
        options={{
          gestureEnabled: true,
        }}
      />
      <Stack.Screen
        name="target-countries"
        options={{
          gestureEnabled: true,
        }}
      />
      <Stack.Screen
        name="target-universities"
        options={{
          gestureEnabled: true,
        }}
      />
      <Stack.Screen
        name="plan-selection"
        options={{
          gestureEnabled: true,
        }}
      />
      <Stack.Screen
        name="generating"
        options={{
          gestureEnabled: false,
        }}
      />
      <Stack.Screen
        name="preview"
        options={{
          gestureEnabled: true,
        }}
      />
      <Stack.Screen
        name="subscription"
        options={{
          gestureEnabled: true,
        }}
      />
      <Stack.Screen
        name="payment"
        options={{
          gestureEnabled: true,
        }}
      />
      <Stack.Screen
        name="success"
        options={{
          gestureEnabled: false,
        }}
      />
    </Stack>
  );
}

export default function OnboardingLayout() {
  return (
    <OnboardingProvider>
      <OnboardingStack />
    </OnboardingProvider>
  );
}
