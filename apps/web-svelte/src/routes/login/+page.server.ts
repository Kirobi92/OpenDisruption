import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { base } from '$app/paths';

export const load: PageServerLoad = async ({ locals }) => {
  if (locals.session) {
    throw redirect(302, `${base}/graph`);
  }
  return {};
};

export const actions: Actions = {
  default: async ({ request, fetch, cookies }) => {
    const data = await request.formData();
    const username = data.get('username')?.toString() ?? '';
    const password = data.get('password')?.toString() ?? '';

    if (!username || !password) {
      return fail(400, { error: 'Benutzername und Passwort erforderlich.' });
    }

    const body = new URLSearchParams({ username, password });

    let response: Response;
    try {
      response = await fetch('http://auth:8000/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
      });
    } catch {
      return fail(503, { error: 'Auth-Service nicht erreichbar.' });
    }

    if (!response.ok) {
      const text = await response.text().catch(() => '');
      let msg = 'Login fehlgeschlagen.';
      try {
        const json = JSON.parse(text) as { detail?: string };
        msg = json.detail ?? msg;
      } catch {}
      return fail(401, { error: msg });
    }

    const { access_token } = await response.json() as { access_token: string };

    cookies.set('kirobi_session', access_token, {
      path: '/',
      httpOnly: true,
      secure: false,
      sameSite: 'lax',
      maxAge: 60 * 60 * 8,
    });

    throw redirect(302, `${base}/graph`);
  },
};
