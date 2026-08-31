const RELEASE_BASE =
  "https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/";
const FONT_NAME = /^[A-Za-z0-9][A-Za-z0-9._-]*\.cpfont$/;

export default {
  async fetch(request) {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method not allowed", { status: 405, headers: { Allow: "GET, HEAD" } });
    }

    const url = new URL(request.url);
    const name = decodeURIComponent(url.pathname.slice(1));
    if (!FONT_NAME.test(name)) {
      return new Response("Not found", { status: 404 });
    }

    const upstreamHeaders = new Headers();
    const range = request.headers.get("Range");
    if (range) upstreamHeaders.set("Range", range);

    const upstream = await fetch(RELEASE_BASE + encodeURIComponent(name), {
      method: request.method,
      headers: upstreamHeaders,
      redirect: "follow",
      cf: { cacheEverything: true, cacheTtl: 31536000 },
    });

    const headers = new Headers(upstream.headers);
    headers.set("Cache-Control", "public, max-age=31536000, immutable");
    headers.set("X-Content-Type-Options", "nosniff");
    headers.delete("Set-Cookie");
    return new Response(upstream.body, { status: upstream.status, headers });
  },
};
