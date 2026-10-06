// hoshi.flux7.art: the viewer runs on void behind a Cloudflare tunnel. When void is off, the
// tunnel has no connector and Cloudflare answers 530 (error 1033); show a page that says so.
const OFFLINE = `<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>hoshi world offline</title>
<style>
body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0b0e14;color:#c9d4e3;
font:14px/1.6 "JetBrains Mono",ui-monospace,monospace;text-align:center;padding:16px}
h1{color:#4de1ff;font-size:18px;letter-spacing:.12em;margin:0 0 6px}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:#ff6b6b;margin-right:8px;
box-shadow:0 0 8px #ff6b6b}
p{color:#6b7a90;max-width:460px;margin:10px auto}
</style></head><body><div>
<h1>HOSHI WORLD</h1>
<div><span class="dot"></span>offline</div>
<p>La machine qui fait tourner le monde est éteinte : pas de partie en cours.</p>
<p>Revenez plus tard ; les parties terminées se relisent dès qu'elle est rallumée.</p>
</div></body></html>`;

export default {
  async fetch(request) {
    try {
      const r = await fetch(request);
      if (r.status === 530 || r.status === 502 || r.status === 503 || r.status === 504) return offline();
      return r;
    } catch {
      return offline();
    }
  },
};

function offline() {
  return new Response(OFFLINE, { status: 503, headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" } });
}
