/**
 * SimplifyScreen — Allows users to enter complex text and get a
 * simplified, accessible version powered by the AI inference service.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  StyleSheet,
  Alert,
  AccessibilityInfo,
} from 'react-native';
import { api } from '../services/api';

type Level = 'easy' | 'medium' | 'advanced';

const LEVELS: { key: Level; label: string; description: string }[] = [
  { key: 'easy', label: 'Easy', description: 'Simple words, short sentences' },
  { key: 'medium', label: 'Medium', description: 'Clear language, some detail' },
  { key: 'advanced', label: 'Advanced', description: 'Full detail, better structure' },
];

const SimplifyScreen: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [level, setLevel] = useState<Level>('medium');
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSimplify = async () => {
    if (!inputText.trim()) {
      Alert.alert('Nothing to simplify', 'Please enter some text first.');
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const data = await api.simplifyText(inputText.trim(), level);
      setResult(data.simplified_text);
      AccessibilityInfo.announceForAccessibility('Text simplified successfully.');
    } catch (error: any) {
      Alert.alert(
        'Simplification failed',
        error?.response?.data?.detail ?? 'Please try again later.',
      );
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setInputText('');
    setResult(null);
  };

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
    >
      <Text style={styles.label}>Paste or type your text below:</Text>
      <TextInput
        style={styles.textInput}
        multiline
        numberOfLines={6}
        placeholder="e.g. The mitochondria is the organelle responsible for cellular respiration…"
        placeholderTextColor="#AAA8C4"
        value={inputText}
        onChangeText={setInputText}
        accessibilityLabel="Input text to simplify"
        textAlignVertical="top"
      />

      <Text style={styles.label}>Reading level:</Text>
      <View style={styles.levelRow}>
        {LEVELS.map((l) => (
          <TouchableOpacity
            key={l.key}
            style={[styles.levelButton, level === l.key && styles.levelButtonActive]}
            onPress={() => setLevel(l.key)}
            accessibilityRole="radio"
            accessibilityState={{ selected: level === l.key }}
            accessibilityLabel={`${l.label}: ${l.description}`}
          >
            <Text
              style={[styles.levelLabel, level === l.key && styles.levelLabelActive]}
            >
              {l.label}
            </Text>
            <Text
              style={[styles.levelDesc, level === l.key && styles.levelDescActive]}
            >
              {l.description}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <TouchableOpacity
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={handleSimplify}
        disabled={loading}
        accessibilityRole="button"
        accessibilityLabel="Simplify text"
        accessibilityState={{ busy: loading }}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>✨  Simplify</Text>
        )}
      </TouchableOpacity>

      {result !== null && (
        <View style={styles.resultContainer}>
          <Text style={styles.resultHeading}>✅  Simplified Text</Text>
          <Text style={styles.resultText} selectable>
            {result}
          </Text>
          <TouchableOpacity
            style={styles.clearButton}
            onPress={handleClear}
            accessibilityRole="button"
            accessibilityLabel="Clear and start over"
          >
            <Text style={styles.clearButtonText}>Clear</Text>
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 20,
    paddingBottom: 40,
    backgroundColor: '#F7F3EE',
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#3D405B',
    marginBottom: 8,
    marginTop: 16,
  },
  textInput: {
    backgroundColor: '#fff',
    borderWidth: 1.5,
    borderColor: '#D4CFC8',
    borderRadius: 12,
    padding: 14,
    fontSize: 16,
    color: '#3D405B',
    lineHeight: 24,
    minHeight: 130,
  },
  levelRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 8,
  },
  levelButton: {
    flex: 1,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#D4CFC8',
    backgroundColor: '#fff',
    padding: 12,
    alignItems: 'center',
  },
  levelButtonActive: {
    borderColor: '#81B29A',
    backgroundColor: '#EBF5F0',
  },
  levelLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B6E8A',
    marginBottom: 2,
  },
  levelLabelActive: {
    color: '#3D405B',
  },
  levelDesc: {
    fontSize: 11,
    color: '#AAA8C4',
    textAlign: 'center',
  },
  levelDescActive: {
    color: '#6B7F72',
  },
  button: {
    backgroundColor: '#81B29A',
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 20,
  },
  buttonDisabled: {
    backgroundColor: '#BDD8CC',
  },
  buttonText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#fff',
  },
  resultContainer: {
    marginTop: 28,
    backgroundColor: '#EBF5F0',
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#81B29A',
    padding: 18,
  },
  resultHeading: {
    fontSize: 16,
    fontWeight: '700',
    color: '#3D405B',
    marginBottom: 12,
  },
  resultText: {
    fontSize: 17,
    color: '#3D405B',
    lineHeight: 28,
  },
  clearButton: {
    marginTop: 16,
    alignSelf: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#D4CFC8',
  },
  clearButtonText: {
    fontSize: 14,
    color: '#3D405B',
    fontWeight: '500',
  },
});

export default SimplifyScreen;
