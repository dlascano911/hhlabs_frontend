import { useState, useEffect, useRef } from 'react';
import { audioService } from '../../services/audioService';
import { trackingService } from '../../services/trackingService';
import '../../styles/demos/DemoPage.css';

export function DemoPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [timings, setTimings] = useState({ transcript: null, gemini: null, tts: null });
  const [transcription, setTranscription] = useState('');
  const [geminiResponse, setGeminiResponse] = useState('');
  const [responseAudioUrl, setResponseAudioUrl] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const audioRef = useRef(null);
  
  // Auto-play when new audio is created
  useEffect(() => {
    if (responseAudioUrl && audioRef.current) {
      audioRef.current.play().catch(err => console.log('Error playing audio:', err));
    }
  }, [responseAudioUrl]);
  
  // Simple UUID v4 generator
  const generateUUID = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  };
  
  const [sessionId, setSessionId] = useState(() => generateUUID());

  // Start recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (e) => {
        chunks.push(e.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/wav' });
        await processAudioFile(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setAudioChunks(chunks);
    } catch (err) {
      setError(`Error accessing microphone: ${err.message}`);
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  // Handle file upload
  const handleAudioUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    await processAudioFile(file);
  };

  // Process audio file (complete flow)
  const processAudioFile = async (audioFile) => {
    trackingService.trackDemo();

    setLoading(true);
    setError('');
    setTranscription('');
    setGeminiResponse('');
    setResponseAudioUrl(null);
    setTimings({ transcript: null, gemini: null, tts: null });

    try {
      // Phase 1: Transcribe audio to text
      const t1 = performance.now();
      const transcriptResult = await audioService.audioToText(audioFile);
      const t2 = performance.now();
      const transcriptTime = Math.round(t2 - t1);
      
      setTranscription(transcriptResult.text);
      setTimings(prev => ({ ...prev, transcript: transcriptTime }));

      // Extract detected language from Whisper
      const detectedLanguage = transcriptResult.language_info?.code || transcriptResult.language || 'en';
      console.log('🌐 Detected language:', detectedLanguage, transcriptResult.language_info);

      // Phase 2: Send to Gemini with detected language and session_id
      const t3 = performance.now();
      const API_URL = import.meta.env.VITE_WRAPPER_API_URL || 'https://handheldlabs-backend-45973956798.us-central1.run.app';
      const geminiResponse = await fetch(`${API_URL}/process-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text: transcriptResult.text,
          language: detectedLanguage,
          session_id: sessionId
        })
      });

      if (!geminiResponse.ok) {
        throw new Error(`Error in Gemini: ${geminiResponse.status}`);
      }

      const geminiData = await geminiResponse.json();
      const t4 = performance.now();
      const geminiTime = Math.round(t4 - t3);
      
      setGeminiResponse(geminiData.response);
      setTimings(prev => ({ ...prev, gemini: geminiTime }));

      // Save session_id returned by backend
      if (geminiData.session_id) {
        setSessionId(geminiData.session_id);
        console.log('🔑 Session ID updated:', geminiData.session_id);
      }

      // Phase 3: Convert Gemini response to audio using detected language
      const t5 = performance.now();
      const ttsResult = await audioService.textToAudio(geminiData.response, detectedLanguage);
      const t6 = performance.now();
      const ttsTime = Math.round(t6 - t5);
      
      // Convert base64 to Blob and create URL
      const audioBlob = await fetch(`data:audio/wav;base64,${ttsResult.audio_base64}`).then(res => res.blob());
      const url = URL.createObjectURL(audioBlob);
      setResponseAudioUrl(url);
      setTimings(prev => ({ ...prev, tts: ttsTime }));

    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setTranscription('');
    setGeminiResponse('');
    setResponseAudioUrl(null);
    setError('');
    setTimings({ transcript: null, gemini: null, tts: null });
    setSessionId(generateUUID());
  };

  return (
    <div className="page demo-page">
      <div className="demo-container">
        <div className="demo-card">
          <h1 className="demo-title">🎤 Verba Audio Demo</h1>
          <p className="demo-subtitle">Record or upload audio → Transcription → Gemini → Audio</p>

          {(timings.transcript || timings.gemini || timings.tts) && (
            <div className="timings-box">
              {timings.transcript && <p>⏱️ Transcription: {timings.transcript}ms</p>}
              {timings.gemini && <p>⏱️ Gemini: {timings.gemini}ms</p>}
              {timings.tts && <p>⏱️ TTS: {timings.tts}ms</p>}
              {timings.transcript && timings.gemini && timings.tts && (
                <p><strong>⏱️ Total: {timings.transcript + timings.gemini + timings.tts}ms</strong></p>
              )}
            </div>
          )}

          <div className="demo-input-section">
            <div className="demo-controls" style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
              <button 
                onClick={isRecording ? stopRecording : startRecording}
                disabled={loading}
                className="btn-process"
                style={{ flex: 1 }}
              >
                {isRecording ? '⏹️ Stop Recording' : '🎤 Record Audio'}
              </button>
              
              <label 
                htmlFor="audio-upload" 
                className="btn-process"
                style={{ 
                  flex: 1, 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.5 : 1
                }}
              >
                📤 Upload Audio
              </label>
              <input
                id="audio-upload"
                type="file"
                accept="audio/*"
                onChange={handleAudioUpload}
                disabled={loading}
                style={{ display: 'none' }}
              />
            </div>

            {loading && (
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <p>⏳ Processing...</p>
              </div>
            )}
          </div>

          {transcription && (
            <div className="result-box" style={{ marginTop: '20px' }}>
              <h3>📝 Transcription</h3>
              <p>{transcription}</p>
            </div>
          )}

          {geminiResponse && (
            <div className="result-box gemini" style={{ marginTop: '20px' }}>
              <div className="gemini-header">
                <h3>🤖 Gemini Response</h3>
                {timings.gemini && timings.tts && (
                  <span className="gemini-timing">
                    Gemini: {timings.gemini}ms | Audio: {timings.tts}ms
                  </span>
                )}
              </div>
              <p>{geminiResponse}</p>
            </div>
          )}

          {responseAudioUrl && (
            <div className="result-box" style={{ marginTop: '20px' }}>
              <h3>🔊 Response Audio</h3>
              <audio ref={audioRef} controls src={responseAudioUrl} style={{ width: '100%', marginTop: '10px' }} />
              <button onClick={handleReset} className="btn-reset" style={{ marginTop: '15px' }}>
                New Query
              </button>
            </div>
          )}

          {error && (
            <div className="error-box">
              ⚠️ {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
