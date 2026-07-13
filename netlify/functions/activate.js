// Activare curs — validează cheia de licență prin API-ul Polar și emite cookie-ul de acces.
// Env necesare (Netlify): POLAR_API_KEY (secret), POLAR_ORG_ID, GATE_SECRET (secret).
const crypto = require('crypto');

const POLAR_API = 'https://api.polar.sh/v1/customer-portal/license-keys';
const COOKIE_MAX_AGE = 60 * 60 * 24 * 365; // 1 an

function sign(exp, secret) {
  return crypto.createHmac('sha256', secret).update(String(exp)).digest('hex');
}

function accessCookie(secret) {
  const exp = Date.now() + COOKIE_MAX_AGE * 1000;
  const value = `${exp}.${sign(exp, secret)}`;
  return `ia_access=${value}; Path=/; Max-Age=${COOKIE_MAX_AGE}; HttpOnly; Secure; SameSite=Lax`;
}

function json(statusCode, body, cookie) {
  const headers = { 'Content-Type': 'application/json' };
  if (cookie) headers['Set-Cookie'] = cookie;
  return { statusCode, headers, body: JSON.stringify(body) };
}

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return json(405, { ok: false, error: 'Method not allowed' });
  }

  const { POLAR_API_KEY, POLAR_ORG_ID, GATE_SECRET } = process.env;
  if (!POLAR_API_KEY || !POLAR_ORG_ID || !GATE_SECRET) {
    return json(500, { ok: false, error: 'Serverul nu e configurat complet. Scrie-ne la hello@invata-ai.com.' });
  }

  let key = '';
  try {
    key = String(JSON.parse(event.body || '{}').key || '').trim();
  } catch (e) { /* body invalid */ }

  if (!key) {
    return json(400, { ok: false, error: 'Introdu cheia de acces.' });
  }

  // Acces proprietar (pentru testare) — cheia = GATE_SECRET
  if (key === GATE_SECRET) {
    return json(200, { ok: true }, accessCookie(GATE_SECRET));
  }

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${POLAR_API_KEY}`,
  };

  try {
    // 1) Încearcă activarea (consumă un slot din limita de dispozitive)
    const actRes = await fetch(`${POLAR_API}/activate`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        key,
        organization_id: POLAR_ORG_ID,
        label: 'invata-ai.com',
      }),
    });

    if (actRes.ok) {
      const data = await actRes.json();
      const status = data && data.license_key ? data.license_key.status : 'granted';
      if (status === 'granted') {
        return json(200, { ok: true }, accessCookie(GATE_SECRET));
      }
      return json(403, { ok: false, error: 'Cheia există, dar accesul a fost revocat. Scrie-ne la hello@invata-ai.com.' });
    }

    // 2) Limita de activări atinsă? Cheia poate fi totuși validă (alt dispozitiv) — validăm.
    if (actRes.status === 403) {
      const valRes = await fetch(`${POLAR_API}/validate`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ key, organization_id: POLAR_ORG_ID }),
      });
      if (valRes.ok) {
        const data = await valRes.json();
        if (data && data.status === 'granted') {
          return json(200, { ok: true }, accessCookie(GATE_SECRET));
        }
      }
      return json(403, { ok: false, error: 'Ai atins limita de dispozitive pentru această cheie. Scrie-ne la hello@invata-ai.com și rezolvăm.' });
    }

    if (actRes.status === 404 || actRes.status === 422) {
      return json(404, { ok: false, error: 'Cheie invalidă. Verifică emailul de confirmare a plății și copiaz-o exact.' });
    }

    return json(502, { ok: false, error: 'Nu am putut verifica cheia acum. Încearcă din nou în câteva minute.' });
  } catch (e) {
    return json(502, { ok: false, error: 'Nu am putut verifica cheia acum. Încearcă din nou în câteva minute.' });
  }
};
