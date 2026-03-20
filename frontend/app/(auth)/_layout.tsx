import { Stack } from 'expo-router';

export default function AuthLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="login" />
      {/* Register temporarily disabled due to syntax error */}
      {/* <Stack.Screen name="register" /> */}
    </Stack>
  );
}
