import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

/** Liveness/readiness probe used by Caddy and `make status`. */
export async function GET() {
  return NextResponse.json({
    status: 'ok',
    service: 'kirobi-web',
    time: new Date().toISOString(),
  });
}
