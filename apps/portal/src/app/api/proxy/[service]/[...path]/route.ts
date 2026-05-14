import { NextRequest } from 'next/server';

const SERVICE_MAP: Record<string, string> = {
  auth: 'http://auth:8000',
  api: 'http://api:8000',
  retrieval: 'http://retrieval:8000',
  embeddings: 'http://embeddings:8000',
  ingest: 'http://ingest:8000',
  voice: 'http://voice-processing:8001',
  'image-generation': 'http://image-generation:8011',
  'music-generation': 'http://music-generation:8013',
  'video-generation': 'http://video-generation:8014',
  analytics: 'http://analytics:8010',
  'personal-agents': 'http://personal-agents:8017',
};

export const dynamic = 'force-dynamic';

type Params = Promise<{ service: string; path: string[] }>;

async function proxyRequest(request: NextRequest, params: { service: string; path: string[] }) {
  const targetBase = SERVICE_MAP[params.service];

  if (!targetBase) {
    return Response.json({ error: 'Unbekannter Service.' }, { status: 404 });
  }

  const incomingUrl = new URL(request.url);
  const targetUrl = `${targetBase}/${params.path.join('/')}${incomingUrl.search}`;
  const headers = new Headers(request.headers);
  headers.delete('host');
  headers.delete('connection');

  const init: RequestInit = {
    method: request.method,
    headers,
    redirect: 'manual',
  };

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    const body = await request.arrayBuffer();
    if (body.byteLength > 0) {
      init.body = body;
    }
  }

  try {
    const response = await fetch(targetUrl, init);
    const responseHeaders = new Headers(response.headers);
    responseHeaders.delete('connection');

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    return Response.json(
      {
        error: 'Proxy-Weiterleitung fehlgeschlagen.',
        detail: error instanceof Error ? error.message : 'Unbekannter Fehler',
      },
      { status: 502 },
    );
  }
}

export async function GET(request: NextRequest, { params }: { params: Params }) {
  return proxyRequest(request, await params);
}

export async function POST(request: NextRequest, { params }: { params: Params }) {
  return proxyRequest(request, await params);
}

export async function PUT(request: NextRequest, { params }: { params: Params }) {
  return proxyRequest(request, await params);
}

export async function DELETE(request: NextRequest, { params }: { params: Params }) {
  return proxyRequest(request, await params);
}
