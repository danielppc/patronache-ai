/* Învață AI — banner consimțământ cookies (Google Consent Mode v2)
   Se afișează doar dacă utilizatorul nu a ales încă. Alegerea se ține în localStorage. */
(function () {
  var KEY = 'ia_consent';
  try { if (localStorage.getItem(KEY)) return; } catch (e) { return; }

  function gtagPush() { window.dataLayer = window.dataLayer || []; window.dataLayer.push(arguments); }

  function grant() {
    try { localStorage.setItem(KEY, 'granted'); } catch (e) {}
    gtagPush('consent', 'update', {
      ad_storage: 'granted', ad_user_data: 'granted',
      ad_personalization: 'granted', analytics_storage: 'granted'
    });
    hide();
  }
  function deny() {
    try { localStorage.setItem(KEY, 'denied'); } catch (e) {}
    hide();
  }
  function hide() { var b = document.getElementById('ia-consent'); if (b) b.remove(); }

  function render() {
    var d = document.createElement('div');
    d.id = 'ia-consent';
    d.setAttribute('role', 'dialog');
    d.setAttribute('aria-label', 'Preferințe cookie-uri');
    d.innerHTML =
      '<div style="position:fixed;left:16px;right:16px;bottom:16px;z-index:9999;max-width:560px;margin:0 auto;' +
      'background:#0f172a;color:#e2e8f0;border-radius:14px;padding:18px 20px;box-shadow:0 12px 40px rgba(15,23,42,.35);' +
      'font-family:Inter,system-ui,sans-serif;font-size:14px;line-height:1.55;">' +
      '<strong style="color:#fff;">Cookie-uri</strong><br>' +
      'Folosim cookie-uri pentru statistici anonime (Google Analytics), ca să înțelegem cum e folosit site-ul. ' +
      'Detalii în <a href="/confidentialitate.html" style="color:#a78bfa;">Politica de confidențialitate</a>.' +
      '<div style="margin-top:12px;display:flex;gap:10px;flex-wrap:wrap;">' +
      '<button id="ia-c-acc" style="background:#1e40af;color:#fff;border:0;border-radius:8px;padding:9px 20px;' +
      'font-weight:700;font-size:14px;cursor:pointer;font-family:inherit;">Accept</button>' +
      '<button id="ia-c-ref" style="background:transparent;color:#cbd5e1;border:1px solid #475569;border-radius:8px;' +
      'padding:9px 20px;font-weight:600;font-size:14px;cursor:pointer;font-family:inherit;">Refuz</button>' +
      '</div></div>';
    document.body.appendChild(d);
    document.getElementById('ia-c-acc').onclick = grant;
    document.getElementById('ia-c-ref').onclick = deny;
  }

  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', render); }
  else { render(); }
})();
