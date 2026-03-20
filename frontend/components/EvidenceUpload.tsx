import { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  TextInput,
  Alert,
  Image,
  ScrollView
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import * as DocumentPicker from 'expo-document-picker';

interface EvidenceUploadProps {
  visible: boolean;
  taskId: number;
  taskTitle: string;
  onClose: () => void;
  onUpload: (evidence: any) => void;
}

type EvidenceType = 'file' | 'link' | 'screenshot' | 'note' | 'photo';

export default function EvidenceUpload({
  visible,
  taskId,
  taskTitle,
  onClose,
  onUpload
}: EvidenceUploadProps) {
  const [evidenceType, setEvidenceType] = useState<EvidenceType>('note');
  const [note, setNote] = useState('');
  const [url, setUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  const evidenceTypes = [
    { id: 'note', icon: 'note-text', label: 'Note' },
    { id: 'link', icon: 'link', label: 'Link' },
    { id: 'photo', icon: 'camera', label: 'Photo' },
    { id: 'screenshot', icon: 'monitor-screenshot', label: 'Screenshot' },
    { id: 'file', icon: 'file', label: 'File' },
  ];

  const handlePickImage = async () => {
    try {
      // Request permission first
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'We need photo library access to select images');
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        quality: 1,
      });

      if (!result.canceled && result.assets[0]) {
        const uri = result.assets[0].uri;

        // Validate URI exists
        if (!uri) {
          Alert.alert('Error', 'Failed to get image');
          return;
        }

        setSelectedImage(uri);
      }
    } catch (error) {
      console.error('Failed to pick image:', error);
      Alert.alert('Error', 'Failed to select image. Please try again.');
    }
  };

  const handleTakePhoto = async () => {
    try {
      // Request camera permission
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'We need camera access to take photos');
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        quality: 1,
      });

      if (!result.canceled && result.assets[0]) {
        const uri = result.assets[0].uri;

        if (!uri) {
          Alert.alert('Error', 'Failed to capture photo');
          return;
        }

        setSelectedImage(uri);
      }
    } catch (error) {
      console.error('Failed to take photo:', error);
      Alert.alert('Error', 'Failed to take photo. Please try again.');
    }
  };

  const handlePickFile = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: '*/*',
        copyToCacheDirectory: true,
      });

      if (result.type === 'success') {
        // Validate file exists and has required properties
        if (!result.uri || !result.name) {
          Alert.alert('Error', 'Invalid file selected');
          return;
        }

        // Check file size (max 10MB)
        if (result.size && result.size > 10 * 1024 * 1024) {
          Alert.alert('Error', 'File is too large. Maximum size is 10MB');
          return;
        }

        setSelectedFile(result);
      }
    } catch (error: any) {
      console.error('Failed to pick file:', error);
      if (error.name === 'AbortError') {
        // User cancelled, no need to show error
        return;
      }
      Alert.alert('Error', 'Failed to select file. Please try again.');
    }
  };

  const handleSubmit = () => {
    const evidence: any = {
      task_id: taskId,
      evidence_type: evidenceType,
    };

    if (evidenceType === 'note') {
      if (!note.trim()) {
        Alert.alert('Error', 'Please enter a note');
        return;
      }
      evidence.note = note;
    } else if (evidenceType === 'link') {
      if (!url.trim()) {
        Alert.alert('Error', 'Please enter a URL');
        return;
      }
      evidence.url = url;
    } else if (evidenceType === 'photo' || evidenceType === 'screenshot') {
      if (!selectedImage) {
        Alert.alert('Error', 'Please select an image');
        return;
      }
      evidence.file = selectedImage;
    } else if (evidenceType === 'file') {
      if (!selectedFile) {
        Alert.alert('Error', 'Please select a file');
        return;
      }
      evidence.file = selectedFile;
    }

    onUpload(evidence);
    resetForm();
    onClose();
  };

  const resetForm = () => {
    setNote('');
    setUrl('');
    setSelectedFile(null);
    setSelectedImage(null);
    setEvidenceType('note');
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={styles.container}>
          <View style={styles.header}>
            <View>
              <Text style={styles.title}>Upload Evidence</Text>
              <Text style={styles.subtitle} numberOfLines={1}>{taskTitle}</Text>
            </View>
            <TouchableOpacity onPress={onClose}>
              <MaterialCommunityIcons name="close" size={24} color="#ECECEC" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.content}>
            {/* Evidence Type Selector */}
            <Text style={styles.label}>Evidence Type</Text>
            <View style={styles.typeGrid}>
              {evidenceTypes.map((type) => (
                <TouchableOpacity
                  key={type.id}
                  style={[
                    styles.typeButton,
                    evidenceType === type.id && styles.typeButtonActive
                  ]}
                  onPress={() => setEvidenceType(type.id as EvidenceType)}
                >
                  <MaterialCommunityIcons
                    name={type.icon}
                    size={20}
                    color={evidenceType === type.id ? '#007AFF' : '#8E8E8E'}
                  />
                  <Text style={[
                    styles.typeLabel,
                    evidenceType === type.id && styles.typeLabelActive
                  ]}>
                    {type.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Type-Specific Input */}
            {evidenceType === 'note' && (
              <View style={styles.inputSection}>
                <Text style={styles.label}>Note</Text>
                <TextInput
                  style={[styles.input, styles.textArea]}
                  placeholder="Describe what you did, what you learned, etc."
                  placeholderTextColor="#666"
                  value={note}
                  onChangeText={setNote}
                  multiline
                  numberOfLines={6}
                />
              </View>
            )}

            {evidenceType === 'link' && (
              <View style={styles.inputSection}>
                <Text style={styles.label}>URL</Text>
                <TextInput
                  style={styles.input}
                  placeholder="https://..."
                  placeholderTextColor="#666"
                  value={url}
                  onChangeText={setUrl}
                  keyboardType="url"
                  autoCapitalize="none"
                />
              </View>
            )}

            {(evidenceType === 'photo' || evidenceType === 'screenshot') && (
              <View style={styles.inputSection}>
                <Text style={styles.label}>Image</Text>
                <View style={styles.imageButtons}>
                  <TouchableOpacity
                    style={styles.imageButton}
                    onPress={handlePickImage}
                  >
                    <MaterialCommunityIcons name="image" size={24} color="#007AFF" />
                    <Text style={styles.imageButtonText}>Choose from Gallery</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.imageButton}
                    onPress={handleTakePhoto}
                  >
                    <MaterialCommunityIcons name="camera" size={24} color="#007AFF" />
                    <Text style={styles.imageButtonText}>Take Photo</Text>
                  </TouchableOpacity>
                </View>
                {selectedImage && (
                  <View style={styles.preview}>
                    <Image source={{ uri: selectedImage }} style={styles.previewImage} />
                    <TouchableOpacity
                      style={styles.removeButton}
                      onPress={() => setSelectedImage(null)}
                    >
                      <MaterialCommunityIcons name="close-circle" size={24} color="#FF3B30" />
                    </TouchableOpacity>
                  </View>
                )}
              </View>
            )}

            {evidenceType === 'file' && (
              <View style={styles.inputSection}>
                <Text style={styles.label}>File</Text>
                <TouchableOpacity
                  style={styles.fileButton}
                  onPress={handlePickFile}
                >
                  <MaterialCommunityIcons name="file-upload" size={24} color="#007AFF" />
                  <Text style={styles.fileButtonText}>
                    {selectedFile ? selectedFile.name : 'Choose File'}
                  </Text>
                </TouchableOpacity>
                {selectedFile && (
                  <View style={styles.fileInfo}>
                    <MaterialCommunityIcons name="file" size={20} color="#34C759" />
                    <Text style={styles.fileName}>{selectedFile.name}</Text>
                    <TouchableOpacity onPress={() => setSelectedFile(null)}>
                      <MaterialCommunityIcons name="close" size={20} color="#FF3B30" />
                    </TouchableOpacity>
                  </View>
                )}
              </View>
            )}
          </ScrollView>

          {/* Actions */}
          <View style={styles.actions}>
            <TouchableOpacity
              style={[styles.button, styles.cancelButton]}
              onPress={onClose}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, styles.submitButton]}
              onPress={handleSubmit}
            >
              <MaterialCommunityIcons name="upload" size={18} color="#fff" />
              <Text style={styles.submitButtonText}>Upload Evidence</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'flex-end',
  },
  container: {
    backgroundColor: '#1A1A1A',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#3E3E3E',
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: '#ECECEC',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#8E8E8E',
  },
  content: {
    padding: 20,
  },
  label: {
    fontSize: 15,
    fontWeight: '600',
    color: '#ECECEC',
    marginBottom: 12,
  },
  typeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 24,
  },
  typeButton: {
    flex: 1,
    minWidth: '30%',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#2A2A2A',
    borderWidth: 1,
    borderColor: '#3E3E3E',
  },
  typeButtonActive: {
    backgroundColor: '#007AFF20',
    borderColor: '#007AFF',
  },
  typeLabel: {
    fontSize: 13,
    fontWeight: '500',
    color: '#8E8E8E',
  },
  typeLabelActive: {
    color: '#007AFF',
  },
  inputSection: {
    marginBottom: 20,
  },
  input: {
    backgroundColor: '#2A2A2A',
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    color: '#ECECEC',
    borderWidth: 1,
    borderColor: '#3E3E3E',
  },
  textArea: {
    height: 120,
    textAlignVertical: 'top',
  },
  imageButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  imageButton: {
    flex: 1,
    alignItems: 'center',
    padding: 16,
    borderRadius: 8,
    backgroundColor: '#2A2A2A',
    borderWidth: 1,
    borderColor: '#3E3E3E',
    gap: 8,
  },
  imageButtonText: {
    fontSize: 13,
    color: '#ECECEC',
  },
  preview: {
    marginTop: 12,
    position: 'relative',
  },
  previewImage: {
    width: '100%',
    height: 200,
    borderRadius: 8,
  },
  removeButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
  },
  fileButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 16,
    borderRadius: 8,
    backgroundColor: '#2A2A2A',
    borderWidth: 1,
    borderColor: '#3E3E3E',
  },
  fileButtonText: {
    fontSize: 15,
    color: '#ECECEC',
  },
  fileInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 12,
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#2A2A2A',
  },
  fileName: {
    flex: 1,
    fontSize: 14,
    color: '#ECECEC',
  },
  actions: {
    flexDirection: 'row',
    gap: 12,
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#3E3E3E',
  },
  button: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 14,
    borderRadius: 8,
  },
  cancelButton: {
    backgroundColor: '#2A2A2A',
    borderWidth: 1,
    borderColor: '#3E3E3E',
  },
  submitButton: {
    backgroundColor: '#34C759',
  },
  cancelButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#ECECEC',
  },
  submitButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#fff',
  },
});
