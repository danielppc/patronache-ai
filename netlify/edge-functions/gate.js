// Gate server-side pentru /curs.html — fără cookie de acces valid, redirect la /activare.html.
// Cookie-ul e emis de netlify/functions/activate.js (HMAC-SHA256 cu GATE_SECRET).

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

export default async (request, context) => {
  const secret = Netlify.env.get('GATE_SECRET') || '';
  const redirect = new URL('/activare.html', request.url);

  if (!secret) {
    // Fără secret configurat, cursul rămâne închis (fail-safe).
    return Response.redirect(redirect, 302);
  }

  const cookie = getCookie(request, 'ia_access');
  if (!cookie) return Response.redirect(redirect, 302);

  const dot = cookie.indexOf('.');
  if (dot < 1) return Response.redirect(redirect, 302);

  const exp = cookie.slice(0, dot);
  const sig = cookie.slice(dot + 1);

  const expected = await hmacHex(exp, secret);
  const expNum = Number(exp);

  if (sig !== expected || !Number.isFinite(expNum) || Date.now() > expNum) {
    return Response.redirect(redirect, 302);
  }

  return context.next();
};

export const config = { path: '/curs.html' };
