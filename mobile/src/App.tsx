/**
 * DiverseFocus-IA Mobile App
 * Root navigation setup using React Navigation.
 */

import React from 'react';
import { StatusBar, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import HomeScreen from './screens/HomeScreen';
import SimplifyScreen from './screens/SimplifyScreen';
import TranscribeScreen from './screens/TranscribeScreen';
import ProfileScreen from './screens/ProfileScreen';

export type RootStackParamList = {
  Home: undefined;
  Simplify: undefined;
  Transcribe: undefined;
  Profile: undefined;
};

const Stack = createStackNavigator<RootStackParamList>();

const App: React.FC = () => {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <StatusBar barStyle="dark-content" backgroundColor="#F7F3EE" />
        <Stack.Navigator
          initialRouteName="Home"
          screenOptions={{
            headerStyle: styles.header,
            headerTitleStyle: styles.headerTitle,
            headerTintColor: '#3D405B',
            cardStyle: styles.card,
          }}
        >
          <Stack.Screen
            name="Home"
            component={HomeScreen}
            options={{ title: 'DiverseFocus IA' }}
          />
          <Stack.Screen
            name="Simplify"
            component={SimplifyScreen}
            options={{ title: 'Simplify Text' }}
          />
          <Stack.Screen
            name="Transcribe"
            component={TranscribeScreen}
            options={{ title: 'Transcribe Audio' }}
          />
          <Stack.Screen
            name="Profile"
            component={ProfileScreen}
            options={{ title: 'My Profile' }}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
};

const styles = StyleSheet.create({
  header: {
    backgroundColor: '#F7F3EE',
    elevation: 0,
    shadowOpacity: 0,
    borderBottomWidth: 1,
    borderBottomColor: '#E8E0D5',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#3D405B',
  },
  card: {
    backgroundColor: '#F7F3EE',
  },
});

export default App;
