// Verifică (fără efecte secundare) dacă vizitatorul are cookie de acces valid.
// Folosit de landing ca să arate „Continuă cursul" în loc de „Cumpără" cumpărătorilor.

async function hmacHex(message, secret) {
  const enc = new TextEncoder();
  const cryptoKey = await crypto.subtle.importKey(
    'raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', cryptoKey, enc.encode(message));
  return Array.from(new Uint8Array(sig)).map((b) => b.toString(16).padStart(2, '0')).join('');
}

function getCookie(request, name) {
  const header = request.headers.get('cookie') || '';
  for (const part of header.split(';')) {
    const [k, ...rest] = part.trim().split('=');
    if (k === name) return rest.join('=');
  }
  return null;
}

export default async (request) => {
  const headers = { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' };
  const no = new Response(JSON.stringify({ access: false }), { headers });

  const secret = Netlify.env.get('GATE_SECRET') || '';
  if (!secret) return no;

  const cookie = getCookie(request, 'ia_access');
  if (!cookie) return no;

  const dot = cookie.indexOf('.');
  if (dot < 1) return no;

  const exp = cookie.slice(0, dot);
  const sig = cookie.slice(dot + 1);
  const expected = await hmacHex(exp, secret);
  const expNum = Number(exp);

  if (sig !== expected || !Number.isFinite(expNum) || Date.now() > expNum) return no;

  return new Response(JSON.stringify({ access: true }), { headers });
};

export const config = { path: '/api/session' };
