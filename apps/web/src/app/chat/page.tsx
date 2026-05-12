'use client';

import { useEffect, useState, useRef, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import {
  PaperAirplaneIcon,
  PhotoIcon,
  MicrophoneIcon,
  StopIcon,
  ArrowRightOnRectangleIcon,
  PlusCircleIcon,
  SparklesIcon,
  CpuChipIcon,
  GlobeAltIcon,
  BoltIcon,
  ChatBubbleLeftRightIcon,
  UserCircleIcon,
  AdjustmentsHorizontalIcon,
} from '@heroicons/react/24/outline';
import { useClientSearchParams } from '@/lib/use-client-search-params';

interface User {
  id: string;
  username: string;
  display_name: string;
  role: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  model_used?: string | null;
  metadata?: {
    agent?: string;
    reasoning_mode?: string;
    reasoning_label?: string;
    visible_reasoning_summary?: string[];
    source_trace?: string[];
  } | null;
}

interface Conversation {
  id: string;
  title: string | null;
  zone: string;
  created_at: string;
  updated_at: string;
}

type Zone = 'PUBLIC' | 'WORKSPACE' | 'FAMILY_PRIVATE';

interface Permission {
  zone: Zone | 'SACRED' | 'QUARANTINE';
  can_read: boolean;
  can_write: boolean;
}

interface PermissionsResponse {
  user_id: string;
  username: string;
  zones: Permission[];
}

interface RuntimeOption {
  id: string;
  label: string;
  description?: string;
  active?: boolean;
}

interface ChatRuntimeOptions {
  available_models: string[];
  default_model: string;
  current_defaults: Record<string, string>;
  agent_options: RuntimeOption[];
  reasoning_modes: RuntimeOption[];
  source_modes: RuntimeOption[];
  voice?: {
    available?: boolean;
    [key: string]: unknown;
  };
}

const ZONE_LABELS: Record<Zone, string> = {
  PUBLIC: '🌍 Public',
  WORKSPACE: '💼 Workspace',
  FAMILY_PRIVATE: '👨‍👩‍👦 Family Private',
};

const ZONE_COLORS: Record<Zone, string> = {
  PUBLIC: 'bg-green-500/20 text-green-300 border-green-500/30',
  WORKSPACE: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  FAMILY_PRIVATE: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
};

const DEFAULT_RUNTIME: ChatRuntimeOptions = {
  available_models: [],
  default_model: 'llama3.1:8b',
  current_defaults: {},
  agent_options: [],
  reasoning_modes: [],
  source_modes: [],
  voice: { available: false },
};

export default function ChatPage() {
  const router = useRouter();
  const searchParams = useClientSearchParams();
  const [user, setUser] = useState<User | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [availableZones, setAvailableZones] = useState<Zone[]>(['WORKSPACE', 'FAMILY_PRIVATE', 'PUBLIC']);
  const [selectedZone, setSelectedZone] = useState<Zone>('FAMILY_PRIVATE');
  const [runtimeOptions, setRuntimeOptions] = useState<ChatRuntimeOptions>(DEFAULT_RUNTIME);
  const [selectedModel, setSelectedModel] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('kirobi');
  const [reasoningMode, setReasoningMode] = useState('normal');
  const [sourceModes, setSourceModes] = useState<string[]>(['local']);
  const [showReasoning, setShowReasoning] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [recording, setRecording] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const deeplinkHandledRef = useRef(false);
  const pendingNewConversationRef = useRef(false);
  const deeplinkZoneRef = useRef<Zone | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const axiosInstance = axios.create({
    baseURL: '/api',
    headers: {
      Authorization: `Bearer ${typeof window !== 'undefined' ? localStorage.getItem('access_token') : ''}`,
    },
  });

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/');
      return;
    }

    const zoneParam = searchParams.get('zone');
    if (zoneParam === 'PUBLIC' || zoneParam === 'WORKSPACE' || zoneParam === 'FAMILY_PRIVATE') {
      deeplinkZoneRef.current = zoneParam;
      setSelectedZone(zoneParam);
    }

    const promptParam = searchParams.get('prompt');
    if (promptParam) {
      setInput(promptParam);
    }

    pendingNewConversationRef.current = searchParams.get('new') === '1';

    loadUser();
    loadPermissions();
    loadConversations();
    loadRuntimeOptions();
  }, [router, searchParams]);

  useEffect(() => {
    if (!pendingNewConversationRef.current || deeplinkHandledRef.current) {
      return;
    }
    const preferredZone =
      deeplinkZoneRef.current && availableZones.includes(deeplinkZoneRef.current)
        ? deeplinkZoneRef.current
        : selectedZone;
    deeplinkHandledRef.current = true;
    void createNewConversation(preferredZone);
  }, [availableZones, selectedZone]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadUser = async () => {
    try {
      const response = await axiosInstance.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to load user:', error);
      router.push('/');
    }
  };

  const loadPermissions = async () => {
    try {
      const response = await axiosInstance.get<PermissionsResponse>('/auth/me/permissions');
      const writable = response.data.zones
        .filter((permission) => permission.can_write && ZONE_LABELS[permission.zone as Zone])
        .map((permission) => permission.zone as Zone);
      if (writable.length > 0) {
        setAvailableZones(writable);
        if (!writable.includes(selectedZone)) {
          setSelectedZone(writable[0]);
        }
      }
    } catch (error) {
      console.error('Failed to load permissions:', error);
    }
  };

  const loadRuntimeOptions = async () => {
    try {
      const response = await axiosInstance.get<ChatRuntimeOptions>('/chat/runtime/options');
      const next = response.data;
      setRuntimeOptions(next);
      if (!selectedModel) {
        setSelectedModel(next.default_model || '');
      }
    } catch (error) {
      console.error('Failed to load chat runtime options:', error);
    }
  };

  const loadConversations = async () => {
    try {
      const response = await axiosInstance.get('/conversations');
      setConversations(response.data);

      // Load most recent conversation
      if (response.data.length > 0 && !activeConversation && !pendingNewConversationRef.current) {
        selectConversation(response.data[0]);
      }
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const selectConversation = async (conversation: Conversation) => {
    setActiveConversation(conversation);
    setSidebarOpen(false);

    try {
      const response = await axiosInstance.get(`/conversations/${conversation.id}/messages`);
      setMessages(response.data);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const createNewConversation = async (zoneOverride?: Zone) => {
    const zone = zoneOverride ?? selectedZone;
    try {
      const response = await axiosInstance.post('/conversations', {
        title: `${ZONE_LABELS[zone]} Gespräch`,
        zone,
      });

      const newConv = response.data;
      setConversations([newConv, ...conversations]);
      setActiveConversation(newConv);
      setMessages([]);
      setSidebarOpen(false);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || !activeConversation || loading) return;

    const userMessage = input;
    setInput('');
    setLoading(true);

    // Optimistically add user message
    const tempUserMessage: Message = {
      id: 'temp-' + Date.now(),
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
      metadata: {
        agent: selectedAgent,
        reasoning_mode: reasoningMode,
      },
    };
    setMessages([...messages, tempUserMessage]);

    try {
      await axiosInstance.post(
        `/conversations/${activeConversation.id}/messages`,
        {
          content: userMessage,
          model: selectedModel || undefined,
          agent: selectedAgent,
          reasoning_mode: reasoningMode,
          source_modes: sourceModes,
          web_search: sourceModes.includes('websearch'),
          deep_research: sourceModes.includes('deep-research'),
          show_reasoning: showReasoning,
        }
      );

      // Reload messages to get the full conversation including AI response
      const messagesResponse = await axiosInstance.get(
        `/conversations/${activeConversation.id}/messages`
      );
      setMessages(messagesResponse.data);
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSourceMode = (mode: string) => {
    setSourceModes((current) => {
      if (mode === 'local') {
        return current.includes('local') ? ['local'] : ['local'];
      }

      const next = current.filter((item) => item !== 'local');
      if (next.includes(mode)) {
        return next.filter((item) => item !== mode).length > 0
          ? next.filter((item) => item !== mode)
          : ['local'];
      }

      return [...next, mode];
    });
  };

  const toggleVoiceRecording = async () => {
    if (recording && mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setRecording(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      audioChunksRef.current = [];

      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        setTranscribing(true);
        try {
          const blob = new Blob(audioChunksRef.current, { type: recorder.mimeType || 'audio/webm' });
          const formData = new FormData();
          formData.append('audio_file', blob, 'voice-message.webm');
          formData.append('language', 'de');
          const response = await fetch('/voice/stt/transcribe', {
            method: 'POST',
            body: formData,
          });
          if (!response.ok) {
            throw new Error('STT request failed');
          }
          const payload = await response.json();
          const transcript = payload.text || payload.transcription || '';
          if (transcript) {
            setInput((current) => (current ? `${current} ${transcript}` : transcript));
          }
        } catch (error) {
          console.error('Failed to transcribe voice input:', error);
          alert('Spracheingabe konnte nicht transkribiert werden.');
        } finally {
          mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
          mediaStreamRef.current = null;
          audioChunksRef.current = [];
          setTranscribing(false);
          setRecording(false);
        }
      };

      recorder.start();
      setRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('Mikrofonzugriff wurde nicht erlaubt oder ist nicht verfügbar.');
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const uploadZone = activeConversation?.zone ?? selectedZone;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('zone', uploadZone);
    if (uploadZone === 'FAMILY_PRIVATE') {
      const approvalNote = window.prompt(
        'FAMILY_PRIVATE-Upload bleibt lokal. Bitte kurze Freigabe-Notiz eingeben:',
        'Bewusst lokal für FAMILY_PRIVATE-Suche freigegeben'
      );
      if (!approvalNote?.trim()) {
        setUploading(false);
        return;
      }
      formData.append('human_approved', 'true');
      formData.append('approval_note', approvalNote.trim());
    }

    try {
      await axiosInstance.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Add a message about the uploaded file
      if (activeConversation) {
        setInput(`[Datei hochgeladen: ${file.name}]\n\n`);
      }
    } catch (error) {
      console.error('Failed to upload file:', error);
      alert('Datei-Upload fehlgeschlagen');
    } finally {
      setUploading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.push('/');
  };

  useEffect(() => {
    return () => {
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const sourceModeLabel = useMemo(() => {
    if (sourceModes.includes('deep-research')) return 'Deep Research intent';
    if (sourceModes.includes('websearch')) return 'Websearch intent';
    return 'Local RAG';
  }, [sourceModes]);

  const activeThinkingLabel = useMemo(() => {
    const mode = runtimeOptions.reasoning_modes.find((item) => item.id === reasoningMode);
    return mode?.label ?? reasoningMode;
  }, [runtimeOptions.reasoning_modes, reasoningMode]);

  const selectedAgentLabel = useMemo(() => {
    const agent = runtimeOptions.agent_options.find((item) => item.id === selectedAgent);
    return agent?.label ?? selectedAgent;
  }, [runtimeOptions.agent_options, selectedAgent]);

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-white">Laden...</div>
      </div>
    );
  }

  return (
    <div className="flex h-full bg-gray-900 text-white">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0 fixed md:static inset-y-0 left-0 z-50 w-64 bg-gray-800 border-r border-gray-700 transition-transform duration-300 ease-in-out`}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center space-x-3 mb-4">
              <UserCircleIcon className="w-10 h-10 text-kirobi-500" />
              <div>
                <p className="font-semibold">{user.display_name}</p>
                <p className="text-xs text-gray-400">@{user.username}</p>
              </div>
            </div>

            <button
              onClick={() => void createNewConversation()}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-kirobi-600 hover:bg-kirobi-700 rounded-lg transition-colors"
            >
              <PlusCircleIcon className="w-5 h-5" />
              <span>Neues Gespräch</span>
            </button>
            <div className="mt-3 space-y-2">
              <p className="text-xs uppercase tracking-wide text-gray-500">MVP-Zone</p>
              <div className="flex flex-wrap gap-2">
                {availableZones.map((zone) => (
                  <button
                    key={zone}
                    type="button"
                    onClick={() => setSelectedZone(zone)}
                    className={`rounded-lg border px-2 py-1 text-xs ${
                      selectedZone === zone
                        ? ZONE_COLORS[zone]
                        : 'border-gray-600 bg-gray-700 text-gray-300'
                    }`}
                  >
                    {ZONE_LABELS[zone]}
                  </button>
                ))}
              </div>
              <p className="text-xs text-gray-500">
                SACRED und QUARANTINE sind im MVP absichtlich ausgeschlossen.
              </p>
              {searchParams.get('prompt') && (
                <p className="text-xs text-kirobi-300">
                  Deeplink aktiv: Prompt wurde aus Telegram vorausgefüllt.
                </p>
              )}
            </div>
          </div>

          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto p-2">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => selectConversation(conv)}
                className={`w-full text-left px-3 py-2 rounded-lg mb-1 transition-colors ${
                  activeConversation?.id === conv.id
                    ? 'bg-kirobi-600'
                    : 'hover:bg-gray-700'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <ChatBubbleLeftRightIcon className="w-4 h-4 flex-shrink-0" />
                  <span className="truncate text-sm">
                    {conv.title || 'Neues Gespräch'}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(conv.updated_at).toLocaleDateString('de-DE')} · {conv.zone}
                </p>
              </button>
            ))}
          </div>

          {/* Logout Button */}
          <div className="p-4 border-t border-gray-700">
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
            >
              <ArrowRightOnRectangleIcon className="w-5 h-5" />
              <span>Abmelden</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Mobile Header */}
        <div className="md:hidden bg-gray-800 border-b border-gray-700 p-3 flex items-center justify-between">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-gray-400 hover:text-white p-1"
          >
            <ChatBubbleLeftRightIcon className="w-6 h-6" />
          </button>
          <span className="font-medium text-sm truncate max-w-[140px] text-gray-200">
            {selectedModel || runtimeOptions.default_model}
          </span>
          {/* mobile settings toggle is now the universal one in the header row */}
          <span className="w-8" />
        </div>

        {activeConversation && (
          <div className="relative border-b border-gray-700 bg-gray-800/60 px-4 py-2 text-sm">
            {/* Status badges row — always visible, small */}
            <div className="flex flex-wrap items-center gap-1.5 min-h-[2rem]">
              <span className={`rounded-full border px-2 py-0.5 text-xs ${ZONE_COLORS[activeConversation.zone as Zone] ?? 'border-gray-600 bg-gray-700 text-gray-300'}`}>
                {ZONE_LABELS[activeConversation.zone as Zone] ?? activeConversation.zone}
              </span>
              <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2 py-0.5 text-xs text-cyan-200">
                {selectedAgentLabel}
              </span>
              <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-xs text-amber-200 max-w-[120px] truncate">
                {selectedModel || runtimeOptions.default_model}
              </span>
              <span className="rounded-full border border-fuchsia-500/30 bg-fuchsia-500/10 px-2 py-0.5 text-xs text-fuchsia-200 hidden sm:inline">
                {activeThinkingLabel}
              </span>
              {/* Settings toggle — visible on all screen sizes */}
              <button
                onClick={() => setSettingsOpen(!settingsOpen)}
                className={`ml-auto flex items-center gap-1 rounded-lg border px-2 py-1 text-xs transition-colors ${
                  settingsOpen
                    ? 'border-kirobi-500/60 bg-kirobi-500/15 text-kirobi-300'
                    : 'border-gray-700 text-gray-400 hover:border-gray-500 hover:text-white'
                }`}
                title="Einstellungen"
              >
                <AdjustmentsHorizontalIcon className="h-4 w-4" />
                <span className="hidden sm:inline">Einstellungen</span>
              </button>
            </div>

            {/* Settings overlay — appears OVER messages, not pushing them down */}
            {settingsOpen && (
              <div className="absolute left-0 right-0 top-full z-30 border-b border-gray-700 bg-gray-900/97 px-4 py-4 shadow-2xl backdrop-blur-md">
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <label className="space-y-1">
                <span className="flex items-center gap-2 text-xs uppercase tracking-wide text-gray-500">
                  <SparklesIcon className="h-4 w-4" />
                  Agent
                </span>
                <select
                  value={selectedAgent}
                  onChange={(e) => setSelectedAgent(e.target.value)}
                  className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white focus:border-kirobi-500 focus:outline-none"
                >
                  {runtimeOptions.agent_options.map((agent) => (
                    <option key={agent.id} value={agent.id}>
                      {agent.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="space-y-1">
                <span className="flex items-center gap-2 text-xs uppercase tracking-wide text-gray-500">
                  <CpuChipIcon className="h-4 w-4" />
                  Modell
                </span>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white focus:border-kirobi-500 focus:outline-none"
                >
                  {(runtimeOptions.available_models.length > 0
                    ? runtimeOptions.available_models
                    : [runtimeOptions.default_model]
                  ).map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
              </label>
              <div className="space-y-1 lg:col-span-2">
                <span className="flex items-center gap-2 text-xs uppercase tracking-wide text-gray-500">
                  <BoltIcon className="h-4 w-4" />
                  Denkgrad
                </span>
                <div className="flex flex-wrap gap-2">
                  {runtimeOptions.reasoning_modes.map((mode) => (
                    <button
                      key={mode.id}
                      type="button"
                      onClick={() => setReasoningMode(mode.id)}
                      className={`rounded-lg border px-3 py-2 text-xs transition-colors ${
                        reasoningMode === mode.id
                          ? 'border-fuchsia-500 bg-fuchsia-500/15 text-fuchsia-100'
                          : 'border-gray-700 bg-gray-900 text-gray-300 hover:border-gray-500'
                      }`}
                    >
                      {mode.label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="space-y-1 lg:col-span-3">
                <span className="flex items-center gap-2 text-xs uppercase tracking-wide text-gray-500">
                  <GlobeAltIcon className="h-4 w-4" />
                  Quellen & Modi
                </span>
                <div className="flex flex-wrap gap-2">
                  {runtimeOptions.source_modes.map((mode) => (
                    <button
                      key={mode.id}
                      type="button"
                      onClick={() => toggleSourceMode(mode.id)}
                      className={`rounded-lg border px-3 py-2 text-xs transition-colors ${
                        sourceModes.includes(mode.id)
                          ? 'border-emerald-500 bg-emerald-500/15 text-emerald-100'
                          : 'border-gray-700 bg-gray-900 text-gray-300 hover:border-gray-500'
                      }`}
                    >
                      {mode.label}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-gray-500">
                  Local RAG läuft heute produktiv. Websearch und Deep Research sind als Runtime-Intent sichtbar und werden in der Antwortspur markiert.
                </p>
              </div>
              <label className="flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-300">
                <input
                  type="checkbox"
                  checked={showReasoning}
                  onChange={(e) => setShowReasoning(e.target.checked)}
                  className="rounded border-gray-600 bg-gray-800 text-kirobi-500 focus:ring-kirobi-500"
                />
                Sichtbare Reasoning-Spur anzeigen
              </label>
            </div>
                <p className="mt-3 text-xs text-gray-500">
                  Antworten nutzen nur freigegebenen Kontext aus dieser Zone. Versteckte Chain-of-Thought wird nicht angezeigt.
                </p>
                {/* Click outside to close */}
                <button
                  onClick={() => setSettingsOpen(false)}
                  className="mt-3 w-full rounded-lg border border-gray-700 py-1.5 text-xs text-gray-400 hover:text-white hover:border-gray-500 transition-colors"
                >
                  ✕ Schließen
                </button>
              </div>
            )}
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {!activeConversation ? (
            <div className="h-full flex items-center justify-center text-gray-400">
              <div className="text-center">
                <ChatBubbleLeftRightIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Wähle ein Gespräch oder starte ein neues</p>
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="h-full flex items-center justify-center text-gray-400">
              <div className="text-center">
                <p className="text-lg mb-2">Hallo {user.display_name}! 👋</p>
                <p>Wie kann ich dir heute helfen?</p>
                <p className="mt-2 text-xs text-gray-500">
                  Dieses Gespräch läuft in {ZONE_LABELS[activeConversation.zone as Zone] ?? activeConversation.zone}.
                </p>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] md:max-w-[70%] p-4 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-kirobi-600'
                      : 'bg-gray-700'
                  }`}
                >
                   <ReactMarkdown className="prose prose-invert prose-sm max-w-none">
                     {message.content}
                   </ReactMarkdown>
                   {message.role === 'assistant' && (message.model_used || message.metadata?.visible_reasoning_summary?.length) && (
                     <div className="mt-3 space-y-2 rounded-lg border border-gray-600/60 bg-gray-800/70 p-3">
                       <div className="flex flex-wrap gap-2 text-xs">
                         {message.model_used && (
                           <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-amber-200">
                             Modell: {message.model_used}
                           </span>
                         )}
                         {message.metadata?.agent && (
                           <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2 py-0.5 text-cyan-200">
                             Agent: {message.metadata.agent}
                           </span>
                         )}
                         {message.metadata?.reasoning_label && (
                           <span className="rounded-full border border-fuchsia-500/30 bg-fuchsia-500/10 px-2 py-0.5 text-fuchsia-200">
                             Denken: {message.metadata.reasoning_label}
                           </span>
                         )}
                       </div>
                       {showReasoning && message.metadata?.visible_reasoning_summary?.length ? (
                         <div>
                           <p className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-400">Runtime-Spur</p>
                           <ul className="space-y-1 text-xs text-gray-300">
                             {message.metadata.visible_reasoning_summary.map((item) => (
                               <li key={item}>• {item}</li>
                             ))}
                           </ul>
                         </div>
                       ) : null}
                       {message.metadata?.source_trace?.length ? (
                         <p className="text-xs text-gray-500">
                           Quellenpfad: {message.metadata.source_trace.join(' -> ')}
                         </p>
                       ) : null}
                     </div>
                   )}
                   <p className="text-xs text-gray-400 mt-2">
                     {new Date(message.created_at).toLocaleTimeString('de-DE', {
                       hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-700 p-4 rounded-lg space-y-3">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <div className="space-y-1 text-xs text-gray-300">
                  <p>
                    {selectedAgentLabel} denkt mit <span className="text-fuchsia-300">{activeThinkingLabel}</span> über{' '}
                    <span className="text-amber-300">{selectedModel || runtimeOptions.default_model}</span> nach.
                  </p>
                  <p className="text-gray-500">
                    Quellenmodus: {sourceModeLabel}
                  </p>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        {activeConversation && (
          <div className="border-t border-gray-700 p-4">
            <form onSubmit={sendMessage} className="flex items-end space-x-2">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept="application/pdf,.txt,.md,text/plain,text/markdown"
                className="hidden"
              />

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="flex-shrink-0 p-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50"
              >
                <PhotoIcon className="w-5 h-5" />
              </button>

              <button
                type="button"
                onClick={() => void toggleVoiceRecording()}
                disabled={transcribing || !runtimeOptions.voice?.available}
                className={`flex-shrink-0 rounded-lg p-3 transition-colors disabled:opacity-50 ${
                  recording
                    ? 'bg-red-600 hover:bg-red-700'
                    : 'bg-gray-700 hover:bg-gray-600'
                }`}
                title={runtimeOptions.voice?.available ? 'Spracheingabe' : 'Voice-Service nicht verfügbar'}
              >
                {recording ? <StopIcon className="w-5 h-5" /> : <MicrophoneIcon className="w-5 h-5" />}
              </button>

              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage(e);
                  }
                }}
                placeholder={transcribing ? 'Sprache wird transkribiert...' : 'Schreibe eine Nachricht...'}
                className="flex-1 bg-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-kirobi-500 resize-none"
                rows={1}
                disabled={loading || transcribing}
              />

              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="flex-shrink-0 p-3 bg-kirobi-600 hover:bg-kirobi-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <PaperAirplaneIcon className="w-5 h-5" />
              </button>
            </form>

            <p className="text-xs text-gray-500 mt-2 text-center">
              🔒 Deine Daten bleiben privat und lokal · Zone {ZONE_LABELS[activeConversation.zone as Zone] ?? activeConversation.zone} · Modell {selectedModel || runtimeOptions.default_model} · Agent {selectedAgentLabel}
            </p>
          </div>
        )}
      </div>

      {/* Sidebar Overlay (Mobile) */}
      {sidebarOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
