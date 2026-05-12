'use client';

import { formatDistanceToNow } from 'date-fns';
import { de } from 'date-fns/locale';
import { motion } from 'framer-motion';
import {
  Menu,
  Mic,
  Paperclip,
  Plus,
  Search,
  SendHorizontal,
  X,
} from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useMemo, useRef, useState } from 'react';

import { AgentAvatar } from '@/components/chat/AgentAvatar';
import { ChatBubble } from '@/components/chat/ChatBubble';
import { BottomNav } from '@/components/layout/BottomNav';
import { Header } from '@/components/layout/Header';
import { useRequireAuth } from '@/lib/auth';
import {
  createConversation,
  sendMessage,
  uploadFile,
  useConversations,
  useMessages,
  type AttachmentReference,
  type Message,
} from '@/lib/api';

function ChatPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isLoading, isAuthenticated } = useRequireAuth();
  const { data: conversations = [], mutate: mutateConversations } = useConversations();
  const activeConversationId = searchParams.get('conversation') ?? conversations[0]?.id ?? null;
  const { data: messages = [], mutate: mutateMessages } = useMessages(activeConversationId);

  const [search, setSearch] = useState('');
  const [composer, setComposer] = useState('');
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [pendingAttachments, setPendingAttachments] = useState<AttachmentReference[]>([]);
  const [isSending, setIsSending] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!activeConversationId && conversations.length > 0) {
      router.replace(`/chat?conversation=${conversations[0].id}`);
    }
  }, [activeConversationId, conversations, router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const filteredConversations = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) {
      return conversations;
    }
    return conversations.filter((conversation) => conversation.title.toLowerCase().includes(term));
  }, [conversations, search]);

  const handleCreateConversation = async () => {
    const conversation = await createConversation(`Neuer Chat · ${new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}`, 'WORKSPACE');
    await mutateConversations((current = []) => [conversation, ...current], false);
    router.push(`/chat?conversation=${conversation.id}`);
    setMobileSidebarOpen(false);
    return conversation;
  };

  const handleAttachFile = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) {
      return;
    }

    const uploaded = await uploadFile(selectedFile, 'WORKSPACE');
    const attachment: AttachmentReference = {
      id: String(uploaded.id ?? uploaded.fileId ?? selectedFile.name),
      name: String(uploaded.name ?? selectedFile.name),
      url: uploaded.url ? String(uploaded.url) : undefined,
      path: uploaded.path ? String(uploaded.path) : undefined,
      zone: 'WORKSPACE',
    };

    setPendingAttachments((current) => [...current, attachment]);
    setComposer((current) => `${current}${current ? '\n' : ''}[Anhang: ${attachment.name}]`);
    event.target.value = '';
  };

  const handleSend = async () => {
    const content = composer.trim();

    if (!content && pendingAttachments.length === 0) {
      return;
    }

    setIsSending(true);

    try {
      const targetConversation = activeConversationId
        ? { id: activeConversationId }
        : await handleCreateConversation();

      const optimisticMessage: Message = {
        id: `optimistic-${Date.now()}`,
        role: 'user',
        content,
        createdAt: new Date().toISOString(),
        attachments: pendingAttachments,
      };

      setComposer('');
      setPendingAttachments([]);

      if (targetConversation.id === activeConversationId) {
        await mutateMessages((current = []) => [...current, optimisticMessage], false);
      }

      const result = await sendMessage(targetConversation.id, content, pendingAttachments);

      if (targetConversation.id === activeConversationId) {
        await mutateMessages(
          (current = []) => {
            const withoutOptimistic = current.filter((message) => message.id !== optimisticMessage.id);
            return [
              ...withoutOptimistic,
              result.userMessage,
              ...(result.assistantMessage ? [result.assistantMessage] : []),
            ];
          },
          false,
        );
      } else {
        router.replace(`/chat?conversation=${targetConversation.id}`);
      }

      await mutateConversations();
    } finally {
      setIsSending(false);
    }
  };

  if (isLoading || !isAuthenticated) {
    return <div className="min-h-screen bg-void" />;
  }

  return (
    <div className="min-h-screen pb-24 md:pb-0">
      <Header title="Chat" />
      <main className="flex min-h-screen pt-14">
        <aside
          className={`fixed inset-y-14 left-0 z-30 w-[88vw] max-w-sm border-r border-white/10 bg-void-deep/95 p-4 backdrop-blur-xl transition md:static md:w-80 md:translate-x-0 ${
            mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <div className="mb-4 flex items-center justify-between md:hidden">
            <h2 className="text-lg font-semibold">Gespräche</h2>
            <button type="button" onClick={() => setMobileSidebarOpen(false)} className="rounded-full border border-white/10 p-2">
              <X className="h-4 w-4" />
            </button>
          </div>
          <button
            type="button"
            onClick={() => void handleCreateConversation()}
            className="mb-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-kirobi-400 to-aurora-violet px-4 py-3 font-semibold text-void shadow-glow-cyan"
          >
            <Plus className="h-4 w-4" />
            Neuer Chat
          </button>
          <div className="relative mb-4">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-white/35" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Gespräche suchen"
              className="h-11 w-full rounded-2xl border border-white/10 bg-white/5 pl-11 pr-4 text-sm outline-none focus:border-aurora-cyan/40"
            />
          </div>
          <div className="space-y-3 overflow-y-auto pb-10">
            {filteredConversations.map((conversation) => {
              const active = conversation.id === activeConversationId;

              return (
                <button
                  key={conversation.id}
                  type="button"
                  onClick={() => {
                    router.push(`/chat?conversation=${conversation.id}`);
                    setMobileSidebarOpen(false);
                  }}
                  className={`w-full rounded-3xl border p-4 text-left transition ${
                    active
                      ? 'border-aurora-cyan/35 bg-white/10 shadow-glow-cyan'
                      : 'border-white/10 bg-white/5 hover:bg-white/10'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <AgentAvatar name={conversation.agent} size="sm" />
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-medium text-white">{conversation.title}</div>
                      <div className="mt-1 text-xs text-white/45">
                        {formatDistanceToNow(new Date(conversation.updatedAt), { addSuffix: true, locale: de })}
                      </div>
                    </div>
                    <span className="rounded-full border border-white/10 px-2 py-1 text-[10px] uppercase tracking-[0.2em] text-white/45">
                      {conversation.agent}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col bg-void px-4 pb-20 pt-4 md:px-6">
          <div className="mb-4 flex items-center justify-between gap-3 md:hidden">
            <button
              type="button"
              onClick={() => setMobileSidebarOpen(true)}
              className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/5"
            >
              <Menu className="h-5 w-5" />
            </button>
            <button
              type="button"
              onClick={() => router.push(activeConversationId ? `/voice?conversation=${activeConversationId}` : '/voice')}
              className="inline-flex h-11 items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 text-sm text-white/75"
            >
              <Mic className="h-4 w-4" />
              Voice
            </button>
          </div>

          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} className="flex-1 overflow-y-auto">
            <div className="mx-auto flex max-w-4xl flex-col gap-5 py-6">
              {messages.length > 0 ? (
                messages.map((message) => (
                  <ChatBubble
                    key={message.id}
                    role={message.role === 'user' ? 'user' : 'assistant'}
                    content={message.content}
                    timestamp={new Date(message.createdAt)}
                    agentName={message.agentName ?? 'kirobi'}
                    modelUsed={message.modelUsed}
                  />
                ))
              ) : (
                <div className="rounded-[2rem] border border-dashed border-white/10 bg-white/5 p-8 text-center text-white/55">
                  Starte eine Unterhaltung. Kirobi wartet bereits auf deinen ersten Gedanken.
                </div>
              )}

              {isSending ? (
                <div className="flex items-center gap-3 rounded-3xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/60">
                  <AgentAvatar name="kirobi" size="sm" />
                  <div className="flex items-center gap-1">
                    <span className="h-2 w-2 rounded-full bg-aurora-cyan animate-bounce" />
                    <span className="h-2 w-2 rounded-full bg-aurora-cyan animate-bounce [animation-delay:0.15s]" />
                    <span className="h-2 w-2 rounded-full bg-aurora-cyan animate-bounce [animation-delay:0.3s]" />
                  </div>
                  <span>Kirobi denkt gerade nach...</span>
                </div>
              ) : null}
              <div ref={messagesEndRef} />
            </div>
          </motion.div>

          <div className="sticky bottom-16 mt-4 md:bottom-4">
            <div className="mx-auto max-w-4xl rounded-[2rem] border border-white/10 bg-void-deep/90 p-4 shadow-card backdrop-blur-xl">
              {pendingAttachments.length > 0 ? (
                <div className="mb-3 flex flex-wrap gap-2">
                  {pendingAttachments.map((attachment) => (
                    <span key={attachment.id ?? attachment.name} className="rounded-full border border-aurora-cyan/20 bg-aurora-cyan/10 px-3 py-1 text-xs text-aurora-cyan">
                      {attachment.name}
                    </span>
                  ))}
                </div>
              ) : null}
              <div className="flex items-end gap-3">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-white/70 transition hover:text-white"
                >
                  <Paperclip className="h-5 w-5" />
                </button>
                <textarea
                  value={composer}
                  onChange={(event) => setComposer(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                      event.preventDefault();
                      void handleSend();
                    }
                  }}
                  placeholder="Schreib Kirobi, was dich gerade bewegt..."
                  className="min-h-[60px] flex-1 resize-none rounded-3xl border border-white/10 bg-white/5 px-4 py-4 text-sm outline-none focus:border-aurora-cyan/35"
                />
                <button
                  type="button"
                  onClick={() => router.push(activeConversationId ? `/voice?conversation=${activeConversationId}` : '/voice')}
                  className="hidden h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-white/70 transition hover:text-white md:inline-flex"
                >
                  <Mic className="h-5 w-5" />
                </button>
                <button
                  type="button"
                  onClick={() => void handleSend()}
                  disabled={isSending}
                  className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-r from-kirobi-400 to-aurora-violet text-void shadow-glow-cyan disabled:opacity-60"
                >
                  <SendHorizontal className="h-5 w-5" />
                </button>
              </div>
              <input ref={fileInputRef} type="file" className="hidden" onChange={handleAttachFile} />
            </div>
          </div>
        </div>
      </main>
      <BottomNav />
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-void" />}>
      <ChatPageContent />
    </Suspense>
  );
}
