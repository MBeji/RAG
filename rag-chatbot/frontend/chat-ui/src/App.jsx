// src/App.jsx
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios'; // Used for file uploads

// Constants
const BACKEND_URL = 'http://localhost:8000'; // URL for the backend API
const CHAT_HISTORY_KEY = 'ragChatHistory'; // Key for storing chat history in localStorage

// Initial message to display when the chat is empty or newly loaded
const initialWelcomeMessage = { 
  id: 'initial_bot_msg', 
  type: 'bot', 
  text: 'Welcome! Upload a document and ask questions.' 
};

/**
 * Main application component for the RAG Chatbot.
 * Handles chat interactions, file uploads, drag-and-drop, and conversation history.
 */
function App() {
  // State for the chat log, initialized from localStorage or with a welcome message
  const [chatLog, setChatLog] = useState(() => {
    try {
      const storedHistory = localStorage.getItem(CHAT_HISTORY_KEY);
      if (storedHistory) {
        const parsedHistory = JSON.parse(storedHistory);
        return Array.isArray(parsedHistory) && parsedHistory.length > 0 
               ? parsedHistory 
               : [initialWelcomeMessage];
      }
    } catch (error) {
      console.error("Error loading chat history from localStorage:", error);
    }
    return [initialWelcomeMessage];
  });

  // State for the current message being typed by the user
  const [message, setMessage] = useState('');
  // State for the currently selected file for upload
  const [selectedFile, setSelectedFile] = useState(null);
  // State to indicate if a file upload is in progress
  const [isUploading, setIsUploading] = useState(false);
  // State for the file upload progress percentage (0-100)
  const [uploadProgressPercent, setUploadProgressPercent] = useState(0);
  // State for displaying status messages related to file uploads
  const [uploadStatus, setUploadStatus] = useState('');
  // State to indicate if the bot is currently processing a chat message
  const [isBotThinking, setIsBotThinking] = useState(false);
  // State to manage visual feedback when dragging a file over the drop zone
  const [isDraggingOver, setIsDraggingOver] = useState(false);

  // Ref to the chat log container for automatic scrolling
  const chatLogRef = useRef(null);

  // Effect to scroll to the bottom of the chat log when new messages are added
  useEffect(() => {
    if (chatLogRef.current) {
      chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
    }
  }, [chatLog]);

  // Effect to save the chat history to localStorage whenever the chatLog state changes
  useEffect(() => {
    try {
      localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(chatLog));
    } catch (error) {
      console.error("Error saving chat history to localStorage:", error);
    }
  }, [chatLog]);

  /**
   * Handles clearing the chat history from localStorage and resetting the chat log.
   */
  const handleClearChat = () => {
    if (window.confirm("Are you sure you want to clear the chat history? This action cannot be undone.")) {
      localStorage.removeItem(CHAT_HISTORY_KEY);
      setChatLog([initialWelcomeMessage]); // Reset to initial state
      setUploadStatus("Chat history cleared."); 
    }
  };
  
  /**
   * Handles sending a user's message to the backend and processing the streamed response.
   */
  const handleSendMessage = async () => {
    if (message.trim() === '' || isBotThinking) return; // Prevent sending empty or while bot is busy

    const userMessageText = message;
    const userMessage = { id: `user_${Date.now()}`, type: 'user', text: userMessageText };
    
    // Add user message to chat log and clear input
    setChatLog(prevLog => [...prevLog, userMessage]);
    setMessage('');
    setIsBotThinking(true); // Indicate bot is processing

    // Create a placeholder for the bot's response message to which tokens will be appended
    const botMessageId = `bot_${Date.now()}`;
    setChatLog(prevLog => [...prevLog, { id: botMessageId, type: 'bot', text: '...' }]); 

    try {
      // Fetch API call to the backend's /chat endpoint for streaming response
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json', 
          'Accept': 'text/event-stream' // Crucial for Server-Sent Events (SSE)
        },
        body: JSON.stringify({ query: userMessageText }), // Send only query; backend uses defaults for other params
      });

      if (!response.ok) { // Handle HTTP errors (e.g., 4xx, 5xx)
        const errorData = await response.json().catch(() => ({ detail: "Unknown server error during stream setup." }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      // Process the streamed response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = ''; // Buffer for incoming chunks
      let currentBotText = ''; // Accumulates text for the 'token' part of the response
      let sourcesText = '';    // Stores formatted sources text

      while (true) {
        const { done, value } = await reader.read();
        if (done) break; // Stream finished

        buffer += decoder.decode(value, { stream: true }); // Append chunk to buffer
        
        let eolIndex; // End-of-line index for SSE message separation (\n\n)
        // Process all complete SSE messages in the buffer
        while ((eolIndex = buffer.indexOf('\n\n')) !== -1) {
            const line = buffer.substring(0, eolIndex).trim(); // Get one SSE message
            buffer = buffer.substring(eolIndex + 2); // Remove processed message from buffer

            if (line.startsWith("data: ")) { // Check for SSE data prefix
                const jsonData = line.substring(5); // Extract JSON payload
                try {
                    const event = JSON.parse(jsonData); // Parse JSON payload
                    
                    // Handle 'sources' event: update chat log with source information
                    if (event.type === 'sources') {
                        sourcesText = "Sources:\n" + event.data.map(
                            s => `- ${s.source_file} (chunk ${s.chunk_number}, dist: ${s.distance?.toFixed(4) ?? 'N/A'})`
                        ).join('\n');
                        // Update the bot message placeholder to show sources, then '...' for incoming tokens
                        setChatLog(prev => prev.map(msg => 
                            msg.id === botMessageId 
                            ? { ...msg, text: `${sourcesText}\n\n...` } 
                            : msg
                        ));
                    } 
                    // Handle 'token' event: append token to current bot text
                    else if (event.type === 'token') {
                        currentBotText += event.data;
                        // Update chat log with accumulated tokens, prepending sources if available
                        // Note: Frequent setChatLog calls for each token enable the streaming effect.
                        setChatLog(prev => prev.map(msg => 
                            msg.id === botMessageId 
                            ? { ...msg, text: sourcesText ? `${sourcesText}\n\n${currentBotText}` : currentBotText } 
                            : msg
                        ));
                    } 
                    // Handle 'error' event from backend (e.g., no documents found, LLM error)
                    else if (event.type === 'error') {
                        const errorMsg = event.data.llm_response || "An error occurred during streaming.";
                        setChatLog(prev => prev.map(msg => 
                            msg.id === botMessageId 
                            ? { ...msg, text: errorMsg, type: 'error' } // Mark message as error type
                            : msg
                        ));
                        setIsBotThinking(false); // Stop thinking indicator
                        return; // End processing for this message
                    } 
                    // Handle 'end' event: stream finished successfully
                    else if (event.type === 'end') {
                        // Final update to ensure the complete message is displayed without '...'
                        setChatLog(prev => prev.map(msg => 
                            msg.id === botMessageId 
                            ? { ...msg, text: sourcesText ? `${sourcesText}\n\n${currentBotText}` : currentBotText } 
                            : msg
                        ));
                        setIsBotThinking(false); // Stop thinking indicator
                        return; // End processing for this message
                    }
                } catch (e) { 
                    console.error("Error parsing SSE event:", e, "Raw data:", jsonData);
                    setChatLog(prev => prev.map(msg => 
                        msg.id === botMessageId 
                        ? { ...msg, text: "Error parsing stream data. See console for details.", type: 'error' } 
                        : msg
                    ));
                    setIsBotThinking(false); 
                    return; 
                }
            }
        }
      }
      // If stream ends abruptly without an 'end' or 'error' event
      if (isBotThinking) { 
          setIsBotThinking(false);
          // Ensure final text is displayed if placeholder '...' was still visible
          setChatLog(prev => prev.map(msg => 
              msg.id === botMessageId && msg.text.endsWith('...')
              ? { ...msg, text: sourcesText ? `${sourcesText}\n\n${currentBotText}` : currentBotText } 
              : msg
          ));
      }
    } catch (error) { // Catch errors from fetch() or initial response handling
      console.error("Chat API fetch error:", error);
      setChatLog(prev => prev.map(msg => 
        msg.id === botMessageId 
        ? { ...msg, text: `Error: ${error.message}`, type: 'error' } // Mark message as error type
        : msg
      ));
      setIsBotThinking(false); // Ensure thinking indicator is reset
    }
  };

  /**
   * Handles file selection via the file input dialog.
   */
  const handleFileChange = (event) => {
    const file = event.target.files ? event.target.files[0] : null;
    if (file) {
      setSelectedFile(file);
      setUploadStatus(`Selected file: ${file.name}`);
      setUploadProgressPercent(0); // Reset progress for new file selection
    } 
    // Not clearing selectedFile or uploadStatus if dialog is cancelled,
    // to preserve a previously selected/dragged file.
  };
  
  /**
   * Handles drag-over event for the drop zone.
   */
  const handleDragOver = (event) => {
    event.preventDefault(); // Necessary to allow dropping
    setIsDraggingOver(true); // Set state for visual feedback
  };

  /**
   * Handles drag-leave event for the drop zone.
   */
  const handleDragLeave = (event) => {
    event.preventDefault();
    setIsDraggingOver(false); // Reset visual feedback
  };

  /**
   * Handles file drop event onto the drop zone.
   */
  const handleDrop = (event) => {
    event.preventDefault();
    setIsDraggingOver(false); // Reset visual feedback
    const files = event.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      const allowedTypes = [".pdf", ".txt", ".docx", ".md", ".csv"];
      const fileExtension = "." + file.name.split('.').pop().toLowerCase();

      // Validate file type
      if (!allowedTypes.includes(fileExtension)) {
          setUploadStatus(`File type ${fileExtension} not allowed. Permitted: ${allowedTypes.join(', ')}.`);
          setSelectedFile(null); // Clear selection
          if (document.getElementById('fileInput')) { document.getElementById('fileInput').value = ""; } // Reset file input
          return;
      }
      setSelectedFile(file); // Set the dropped file as selected
      setUploadStatus(`Selected file: ${file.name} (dragged)`);
      setUploadProgressPercent(0); // Reset progress
      // Clear the file input visually, as the state now holds the dragged file
      if (document.getElementById('fileInput')) { document.getElementById('fileInput').value = ""; }
    }
  };

  /**
   * Handles uploading the selected file to the backend.
   */
  const handleFileUpload = async () => {
     if (!selectedFile) { 
       setUploadStatus("Please select a file first."); 
       return; 
     }

    const formData = new FormData();
    formData.append('file', selectedFile);
    // Optionally, append other form data like 'embedding_model_name' if UI allows selection
    // formData.append('embedding_model_name', 'your_chosen_model'); 
    
    setIsUploading(true); // Set uploading state for UI feedback
    setUploadProgressPercent(0); // Reset progress for new upload
    setUploadStatus(`Uploading "${selectedFile.name}"...`);

    try {
      // Post file to backend /upload endpoint using axios for progress tracking
      const response = await axios.post(`${BACKEND_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) { 
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgressPercent(percentCompleted);
          }
        },
      });
      // Update status with success message from backend
      setUploadStatus(response.data.message || `File "${selectedFile.name}" uploaded successfully.`);
      // Add a confirmation message to the chat log
      setChatLog(prevLog => [...prevLog, { 
        id: `bot_upload_status_${Date.now()}`, 
        type: 'bot', 
        text: `Successfully processed "${selectedFile.name}" (model: ${response.data.embedding_model_name}). You can now ask questions about it.` 
      }]);
    } catch (error) { // Handle upload errors
      console.error("File upload error:", error);
      let errMsg = `Error uploading "${selectedFile.name}".`;
      if (error.response?.data?.detail) { // Use detailed error from backend if available
        errMsg += ` Server: ${error.response.data.detail}`;
      } else if (error.message) {
        errMsg += ` Details: ${error.message}`;
      }
      setUploadStatus(errMsg); // Display error in upload status area
    } finally { // Reset states after upload attempt
      setIsUploading(false);
      setSelectedFile(null); // Clear file selection
      // Do not reset uploadProgressPercent here, so user can see final state if needed
      // Reset file input field visually
      if (document.getElementById('fileInput')) { 
        document.getElementById('fileInput').value = "";
      }
    }
  };

  // JSX for the component
  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center p-4 font-sans">
      {/* Header Section */}
      <header className="w-full max-w-3xl mx-auto mb-2 flex justify-between items-center">
        <h1 className="text-4xl font-bold text-center text-blue-400 flex-grow">RAG Chatbot</h1>
        <button 
          onClick={handleClearChat} 
          title="Clear chat history"
          className="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-md text-sm transition-colors duration-150"
        >
          Clear Chat
        </button>
      </header>
      
      {/* Chat Messages Display Area */}
      <div 
        ref={chatLogRef} 
        className="w-full max-w-3xl h-96 bg-gray-800 rounded-lg p-4 overflow-y-auto mb-4 shadow-xl scroll-smooth"
        aria-live="polite" // Announce new messages to screen readers
      >
        {chatLog.map((entry) => ( 
          <div 
            key={entry.id} 
            className={`mb-3 p-3 rounded-lg max-w-[85%] break-words ${
              entry.type === 'user' ? 'bg-blue-600 ml-auto' : 
              entry.type === 'error' ? 'bg-red-700 mr-auto' : // Style for error messages
              'bg-gray-700 mr-auto' // Default bot message style
            }`}
          >
            <p className="text-sm whitespace-pre-wrap">{entry.text}</p>
          </div>
        ))}
      </div>
      
      {/* Upload Status and Progress Bar Area */}
      {uploadStatus && ( // Only show if there's an upload status message
        <div 
          id="uploadStatusArea" // Added ID for aria-describedby
          className="w-full max-w-3xl p-3 mb-4 bg-gray-700 rounded-lg shadow-md text-center"
        >
          <p className="text-sm text-gray-300 mb-1">{uploadStatus}</p>
          {isUploading && ( // Show progress bar only when uploading
            <div className="w-full bg-gray-600 rounded-full h-2.5 dark:bg-gray-500">
              <div 
                className="bg-blue-500 h-2.5 rounded-full transition-all duration-100 ease-linear" 
                style={{ width: `${uploadProgressPercent}%` }}
                role="progressbar"
                aria-valuenow={uploadProgressPercent}
                aria-valuemin="0"
                aria-valuemax="100"
                aria-label="Upload progress"
              ></div>
            </div>
          )}
        </div>
      )}

      {/* Message Input Section */}
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
            aria-label="Chat message input"
          />
          <button 
            onClick={handleSendMessage} 
            disabled={isBotThinking || message.trim() === ''} 
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold p-3 rounded-r-md transition-colors duration-150 disabled:opacity-50"
            aria-label="Send chat message"
          >
            {isBotThinking ? '...' : 'Send'}
          </button>
        </div>
      </div>
      
      {/* File Upload Section with Drag and Drop */}
      <div className="w-full max-w-3xl p-4 bg-gray-800 rounded-lg shadow-xl">
        <h2 className="text-xl font-semibold mb-3 text-center text-blue-400">Upload Documents</h2>
        {/* Drag and Drop Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          role="button" // Semantically a button-like region for interaction
          tabIndex={0} // Make it focusable
          aria-label="Drag and drop file upload zone"
          className={`flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-lg cursor-pointer
                      ${isDraggingOver ? 'border-blue-500 bg-gray-700' : 'border-gray-600 hover:border-gray-500 hover:bg-gray-750'}
                      transition-colors duration-150 ease-in-out mb-4`}
        >
          <p className="text-gray-400 text-center">
            {isDraggingOver ? "Release to drop file" : "Drag & drop a file here, or click below to select"}
          </p>
        </div>
        {/* Traditional File Input and Upload Button */}
        <div className="flex flex-col items-center space-y-3">
          <label htmlFor="fileInput" className="sr-only">Choose file to upload</label>
          <input 
            id="fileInput" 
            type="file" 
            onChange={handleFileChange} 
            disabled={isUploading} 
            className="block w-full max-w-xs text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 disabled:opacity-50" 
            accept=".pdf,.txt,.docx,.md,.csv"
            aria-describedby="uploadStatusArea" // Link to status updates
          />
          <button 
            onClick={handleFileUpload} 
            disabled={!selectedFile || isUploading} 
            className="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded-md transition-colors duration-150 disabled:opacity-50"
          >
            {isUploading ? `Uploading ${uploadProgressPercent}%...` : 'Upload File'}
          </button>
        </div>
      </div>
    </div>
  );
}
export default App;
```
