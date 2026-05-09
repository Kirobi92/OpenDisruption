import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { base } from '$app/paths';

export const load: PageServerLoad = async ({ locals }) => {
  if (!locals.session) {
    throw redirect(302, `${base}/login`);
  }
  return {};
};
