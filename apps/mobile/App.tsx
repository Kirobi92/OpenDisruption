/**
 * Kirobi Family — Mobile App
 * React Native / Expo 51
 *
 * Einstiegspunkt mit Tab-Navigation: Chat, Status, Familie
 * API-URL via EXPO_PUBLIC_API_URL (default: http://kirobi.local/api)
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  SafeAreaView,
  TouchableOpacity,
  ScrollView,
  StatusBar,
} from 'react-native';

// API-Konfiguration
const API_URL =
  process.env.EXPO_PUBLIC_API_URL ?? 'http://kirobi.local/api';

// ─── Farb-Palette ────────────────────────────────────────────────────────────
const colors = {
  bg: '#0f0f1a',
  surface: '#1a1a2e',
  primary: '#6c63ff',
  accent: '#ff6584',
  text: '#e8e8f0',
  muted: '#8888aa',
  success: '#4ade80',
  border: '#2a2a3e',
};

// ─── Typen ───────────────────────────────────────────────────────────────────
type Tab = 'chat' | 'status' | 'familie';

interface ApiStatus {
  status: 'ok' | 'error' | 'loading';
  message: string;
}

// ─── Splash Screen ───────────────────────────────────────────────────────────
function SplashScreen({ onReady }: { onReady: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onReady, 2000);
    return () => clearTimeout(timer);
  }, [onReady]);

  return (
    <View style={styles.splash}>
      <Text style={styles.splashLogo}>🤖</Text>
      <Text style={styles.splashTitle}>Kirobi</Text>
      <Text style={styles.splashSubtitle}>Dein Familien-Assistent</Text>
      <ActivityIndicator
        color={colors.primary}
        size="small"
        style={{ marginTop: 32 }}
      />
    </View>
  );
}

// ─── Chat Tab ────────────────────────────────────────────────────────────────
function ChatTab() {
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([
    { role: 'assistant', text: 'Hallo! Wie kann ich dir helfen?' },
  ]);
  const [input, setInput] = useState('');

  return (
    <SafeAreaView style={styles.tab}>
      <Text style={styles.tabTitle}>💬 Chat</Text>
      <ScrollView style={styles.messageList}>
        {messages.map((msg, i) => (
          <View
            key={i}
            style={[
              styles.messageBubble,
              msg.role === 'user' ? styles.userBubble : styles.assistantBubble,
            ]}
          >
            <Text style={styles.messageText}>{msg.text}</Text>
          </View>
        ))}
      </ScrollView>
      <View style={styles.inputRow}>
        <Text style={styles.inputPlaceholder}>
          Chat-Eingabe — kommt bald ✨
        </Text>
      </View>
    </SafeAreaView>
  );
}

// ─── Status Tab ──────────────────────────────────────────────────────────────
function StatusTab() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>({
    status: 'loading',
    message: 'Verbinde...',
  });

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch(`${API_URL}/health`, {
          signal: AbortSignal.timeout(5000),
        });
        if (res.ok) {
          setApiStatus({ status: 'ok', message: 'Kirobi Stack erreichbar ✓' });
        } else {
          setApiStatus({
            status: 'error',
            message: `HTTP ${res.status}`,
          });
        }
      } catch {
        setApiStatus({
          status: 'error',
          message: 'Stack nicht erreichbar',
        });
      }
    };
    check();
  }, []);

  const statusColor =
    apiStatus.status === 'ok'
      ? colors.success
      : apiStatus.status === 'error'
        ? colors.accent
        : colors.muted;

  return (
    <SafeAreaView style={styles.tab}>
      <Text style={styles.tabTitle}>📡 Status</Text>
      <View style={styles.card}>
        <Text style={styles.cardLabel}>API-Endpunkt</Text>
        <Text style={styles.cardValue}>{API_URL}</Text>
      </View>
      <View style={styles.card}>
        <Text style={styles.cardLabel}>Verbindung</Text>
        <Text style={[styles.cardValue, { color: statusColor }]}>
          {apiStatus.status === 'loading' && (
            <ActivityIndicator size="small" color={colors.muted} />
          )}
          {apiStatus.message}
        </Text>
      </View>
      <View style={styles.card}>
        <Text style={styles.cardLabel}>App-Version</Text>
        <Text style={styles.cardValue}>1.0.0 (Expo 51)</Text>
      </View>
    </SafeAreaView>
  );
}

// ─── Familie Tab ─────────────────────────────────────────────────────────────
function FamilieTab() {
  const members = [
    { name: 'Sven', emoji: '👨', role: 'Admin' },
    { name: 'Familie', emoji: '👨‍👩‍👦', role: 'Mitglieder' },
  ];

  return (
    <SafeAreaView style={styles.tab}>
      <Text style={styles.tabTitle}>👨‍👩‍👦 Familie</Text>
      {members.map((m) => (
        <View key={m.name} style={styles.card}>
          <Text style={styles.memberEmoji}>{m.emoji}</Text>
          <View>
            <Text style={styles.cardValue}>{m.name}</Text>
            <Text style={styles.cardLabel}>{m.role}</Text>
          </View>
        </View>
      ))}
      <Text style={styles.hint}>
        Familienprofil-Verwaltung kommt in einer späteren Version.
      </Text>
    </SafeAreaView>
  );
}

// ─── Tab-Bar ─────────────────────────────────────────────────────────────────
const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: 'chat', label: 'Chat', icon: '💬' },
  { key: 'status', label: 'Status', icon: '📡' },
  { key: 'familie', label: 'Familie', icon: '👨‍👩‍👦' },
];

// ─── Root App ────────────────────────────────────────────────────────────────
export default function App() {
  const [ready, setReady] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('chat');

  if (!ready) {
    return <SplashScreen onReady={() => setReady(true)} />;
  }

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor={colors.bg} />

      {/* Tab-Inhalt */}
      <View style={styles.content}>
        {activeTab === 'chat' && <ChatTab />}
        {activeTab === 'status' && <StatusTab />}
        {activeTab === 'familie' && <FamilieTab />}
      </View>

      {/* Tab-Bar */}
      <View style={styles.tabBar}>
        {TABS.map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={styles.tabBarItem}
            onPress={() => setActiveTab(tab.key)}
            accessibilityRole="button"
            accessibilityLabel={tab.label}
          >
            <Text style={styles.tabBarIcon}>{tab.icon}</Text>
            <Text
              style={[
                styles.tabBarLabel,
                activeTab === tab.key && styles.tabBarLabelActive,
              ]}
            >
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

// ─── Styles ──────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  content: {
    flex: 1,
  },
  // Splash
  splash: {
    flex: 1,
    backgroundColor: colors.bg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  splashLogo: {
    fontSize: 72,
    marginBottom: 16,
  },
  splashTitle: {
    fontSize: 40,
    fontWeight: '700',
    color: colors.text,
    letterSpacing: 2,
  },
  splashSubtitle: {
    fontSize: 16,
    color: colors.muted,
    marginTop: 8,
  },
  // Tabs
  tab: {
    flex: 1,
    backgroundColor: colors.bg,
    padding: 16,
  },
  tabTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.text,
    marginBottom: 20,
    marginTop: 8,
  },
  // Chat
  messageList: {
    flex: 1,
  },
  messageBubble: {
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    maxWidth: '80%',
  },
  userBubble: {
    backgroundColor: colors.primary,
    alignSelf: 'flex-end',
  },
  assistantBubble: {
    backgroundColor: colors.surface,
    alignSelf: 'flex-start',
  },
  messageText: {
    color: colors.text,
    fontSize: 15,
  },
  inputRow: {
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingVertical: 12,
    alignItems: 'center',
  },
  inputPlaceholder: {
    color: colors.muted,
    fontSize: 14,
  },
  // Cards
  card: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  cardLabel: {
    color: colors.muted,
    fontSize: 12,
    marginBottom: 2,
  },
  cardValue: {
    color: colors.text,
    fontSize: 15,
    fontWeight: '500',
  },
  memberEmoji: {
    fontSize: 32,
  },
  hint: {
    color: colors.muted,
    fontSize: 13,
    textAlign: 'center',
    marginTop: 16,
  },
  // Tab-Bar
  tabBar: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingBottom: 8,
    paddingTop: 8,
  },
  tabBarItem: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 4,
  },
  tabBarIcon: {
    fontSize: 22,
  },
  tabBarLabel: {
    fontSize: 11,
    color: colors.muted,
    marginTop: 2,
  },
  tabBarLabelActive: {
    color: colors.primary,
    fontWeight: '600',
  },
});
