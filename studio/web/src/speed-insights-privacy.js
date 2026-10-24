// Only the checked-in RRREMERGEN React bundle is in this telemetry scope.
const PATHS = new Set(['/rrremergen', '/rrremergen/', '/rrremergen/index.html']);
const HASHES = new Set(['', '#rrremergen', '#servizi', '#come-funziona', '#chi-siamo', '#contatto']);

export function isRrremergenLocation(location) {
  return Boolean(location && PATHS.has(location.pathname) && HASHES.has(location.hash));
}

/**
 * @param {Parameters<import('@vercel/speed-insights').BeforeSendMiddleware>[0]} event
 * @param {string} origin Current browser origin; never a configured external collector.
 * @returns {ReturnType<import('@vercel/speed-insights').BeforeSendMiddleware>}
 */
export function sanitizeSpeedInsightsEvent(event, origin) {
  try {
    if (event?.type !== 'vital' || typeof event.url !== 'string') return null;
    const pageOrigin = new URL(origin);
    const url = new URL(event.url);
    if (!['http:', 'https:'].includes(pageOrigin.protocol) ||
        pageOrigin.username || pageOrigin.password ||
        url.origin !== pageOrigin.origin || url.username || url.password ||
        !isRrremergenLocation(url)) return null;

    // Return only the SDK's documented fields. Never forward caller-supplied
    // properties, dynamic route values, query strings, fragments or form values.
    return { type: 'vital', url: `${pageOrigin.origin}/rrremergen/`, route: '/rrremergen' };
  } catch {
    // Malformed URLs or unexpected event shapes must fail closed.
    return null;
  }
}
