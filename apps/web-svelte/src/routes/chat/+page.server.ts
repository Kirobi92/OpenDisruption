import { redirect } from '@sveltejs/kit';
import { base } from '$app/paths';

export const load = async ({ locals, fetch }: any) => {
  if (!locals.session) throw redirect(302, `${base}/login`);
  const token = locals.session;
  let user = null;
  try {
    const res = await fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } });
    if (res.ok) user = await res.json();
  } catch {}
  return { session: token, user };
};
