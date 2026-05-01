import { useEffect, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '';
const POLL_INTERVAL = 5000; // ms between retries while waking up
const MAX_ATTEMPTS = 24;    // ~2 min total before giving up

export default function BackendStatus({ onReady }) {
  const [status, setStatus] = useState('checking'); // 'checking' | 'waking' | 'ready' | 'error'
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let timer;

    const ping = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(4000) });
        if (res.ok) {
          setStatus('ready');
          onReady?.();
          return;
        }
      } catch {
        // still waking up
      }

      setAttempt(prev => {
        const next = prev + 1;
        if (next >= MAX_ATTEMPTS) {
          setStatus('error');
        } else {
          setStatus('waking');
          timer = setTimeout(ping, POLL_INTERVAL);
        }
        return next;
      });
    };

    ping();
    return () => clearTimeout(timer);
  }, []);

  if (status === 'ready') {
    return (
      <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/20 border border-emerald-400/40 text-emerald-300 text-sm font-medium backdrop-blur-sm">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-none inline-block" />
        Backend is up — you&apos;re good to go!
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/20 border border-red-400/40 text-red-300 text-sm font-medium backdrop-blur-sm">
        <span className="w-2 h-2 rounded-full bg-red-400 inline-block" />
        Backend unavailable — please try again later
      </div>
    );
  }

  // 'checking' or 'waking'
  return (
    <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-yellow-500/20 border border-yellow-400/40 text-yellow-200 text-sm font-medium backdrop-blur-sm">
      <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse inline-block" />
      {status === 'checking' ? 'Connecting to backend…' : `Backend is waking up, please wait… (${attempt}/${MAX_ATTEMPTS})`}
    </div>
  );
}
