import { NextRequest, NextResponse } from 'next/server';

// ─── Service Port Map ─────────────────────────────────────────────────────────
// All ports bind to KIROBI_BIND_HOST (default 127.0.0.1)
// Never expose credentials or SACRED data through this proxy.

const SERVICE_PORTS: Record<string, number> = {
  'auth':             8002,
  'api':              8003,
  'embeddings':       8004,
  'telegram':         8005,
  'retrieval':        8006,
  'ingest':           8007,
  'model-routing':    8009,
  'analytics':        8010,
  'image-generation': 8011,
  'media-processing': 8012,
  'music-generation': 8013,
  'video-generation': 8014,
  'ollama':           11434,
};

const BIND_HOST = process.env.KIROBI_BIND_HOST ?? '127.0.0.1';

// Only allow health-check and read-only paths through this proxy.
// Mutations must go through the main API service with proper auth.
const ALLOWED_PATH_PREFIXES = [
  '/health',
  '/api/health',
  '/api/tags',   // Ollama model list
  '/tasks',
  '/stats',
];

function isAllowedPath(path: string): boolean {
  return ALLOWED_PATH_PREFIXES.some(prefix => path.startsWith(prefix));
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ service: string; path?: string[] }> }
): Promise<NextResponse> {
  const { service, path: pathSegments } = await params;

  const port = SERVICE_PORTS[service];
  if (!port) {
    return NextResponse.json(
      { error: `Unknown service: ${service}` },
      { status: 404 }
    );
  }

  const upstreamPath = pathSegments ? `/${pathSegments.join('/')}` : '/health';

  if (!isAllowedPath(upstreamPath)) {
    return NextResponse.json(
      { error: 'Path not allowed through dashboard proxy' },
      { status: 403 }
    );
  }

  const upstreamUrl = `http://${BIND_HOST}:${port}${upstreamPath}${request.nextUrl.search}`;

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    const upstream = await fetch(upstreamUrl, {
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
        'X-Dashboard-Proxy': '1',
      },
    });

    clearTimeout(timeout);

    const contentType = upstream.headers.get('content-type') ?? '';
    if (contentType.includes('application/json')) {
      const data: unknown = await upstream.json();
      return NextResponse.json(data, { status: upstream.status });
    }

    const text = await upstream.text();
    return new NextResponse(text, {
      status: upstream.status,
      headers: { 'Content-Type': contentType || 'text/plain' },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    const isTimeout = message.includes('abort') || message.includes('timeout');
    return NextResponse.json(
      {
        error: isTimeout ? 'Service timeout' : 'Service unreachable',
        service,
        port,
      },
      { status: 503 }
    );
  }
}
