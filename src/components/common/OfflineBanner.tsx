import React, { useState, useEffect } from 'react';
import { WifiOff, X, RefreshCw } from 'lucide-react';
import { subscribeToApiStatus, api } from '../../services/api';

export const OfflineBanner: React.FC = () => {
  const [isOffline, setIsOffline] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    // Initial backend check
    api.checkHealth();
    const unsub = subscribeToApiStatus(offline => {
      setIsOffline(offline);
      if (!offline) {
        setDismissed(false);
      }
    });
    return unsub;
  }, []);

  const handleRetry = async () => {
    setChecking(true);
    await api.checkHealth();
    setChecking(false);
  };

  if (!isOffline || dismissed) return null;

  return (
    <div className="bg-gradient-to-r from-amber-600 to-amber-700 text-white px-4 py-2.5 text-xs font-semibold flex items-center justify-between shadow-md z-50 animate-in fade-in slide-in-from-top-1 border-b border-amber-800">
      <div className="flex items-center gap-2.5">
        <WifiOff className="w-4 h-4 text-amber-200 flex-shrink-0 animate-pulse" />
        <span className="leading-tight">
          <strong>Offline Mode Active:</strong> Live backend server is unreachable. Working with cached grievance data and local AI fallback.
        </span>
      </div>
      <div className="flex items-center gap-2.5 flex-shrink-0 ml-3">
        <button
          type="button"
          onClick={handleRetry}
          disabled={checking}
          className="px-3 py-1 rounded-full bg-white/20 hover:bg-white/30 text-[11px] font-bold flex items-center gap-1.5 transition-colors focus-ring"
        >
          <RefreshCw className={`w-3 h-3 ${checking ? 'animate-spin' : ''}`} />
          <span>{checking ? 'Connecting...' : 'Reconnect'}</span>
        </button>
        <button
          type="button"
          onClick={() => setDismissed(true)}
          className="p-1 rounded-full hover:bg-white/20 text-white/80 hover:text-white transition-colors"
          title="Dismiss offline banner"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

