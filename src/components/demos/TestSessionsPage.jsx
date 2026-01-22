import { useState, useEffect, useRef } from 'react';
import { trackingService } from '../../services/trackingService';
import '../../styles/demos/TestSessionsPage.css';

export function TestSessionsPage() {
  // Simple UUID v4 generator
  const generateUUID = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  };

  const [sessionId, setSessionId] = useState(() => generateUUID());
  const [messageCount, setMessageCount] = useState(0);
  const [topicChangeCount, setTopicChangeCount] = useState(0);
  const [responseTimes, setResponseTimes] = useState([]);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const chatAreaRef = useRef(null);

  useEffect(() => {
    if (chatAreaRef.current) {
      chatAreaRef.current.scrollTop = chatAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const addMessage = (type, text, time = null, topicChanged = false) => {
    const now = new Date().toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });

    setMessages(prev => [...prev, {
      type,
      text,
      time,
      topicChanged,
      timestamp: now
    }]);
  };

  const sendMessage = async () => {
    const message = userInput.trim();
    if (!message) return;

    setIsLoading(true);
    setUserInput('');

    addMessage('user', message);

    try {
      const startTime = performance.now();
      const API_URL = import.meta.env.VITE_WRAPPER_API_URL || 'https://handheldlabs-backend-45973956798.us-central1.run.app';

      const response = await fetch(`${API_URL}/process-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: message,
          language: 'es',
          session_id: sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      const endTime = performance.now();
      const responseTime = Math.round(endTime - startTime);

      // Update session_id and detect topic change
      if (data.session_id) {
        const isNewSession = sessionId !== data.session_id;
        setSessionId(data.session_id);
        
        if (isNewSession && messageCount > 0) {
          setTopicChangeCount(prev => prev + 1);
        }
      }

      addMessage('assistant', data.response, responseTime, data.topic_changed);

      setMessageCount(prev => prev + 1);
      setResponseTimes(prev => [...prev, responseTime]);

      setConversationHistory(prev => [...prev, {
        timestamp: new Date().toISOString(),
        user: message,
        assistant: data.response,
        sessionId: data.session_id,
        responseTime: responseTime
      }]);

    } catch (error) {
      console.error('Error:', error);
      addMessage('system', `❌ Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isLoading) {
      sendMessage();
    }
  };

  const resetSession = () => {
    if (!confirm('Are you sure you want to restart the session?')) return;

    setSessionId(generateUUID());
    setMessageCount(0);
    setTopicChangeCount(0);
    setResponseTimes([]);
    setConversationHistory([]);
    setMessages([]);
  };

  const exportConversation = () => {
    if (conversationHistory.length === 0) {
      alert('No conversation to export');
      return;
    }

    const exportData = {
      sessionId: sessionId,
      messageCount: messageCount,
      topicChanges: topicChangeCount,
      averageResponseTime: responseTimes.length > 0 
        ? Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length)
        : 0,
      conversation: conversationHistory,
      exportedAt: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
      type: 'application/json' 
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation-${sessionId?.substring(0, 8)}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);

    alert('✅ Conversation exported successfully');
  };

  const runTestScenario = async (scenario) => {
    const scenarios = {
      'same-topic': [
        'Do you know about Rome?',
        'I want to go on vacation',
        'What pizza do you recommend?',
        'How much does the flight cost?'
      ],
      'topic-change': [
        'Do you know about Rome?',
        'I want to go on vacation',
        'How many legs does a spider have?',
        'Where do spiders live?'
      ],
      'multi-lang': [
        'Hola, ¿cómo estás?',
        'Hello, how are you?',
        'Bonjour, comment allez-vous?',
        'Can you help me in Spanish?'
      ],
      'context-test': [
        'I want to go to Italy',
        'How much does it cost?',
        'What about the hotel?',
        'What documents do I need?'
      ]
    };

    const scenarioMessages = scenarios[scenario];
    if (!scenarioMessages) return;

    for (let i = 0; i < scenarioMessages.length; i++) {
      setUserInput(scenarioMessages[i]);
      await new Promise(resolve => setTimeout(resolve, 100));
      await sendMessage();
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  };

  const avgTime = responseTimes.length > 0 
    ? Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length)
    : 0;

  const lastTime = responseTimes.length > 0 ? responseTimes[responseTimes.length - 1] : 0;
  const maxTime = 5000;
  const percentage = Math.min((lastTime / maxTime) * 100, 100);

  return (
    <div className="page test-sessions-page">
      <div className="test-sessions-container">
        <div className="test-main-panel">
          <div className="test-header">
            <h1>🧪 Conversational Session Tests</h1>
            <p>Test context management and topic change detection system</p>
            <div className="test-session-info">
              <div>
                <strong>Session ID:</strong>{' '}
                <span className="test-session-id">
                  {sessionId ? `${sessionId.substring(0, 8)}...${sessionId.substring(sessionId.length - 8)}` : 'No active session'}
                </span>
              </div>
              <div>
                <strong>Messages:</strong> <span>{messageCount}</span>
              </div>
            </div>
          </div>

          <div className="test-chat-area" ref={chatAreaRef}>
            {messages.length === 0 ? (
              <div className="test-empty-state">
                <div className="test-empty-icon">💬</div>
                <h3>Start a conversation</h3>
                <p>Type a message to begin the session</p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className="test-message">
                  <div className="test-message-header">
                    {msg.type === 'user' && <span className="test-badge">YOU</span>}
                    {msg.type === 'assistant' && (
                      <>
                        <span className="test-badge">VERBA AI</span>
                        {msg.topicChanged && <span className="test-topic-badge">🔄 Topic change</span>}
                      </>
                    )}
                  </div>
                  <div className={`test-message-${msg.type}`}>
                    {msg.text}
                    <div className="test-message-time">
                      {msg.time && <span>⏱️ {msg.time}ms</span>}
                      <span>🕐 {msg.timestamp}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="test-input-area">
            <input
              type="text"
              className="test-input-field"
              placeholder="Type your message here..."
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
            />
            <button 
              className="test-btn-send" 
              onClick={sendMessage}
              disabled={isLoading}
            >
              {isLoading ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>

        <div className="test-sidebar">
          <div className="test-stats-panel">
            <h2>📊 Statistics</h2>
            
            <div className="test-stat-item">
              <div className="test-stat-label">Total Messages</div>
              <div className="test-stat-value">{messageCount}</div>
            </div>

            <div className="test-stat-item">
              <div className="test-stat-label">Topic Changes</div>
              <div className="test-stat-value">{topicChangeCount}</div>
            </div>

            <div className="test-stat-item">
              <div className="test-stat-label">Average Time</div>
              <div className="test-stat-value">{avgTime > 0 ? `${avgTime}ms` : '—'}</div>
            </div>

            {lastTime > 0 && (
              <div className="test-performance">
                <strong>⚡ Last Time</strong>
                <div className="test-chart-bar">
                  <div className="test-chart-fill" style={{ width: `${percentage}%` }}>
                    {lastTime}ms
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="test-controls-panel">
            <h2>🎮 Controls</h2>
            
            <button className="test-control-btn test-btn-reset" onClick={resetSession}>
              🔄 Restart Session
            </button>

            <button className="test-control-btn test-btn-export" onClick={exportConversation}>
              💾 Export Conversation
            </button>

            <div className="test-scenarios">
              <strong>🧪 Test Scenarios</strong>
              
              <div className="test-scenario" onClick={() => runTestScenario('same-topic')}>
                ✅ Same Topic (Rome Travel)
              </div>
              
              <div className="test-scenario" onClick={() => runTestScenario('topic-change')}>
                🔄 Topic Change (Rome → Spiders)
              </div>
              
              <div className="test-scenario" onClick={() => runTestScenario('multi-lang')}>
                🌍 Multi-language (ES → EN)
              </div>

              <div className="test-scenario" onClick={() => runTestScenario('context-test')}>
                📚 Context Test (Ambiguous questions)
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
