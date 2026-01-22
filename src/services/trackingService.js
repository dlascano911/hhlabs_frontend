// Servicio de tracking de acciones de usuario
// Las acciones se persisten en el backend mediante llamadas a POST /api/track
const API_URL = import.meta.env.VITE_WRAPPER_API_URL || 'https://handheldlabs-backend-45973956798.us-central1.run.app';

class TrackingService {
  constructor() {
    this.sessionId = this.getOrCreateSessionId();
  }

  // Generar UUID v4 simple (compatible con navegadores)
  generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  // Obtener o crear session_id único con UUID
  getOrCreateSessionId() {
    let sessionId = sessionStorage.getItem('session_id');
    if (!sessionId) {
      sessionId = this.generateUUID();
      sessionStorage.setItem('session_id', sessionId);
    }
    return sessionId;
  }

  // Enviar evento de tracking al backend
  // El backend se encarga de persistir el evento
  async track(action, conversion = false) {
    try {
      const data = {
        session_id: this.sessionId,
        action,
        conversion,
        referrer: document.referrer || '',
        page_url: window.location.href
      };

      // Llamada POST al backend - sin bloquear la app si falla
      fetch(`${API_URL}/api/track`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      }).catch(err => console.warn('⚠️ Tracking error:', err.message));

      return true;
    } catch (error) {
      console.error('❌ Error preparing tracking:', error);
      return false;
    }
  }

  // ============================================
  // Métodos específicos para diferentes acciones
  // ============================================

  trackPageView(page) {
    return this.track(`page_view:${page}`);
  }

  trackClick(element) {
    return this.track(`click:${element}`);
  }

  trackPurchase(product) {
    return this.track(`purchase:${product}`, true);
  }

  trackDemo() {
    return this.track('demo_started');
  }

  trackContact() {
    return this.track('contact_submitted');
  }

  trackNavigation(from, to) {
    return this.track(`navigation:${from}_to_${to}`);
  }

  trackScroll(depth) {
    return this.track(`scroll:${depth}%`);
  }

  trackTimeOnPage(seconds) {
    return this.track(`time_on_page:${seconds}s`);
  }

  trackFormStart(formName) {
    return this.track(`form_start:${formName}`);
  }

  trackFormAbandoned(formName) {
    return this.track(`form_abandoned:${formName}`);
  }

  trackVideo(action, videoId) {
    return this.track(`video_${action}:${videoId}`);
  }

  trackError(errorType, errorMsg) {
    return this.track(`error:${errorType}:${errorMsg.substring(0, 100)}`);
  }

  trackSearch(query) {
    return this.track(`search:${query}`);
  }
}

// Exportar instancia única
export const trackingService = new TrackingService();
