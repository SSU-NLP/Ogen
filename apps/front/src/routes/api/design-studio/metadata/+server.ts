import { json } from '@sveltejs/kit';
import { dev } from '$app/environment';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

import type { RequestHandler } from './$types';
import { designSystemMetadata } from '$lib/ds';

const METADATA_FILE = resolve(process.cwd(), 'src/lib/design-studio.metadata.json');

export const GET: RequestHandler = async () => {
  try {
    const raw = await readFile(METADATA_FILE, 'utf-8');
    const parsed = JSON.parse(raw);
    return json(parsed);
  } catch {
    // Fallback to ds.ts metadata if file does not exist or is invalid.
    return json(designSystemMetadata);
  }
};

export const POST: RequestHandler = async ({ request }) => {
  if (!dev) {
    return new Response('File persistence is only enabled in dev.', { status: 403 });
  }

  const body = (await request.json()) as { metadata?: unknown };
  if (!body || typeof body !== 'object' || !body.metadata || typeof body.metadata !== 'object') {
    return new Response('Invalid payload: expected { metadata: object }', { status: 400 });
  }

  const serialized = JSON.stringify(body.metadata, null, 2) + '\n';
  await writeFile(METADATA_FILE, serialized, 'utf-8');
  return json({ ok: true, path: 'src/lib/design-studio.metadata.json' });
};
