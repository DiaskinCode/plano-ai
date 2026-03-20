// Safe wrappers for keyboard-controller components that work in Expo Go
import React, { useState, useEffect } from 'react';
import { View, Keyboard, KeyboardAvoidingView as RNKeyboardAvoidingView, Platform, ViewProps } from 'react-native';

// Try to import from keyboard-controller, fall back to RN components if not available
let KeyboardStickyViewNative: React.ComponentType<any> | null = null;
let KeyboardAvoidingViewNative: React.ComponentType<any> | null = null;

try {
  const keyboardController = require('react-native-keyboard-controller');
  KeyboardStickyViewNative = keyboardController.KeyboardStickyView;
  KeyboardAvoidingViewNative = keyboardController.KeyboardAvoidingView;
} catch (e) {
  // Fallback for Expo Go
  console.warn('react-native-keyboard-controller not available, using fallbacks');
}

interface KeyboardStickyViewProps extends ViewProps {
  offset?: { closed?: number; opened?: number };
  children: React.ReactNode;
}

export const SafeKeyboardStickyView: React.FC<KeyboardStickyViewProps> = ({
  children,
  style,
  offset,
  ...props
}) => {
  const [keyboardHeight, setKeyboardHeight] = useState(0);

  useEffect(() => {
    // Only use fallback keyboard logic if native module is not available
    if (KeyboardStickyViewNative) return;

    const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';

    const showListener = Keyboard.addListener(showEvent, (e) => {
      setKeyboardHeight(e.endCoordinates.height);
    });
    const hideListener = Keyboard.addListener(hideEvent, () => {
      setKeyboardHeight(0);
    });

    return () => {
      showListener.remove();
      hideListener.remove();
    };
  }, []);

  if (KeyboardStickyViewNative) {
    return (
      <KeyboardStickyViewNative style={style} offset={offset} {...props}>
        {children}
      </KeyboardStickyViewNative>
    );
  }

  // Calculate bottom position based on keyboard state
  const bottomOffset = keyboardHeight > 0
    ? keyboardHeight + (offset?.opened ?? 0)
    : (offset?.closed ?? 0);

  // Fallback: View that responds to keyboard events
  return (
    <View
      style={[
        {
          position: 'absolute',
          bottom: bottomOffset,
          left: 0,
          right: 0,
          zIndex: 1000,
        },
        style,
      ]}
      {...props}
    >
      {children}
    </View>
  );
};

interface KeyboardAvoidingViewProps extends ViewProps {
  behavior?: 'height' | 'position' | 'padding';
  keyboardVerticalOffset?: number;
  children: React.ReactNode;
}

export const SafeKeyboardAvoidingView: React.FC<KeyboardAvoidingViewProps> = ({
  children,
  behavior,
  keyboardVerticalOffset,
  style,
  ...props
}) => {
  if (KeyboardAvoidingViewNative) {
    return (
      <KeyboardAvoidingViewNative
        style={style}
        behavior={behavior}
        keyboardVerticalOffset={keyboardVerticalOffset}
        {...props}
      >
        {children}
      </KeyboardAvoidingViewNative>
    );
  }

  // Fallback: use React Native's KeyboardAvoidingView
  return (
    <RNKeyboardAvoidingView
      style={[{ flex: 1 }, style]}
      behavior={behavior ?? (Platform.OS === 'ios' ? 'padding' : 'height')}
      keyboardVerticalOffset={keyboardVerticalOffset}
      {...props}
    >
      {children}
    </RNKeyboardAvoidingView>
  );
};
