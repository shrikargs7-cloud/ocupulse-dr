import { useEffect, useRef, useCallback } from 'react';
import { analytics } from '../services/analytics';

export const useAnalytics = () => {
  const sessionStarted = useRef(false);

  const trackEvent = useCallback((type: string, data: any) => {
    analytics.trackEvent(type, data);
  }, []);

  const trackPageView = useCallback((page: string) => {
    analytics.trackEvent('page_view', { page, timestamp: new Date().toISOString() });
  }, []);

  const trackAnalysis = useCallback((imageId: number, result: any) => {
    analytics.trackAnalysis(imageId, result);
  }, []);

  const trackError = useCallback((error: string, context: any = {}) => {
    analytics.trackError(error, context);
  }, []);

  useEffect(() => {
    if (!sessionStarted.current) {
      analytics.startTracking();
      analytics.trackSessionStart();
      sessionStarted.current = true;
    }

    return () => {
      if (sessionStarted.current) {
        analytics.trackSessionEnd();
        analytics.stopTracking();
        sessionStarted.current = false;
      }
    };
  }, []);

  return {
    trackEvent,
    trackPageView,
    trackAnalysis,
    trackError,
    getStats: analytics.getStats.bind(analytics),
  };
};

export default useAnalytics;