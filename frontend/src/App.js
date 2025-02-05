import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [liveConversation, setLiveConversation] = useState([]);

  // Fetch chat history when the app loads
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:5000/history');
        setChatHistory(response.data);
      } catch (error) {
        console.error('Error fetching chat history:', error);
      }
    };
    fetchHistory();
  }, []);

  const handleSendMessage = async () => {
    if (message.trim()) {
      setLiveConversation(prev => [...prev, { type: 'user', text: message }]);
      setMessage(''); // Clear the input field

      try {
        const response = await axios.post('http://127.0.0.1:5000/chat', {
          message: message,
        });

        if (response.data.error) {
          setLiveConversation(prev => [
            ...prev,
            { type: 'error', text: 'Error: ' + response.data.error },
          ]);
        } else {
          setLiveConversation(prev => [
            ...prev,
            { type: 'bot', text: response.data.message || 'No response from bot' },
          ]);
        }
      } catch (error) {
        setLiveConversation(prev => [
          ...prev,
          { type: 'error', text: 'Failed to communicate with the backend' },
        ]);
      }
    }
  };

  return (
    <div className="App">
      <div className="left-side">
        <h2>Chat History</h2>
        <div className="history-box">
          {chatHistory.map((chat, index) => (
            <div key={index} className={chat.user_message ? 'user-message' : 'bot-message'}>
              {chat.user_message || chat.bot_response}
            </div>
          ))}
        </div>
      </div>
      <div className="right-side">
        <h1>Gemini Chatbot</h1>
        <div className="chat-box">
          {liveConversation.map((chat, index) => (
            <div key={index} className={chat.type === 'user' ? 'user-message' : chat.type === 'bot' ? 'bot-message' : 'error-message'}>
              {chat.text}
            </div>
          ))}
        </div>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type a message..."
        />
        <button onClick={handleSendMessage}>Send</button>
      </div>
    </div>
  );
}

export default App;
