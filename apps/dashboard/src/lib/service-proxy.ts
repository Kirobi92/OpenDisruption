import { NextRequest, NextResponse } from 'next/server';

type ServiceProxyDefinition = {
  host: string;   // Docker service name (resolved on kirobi-net)
  port: number;   // Internal container port
  defaultPath: string;
  allowedPrefixes?: string[];
  allowedExact?: string[];
};

// Uses Docker service hostnames (kirobi-net) + internal ports.
// External port mappings only apply when accessing from outside Docker.
const SERVICE_PROXY_DEFINITIONS: Record<string, ServiceProxyDefinition> = {
  auth: { host: 'auth', port: 8000, defaultPath: '/health', allowedPrefixes: ['/health', '/stats'] },
  api: { host: 'api', port: 8000, defaultPath: '/health', allowedPrefixes: ['/health', '/control', '/dashboard', '/tasks'] },
  'voice-processing': { host: 'voice-processing', port: 8001, defaultPath: '/health', allowedPrefixes: ['/health'] },
  embeddings: { host: 'embeddings', port: 8000, defaultPath: '/health', allowedPrefixes: ['/health'] },
  telegram: { host: 'telegram', port: 8005, defaultPath: '/ready', allowedPrefixes: ['/health', '/ready'] },
  'telegram-hermes': { host: 'telegram-hermes', port: 8005, defaultPath: '/health', allowedPrefixes: ['/health', '/ready'] },
  ingest: { host: 'ingest', port: 8000, defaultPath: '/health', allowedPrefixes: ['/health'] },
  retrieval: { host: 'retrieval', port: 8000, defaultPath: '/health', allowedPrefixes: ['/health'] },
  'model-routing': { host: 'model-routing', port: 8009, defaultPath: '/health', allowedPrefixes: ['/health'] },
  analytics: { host: 'analytics', port: 8010, defaultPath: '/health', allowedPrefixes: ['/health', '/stats'] },
  'image-generation': { host: 'image-generation', port: 8011, defaultPath: '/health', allowedPrefixes: ['/health'] },
  'media-processing': { host: 'media-processing', port: 8012, defaultPath: '/health', allowedPrefixes: ['/health'] },
  'music-generation': { host: 'music-generation', port: 8013, defaultPath: '/health', allowedPrefixes: ['/health'] },
  'video-generation': { host: 'video-generation', port: 8014, defaultPath: '/health', allowedPrefixes: ['/health'] },
  ollama: { host: 'ollama', port: 11434, defaultPath: '/api/tags', allowedPrefixes: ['/api/tags'] },
  'open-webui': { host: 'open-webui', port: 8080, defaultPath: '/api/v1/ping', allowedPrefixes: ['/api/v1/ping'] },
  flowise: { host: 'flowise', port: 3000, defaultPath: '/api/v1/ping', allowedPrefixes: ['/api/v1/ping'] },
  web: { host: 'web', port: 3000, defaultPath: '/', allowedExact: ['/'] },
  dashboard: { host: 'dashboard', port: 3003, defaultPath: '/', allowedExact: ['/'] },
  'voice-app': { host: 'voice', port: 3004, defaultPath: '/', allowedExact: ['/'] },
  'web-svelte': { host: 'web-svelte', port: 3007, defaultPath: '/login', allowedPrefixes: ['/login', '/graph'] },
  qdrant: { host: 'qdrant', port: 6333, defaultPath: '/healthz', allowedPrefixes: ['/healthz', '/dashboard'] },
  'hermes-runtime': { host: 'hermes-runtime', port: 9119, defaultPath: '/', allowedExact: ['/'] },
  'openclaw-gateway': { host: 'openclaw-gateway', port: 18789, defaultPath: '/healthz', allowedPrefixes: ['/healthz'] },
  opencode: { host: 'opencode', port: 4096, defaultPath: '/', allowedExact: ['/'] },
};

function isAllowedPath(definition: ServiceProxyDefinition, path: string): boolean {
  if (definition.allowedExact?.includes(path)) return true;
  return definition.allowedPrefixes?.some((prefix) => path.startsWith(prefix)) ?? false;
}

export async function handleServiceProxy(
  request: NextRequest,
  service: string,
  pathSegments?: string[]
): Promise<NextResponse> {
  const definition = SERVICE_PROXY_DEFINITIONS[service];

  if (!definition) {
    return NextResponse.json({ error: `Unknown service: ${service}` }, { status: 404 });
  }

  const upstreamPath = pathSegments && pathSegments.length > 0 ? `/${pathSegments.join('/')}` : definition.defaultPath;
  if (!isAllowedPath(definition, upstreamPath)) {
    return NextResponse.json({ error: 'Path not allowed through dashboard proxy' }, { status: 403 });
  }

  const upstreamUrl = `http://${definition.host}:${definition.port}${upstreamPath}${request.nextUrl.search}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);

  try {
    const upstream = await fetch(upstreamUrl, {
      signal: controller.signal,
      headers: {
        Accept: 'application/json, text/html, text/plain;q=0.8, */*;q=0.5',
        'X-Dashboard-Proxy': '1',
      },
    });

    const contentType = upstream.headers.get('content-type') ?? 'text/plain';
    if (contentType.includes('application/json')) {
      const data: unknown = await upstream.json();
      return NextResponse.json(data, { status: upstream.status });
    }

    const body = await upstream.text();
    return new NextResponse(body, {
      status: upstream.status,
      headers: { 'Content-Type': contentType },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    const isTimeout = message.toLowerCase().includes('abort') || message.toLowerCase().includes('timeout');
    return NextResponse.json(
      {
        error: isTimeout ? 'Service timeout' : 'Service unreachable',
        service,
        port: definition.port,
      },
      { status: 503 }
    );
  } finally {
    clearTimeout(timeout);
  }
}
