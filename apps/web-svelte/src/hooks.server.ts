import type { Handle } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';
import { base } from '$app/paths';

export const handle: Handle = async ({ event, resolve }) => {
  const session = event.cookies.get('kirobi_session');
  const path = event.url.pathname;

  const publicPaths = [`${base}/login`, `${base}/login/`];
  const isPublic = publicPaths.some((p) => path === p || path.startsWith(p));

  if (path.includes('/_app/') || path.startsWith('/v2/_app/') || path === `${base}/favicon.png`) {
    return resolve(event);
  }

  if (!isPublic) {
    if (!session) {
      throw redirect(302, `${base}/login`);
    }
    event.locals.session = session;
  }

  return resolve(event);
};

declare global {
  namespace App {
    interface Locals {
      session?: string;
    }
  }
}
