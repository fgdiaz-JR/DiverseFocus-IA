/**
 * TranscribeScreen — Upload or record an audio file and receive a
 * text transcript. The result can then be simplified inline.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  StyleSheet,
  Alert,
} from 'react-native';
import DocumentPicker, { types } from 'react-native-document-picker';
import { api } from '../services/api';

interface TranscriptResult {
  transcript: string;
  language: string;
}

const TranscribeScreen: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<{ name: string; uri: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TranscriptResult | null>(null);
  const [simplifying, setSimplifying] = useState(false);
  const [simplifiedText, setSimplifiedText] = useState<string | null>(null);

  const pickAudioFile = async () => {
    try {
      const [file] = await DocumentPicker.pick({
        type: [types.audio],
        copyTo: 'cachesDirectory',
      });
      setSelectedFile({ name: file.name ?? 'audio', uri: file.fileCopyUri ?? file.uri });
      setResult(null);
      setSimplifiedText(null);
    } catch (err) {
      if (!DocumentPicker.isCancel(err)) {
        Alert.alert('File selection failed', 'Please try again.');
      }
    }
  };

  const handleTranscribe = async () => {
    if (!selectedFile) {
      Alert.alert('No file selected', 'Please pick an audio file first.');
      return;
    }
    setLoading(true);
    try {
      const data = await api.transcribeAudio(selectedFile.uri, selectedFile.name);
      setResult({ transcript: data.transcript, language: data.language });
    } catch (error: any) {
      Alert.alert(
        'Transcription failed',
        error?.response?.data?.detail ?? 'Please try again later.',
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSimplify = async () => {
    if (!result?.transcript) return;
    setSimplifying(true);
    try {
      const data = await api.simplifyText(result.transcript, 'easy');
      setSimplifiedText(data.simplified_text);
    } catch (error: any) {
      Alert.alert('Simplification failed', error?.response?.data?.detail ?? 'Please try again.');
    } finally {
      setSimplifying(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.heading}>🎙️  Audio Transcription</Text>
      <Text style={styles.subheading}>
        Upload an audio file and we will convert it to text using Whisper AI.
      </Text>

      {/* File picker */}
      <TouchableOpacity
        style={styles.pickButton}
        onPress={pickAudioFile}
        accessibilityRole="button"
        accessibilityLabel="Pick an audio file from your device"
      >
        <Text style={styles.pickButtonText}>📁  Choose Audio File</Text>
      </TouchableOpacity>

      {selectedFile && (
        <View style={styles.fileInfo}>
          <Text style={styles.fileName} numberOfLines={1}>
            🎵  {selectedFile.name}
          </Text>
        </View>
      )}

      {/* Transcribe button */}
      <TouchableOpacity
        style={[
          styles.transcribeButton,
          (!selectedFile || loading) && styles.buttonDisabled,
        ]}
        onPress={handleTranscribe}
        disabled={!selectedFile || loading}
        accessibilityRole="button"
        accessibilityLabel="Start transcription"
        accessibilityState={{ busy: loading }}
      >
        {loading ? (
          <View style={styles.row}>
            <ActivityIndicator color="#fff" style={{ marginRight: 8 }} />
            <Text style={styles.transcribeButtonText}>Transcribing…</Text>
          </View>
        ) : (
          <Text style={styles.transcribeButtonText}>▶  Transcribe</Text>
        )}
      </TouchableOpacity>

      {/* Progress indicator */}
      {loading && (
        <View style={styles.progressContainer}>
          <Text style={styles.progressText}>
            Processing audio… this may take a moment.
          </Text>
        </View>
      )}

      {/* Result */}
      {result && (
        <View style={styles.resultContainer}>
          <Text style={styles.resultHeading}>
            📝  Transcript{' '}
            <Text style={styles.langBadge}>({result.language.toUpperCase()})</Text>
          </Text>
          <Text style={styles.transcript} selectable>
            {result.transcript}
          </Text>

          <TouchableOpacity
            style={[styles.simplifyButton, simplifying && styles.buttonDisabled]}
            onPress={handleSimplify}
            disabled={simplifying}
            accessibilityRole="button"
            accessibilityLabel="Simplify this transcript"
          >
            {simplifying ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.simplifyButtonText}>✨  Simplify This Transcript</Text>
            )}
          </TouchableOpacity>
        </View>
      )}

      {/* Simplified transcript */}
      {simplifiedText && (
        <View style={styles.simplifiedContainer}>
          <Text style={styles.resultHeading}>✅  Simplified Version</Text>
          <Text style={styles.simplifiedText} selectable>
            {simplifiedText}
          </Text>
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
  heading: {
    fontSize: 22,
    fontWeight: '700',
    color: '#3D405B',
    marginBottom: 8,
  },
  subheading: {
    fontSize: 15,
    color: '#6B6E8A',
    lineHeight: 22,
    marginBottom: 24,
  },
  pickButton: {
    backgroundColor: '#F4EAF4',
    borderWidth: 1.5,
    borderColor: '#CBA8DC',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  pickButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#3D405B',
  },
  fileInfo: {
    marginTop: 12,
    backgroundColor: '#EDE9F4',
    borderRadius: 8,
    padding: 10,
  },
  fileName: {
    fontSize: 14,
    color: '#5A3E8A',
  },
  transcribeButton: {
    marginTop: 20,
    backgroundColor: '#8B5CF6',
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
  },
  buttonDisabled: {
    backgroundColor: '#C4B8DC',
  },
  transcribeButtonText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#fff',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  progressContainer: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#EDE9F4',
    borderRadius: 10,
  },
  progressText: {
    fontSize: 14,
    color: '#6B6E8A',
    textAlign: 'center',
  },
  resultContainer: {
    marginTop: 28,
    backgroundColor: '#EDE9F4',
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#CBA8DC',
    padding: 18,
  },
  resultHeading: {
    fontSize: 16,
    fontWeight: '700',
    color: '#3D405B',
    marginBottom: 10,
  },
  langBadge: {
    fontSize: 12,
    color: '#8B5CF6',
    fontWeight: '500',
  },
  transcript: {
    fontSize: 16,
    color: '#3D405B',
    lineHeight: 26,
  },
  simplifyButton: {
    marginTop: 16,
    backgroundColor: '#81B29A',
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
  },
  simplifyButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#fff',
  },
  simplifiedContainer: {
    marginTop: 20,
    backgroundColor: '#EBF5F0',
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#81B29A',
    padding: 18,
  },
  simplifiedText: {
    fontSize: 17,
    color: '#3D405B',
    lineHeight: 28,
  },
});

export default TranscribeScreen;
