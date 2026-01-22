// Servicio de audio con Handheld Labs API
const API_URL = import.meta.env.VITE_WRAPPER_API_URL || 'https://handheldlabs-backend-45973956798.us-central1.run.app';
const API_TOKEN = 'handheldlabs-api-token-2026';

export const audioService = {
  /**
   * Convertir texto a audio usando Piper TTS
   * @param {string} text - Texto a convertir
   * @param {string} languageOrVoice - Código de idioma (ej: 'es', 'en') o nombre de voz específico
   * @returns {Promise<{audio_base64: string, format: string, voice: string, metadata: object}>}
   */
  textToAudio: async (text, languageOrVoice = 'en') => {
    try {
      console.log('🔊 Convirtiendo texto a audio:', text.substring(0, 50) + '...');
      console.log('🌐 Idioma/Voz:', languageOrVoice);
      
      // Construir payload: si es código de idioma, usar 'language', si no, usar 'voice'
      const isLanguageCode = languageOrVoice.length <= 3 && !languageOrVoice.includes('_');
      const payload = isLanguageCode 
        ? { text, language: languageOrVoice }  // ← Usar código de idioma
        : { text, voice: languageOrVoice };     // ← Usar voz específica
      
      console.log('📤 Payload:', payload);
      
      const response = await fetch(`${API_URL}/text-to-audio`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${API_TOKEN}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Error en text-to-audio: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('✅ Audio generado:', {
        formato: data.format,
        voz: data.voice,
        longitud: data.text_length,
        sample_rate: data.metadata?.sample_rate
      });

      return data;
    } catch (error) {
      console.error('❌ Error en textToAudio:', error);
      throw error;
    }
  },

  /**
   * Convertir audio a texto usando Whisper
   * @param {File|Blob} audioFile - Archivo de audio a transcribir
   * @returns {Promise<{text: string, model: string, language: string, duration: number}>}
   */
  audioToText: async (audioFile) => {
    try {
      console.log('📝 Transcribiendo audio:', audioFile.name || 'audio.wav');
      
      const formData = new FormData();
      formData.append('file', audioFile);

      const response = await fetch(`${API_URL}/audio-to-text`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${API_TOKEN}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Error en audio-to-text: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('✅ Audio transcrito:', {
        texto: data.text.substring(0, 100) + '...',
        modelo: data.model,
        idioma: data.language,
        duración: data.duration
      });

      return data;
    } catch (error) {
      console.error('❌ Error en audioToText:', error);
      throw error;
    }
  },

  /**
   * Procesar texto (mantiene compatibilidad con código existente)
   * @param {string} text - Texto a procesar
   * @returns {Promise<{response: string, text: string}>}
   */
  processText: async (text) => {
    try {
      console.log('📝 Procesando texto:', text);
      
      // Por ahora mantiene el procesamiento simulado
      // Si quieres usar text-to-audio aquí, descomenta:
      // const audioData = await audioService.textToAudio(text);
      // return { response: `Audio generado con formato ${audioData.format}`, text };
      
      await new Promise(resolve => setTimeout(resolve, 500));
      const response = `He recibido tu mensaje: "${text}". Esta es una respuesta simulada.`;
      
      return { response, text };
    } catch (error) {
      console.error('❌ Error en processText:', error);
      throw error;
    }
  }
}
