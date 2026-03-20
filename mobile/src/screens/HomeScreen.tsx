/**
 * HomeScreen — Main landing screen for DiverseFocus-IA.
 * Uses low-visual-stimulation design with soft, calming colours.
 */

import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  AccessibilityInfo,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { StackNavigationProp } from '@react-navigation/stack';
import type { RootStackParamList } from '../App';

type HomeNavProp = StackNavigationProp<RootStackParamList, 'Home'>;

interface FeatureCard {
  title: string;
  description: string;
  emoji: string;
  route: keyof RootStackParamList;
  backgroundColor: string;
  borderColor: string;
}

const FEATURE_CARDS: FeatureCard[] = [
  {
    title: 'Simplify Text',
    description: 'Turn complex writing into clear, easy-to-read language.',
    emoji: '📖',
    route: 'Simplify',
    backgroundColor: '#EAF4F4',
    borderColor: '#A8DADC',
  },
  {
    title: 'Transcribe Audio',
    description: 'Convert speech or recordings into readable text.',
    emoji: '🎙️',
    route: 'Transcribe',
    backgroundColor: '#F4EAF4',
    borderColor: '#CBA8DC',
  },
  {
    title: 'My History',
    description: 'Review your past simplifications and transcriptions.',
    emoji: '📋',
    route: 'Profile',
    backgroundColor: '#F4F4EA',
    borderColor: '#DCDAA8',
  },
];

const HomeScreen: React.FC = () => {
  const navigation = useNavigation<HomeNavProp>();

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      accessibilityRole="main"
    >
      <View style={styles.hero}>
        <Text style={styles.heroEmoji} accessibilityElementsHidden>🧠</Text>
        <Text style={styles.heroTitle}>Welcome to{'\n'}DiverseFocus IA</Text>
        <Text style={styles.heroSubtitle}>
          A calm, accessible learning space designed for you.
        </Text>
      </View>

      <Text style={styles.sectionTitle}>What would you like to do?</Text>

      {FEATURE_CARDS.map((card) => (
        <TouchableOpacity
          key={card.route}
          style={[
            styles.card,
            { backgroundColor: card.backgroundColor, borderColor: card.borderColor },
          ]}
          onPress={() => navigation.navigate(card.route)}
          accessibilityRole="button"
          accessibilityLabel={`${card.title}: ${card.description}`}
          activeOpacity={0.75}
        >
          <Text style={styles.cardEmoji}>{card.emoji}</Text>
          <View style={styles.cardContent}>
            <Text style={styles.cardTitle}>{card.title}</Text>
            <Text style={styles.cardDescription}>{card.description}</Text>
          </View>
          <Text style={styles.cardArrow} accessibilityElementsHidden>›</Text>
        </TouchableOpacity>
      ))}

      <TouchableOpacity
        style={styles.profileButton}
        onPress={() => navigation.navigate('Profile')}
        accessibilityRole="button"
        accessibilityLabel="View your profile and settings"
      >
        <Text style={styles.profileButtonText}>⚙️  My Profile & Settings</Text>
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
  hero: {
    alignItems: 'center',
    paddingVertical: 28,
    marginBottom: 8,
  },
  heroEmoji: {
    fontSize: 56,
    marginBottom: 12,
  },
  heroTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#3D405B',
    textAlign: 'center',
    lineHeight: 36,
    marginBottom: 10,
  },
  heroSubtitle: {
    fontSize: 16,
    color: '#6B6E8A',
    textAlign: 'center',
    lineHeight: 24,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#3D405B',
    marginBottom: 16,
    marginTop: 8,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 16,
    borderWidth: 1.5,
    padding: 18,
    marginBottom: 14,
  },
  cardEmoji: {
    fontSize: 32,
    marginRight: 14,
  },
  cardContent: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: '#3D405B',
    marginBottom: 4,
  },
  cardDescription: {
    fontSize: 14,
    color: '#6B6E8A',
    lineHeight: 20,
  },
  cardArrow: {
    fontSize: 24,
    color: '#A0A3C4',
    marginLeft: 8,
  },
  profileButton: {
    marginTop: 24,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#EDEAF6',
    borderWidth: 1,
    borderColor: '#C5C0E0',
    alignItems: 'center',
  },
  profileButtonText: {
    fontSize: 16,
    color: '#3D405B',
    fontWeight: '500',
  },
});

export default HomeScreen;
