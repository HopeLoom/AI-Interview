import { ModeAwareRouter } from '@/components/routing/ModeAwareRouter';
import webSocketService from '@/lib/websocketService';
import { useEffect } from 'react';

function Router() {
  return <ModeAwareRouter />;
}

function App() {
  useEffect(() => {
    // Initialize WebSocket connection when app starts
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
    console.log('apiBaseUrl', apiBaseUrl);

    try {
      let resolvedBase = apiBaseUrl;

      if (resolvedBase && !/^https?:\/\//i.test(resolvedBase)) {
        resolvedBase = `${window.location.protocol}//${resolvedBase}`;
      }

      const url = resolvedBase ? new URL(resolvedBase) : new URL(window.location.origin);
      url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
      url.pathname = '/ws';
      url.search = '';
      url.hash = '';

      webSocketService.connect(url.toString());
    } catch (error) {
      console.error('Failed to construct WebSocket URL, falling back to window location', error);
      const fallbackUrl = new URL(window.location.origin);
      fallbackUrl.protocol = fallbackUrl.protocol === 'https:' ? 'wss:' : 'ws:';
      fallbackUrl.pathname = '/ws';
      webSocketService.connect(fallbackUrl.toString());
    }
    // Cleanup on app unmount
    return () => {
      webSocketService.disconnect();
    };
  }, []);

  return <Router />;
}

export default App;
