import { NextRequest } from 'next/server'
import { handleServiceProxy } from '@/lib/service-proxy'

async function proxy(request: NextRequest, params: Promise<{ service: string; path?: string[] }>) {
  const { service, path } = await params
  return handleServiceProxy(request, service, path)
}

export async function GET(request: NextRequest, context: { params: Promise<{ service: string; path?: string[] }> }) {
  return proxy(request, context.params)
}

export async function POST(request: NextRequest, context: { params: Promise<{ service: string; path?: string[] }> }) {
  return proxy(request, context.params)
}

export async function PUT(request: NextRequest, context: { params: Promise<{ service: string; path?: string[] }> }) {
  return proxy(request, context.params)
}

export async function PATCH(request: NextRequest, context: { params: Promise<{ service: string; path?: string[] }> }) {
  return proxy(request, context.params)
}

export async function DELETE(request: NextRequest, context: { params: Promise<{ service: string; path?: string[] }> }) {
  return proxy(request, context.params)
}
