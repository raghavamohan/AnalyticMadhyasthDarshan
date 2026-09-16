/* Embedded in release HTML before hashing; never added at request time. */
(() => {
  'use strict';
  if (window.__amdAnalyticsInitialized) return;
  window.__amdAnalyticsInitialized = true;
  if (location.protocol !== 'https:' || location.hostname !== 'analyticmadhyasthdarshan.org' ||
      window.top !== window.self) return;

  const key = 'amd.analytics.excluded';
  const url = new URL(location.href);
  const preference = url.searchParams.get('analytics');
  let excluded = false;
  let storageAvailable = true;
  try {
    if (preference === 'off') localStorage.setItem(key, '1');
    if (preference === 'on') localStorage.removeItem(key);
    excluded = localStorage.getItem(key) === '1';
  } catch (_) {
    // Never accidentally count an opt-out when browser storage is unavailable.
    excluded = true;
    storageAvailable = false;
  }

  if (['off', 'on', 'status'].includes(preference)) {
    url.searchParams.delete('analytics');
    try { history.replaceState(history.state, '', url.href); } catch (_) { /* harmless */ }
    const showStatus = () => {
      const notice = document.createElement('aside');
      notice.setAttribute('role', 'status');
      notice.style.cssText = 'padding:16px;margin:16px;border:1px solid #1a5276;background:#f7f4ef;color:#1a1612;font:16px/1.5 system-ui;position:relative;z-index:10000';
      notice.textContent = !storageAvailable
        ? 'Analytics is off for this page. Your browser blocked saving the preference; allow site storage and open the exclusion link again.'
        : excluded
          ? 'Your visits are excluded from analytics in this browser. Repeat this on your other devices and browser profiles. Clearing site data removes this preference.'
          : 'Analytics is enabled in this browser.';
      document.body.prepend(notice);
    };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', showStatus, {once: true});
    else showStatus();
    // Preference/status pages are maintenance traffic, including re-enabling.
    return;
  }

  if (excluded || navigator.webdriver || window.__AMD_DISABLE_ANALYTICS__ ||
      navigator.onLine === false || /HeadlessChrome|Playwright|Puppeteer|Lighthouse|AMD-Publication-Audit/i.test(navigator.userAgent)) return;
  // Portal work and personal notebooks are not readership; avoid collecting their URLs.
  if (/^\/Studies\/(?:portal\/|submit\.html$|notebook\.html$)/.test(location.pathname)) return;
  if (document.querySelector('script[data-cf-beacon]')) return;

  const beacon = document.createElement('script');
  beacon.defer = true;
  beacon.src = 'https://static.cloudflareinsights.com/beacon.min.js';
  // Public site identifier, not an API credential. Manual installation posts to
  // cloudflareinsights.com, outside our immutable site's request router.
  beacon.setAttribute('data-cf-beacon', JSON.stringify({token: 'd0ff8fdbff3b4fe39838c048896422ae', spa: false}));
  document.head.appendChild(beacon);
})();
