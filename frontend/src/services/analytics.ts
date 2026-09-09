import axios from 'axios';
import { wsService } from './websocket';

interface AnalyticsEvent {
  type: string;
  timestamp: string;
  data: any;
}

class AnalyticsService {
  private events: AnalyticsEvent[] = [];
  private isTracking = false;
  private flushInterval: ReturnType<typeof setInterval> | null = null;

  startTracking(intervalMs: number = 5000) {
    if (this.isTracking) return;
    this.isTracking = true;
    this.flushInterval = setInterval(() => this.flush(), intervalMs);
  }

  stopTracking() {
    this.isTracking = false;
    if (this.flushInterval) {
      clearTimeout(this.flushInterval);
      this.flushInterval = null;
    }
    this.flush();
  }

  trackEvent(type: string, data: any) {
    this.events.push({
      type,
      timestamp: new Date().toISOString(),
      data,
    });

    if (this.events.length > 50) {
      this.flush();
    }
  }

  trackAnalysis(imageId: number, result: any) {
    this.trackEvent('analysis_complete', {
      imageId,
      grade: result.grading?.grade,
      confidence: result.grading?.confidence,
      processingTime: result.processing_time,
      referable: result.grading?.is_referable,
    });
  }

  trackUpload(fileSize: number, success: boolean) {
    this.trackEvent('image_upload', {
      fileSize,
      success,
    });
  }

  trackError(error: string, context: any = {}) {
    this.trackEvent('error', {
      error,
      context,
    });
  }

  trackSessionStart() {
    this.trackEvent('session_start', {
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
    });
  }

  trackSessionEnd() {
    this.trackEvent('session_end', {
      duration: this.events.length > 0 
        ? Date.now() - new Date(this.events[0].timestamp).getTime()
        : 0,
    });
    this.flush();
  }

  private async flush() {
    if (this.events.length === 0) return;

    const eventsToSend = [...this.events];
    this.events = [];

    try {
      await axios.post('/api/v1/analytics/batch', {
        events: eventsToSend,
        timestamp: new Date().toISOString(),
      });

      if (wsService.isConnected()) {
        wsService.send({
          type: 'analytics',
          events: eventsToSend,
        });
      }
    } catch (error) {
      console.error('Failed to send analytics:', error);
      this.events = [...eventsToSend, ...this.events];
    }
  }

  getStats(): {
    totalEvents: number;
    eventTypes: Record<string, number>;
    sessionDuration: number;
  } {
    const eventTypes: Record<string, number> = {};
    this.events.forEach(event => {
      eventTypes[event.type] = (eventTypes[event.type] || 0) + 1;
    });

    return {
      totalEvents: this.events.length,
      eventTypes,
      sessionDuration: this.events.length > 0
        ? Date.now() - new Date(this.events[0].timestamp).getTime()
        : 0,
    };
  }

  clearEvents() {
    this.events = [];
  }
}

export const analytics = new AnalyticsService();
export default analytics;