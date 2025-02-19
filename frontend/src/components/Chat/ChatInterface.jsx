import { useState, useEffect, useRef } from 'react';
import './styles.css';
import { 
  Person as PersonIcon, 
  SmartToy as SmartToyIcon, 
  Send as SendIcon,
  AutoAwesome as AutoAwesomeIcon
} from '@mui/icons-material';
import { Tooltip, CircularProgress } from '@mui/material';
import { chatService } from '../../services/api';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Add initial greeting when component mounts
  useEffect(() => {
    console.log('ChatInterface mounted');
    const initialGreeting = {
      content: "Hi! I'm Jessi from SkillUp Teaching Consultancy. How can I help you today?",
      isUser: false,
      source: 'greeting',
      timestamp: new Date().toISOString()
    };
    setMessages([initialGreeting]);
  }, []);

  // Add message logging
  useEffect(() => {
    console.log('Messages updated:', messages);
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      content: input,
      isUser: true,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const data = await chatService.sendMessage(input);
      console.log('Response received:', data);

      const botMessage = {
        content: data.content,
        isUser: false,
        source: data.source,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        content: "An error occurred while sending the message. Please try again.",
        isUser: false,
        source: 'error',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const getSourceIcon = (source) => {
    switch(source) {
      case 'ai':
        return <AutoAwesomeIcon fontSize="small" sx={{ color: '#10B981' }} />;
      case 'faq':
        return <SmartToyIcon fontSize="small" sx={{ color: '#6366F1' }} />;
      case 'greeting':
        return <SmartToyIcon fontSize="small" sx={{ color: '#4ADE80' }} />;
      default:
        return <SmartToyIcon fontSize="small" sx={{ color: '#6366F1' }} />;
    }
  };

  // Add error boundary
  useEffect(() => {
    const handleError = (error) => {
      console.error('Rendering error:', error);
    };

    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);

  return (
    <div className="chat-container">
      <div className="chat-box">
        <div className="chat-header">
          <div className="header-content">
            <div className="header-main">
              <h1 className="header-title">Jessi</h1>
              <div className="online-status">
                <div className="status-dot"></div>
                <span>online</span>
              </div>
            </div>
            {/* <div className="subtitle">Your Educational Journey Guide</div>
            <div className="header-description">
              Expert assistance for courses, admissions, and career guidance
            </div> */}
          </div>
        </div>

        <div className="messages-container">
          {messages.map((message, index) => (
            <div key={index} className={`message-item ${message.isUser ? 'user' : ''}`}>
              <div className={`avatar ${message.isUser ? 'user' : 'bot'}`}>
                {message.isUser ? <PersonIcon /> : <SmartToyIcon />}
              </div>
              <div className="message-bubble">
                <div className="message-content">{message.content}</div>
                {!message.isUser && message.source && (
                  <Tooltip title={`Response from ${message.source}`}>
                    <span className={`source-icon ${message.source}`}>
                      {getSourceIcon(message.source)}
                    </span>
                  </Tooltip>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <input
            className="message-input"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            disabled={loading}
          />
          <button
            className="send-button"
            onClick={handleSend}
            disabled={loading}
          >
            {loading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              <>
                Send
                <SendIcon />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface; 