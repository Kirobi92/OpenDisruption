import { NextRequest, NextResponse } from 'next/server';

type ServiceProxyDefinition = {
  port: number;
  defaultPath: string;
  allowedPrefixes?: string[];
  allowedExact?: string[];
};

const SERVICE_PROXY_DEFINITIONS: Record<string, ServiceProxyDefinition> = {
  auth: { port: 8002, defaultPath: '/health', allowedPrefixes: ['/health', '/stats'] },
  api: { port: 8003, defaultPath: '/health', allowedPrefixes: ['/health', '/control', '/dashboard', '/tasks'] },
  'voice-processing': { port: 8001, defaultPath: '/health', allowedPrefixes: ['/health'] },
  embeddings: { port: 8004, defaultPath: '/health', allowedPrefixes: ['/health'] },
  telegram: { port: 8005, defaultPath: '/health', allowedPrefixes: ['/health'] },
  ingest: { port: 8007, defaultPath: '/health', allowedPrefixes: ['/health'] },
  retrieval: { port: 8006, defaultPath: '/health', allowedPrefixes: ['/health'] },
  'model-routing': { port: 8009, defaultPath: '/health', allowedPrefixes: ['/health'] },
  analytics: { port: 8010, defaultPath: '/health', allowedPrefixes: ['/health', '/stats'] },
  'image-generation': { port: 8011, defaultPath: '/health', allowedPrefixes: ['/health'] },
  'media-processing': { port: 8012, defaultPath: '/health', allowedPrefixes: ['/health'] },
  'music-generation': { port: 8013, defaultPath: '/health', allowedPrefixes: ['/health'] },
  'video-generation': { port: 8014, defaultPath: '/health', allowedPrefixes: ['/health'] },
  ollama: { port: 11434, defaultPath: '/api/tags', allowedPrefixes: ['/api/tags'] },
  'open-webui': { port: 3000, defaultPath: '/api/v1/ping', allowedPrefixes: ['/api/v1/ping'] },
  flowise: { port: 3001, defaultPath: '/api/v1/ping', allowedPrefixes: ['/api/v1/ping'] },
  web: { port: 3002, defaultPath: '/', allowedExact: ['/'] },
  dashboard: { port: 3003, defaultPath: '/', allowedExact: ['/'] },
  'voice-app': { port: 3004, defaultPath: '/', allowedExact: ['/'] },
  'web-svelte': { port: 3007, defaultPath: '/v2/login', allowedPrefixes: ['/v2/login'] },
  qdrant: { port: 6333, defaultPath: '/healthz', allowedPrefixes: ['/healthz', '/dashboard'] },
  'hermes-runtime': { port: 9119, defaultPath: '/', allowedExact: ['/'] },
  'openclaw-gateway': { port: 18789, defaultPath: '/healthz', allowedPrefixes: ['/healthz'] },
};

const BIND_HOST = process.env.KIROBI_BIND_HOST ?? '127.0.0.1';

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

  const upstreamUrl = `http://${BIND_HOST}:${definition.port}${upstreamPath}${request.nextUrl.search}`;
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
