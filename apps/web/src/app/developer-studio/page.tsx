'use client';

import Link from 'next/link';
import {
  ArrowUpRightIcon,
  CodeBracketSquareIcon,
  CommandLineIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

const VSCODE_URI = 'vscode://file/home/sven/OpenDisruption';
const VSCODE_WEB_URI = 'vscode://file/home/sven/OpenDisruption/apps/web';

export default function DeveloperStudioPage() {
  return (
    <div className="min-h-[calc(100vh-80px)] px-4 py-6 sm:px-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <section className="rounded-[2rem] border border-white/10 bg-gradient-to-br from-slate-950 via-gray-900 to-slate-950 p-6">
          <span className="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-emerald-200">
            <CodeBracketSquareIcon className="h-4 w-4" />
            Developer Studio
          </span>
          <h1 className="mt-4 text-3xl font-bold text-white">Der lokale Developer-Workspace im Control Center.</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-gray-400">
            Voll eingebettetes VS Code ist aktuell nicht als lokaler Service konfiguriert. Deshalb bekommst du hier den bestmöglichen sicheren Weg: direkte VS Code-Deep-Links, repo-nahe Shortcuts und die Opencode-Workbench im selben UI-Ökosystem.
          </p>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <div className="grid gap-4 sm:grid-cols-2">
            <a href={VSCODE_URI} className="rounded-[2rem] border border-white/10 bg-gray-950/70 p-5 transition hover:border-kirobi-500/30">
              <p className="text-sm font-semibold text-white">Repo in VS Code öffnen</p>
              <p className="mt-2 text-sm text-gray-400">Öffnet den lokalen Workspace direkt im Desktop-VS-Code, falls das URI-Schema registriert ist.</p>
              <ArrowUpRightIcon className="mt-6 h-5 w-5 text-kirobi-300" />
            </a>
            <a href={VSCODE_WEB_URI} className="rounded-[2rem] border border-white/10 bg-gray-950/70 p-5 transition hover:border-kirobi-500/30">
              <p className="text-sm font-semibold text-white">Web-App Slice öffnen</p>
              <p className="mt-2 text-sm text-gray-400">Direkter Deep Link in den Frontend-Bereich für schnelle UI-Arbeit.</p>
              <ArrowUpRightIcon className="mt-6 h-5 w-5 text-kirobi-300" />
            </a>
            <Link href="/workbench?surface=open-webui" className="rounded-[2rem] border border-white/10 bg-gray-950/70 p-5 transition hover:border-kirobi-500/30">
              <p className="text-sm font-semibold text-white">Opencode / Workbench</p>
              <p className="mt-2 text-sm text-gray-400">Sicherer Einstieg in die aktuelle Workbench-Oberfläche statt unkontrollierter Nebensurfaces.</p>
              <SparklesIcon className="mt-6 h-5 w-5 text-violet-300" />
            </Link>
            <Link href="/dashboard/tasks" className="rounded-[2rem] border border-white/10 bg-gray-950/70 p-5 transition hover:border-kirobi-500/30">
              <p className="text-sm font-semibold text-white">Code-Orchestrierung</p>
              <p className="mt-2 text-sm text-gray-400">Tasks, Operator-Hinweise und Ausführungsstatus für Code-Workflows.</p>
              <CommandLineIcon className="mt-6 h-5 w-5 text-amber-300" />
            </Link>
          </div>

          <div className="space-y-4 rounded-[2rem] border border-white/10 bg-gray-950/70 p-5">
            <p className="text-sm font-semibold text-white">Warum noch kein eingebettetes VS Code?</p>
            <div className="space-y-3 text-sm leading-6 text-gray-400">
              <p>Im aktuellen Stack läuft noch kein lokaler code-server- oder VS-Code-Web-Service hinter Caddy.</p>
              <p>Statt eine halbgare Cloud- oder Fremdlösung einzubauen, bleibt der aktuelle Weg lokal, transparent und kontrollierbar.</p>
              <p>Wenn später ein echter lokaler Web-IDE-Service ergänzt wird, ist diese Seite der richtige Ankerpunkt für die Einbettung im Control Center.</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Current best path</p>
              <p className="mt-2 text-sm text-white">VS Code Deep Link + Workbench + Task-Orchestrierung</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
