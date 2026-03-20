import { Stack } from 'expo-router';
// import { useEffect } from 'react';
// import { Platform, Text, TextInput } from 'react-native';
import '@/services/i18n'; // Initialize i18n
// import analytics from '@/services/analytics';

export default function RootLayout() {
  // useEffect(() => {
  //   // Initialize Mixpanel analytics
  //   analytics.initialize();

  //   // Set default font for all Text and TextInput components
  //   const defaultFontFamily = Platform.OS === 'ios' ? 'Helvetica Neue' : 'sans-serif';

  //   // @ts-ignore
  //   Text.defaultProps = Text.defaultProps || {};
  //   // @ts-ignore
  //   Text.defaultProps.style = { fontFamily: defaultFontFamily };

  //   // @ts-ignore
  //   TextInput.defaultProps = TextInput.defaultProps || {};
  //   // @ts-ignore
  //   TextInput.defaultProps.style = { fontFamily: defaultFontFamily };
  // }, []);

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="index" />
      <Stack.Screen name="(intro)" />
      <Stack.Screen name="(auth)" />
      <Stack.Screen name="(onboarding)" />
      <Stack.Screen name="(main)" />
    </Stack>
  );
}
