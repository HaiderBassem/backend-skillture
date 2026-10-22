// The logged-in session lives in a tiny external store backed by localStorage, so the API
// client (plain TypeScript) and React (useSyncExternalStore) both read the same source.
//
// Trade-off: a token in localStorage can be read by any script on the page (XSS). That is the
// usual choice for a bearer-token API with no cookies; keep dependencies few and never render
// untrusted HTML to keep that risk small.

import type { Account } from "@/lib/types";

const KEY = "cc.auth";

export interface Session {
  token: string;
  expiresAt: number; // epoch milliseconds
  account: Account;
}

function read(): Session | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const session = JSON.parse(raw) as Session;
    return session.expiresAt > Date.now() ? session : null;
  } catch {
    return null;
  }
}

let current: Session | null = read();
let expiryTimer: number | undefined;
const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((listener) => listener());
}

function scheduleExpiry() {
  window.clearTimeout(expiryTimer);
  if (!current) return;
  const wait = current.expiresAt - Date.now();
  expiryTimer = window.setTimeout(() => setSession(null), Math.max(0, Math.min(wait, 2 ** 31 - 1)));
}

export function setSession(session: Session | null) {
  current = session;
  try {
    if (session) localStorage.setItem(KEY, JSON.stringify(session));
    else localStorage.removeItem(KEY);
  } catch {
    // Storage blocked (private mode): the session just lasts until the tab closes.
  }
  scheduleExpiry();
  notify();
}

export const getSession = (): Session | null => current;

export const getToken = (): string | null => (current && current.expiresAt > Date.now() ? current.token : null);

export function subscribeSession(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

// Keep several tabs in step: signing out in one signs out in all.
window.addEventListener("storage", (event) => {
  if (event.key === KEY) {
    current = read();
    scheduleExpiry();
    notify();
  }
});
scheduleExpiry();
