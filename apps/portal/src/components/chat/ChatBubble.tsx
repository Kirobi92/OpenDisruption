'use client';

import { format } from 'date-fns';
import { Check, Copy } from 'lucide-react';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { AgentAvatar } from '@/components/chat/AgentAvatar';

export function ChatBubble({
  role,
  content,
  timestamp,
  agentName = 'kirobi',
  modelUsed,
}: {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  agentName?: string;
  modelUsed?: string;
}) {
  const isUser = role === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1200);
  };

  return (
    <div className={`group flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-3xl gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {!isUser && <AgentAvatar name={agentName} size="sm" />}
        <div className="space-y-2">
          <div
            className={`relative rounded-3xl border px-4 py-3 shadow-card transition ${
              isUser
                ? 'border-kirobi-400/30 border-l-2 bg-void-rise text-white'
                : 'border-white/10 bg-white/5 text-white/90'
            }`}
          >
            <button
              type="button"
              onClick={handleCopy}
              className="absolute right-3 top-3 opacity-0 transition group-hover:opacity-100"
              aria-label="Nachricht kopieren"
            >
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-black/20 text-white/70">
                {copied ? <Check className="h-4 w-4 text-aurora-cyan" /> : <Copy className="h-4 w-4" />}
              </span>
            </button>

            {!isUser && (
              <div className="mb-3 flex items-center gap-2 text-xs text-white/50">
                <span className="rounded-full border border-aurora-cyan/20 bg-aurora-cyan/10 px-2 py-1 font-medium text-aurora-cyan">
                  {agentName}
                </span>
                {modelUsed ? <span>{modelUsed}</span> : null}
              </div>
            )}

            <div className="prose prose-invert max-w-none prose-p:leading-7 prose-pre:rounded-2xl prose-pre:bg-black/30 prose-strong:text-white">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
            </div>
          </div>
          <div className={`px-2 text-xs text-white/40 ${isUser ? 'text-right' : 'text-left'}`}>
            {format(timestamp, 'HH:mm')}
          </div>
        </div>
      </div>
    </div>
  );
}
