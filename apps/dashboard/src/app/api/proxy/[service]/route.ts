import { NextRequest } from 'next/server';
import { handleServiceProxy } from '@/lib/service-proxy';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ service: string }> }
) {
  const { service } = await params;
  return handleServiceProxy(request, service);
}
