/**
 * ProfileScreen — User profile and accessibility preferences.
 */

import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  Switch,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { api, type UserProfile } from '../services/api';

type FontSize = 'small' | 'medium' | 'large';

const FONT_SIZE_OPTIONS: FontSize[] = ['small', 'medium', 'large'];

const ProfileScreen: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Preference state
  const [highContrast, setHighContrast] = useState(false);
  const [fontSize, setFontSize] = useState<FontSize>('medium');
  const [simplifiedLanguage, setSimplifiedLanguage] = useState(false);

  const fetchProfile = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getProfile();
      setProfile(data);
      setHighContrast(data.preferences?.high_contrast ?? false);
      setFontSize((data.preferences?.font_size as FontSize) ?? 'medium');
      setSimplifiedLanguage(data.preferences?.simplified_language ?? false);
    } catch (error: any) {
      Alert.alert('Error', 'Could not load profile. Please check your connection.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.updateProfile({
        preferences: {
          high_contrast: highContrast,
          font_size: fontSize,
          simplified_language: simplifiedLanguage,
        },
      });
      Alert.alert('Saved! ✅', 'Your preferences have been updated.');
    } catch (error: any) {
      Alert.alert('Save failed', 'Please try again.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#81B29A" />
        <Text style={styles.loadingText}>Loading your profile…</Text>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {/* User info card */}
      <View style={styles.profileCard}>
        <Text style={styles.avatar}>👤</Text>
        <View>
          <Text style={styles.username}>{profile?.username ?? 'User'}</Text>
          {profile?.email && <Text style={styles.email}>{profile.email}</Text>}
        </View>
      </View>

      <Text style={styles.sectionTitle}>Accessibility Preferences</Text>
      <Text style={styles.sectionSubtitle}>
        Adjust these settings to make the app more comfortable for you.
      </Text>

      {/* High contrast */}
      <View style={styles.preferenceRow}>
        <View style={styles.prefInfo}>
          <Text style={styles.prefTitle}>🌗  High Contrast Mode</Text>
          <Text style={styles.prefDesc}>
            Increases text/background contrast for easier reading.
          </Text>
        </View>
        <Switch
          value={highContrast}
          onValueChange={setHighContrast}
          trackColor={{ false: '#D4CFC8', true: '#81B29A' }}
          thumbColor={highContrast ? '#fff' : '#fff'}
          accessibilityLabel="Toggle high contrast mode"
          accessibilityRole="switch"
        />
      </View>

      {/* Simplified language */}
      <View style={styles.preferenceRow}>
        <View style={styles.prefInfo}>
          <Text style={styles.prefTitle}>💬  Simplified Language</Text>
          <Text style={styles.prefDesc}>
            Automatically request easy language in AI responses.
          </Text>
        </View>
        <Switch
          value={simplifiedLanguage}
          onValueChange={setSimplifiedLanguage}
          trackColor={{ false: '#D4CFC8', true: '#81B29A' }}
          thumbColor="#fff"
          accessibilityLabel="Toggle simplified language"
          accessibilityRole="switch"
        />
      </View>

      {/* Font size */}
      <View style={styles.fontSizeSection}>
        <Text style={styles.prefTitle}>🔠  Font Size</Text>
        <View style={styles.fontSizeRow}>
          {FONT_SIZE_OPTIONS.map((size) => (
            <TouchableOpacity
              key={size}
              style={[
                styles.fontSizeButton,
                fontSize === size && styles.fontSizeButtonActive,
              ]}
              onPress={() => setFontSize(size)}
              accessibilityRole="radio"
              accessibilityState={{ selected: fontSize === size }}
              accessibilityLabel={`Font size: ${size}`}
            >
              <Text
                style={[
                  styles.fontSizeLabel,
                  { fontSize: size === 'small' ? 13 : size === 'large' ? 19 : 16 },
                  fontSize === size && styles.fontSizeLabelActive,
                ]}
              >
                Aa
              </Text>
              <Text style={[styles.fontSizeName, fontSize === size && styles.fontSizeLabelActive]}>
                {size.charAt(0).toUpperCase() + size.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Save button */}
      <TouchableOpacity
        style={[styles.saveButton, saving && styles.saveButtonDisabled]}
        onPress={handleSave}
        disabled={saving}
        accessibilityRole="button"
        accessibilityLabel="Save preferences"
      >
        {saving ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.saveButtonText}>💾  Save Preferences</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 20,
    paddingBottom: 40,
    backgroundColor: '#F7F3EE',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F7F3EE',
  },
  loadingText: {
    marginTop: 12,
    color: '#6B6E8A',
    fontSize: 15,
  },
  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 18,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#E8E0D5',
    gap: 14,
  },
  avatar: {
    fontSize: 40,
  },
  username: {
    fontSize: 20,
    fontWeight: '700',
    color: '#3D405B',
  },
  email: {
    fontSize: 14,
    color: '#6B6E8A',
    marginTop: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#3D405B',
    marginBottom: 6,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#6B6E8A',
    marginBottom: 20,
    lineHeight: 20,
  },
  preferenceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#E8E0D5',
    padding: 16,
    marginBottom: 12,
  },
  prefInfo: {
    flex: 1,
    marginRight: 12,
  },
  prefTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#3D405B',
    marginBottom: 3,
  },
  prefDesc: {
    fontSize: 13,
    color: '#6B6E8A',
    lineHeight: 18,
  },
  fontSizeSection: {
    backgroundColor: '#fff',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#E8E0D5',
    padding: 16,
    marginBottom: 12,
  },
  fontSizeRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 12,
  },
  fontSizeButton: {
    flex: 1,
    alignItems: 'center',
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: '#D4CFC8',
    paddingVertical: 12,
    backgroundColor: '#F7F3EE',
  },
  fontSizeButtonActive: {
    borderColor: '#81B29A',
    backgroundColor: '#EBF5F0',
  },
  fontSizeLabel: {
    color: '#6B6E8A',
    fontWeight: '700',
  },
  fontSizeLabelActive: {
    color: '#3D405B',
  },
  fontSizeName: {
    fontSize: 12,
    color: '#6B6E8A',
    marginTop: 4,
  },
  saveButton: {
    backgroundColor: '#81B29A',
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 24,
  },
  saveButtonDisabled: {
    backgroundColor: '#BDD8CC',
  },
  saveButtonText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#fff',
  },
});

export default ProfileScreen;
