import { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Modal,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

interface InputSlot {
  type: 'text' | 'choice';
  question: string;
  options?: string[];
}

interface LetsGoModalProps {
  visible: boolean;
  task: {
    id: number;
    title: string;
    lets_go_inputs?: InputSlot[];
    artifact_template?: any;
  };
  onClose: () => void;
  onComplete: (artifact: any) => void;
}

export default function LetsGoModal({
  visible,
  task,
  onClose,
  onComplete
}: LetsGoModalProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentSlotIndex, setCurrentSlotIndex] = useState(0);
  const [artifact, setArtifact] = useState<any>(null);
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    if (visible) {
      initializeChat();
    }
  }, [visible]);

  const initializeChat = () => {
    const welcomeMessage: Message = {
      id: Date.now().toString(),
      type: 'ai',
      content: `Let's work on: ${task.title}\n\nI'll help you complete this step by step. Ready to start?`,
      timestamp: new Date()
    };

    setMessages([welcomeMessage]);
    setCurrentSlotIndex(0);
    setArtifact(null);

    // If there are input slots, ask the first question
    if (task.lets_go_inputs && task.lets_go_inputs.length > 0) {
      const firstSlot = task.lets_go_inputs[0];
      addAIMessage(firstSlot.question);
    }
  };

  const addAIMessage = (content: string) => {
    const message: Message = {
      id: Date.now().toString(),
      type: 'ai',
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, message]);
    scrollToBottom();
  };

  const addUserMessage = (content: string) => {
    const message: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, message]);
    setInputText('');
    scrollToBottom();
  };

  const scrollToBottom = () => {
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userInput = inputText.trim();
    addUserMessage(userInput);

    // Move to next slot if available
    if (task.lets_go_inputs && currentSlotIndex < task.lets_go_inputs.length - 1) {
      const nextIndex = currentSlotIndex + 1;
      setCurrentSlotIndex(nextIndex);
      const nextSlot = task.lets_go_inputs[nextIndex];

      setTimeout(() => {
        addAIMessage(nextSlot.question);
      }, 500);
    } else {
      // All inputs collected, generate artifact
      setTimeout(() => {
        generateArtifact();
      }, 500);
    }
  };

  const handleChipSelect = (option: string) => {
    addUserMessage(option);

    // Move to next slot
    if (task.lets_go_inputs && currentSlotIndex < task.lets_go_inputs.length - 1) {
      const nextIndex = currentSlotIndex + 1;
      setCurrentSlotIndex(nextIndex);
      const nextSlot = task.lets_go_inputs[nextIndex];

      setTimeout(() => {
        addAIMessage(nextSlot.question);
      }, 500);
    } else {
      setTimeout(() => {
        generateArtifact();
      }, 500);
    }
  };

  const generateArtifact = async () => {
    setLoading(true);
    addAIMessage("Great! Let me compile everything for you...");

    // Simulate artifact generation
    setTimeout(() => {
      const mockArtifact = {
        type: 'shortlist',
        content: {
          items: [
            'Stanford University - MS CS',
            'MIT - EECS Graduate Program',
            'Carnegie Mellon - CS Graduate'
          ],
          notes: 'Top programs matching your criteria'
        }
      };

      setArtifact(mockArtifact);
      setLoading(false);
      addAIMessage("✨ Done! Here's your shortlist. Review it and let me know if you want to make any changes.");
    }, 2000);
  };

  const handleComplete = () => {
    if (artifact) {
      onComplete(artifact);
      onClose();
    }
  };

  const currentSlot = task.lets_go_inputs?.[currentSlotIndex];

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={false}
      onRequestClose={onClose}
    >
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerContent}>
            <MaterialCommunityIcons name="chat" size={24} color="#007AFF" />
            <Text style={styles.headerTitle}>Let's Go</Text>
          </View>
          <TouchableOpacity onPress={onClose}>
            <MaterialCommunityIcons name="close" size={24} color="#ECECEC" />
          </TouchableOpacity>
        </View>

        {/* Chat Messages */}
        <ScrollView
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
        >
          {messages.map((message) => (
            <View
              key={message.id}
              style={[
                styles.messageBubble,
                message.type === 'user' ? styles.userBubble : styles.aiBubble
              ]}
            >
              <Text style={[
                styles.messageText,
                message.type === 'user' ? styles.userText : styles.aiText
              ]}>
                {message.content}
              </Text>
              <Text style={styles.messageTime}>
                {message.timestamp.toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </Text>
            </View>
          ))}

          {loading && (
            <View style={styles.loadingBubble}>
              <ActivityIndicator size="small" color="#8E8E8E" />
              <Text style={styles.loadingText}>Thinking...</Text>
            </View>
          )}

          {/* Artifact Preview */}
          {artifact && (
            <View style={styles.artifactPreview}>
              <Text style={styles.artifactTitle}>Generated Artifact</Text>
              <View style={styles.artifactContent}>
                {artifact.content.items.map((item: string, index: number) => (
                  <Text key={index} style={styles.artifactItem}>• {item}</Text>
                ))}
              </View>
              <TouchableOpacity
                style={styles.completeButton}
                onPress={handleComplete}
              >
                <MaterialCommunityIcons name="check-circle" size={20} color="#fff" />
                <Text style={styles.completeButtonText}>Save & Complete</Text>
              </TouchableOpacity>
            </View>
          )}
        </ScrollView>

        {/* Input Area */}
        {!artifact && (
          <View style={styles.inputContainer}>
            {/* Quick Reply Chips */}
            {currentSlot?.type === 'choice' && currentSlot.options && (
              <ScrollView
                horizontal
                style={styles.chipsContainer}
                showsHorizontalScrollIndicator={false}
              >
                {currentSlot.options.map((option, index) => (
                  <TouchableOpacity
                    key={index}
                    style={styles.chip}
                    onPress={() => handleChipSelect(option)}
                  >
                    <Text style={styles.chipText}>{option}</Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            )}

            {/* Text Input */}
            {(!currentSlot || currentSlot.type === 'text') && (
              <View style={styles.inputRow}>
                <TextInput
                  style={styles.input}
                  placeholder="Type your response..."
                  placeholderTextColor="#666"
                  value={inputText}
                  onChangeText={setInputText}
                  multiline
                  maxLength={500}
                />
                <TouchableOpacity
                  style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
                  onPress={handleSendMessage}
                  disabled={!inputText.trim()}
                >
                  <MaterialCommunityIcons
                    name="send"
                    size={20}
                    color={inputText.trim() ? '#fff' : '#666'}
                  />
                </TouchableOpacity>
              </View>
            )}
          </View>
        )}
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1A1A1A',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    paddingTop: 60,
    backgroundColor: '#2A2A2A',
    borderBottomWidth: 1,
    borderBottomColor: '#3E3E3E',
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ECECEC',
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
    gap: 12,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#007AFF',
  },
  aiBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#2A2A2A',
    borderWidth: 1,
    borderColor: '#3E3E3E',
  },
  messageText: {
    fontSize: 15,
    lineHeight: 21,
  },
  userText: {
    color: '#fff',
  },
  aiText: {
    color: '#ECECEC',
  },
  messageTime: {
    fontSize: 11,
    color: '#8E8E8E',
    marginTop: 4,
  },
  loadingBubble: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    borderRadius: 12,
    backgroundColor: '#2A2A2A',
    alignSelf: 'flex-start',
  },
  loadingText: {
    fontSize: 14,
    color: '#8E8E8E',
  },
  artifactPreview: {
    backgroundColor: '#2A2A2A',
    borderRadius: 12,
    padding: 16,
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#34C759',
  },
  artifactTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#34C759',
    marginBottom: 12,
  },
  artifactContent: {
    backgroundColor: '#1A1A1A',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  artifactItem: {
    fontSize: 14,
    color: '#ECECEC',
    marginBottom: 6,
  },
  completeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#34C759',
    paddingVertical: 12,
    borderRadius: 8,
  },
  completeButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#fff',
  },
  inputContainer: {
    backgroundColor: '#2A2A2A',
    borderTopWidth: 1,
    borderTopColor: '#3E3E3E',
  },
  chipsContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#3E3E3E',
  },
  chip: {
    backgroundColor: '#1A1A1A',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 16,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#3E3E3E',
  },
  chipText: {
    fontSize: 14,
    color: '#ECECEC',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 12,
    gap: 8,
  },
  input: {
    flex: 1,
    backgroundColor: '#1A1A1A',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    color: '#ECECEC',
    maxHeight: 100,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#007AFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#3E3E3E',
  },
});
