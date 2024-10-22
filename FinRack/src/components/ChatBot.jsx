// src/components/ChatBot.jsx
import React, { useState, useEffect } from 'react';
import { GoogleGenerativeAI } from "@google/generative-ai";

const ChatBot = () => {
  const [messages, setMessages] = useState([]); // State for chat messages
  const [newMessage, setNewMessage] = useState(''); // State for new message input
  const [chatSession, setChatSession] = useState(null); // State for chat session
  const [isResizing, setIsResizing] = useState(false); // State for resizing
  const [size, setSize] = useState({ width: 400, height: 500 }); // Initial size of the chatbot
  const [isVisible, setIsVisible] = useState(true); // State for visibility

  const generationConfig = {
    temperature: 0.7,
    topP: 0.9,
    topK: 40,
    maxOutputTokens: 150,
    responseMimeType: "text/plain",
  };

  useEffect(() => {
    const apiKey = 'AIzaSyCRTKY1MItjr-xCVB41ptrJqlUTr5RX0o4'; // Your provided API key
    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

    // Start a chat session
    const session = model.startChat({ generationConfig, history: [] });
    setChatSession(session);
  }, []);

  const handleSendMessage = async (e) => {
    e.preventDefault(); // Prevent default form submission
    if (!newMessage.trim() || !chatSession) return; // Don't send empty messages

    // Add user message to the chat
    const userMessage = { sender: 'User', message: newMessage };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setNewMessage(''); // Clear the input field

    // Send message to the chat session
    try {
      const result = await chatSession.sendMessage(newMessage); // Send the new message
      const botMessage = { sender: 'ChatBot', message: result.response.text().trim() }; // Get bot response
      setMessages((prevMessages) => [...prevMessages, botMessage]); // Add bot response to chat
    } catch (error) {
      const errorMessage = { sender: 'ChatBot', message: 'Error: ' + error.message };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    }
  };

  const handleMouseDown = (e, direction) => {
    setIsResizing(direction);
    e.preventDefault();
  };

  const handleMouseMove = (e) => {
    if (isResizing) {
      const newWidth = Math.max(300, e.clientX - e.target.getBoundingClientRect().left);
      const newHeight = Math.max(300, e.clientY - e.target.getBoundingClientRect().top);
      setSize({ width: newWidth, height: newHeight });
    }
  };

  const handleMouseUp = () => {
    setIsResizing(false);
  };

  const handleToggleVisibility = () => {
    setIsVisible((prev) => !prev);
  };

  return (
    <div
      className={`fixed bottom-0 right-0 transition-transform transform ${isVisible ? 'translate-y-0' : 'translate-y-full'} bg-gray-100 rounded-lg shadow-lg border border-gray-300`}
      style={{ width: `${size.width}px`, height: `${size.height}px`, zIndex: 1000 }}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      <div className="flex justify-between items-center p-2 border-b">
        <h2 className="text-lg font-semibold text-gray-800">Chat with Gemini</h2>
        <button onClick={handleToggleVisibility} className="text-red-500">
          &times;
        </button>
      </div>
      <div className="flex-1 overflow-y-auto mb-4 p-2">
        {messages.map((msg, index) => (
          <div key={index} className={`my-2 p-2 rounded-lg ${msg.sender === 'User' ? 'bg-blue-200 text-gray-800 self-end' : 'bg-green-200 text-gray-800 self-start'}`}>
            <strong style={{ fontSize: '0.9rem' }}>{msg.sender}:</strong>
            <p style={{ fontSize: '0.9rem' }}>{msg.message}</p>
          </div>
        ))}
      </div>
      <form onSubmit={handleSendMessage} className="flex">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type your message..."
          className="border border-gray-300 rounded-md p-2 flex-grow mr-2"
          style={{ fontSize: '0.9rem' }}
        />
        <button type="submit" className="bg-blue-500 text-white p-2 rounded-md">Send</button>
      </form>
      {/* Resizing handles */}
      <div className="resize-handle bottom-right" onMouseDown={(e) => handleMouseDown(e, 'bottom-right')}></div>
      <div className="resize-handle bottom-left" onMouseDown={(e) => handleMouseDown(e, 'bottom-left')}></div>
      <div className="resize-handle top-right" onMouseDown={(e) => handleMouseDown(e, 'top-right')}></div>
      <div className="resize-handle top-left" onMouseDown={(e) => handleMouseDown(e, 'top-left')}></div>
    </div>
  );
};

export default ChatBot;
