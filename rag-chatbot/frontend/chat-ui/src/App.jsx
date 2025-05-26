// src/App.jsx
import React, { useState, useEffect, useRef } from 'react'; // Added useEffect, useRef
import axios from 'axios';

const BACKEND_URL = 'http://localhost:8000';

function App() {
  const [message, setMessage] = useState('');
  const [chatLog, setChatLog] = useState([
    { id: 'initial_bot_msg', type: 'bot', text: 'Welcome! Upload a document and ask questions.' },
  ]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isBotThinking, setIsBotThinking] = useState(false); // For chat response loading

  // Ref for scrolling chat log
  const chatLogRef = useRef(null);

  useEffect(() => {
    // Scroll to bottom of chat log when new messages are added
    if (chatLogRef.current) {
      chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
    }
  }, [chatLog]);

  const handleSendMessage = async () => {
    if (message.trim() === '') return;

    const userMessage = { id: `user_${Date.now()}`, type: 'user', text: message };
    const botLoadingMessage = { id: `bot_loading_${Date.now()}`, type: 'bot', text: 'Thinking...' };

    setChatLog(prevLog => [...prevLog, userMessage, botLoadingMessage]);
    const currentMessage = message; // Capture message before clearing
    setMessage('');
    setIsBotThinking(true);

    try {
      const response = await axios.post(`${BACKEND_URL}/chat`, {
        query: currentMessage, // Use captured message
        top_k: 3, // Example, make configurable if needed
        model_name: "llama2" // Example, make configurable if needed
      });

      const botResponse = response.data;
      let botMessageText = botResponse.llm_response || "Sorry, I couldn't get a response.";
      
      if (botResponse.sources && botResponse.sources.length > 0) {
        const sourcesText = botResponse.sources.map(
          s => `- ${s.source_file} (chunk ${s.chunk_number})`
        ).join('\n');
        botMessageText += `\n\n**Sources:**\n${sourcesText}`;
      }
      
      const actualBotMessage = { id: `bot_${Date.now()}`, type: 'bot', text: botMessageText };
      
      setChatLog(prevLog => prevLog.filter(msg => msg.id !== botLoadingMessage.id).concat(actualBotMessage) );

    } catch (error) {
      console.error("Chat API error:", error);
      let errorMessageText = "Sorry, something went wrong while fetching the response.";
      if (error.response && error.response.data && error.response.data.detail) {
        errorMessageText += ` Server said: ${error.response.data.detail}`;
      } else if (error.message) {
        errorMessageText += ` Details: ${error.message}`;
      }
      const errorBotMessage = { id: `bot_error_${Date.now()}`, type: 'bot', text: errorMessageText };
      setChatLog(prevLog => prevLog.filter(msg => msg.id !== botLoadingMessage.id).concat(errorBotMessage) );
    } finally {
      setIsBotThinking(false);
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setUploadStatus(`Selected file: ${file.name}`);
    } else {
      setSelectedFile(null);
      setUploadStatus('');
    }
  };

  const handleFileUpload = async () => {
     if (!selectedFile) {
      setUploadStatus("Please select a file first.");
      return;
    }
    const formData = new FormData();
    formData.append('file', selectedFile);
    setIsUploading(true);
    setUploadStatus(`Uploading "${selectedFile.name}"...`);
    try {
      const response = await axios.post(`${BACKEND_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setUploadStatus(response.data.message || `File "${selectedFile.name}" uploaded successfully. Chunks: ${response.data.total_chunks || 'N/A'}`);
      setChatLog(prevLog => [...prevLog, { id: `bot_upload_status_${Date.now()}`, type: 'bot', text: `Successfully processed "${selectedFile.name}". You can now ask questions about it.` }]);
    } catch (error) {
      console.error("File upload error:", error);
      let errorMessage = `Error uploading file "${selectedFile.name}".`;
      if (error.response && error.response.data && error.response.data.detail) {
        errorMessage += ` Server said: ${error.response.data.detail}`;
      } else if (error.message) {
        errorMessage += ` Details: ${error.message}`;
      }
      setUploadStatus(errorMessage);
    } finally {
      setIsUploading(false);
      setSelectedFile(null);
      if (document.getElementById('fileInput')) { 
        document.getElementById('fileInput').value = "";
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center p-4 font-sans">
      <header className="w-full max-w-3xl mx-auto mb-6">
        <h1 className="text-4xl font-bold text-center text-blue-400">RAG Chatbot</h1>
      </header>

      {/* Chat Messages Area */}
      <div ref={chatLogRef} className="w-full max-w-3xl h-96 bg-gray-800 rounded-lg p-4 overflow-y-auto mb-4 shadow-xl scroll-smooth">
        {chatLog.map((entry) => ( 
          <div key={entry.id} className={`mb-3 p-3 rounded-lg max-w-[85%] break-words whitespace-pre-wrap ${ 
            entry.type === 'user' ? 'bg-blue-600 ml-auto' : 'bg-gray-700 mr-auto'
          }`}>
            <p className="text-sm">{entry.text}</p>
          </div>
        ))}
      </div>
      
      {uploadStatus && (
        <div className="w-full max-w-3xl p-3 mb-4 bg-gray-700 rounded-lg shadow-md text-center">
          <p className="text-sm text-gray-300">{uploadStatus}</p>
        </div>
      )}

      {/* Message Input Area */}
      <div className="w-full max-w-3xl p-4 bg-gray-800 rounded-lg shadow-xl mb-6">
        <div className="flex items-center">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !isBotThinking && handleSendMessage()} 
            placeholder={isBotThinking ? "Bot is thinking..." : "Type your message..."}
            className="flex-grow p-3 bg-gray-700 border border-gray-600 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
            disabled={isBotThinking}
          />
          <button
            onClick={handleSendMessage}
            disabled={isBotThinking || message.trim() === ''}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold p-3 rounded-r-md transition duration-150 disabled:opacity-50"
          >
            {isBotThinking ? '...' : 'Send'}
          </button>
        </div>
      </div>
      
      {/* File Upload Section */}
       <div className="w-full max-w-3xl p-4 bg-gray-800 rounded-lg shadow-xl">
        <h2 className="text-xl font-semibold mb-3 text-center text-blue-400">Upload Documents</h2>
        <div className="flex flex-col items-center space-y-3">
          <input
            id="fileInput" 
            type="file"
            onChange={handleFileChange}
            disabled={isUploading}
            className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 disabled:opacity-50"
            accept=".pdf,.txt,.docx,.md,.csv"
          />
          <button
            onClick={handleFileUpload}
            disabled={!selectedFile || isUploading}
            className="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded-md transition duration-150 disabled:opacity-50"
          >
            {isUploading ? 'Uploading...' : 'Upload File'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
