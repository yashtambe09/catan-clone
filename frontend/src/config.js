// Falls back to whatever hostname the page itself was loaded from (not a
// hardcoded 'localhost') so the app works unmodified when a friend loads it
// from this machine's LAN IP during a LAN playtest, not just from localhost.
export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || `http://${window.location.hostname}:8000`
