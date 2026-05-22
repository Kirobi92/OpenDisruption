import { redirect } from '@sveltejs/kit';
import { base } from '$app/paths';

export const load = async ({ locals, fetch }: any) => {
  if (!locals.session) throw redirect(302, `${base}/login`);
  return { session: locals.session };
};
