import React from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from 'react-native';

export interface Project {
  title: string;
  impact: string;
}

interface ProjectRepeaterProps {
  projects: Project[];
  onChange: (projects: Project[]) => void;
  maxProjects: number;
  placeholders: {
    title: string;
    impact: string;
  };
}

export function ProjectRepeater({
  projects,
  onChange,
  maxProjects,
  placeholders
}: ProjectRepeaterProps) {
  const handleAdd = () => {
    if (projects.length < maxProjects) {
      onChange([...projects, { title: '', impact: '' }]);
    }
  };

  const handleRemove = (index: number) => {
    onChange(projects.filter((_, i) => i !== index));
  };

  const handleChange = (index: number, field: 'title' | 'impact', value: string) => {
    const updated = [...projects];
    updated[index][field] = value;
    onChange(updated);
  };

  return (
    <View style={styles.container}>
      {projects.map((project, index) => (
        <View key={index} style={styles.projectCard}>
          <View style={styles.projectHeader}>
            <Text style={styles.projectLabel}>Project {index + 1}</Text>
            <TouchableOpacity
              onPress={() => handleRemove(index)}
              style={styles.removeButton}
            >
              <Text style={styles.removeText}>Remove</Text>
            </TouchableOpacity>
          </View>

          <TextInput
            style={styles.input}
            placeholder={placeholders.title}
            placeholderTextColor="#999"
            value={project.title}
            onChangeText={(value) => handleChange(index, 'title', value)}
          />

          <TextInput
            style={[styles.input, styles.inputMultiline]}
            placeholder={placeholders.impact}
            placeholderTextColor="#999"
            value={project.impact}
            onChangeText={(value) => handleChange(index, 'impact', value)}
            multiline
            numberOfLines={2}
          />
        </View>
      ))}

      {projects.length < maxProjects && (
        <TouchableOpacity onPress={handleAdd} style={styles.addButton}>
          <Text style={styles.addIcon}>+</Text>
          <Text style={styles.addText}>Add Project</Text>
        </TouchableOpacity>
      )}

      {projects.length === 0 && (
        <Text style={styles.emptyHint}>
          Optional but recommended - projects help recruiters understand your impact
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  projectCard: {
    backgroundColor: '#F9F9F9',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  projectHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  projectLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  removeButton: {
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  removeText: {
    color: '#FF3B30',
    fontSize: 13,
    fontWeight: '500',
  },
  input: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 12,
    fontSize: 14,
    borderWidth: 1,
    borderColor: '#D1D1D6',
    marginBottom: 10,
  },
  inputMultiline: {
    minHeight: 60,
    textAlignVertical: 'top',
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#007AFF',
    borderStyle: 'dashed',
    backgroundColor: '#F0F8FF',
  },
  addIcon: {
    fontSize: 20,
    color: '#007AFF',
    marginRight: 8,
    fontWeight: 'bold',
  },
  addText: {
    color: '#007AFF',
    fontSize: 15,
    fontWeight: '600',
  },
  emptyHint: {
    textAlign: 'center',
    color: '#666',
    fontSize: 13,
    fontStyle: 'italic',
    marginTop: 8,
  },
});
