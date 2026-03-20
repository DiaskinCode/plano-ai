import { Stack } from 'expo-router';

export default function IntroLayout() {
  return (
    <Stack screenOptions={{ headerShown: false, animation: 'fade' }}>
      <Stack.Screen name="language" />
      <Stack.Screen name="slide1" />
      <Stack.Screen name="slide2" />
      <Stack.Screen name="slide3" />
      <Stack.Screen name="slide4" />
    </Stack>
  );
}
