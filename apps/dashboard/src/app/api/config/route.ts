import { promises as fs } from 'node:fs';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const execFileAsync = promisify(execFile);
const REPO_ROOT = '/home/sven/OpenDisruption';

type ConfigFileDefinition = {
  id: string;
  label: string;
  path: string;
  editable: boolean;
  description: string;
  warning?: string;
  obfuscate?: boolean;
};

const CONFIG_FILES: ConfigFileDefinition[] = [
  {
    id: 'env',
    label: '.env (maskiert)',
    path: path.join(REPO_ROOT, '.env'),
    editable: false,
    description: 'Aktive lokale Runtime-Konfiguration — sensible Werte werden maskiert dargestellt.',
    obfuscate: true,
  },
  {
    id: 'env-example',
    label: '.env.example',
    path: path.join(REPO_ROOT, '.env.example'),
    editable: false,
    description: 'Template-Referenz für Umgebungsvariablen im Repository.',
  },
  {
    id: 'docker-compose',
    label: 'docker-compose.yml',
    path: path.join(REPO_ROOT, 'docker-compose.yml'),
    editable: true,
    description: 'Compose-Definition für alle Services, Volumes und Netzwerke.',
    warning: 'Container-Neustart erforderlich nach Speichern',
  },
  {
    id: 'hermes-config',
    label: 'Hermes cli-config.yaml',
    path: path.join(REPO_ROOT, 'services/hermes-runtime/config/cli-config.yaml'),
    editable: true,
    description: 'Hermes-Runtime-CLI-Konfiguration für Modelle, Telegram und Streaming.',
  },
  {
    id: 'caddyfile',
    label: 'Caddyfile',
    path: path.join(REPO_ROOT, 'infra/caddy/Caddyfile'),
    editable: true,
    description: 'Caddy-Edge für LAN-/Tailscale-Routing und Reverse-Proxy-Regeln.',
  },
];

type ConfigFileSummary = {
  id: string;
  label: string;
  path: string;
  editable: boolean;
  description: string;
  warning?: string;
  obfuscated: boolean;
};

type ConfigFilePayload = ConfigFileSummary & {
  exists: boolean;
  content: string;
};

function listPayload(): ConfigFileSummary[] {
  return CONFIG_FILES.map((file) => ({
    id: file.id,
    label: file.label,
    path: file.path,
    editable: file.editable,
    description: file.description,
    warning: file.warning,
    obfuscated: Boolean(file.obfuscate),
  }));
}

function getFileDefinition(id: string | null): ConfigFileDefinition | undefined {
  if (!id) return undefined;
  return CONFIG_FILES.find((file) => file.id === id);
}

function looksSensitiveKey(key: string): boolean {
  return /(token|secret|password|passwd|api[_-]?key|auth|jwt|cookie|session|database_url|gh_token|copilot)/i.test(key);
}

function looksSensitiveValue(value: string): boolean {
  if (!value) return false;
  return value.length >= 24 || /^gh[pousr]_/.test(value) || /changeme/i.test(value) || /:.*@/.test(value);
}

function maskValue(value: string): string {
  if (value.length <= 8) return '********';
  return `${value.slice(0, 2)}********${value.slice(-2)}`;
}

function obfuscateEnvContent(content: string): string {
  return content
    .split(/\r?\n/)
    .map((line) => {
      if (!line || line.trimStart().startsWith('#') || !line.includes('=')) return line;
      const [rawKey, ...rest] = line.split('=');
      const key = rawKey.trim();
      const value = rest.join('=');
      if (looksSensitiveKey(key) || looksSensitiveValue(value.trim())) {
        return `${rawKey}=${maskValue(value.trim())}`;
      }
      return line;
    })
    .join('\n');
}

async function readFilePayload(file: ConfigFileDefinition): Promise<ConfigFilePayload> {
  try {
    const rawContent = await fs.readFile(file.path, 'utf8');
    return {
      id: file.id,
      label: file.label,
      path: file.path,
      editable: file.editable,
      description: file.description,
      warning: file.warning,
      obfuscated: Boolean(file.obfuscate),
      exists: true,
      content: file.obfuscate ? obfuscateEnvContent(rawContent) : rawContent,
    };
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      return {
        id: file.id,
        label: file.label,
        path: file.path,
        editable: file.editable,
        description: file.description,
        warning: file.warning,
        obfuscated: Boolean(file.obfuscate),
        exists: false,
        content: '',
      };
    }
    throw error;
  }
}

async function validateDockerCompose(): Promise<void> {
  await execFileAsync('docker', ['compose', 'config', '--quiet'], { cwd: REPO_ROOT });
}

function extractCommandError(error: unknown): string {
  if (typeof error === 'object' && error && 'stderr' in error) {
    const stderr = String((error as { stderr?: string }).stderr ?? '').trim();
    if (stderr) return stderr;
  }
  return error instanceof Error ? error.message : 'Unbekannter Fehler';
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  const fileId = request.nextUrl.searchParams.get('file');

  if (!fileId) {
    return NextResponse.json({ files: listPayload() });
  }

  const file = getFileDefinition(fileId);
  if (!file) {
    return NextResponse.json({ error: 'Datei nicht erlaubt.' }, { status: 404 });
  }

  const payload = await readFilePayload(file);
  return NextResponse.json(payload);
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  const body = (await request.json()) as { id?: string; content?: string };
  const file = getFileDefinition(body.id ?? null);

  if (!file) {
    return NextResponse.json({ error: 'Datei nicht erlaubt.' }, { status: 404 });
  }
  if (!file.editable) {
    return NextResponse.json({ error: 'Diese Datei ist nur lesbar.' }, { status: 403 });
  }
  if (typeof body.content !== 'string') {
    return NextResponse.json({ error: 'Ungültiger Dateiinhalt.' }, { status: 400 });
  }

  const original = await fs.readFile(file.path, 'utf8');

  try {
    await fs.writeFile(file.path, body.content, 'utf8');

    if (file.id === 'docker-compose') {
      try {
        await validateDockerCompose();
      } catch (error) {
        await fs.writeFile(file.path, original, 'utf8');
        return NextResponse.json(
          {
            error: 'docker-compose.yml ist nach dem Speichern ungültig. Änderung wurde zurückgesetzt.',
            details: extractCommandError(error),
          },
          { status: 400 }
        );
      }
    }

    const payload = await readFilePayload(file);
    return NextResponse.json({
      success: true,
      message: file.id === 'docker-compose' ? 'Datei gespeichert und erfolgreich validiert.' : 'Datei gespeichert.',
      file: payload,
    });
  } catch (error) {
    await fs.writeFile(file.path, original, 'utf8');
    return NextResponse.json(
      { error: 'Speichern fehlgeschlagen.', details: extractCommandError(error) },
      { status: 500 }
    );
  }
}
