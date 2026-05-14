'use client';

import axios from 'axios';
import useSWR from 'swr';

export type AttachmentReference = {
  id?: string;
  name: string;
  url?: string;
  path?: string;
  zone?: string;
};

export type Conversation = {
  id: string;
  title: string;
  zone: string;
  createdAt: string;
  updatedAt: string;
  agent: string;
  messageCount: number;
};

export type Message = {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  createdAt: string;
  agentName?: string;
  modelUsed?: string;
  attachments?: AttachmentReference[];
};

export type HealthResponse = {
  status?: string;
  service?: string;
  healthy?: boolean;
  [key: string]: unknown;
};

export type UploadResponse = {
  id?: string;
  fileId?: string;
  url?: string;
  path?: string;
  name?: string;
  [key: string]: unknown;
};

export type SendMessageResult = {
  conversationId: string;
  userMessage: Message;
  assistantMessage: Message | null;
  raw: unknown;
};

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_BASE_PATH ?? '',
  timeout: 15000,
});

apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = window.localStorage.getItem('kirobi.portal.token');

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }

  return config;
});

function unwrap<T>(payload: unknown): T {
  const candidate = payload as { data?: T };
  return (candidate?.data ?? payload) as T;
}

function normalizeConversation(item: unknown, index: number): Conversation {
  const data = (item ?? {}) as Record<string, unknown>;
  const timestamp = new Date().toISOString();

  return {
    id: String(data.id ?? data.conversation_id ?? data.uuid ?? `conversation-${index}`),
    title: String(data.title ?? data.name ?? 'Neuer Chat'),
    zone: String(data.zone ?? 'WORKSPACE'),
    createdAt: String(data.created_at ?? data.createdAt ?? timestamp),
    updatedAt: String(data.updated_at ?? data.updatedAt ?? data.created_at ?? timestamp),
    agent: String(data.agent ?? data.agent_name ?? 'kirobi'),
    messageCount: Number(data.message_count ?? data.messageCount ?? 0),
  };
}

function normalizeMessage(item: unknown, index: number): Message {
  const data = (item ?? {}) as Record<string, unknown>;
  const roleValue = String(data.role ?? data.sender ?? 'assistant');
  const attachments = Array.isArray(data.attachments)
    ? data.attachments.map((attachment) => {
        const value = (attachment ?? {}) as Record<string, unknown>;
        return {
          id: value.id ? String(value.id) : undefined,
          name: String(value.name ?? value.filename ?? 'Datei'),
          url: value.url ? String(value.url) : undefined,
          path: value.path ? String(value.path) : undefined,
          zone: value.zone ? String(value.zone) : undefined,
        } satisfies AttachmentReference;
      })
    : undefined;

  return {
    id: String(data.id ?? data.message_id ?? `message-${index}`),
    role: roleValue === 'user' || roleValue === 'system' ? roleValue : 'assistant',
    content: String(data.content ?? data.text ?? data.message ?? ''),
    createdAt: String(data.created_at ?? data.createdAt ?? new Date().toISOString()),
    agentName: data.agentName ? String(data.agentName) : data.agent_name ? String(data.agent_name) : undefined,
    modelUsed: data.modelUsed ? String(data.modelUsed) : data.model_used ? String(data.model_used) : undefined,
    attachments,
  };
}

function normalizeList<T>(payload: unknown, mapper: (item: unknown, index: number) => T): T[] {
  if (Array.isArray(payload)) {
    return payload.map(mapper);
  }

  const data = (payload ?? {}) as Record<string, unknown>;
  const candidate = data.items ?? data.results ?? data.messages ?? data.conversations ?? data.data;

  if (!Array.isArray(candidate)) {
    return [];
  }

  return candidate.map(mapper);
}

export const fetcher = async <T,>(url: string): Promise<T> => {
  const response = await apiClient.get(url);
  return unwrap<T>(response.data);
};

export function useConversations() {
  return useSWR<Conversation[]>(
    '/api/proxy/api/conversations',
    async (url) => normalizeList<Conversation>(await fetcher(url), normalizeConversation),
    { refreshInterval: 5000 },
  );
}

export function useMessages(conversationId?: string | null) {
  return useSWR<Message[]>(
    conversationId ? `/api/proxy/api/conversations/${conversationId}/messages` : null,
    async (url) => normalizeList<Message>(await fetcher(url), normalizeMessage),
    { refreshInterval: 3000 },
  );
}

export async function createConversation(title: string, zone: string) {
  const response = await apiClient.post('/api/proxy/api/conversations', { title, zone });
  return normalizeConversation(unwrap(response.data), 0);
}

export async function sendMessage(
  convId: string,
  content: string,
  attachments: AttachmentReference[] = [],
): Promise<SendMessageResult> {
  const response = await apiClient.post(`/api/proxy/api/conversations/${convId}/messages`, {
    content,
    attachments,
  });

  const data = unwrap<Record<string, unknown>>(response.data);
  const assistantCandidate =
    data.assistantMessage ?? data.assistant_message ?? data.reply ?? data.response ?? data.ai_message;

  return {
    conversationId: String(data.conversationId ?? data.conversation_id ?? convId),
    userMessage: normalizeMessage(
      data.userMessage ?? data.user_message ?? data.message ?? { role: 'user', content, attachments },
      0,
    ),
    assistantMessage: assistantCandidate
      ? normalizeMessage(
          typeof assistantCandidate === 'string'
            ? { role: 'assistant', content: assistantCandidate }
            : assistantCandidate,
          1,
        )
      : null,
    raw: data,
  };
}

export function useServiceHealth(service: string) {
  return useSWR<HealthResponse>(`/api/proxy/${service}/health`, fetcher, {
    refreshInterval: 10000,
  });
}

export async function uploadFile(file: File, zone: string): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('zone', zone);

  const response = await apiClient.post('/api/proxy/ingest/uploads/text', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return unwrap<UploadResponse>(response.data);
}
