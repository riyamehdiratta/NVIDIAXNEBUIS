import {
  AlertCircle,
  ArrowRight,
  Bot,
  Calendar,
  Check,
  ChevronDown,
  ChevronRight,
  Code,
  Copy,
  Database,
  Flame,
  Folder,
  Globe,
  Layers,
  Link2,
  Maximize2,
  MessageSquare,
  Mic,
  MicOff,
  Minimize2,
  Radio,
  RotateCcw,
  Search,
  Send,
  Sparkles,
  Square,
  Terminal,
  User,
  Volume2,
  VolumeX,
  X,
  Zap,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { api, post } from '../api';
import './LiveAssistant.css';

export function LiveAssistant({ isOpen, onClose, setToast }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hello! I'm your Sovereign Delegate. I'm connected to your workspace memory and apps. What would you like to capture, review, or do?",
      model: 'Threadline Sovereign Substrate',
    },
  ]);
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [continuousCapture, setContinuousCapture] = useState(false);
  const [copiedId, setCopiedId] = useState(null);
  const [showConnectors, setShowConnectors] = useState(false);
  const [connectors, setConnectors] = useState([]);
  const [allTools, setAllTools] = useState([]);
  const [suggestions, setSuggestions] = useState([
    "What's due this week?",
    'Create project workspace with README',
    'Open WhatsApp and chat with Jordan',
    'Play turn-based chess with Jordan',
    'Search GitHub for open issues',
    'Search Google docs for proposal',
    'Read file README.md',
    'Inspect database schema',
    'Search web for Nemotron 3.5',
    'Is this message a scam?',
  ]);

  const recognitionRef = useRef(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      api('/connectors/').then(setConnectors).catch(() => []);
      api('/connectors/all_tools').then((d) => setAllTools(d.tools || [])).catch(() => []);
    }
  }, [isOpen]);

  // Auto-scroll chat feed
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  // Speech Recognition setup (Web Speech API)
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (transcript.trim()) {
          handleSendMessage(transcript.trim());
        }
      };

      recognition.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  // Text to Speech playback
  const speakText = useCallback(
    (text) => {
      if (!voiceEnabled || !window.speechSynthesis) return;
      window.speechSynthesis.cancel(); // Stop any pending speech
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.05;
      utterance.pitch = 1.0;

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => {
        setIsSpeaking(false);
        // In continuous capture mode, resume listening after speaking
        if (continuousCapture && recognitionRef.current) {
          try {
            recognitionRef.current.start();
          } catch (e) {
            // Already started
          }
        }
      };
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    },
    [voiceEnabled, continuousCapture]
  );

  // Toggle voice recognition
  const toggleListening = () => {
    if (!recognitionRef.current) {
      setToast('Microphone speech recognition is not supported in this browser. You can type in the chat box.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      window.speechSynthesis?.cancel();
      setIsSpeaking(false);
      try {
        recognitionRef.current.start();
      } catch (e) {
        console.warn('Error starting speech recognition:', e);
      }
    }
  };

  // Toggle Continuous Capture (Gemini Live Mode)
  const toggleContinuousCapture = () => {
    const nextState = !continuousCapture;
    setContinuousCapture(nextState);
    if (nextState) {
      setToast('Continuous Capture active. Speak naturally; the AI listens and speaks back.');
      if (!isListening && recognitionRef.current) {
        try {
          recognitionRef.current.start();
        } catch (e) {}
      }
    } else {
      if (isListening && recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setToast('Continuous Capture paused.');
    }
  };

  // Send message to live assistant
  const handleSendMessage = async (textToSend) => {
    const content = textToSend || input;
    if (!content.trim()) return;

    const userMsg = { role: 'user', content: content.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsThinking(true);

    try {
      const historyPayload = messages.slice(-6).map((m) => ({ role: m.role, content: m.content }));
      const res = await post('/live/chat', {
        message: content.trim(),
        history: historyPayload,
        continuous_mode: continuousCapture,
      });

      const assistantMsg = {
        role: 'assistant',
        content: res.reply,
        voice_summary: res.voice_summary,
        action_executed: res.action_executed,
        model: res.model_used,
      };

      setMessages((prev) => [...prev, assistantMsg]);
      if (res.suggestions?.length > 0) {
        setSuggestions(res.suggestions);
      }

      // Voice response
      if (res.voice_summary) {
        speakText(res.voice_summary);
      }
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `I ran into an issue processing that: ${e.message}. Please try again.`,
          model: 'System Error',
        },
      ]);
    } finally {
      setIsThinking(false);
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard?.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="live-modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="live-container">
        {/* Header */}
        <header className="live-header">
          <div className="live-header-brand">
            <div className="live-logo-orb">
              <Sparkles size={16} />
            </div>
            <div>
              <h3>Sovereign Live Assistant</h3>
              <span>NVIDIA Nemotron 3.5 & Sovereign Substrate</span>
            </div>
          </div>
          <div className="live-header-actions">
            <button
              className={`live-icon-btn ${showConnectors ? 'active' : ''}`}
              title={showConnectors ? 'Hide connected tools' : 'View connected MCP servers & tools'}
              onClick={() => setShowConnectors(!showConnectors)}
            >
              <Link2 size={15} />
            </button>
            <button
              className={`live-icon-btn ${voiceEnabled ? 'active' : ''}`}
              title={voiceEnabled ? 'Mute AI voice output' : 'Enable AI voice output'}
              onClick={() => {
                const next = !voiceEnabled;
                setVoiceEnabled(next);
                if (!next) window.speechSynthesis?.cancel();
              }}
            >
              {voiceEnabled ? <Volume2 size={15} /> : <VolumeX size={15} />}
            </button>
            <button
              className={`live-icon-btn ${continuousCapture ? 'active' : ''}`}
              title={continuousCapture ? 'Stop continuous capture' : 'Start continuous capture (Gemini Live)'}
              onClick={toggleContinuousCapture}
            >
              <Radio size={15} />
            </button>
            <button
              className="live-icon-btn"
              title="Clear conversation"
              onClick={() => {
                setMessages([
                  {
                    role: 'assistant',
                    content: "Conversation reset. I'm ready for your next request.",
                    model: 'Threadline Sovereign Substrate',
                  },
                ]);
              }}
            >
              <RotateCcw size={15} />
            </button>
            <button className="live-icon-btn" title="Close" onClick={onClose}>
              <X size={17} />
            </button>
          </div>
        </header>

        {/* Connected Tools & MCP Tray */}
        {showConnectors && (
          <div style={{ padding: '12px 18px', background: '#101712', borderBottom: '1px solid #1f2c22' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ font: '600 8px var(--mono)', color: '#88a88e', letterSpacing: '0.6px' }}>
                CONNECTED MCP SERVERS & APP TOOLS ({allTools.length} AVAILABLE)
              </span>
              <span style={{ fontSize: 8, color: '#68826c' }}>{connectors.length} CONNECTORS ACTIVE</span>
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', maxHeight: 85, overflowY: 'auto' }}>
              {allTools.map((t) => (
                <button
                  key={t.name}
                  onClick={() => handleSendMessage(`Run ${t.name}`)}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 4,
                    padding: '3px 8px',
                    borderRadius: 12,
                    border: '1px solid #26382a',
                    background: '#18241c',
                    color: '#b2ccb6',
                    font: '9px var(--mono)',
                    cursor: 'pointer',
                  }}
                  title={t.description}
                >
                  <Zap size={10} color="#7ccf88" />
                  <span>{t.name}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Gemini Live Visualizer Orb */}
        <section className="live-visualizer-section">
          <div
            className={`live-orb-wrapper ${
              isListening ? 'is-listening' : isSpeaking ? 'is-speaking' : isThinking ? 'is-thinking' : ''
            }`}
            onClick={toggleListening}
            title={isListening ? 'Listening... click to pause' : 'Click to speak'}
          >
            <div className="live-orb-aura" />
            <div className="live-orb-core">
              {isListening ? (
                <Mic size={34} />
              ) : isSpeaking ? (
                <Volume2 size={34} />
              ) : isThinking ? (
                <Sparkles size={34} className="spin" />
              ) : (
                <Bot size={34} />
              )}
            </div>
          </div>

          <div className={`live-status-pill ${isListening ? 'recording' : ''}`}>
            {isListening ? (
              <>
                <span className="live-trigger-dot" style={{ background: '#ff7c6b' }} />
                <span>LISTENING... SPEAK FREELY</span>
              </>
            ) : isSpeaking ? (
              <>
                <span className="live-trigger-dot" style={{ background: '#9be57d' }} />
                <span>SPEAKING...</span>
              </>
            ) : isThinking ? (
              <>
                <span className="live-trigger-dot" style={{ background: '#7ec6f0' }} />
                <span>PROCESSING CONTEXT...</span>
              </>
            ) : continuousCapture ? (
              <>
                <span className="live-trigger-dot" />
                <span>CONTINUOUS CAPTURE ACTIVE · TAP ORB TO TALK</span>
              </>
            ) : (
              <>
                <span className="live-trigger-dot" />
                <span>READY · TAP ORB TO SPEAK OR TYPE BELOW</span>
              </>
            )}
          </div>
        </section>

        {/* ChatGPT Style Messages Feed */}
        <div className="live-messages-scroll">
          {messages.map((msg, i) => (
            <div key={i} className={`live-message-row ${msg.role}`}>
              <div className="live-msg-avatar">{msg.role === 'assistant' ? <Bot size={15} /> : <User size={15} />}</div>
              <div className="live-msg-bubble">
                <div>{msg.content}</div>

                {/* Autonomous Action Badges */}
                {msg.action_executed && (
                  <div className="live-action-badge-card">
                    <div className="live-action-badge-left" style={{ width: '100%' }}>
                      {msg.action_executed.type === 'loop_created' && <Calendar size={14} color="#94d88e" />}
                      {msg.action_executed.type === 'draft_created' && <Zap size={14} color="#e0c068" />}
                      {msg.action_executed.type === 'scam_triaged' && <AlertCircle size={14} color="#e27c6f" />}
                      {msg.action_executed.type === 'tool_executed' && <Terminal size={14} color="#76d68b" />}
                      {msg.action_executed.type === 'tool_synthesized' && <Code size={14} color="#94e077" />}
                      {msg.action_executed.type === 'screen_perceived' && <Radio size={14} color="#7ccff0" />}
                      {msg.action_executed.type === 'device_agent_executed' && <Folder size={14} color="#72dec2" />}
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                          <strong>{msg.action_executed.title || msg.action_executed.tool_name || msg.action_executed.type.replace('_', ' ').toUpperCase()}</strong>
                          {msg.action_executed.connector && (
                            <span style={{ fontSize: 7, font: '600 7px var(--mono)', background: '#25422d', color: '#aee494', padding: '1px 5px', borderRadius: 3 }}>
                              {msg.action_executed.connector}
                            </span>
                          )}
                          {msg.action_executed.rung_used && (
                            <span style={{ fontSize: 7, font: '600 7px var(--mono)', background: '#19332e', color: '#7ce4cf', padding: '1px 5px', borderRadius: 3 }}>
                              {msg.action_executed.rung_used}
                            </span>
                          )}
                          {msg.action_executed.verified && (
                            <span style={{ fontSize: 7, font: '600 7px var(--mono)', background: '#1c3924', color: '#97e88b', padding: '1px 5px', borderRadius: 3 }}>
                              POSTCONDITION VERIFIED
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: 9, opacity: 0.85, marginTop: 2 }}>
                          {msg.action_executed.message || 'Action executed successfully in sovereign workspace.'}
                        </div>
                        {msg.action_executed.output && (
                          <details style={{ marginTop: 6 }}>
                            <summary style={{ cursor: 'pointer', font: '600 8px var(--mono)', color: '#88ab8e' }}>
                              Inspect Result Data
                            </summary>
                            <pre style={{ margin: '4px 0 0', padding: 8, background: '#0e1510', border: '1px solid #1e2e22', borderRadius: 4, font: '8px var(--mono)', color: '#97b89c', maxHeight: 130, overflowY: 'auto' }}>
                              {JSON.stringify(msg.action_executed.output, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </div>
                    {msg.action_executed.draft && (
                      <button
                        className="button button-soft"
                        style={{ fontSize: 8, padding: '3px 8px', alignSelf: 'flex-start' }}
                        onClick={() => copyToClipboard(msg.action_executed.draft, i)}
                      >
                        {copiedId === i ? <Check size={11} /> : <Copy size={11} />}
                        {copiedId === i ? 'Copied' : 'Copy Draft'}
                      </button>
                    )}
                  </div>
                )}

                {msg.model && (
                  <div style={{ fontSize: 7, font: 'var(--mono)', color: '#68826d', marginTop: 4 }}>
                    {msg.model}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isThinking && (
            <div className="live-message-row assistant">
              <div className="live-msg-avatar"><Bot size={15} /></div>
              <div className="live-msg-bubble" style={{ color: '#88a88e', fontStyle: 'italic' }}>
                Reasoning with workspace context...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestion Pills */}
        <div className="live-suggestions-bar">
          {suggestions.map((text, idx) => (
            <button key={idx} className="live-suggestion-pill" onClick={() => handleSendMessage(text)}>
              {text}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <form
          className="live-input-bar"
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
        >
          <input
            ref={inputRef}
            className="live-chat-input"
            placeholder={isListening ? 'Listening to your voice...' : 'Ask anything, capture commitments, or dictate thoughts...'}
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button
            type="button"
            className={`live-mic-btn ${isListening ? 'active' : ''}`}
            onClick={toggleListening}
            title={isListening ? 'Stop listening' : 'Speak'}
          >
            {isListening ? <MicOff size={18} /> : <Mic size={18} />}
          </button>
          <button type="submit" className="live-send-btn" disabled={!input.trim()} title="Send">
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}

// Global Launcher Button for Header / Topbar
export function LiveAssistantTrigger({ onClick, isActive }) {
  return (
    <button
      className={`live-trigger-pill ${isActive ? 'is-active' : ''}`}
      onClick={onClick}
      title="Open Gemini Live & ChatGPT Assistant"
    >
      <span className="live-trigger-dot" />
      <Sparkles size={13} />
      <span>Live Assistant</span>
    </button>
  );
}

