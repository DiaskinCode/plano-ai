import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

interface SelectOption {
  value: string;
  label: string;
}

interface SingleSelectProps {
  options: (string | SelectOption)[];
  value: string;
  onChange: (value: string) => void;
}

export function SingleSelect({ options, value, onChange }: SingleSelectProps) {
  return (
    <View style={styles.container}>
      {options.map((option) => {
        const optionValue = typeof option === 'string' ? option : option.value;
        const optionLabel = typeof option === 'string' ? option : option.label;
        const isSelected = value === optionValue;

        return (
          <TouchableOpacity
            key={optionValue}
            onPress={() => onChange(optionValue)}
            style={[
              styles.option,
              isSelected && styles.optionSelected,
            ]}
            activeOpacity={0.7}
          >
            <View style={[
              styles.radio,
              isSelected && styles.radioSelected
            ]}>
              {isSelected && <View style={styles.radioDot} />}
            </View>
            <Text style={[
              styles.optionText,
              isSelected && styles.optionTextSelected
            ]}>
              {optionLabel}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: '#F5F5F5',
    borderWidth: 1,
    borderColor: '#E0E0E0',
    marginBottom: 10,
  },
  optionSelected: {
    backgroundColor: '#E8F3FF',
    borderColor: '#007AFF',
    borderWidth: 2,
  },
  radio: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#CCCCCC',
    marginRight: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  radioSelected: {
    borderColor: '#007AFF',
  },
  radioDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#007AFF',
  },
  optionText: {
    fontSize: 15,
    color: '#333',
    flex: 1,
  },
  optionTextSelected: {
    color: '#007AFF',
    fontWeight: '600',
  },
});
