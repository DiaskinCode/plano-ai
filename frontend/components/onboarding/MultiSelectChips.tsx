import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

interface MultiSelectChipsProps {
  options: string[];
  selectedValues: string[];
  onChange: (values: string[]) => void;
  maxSelections?: number;
}

export function MultiSelectChips({
  options,
  selectedValues,
  onChange,
  maxSelections
}: MultiSelectChipsProps) {
  const handleToggle = (option: string) => {
    if (selectedValues.includes(option)) {
      // Deselect
      onChange(selectedValues.filter(v => v !== option));
    } else {
      // Select (check max limit)
      if (!maxSelections || selectedValues.length < maxSelections) {
        onChange([...selectedValues, option]);
      }
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.chipContainer}>
        {options.map((option) => {
          const isSelected = selectedValues.includes(option);
          return (
            <TouchableOpacity
              key={option}
              onPress={() => handleToggle(option)}
              style={[
                styles.chip,
                isSelected && styles.chipSelected,
              ]}
              activeOpacity={0.7}
            >
              <Text
                style={[
                  styles.chipText,
                  isSelected && styles.chipTextSelected,
                ]}
              >
                {option}
              </Text>
              {isSelected && (
                <Text style={styles.checkmark}>✓</Text>
              )}
            </TouchableOpacity>
          );
        })}
      </View>

      {maxSelections && (
        <Text style={styles.hint}>
          {selectedValues.length} / {maxSelections} selected
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 20,
    backgroundColor: '#F5F5F5',
    borderWidth: 1,
    borderColor: '#E0E0E0',
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  chipSelected: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  chipText: {
    color: '#333',
    fontSize: 14,
    fontWeight: '500',
  },
  chipTextSelected: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  checkmark: {
    marginLeft: 6,
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: 'bold',
  },
  hint: {
    marginTop: 8,
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
});
