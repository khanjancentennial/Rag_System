// // src/components/QueryPage/QueryPage.js
// import React, { useState } from 'react';
// import { useParams } from 'react-router-dom';
// import axios from 'axios';
// import './querypage.css';
// import { ToastContainer, toast } from 'react-toastify';
// import 'react-toastify/dist/ReactToastify.css';

// const apiBaseUrl = process.env.REACT_APP_API_BASE_URL;

// function QueryPage() {
//   const { fileId, fileName } = useParams();
//   const [query, setQuery] = useState('');
//   const [response, setResponse] = useState('');
//   const [loading, setLoading] = useState(false);

//   const handleQueryChange = (event) => {
//     setQuery(event.target.value);
//   };

//   const handleSubmit = async () => {
//     try {
//       setLoading(true);
//       const token = localStorage.getItem('token');
//       const requestBody = {
//         query: query,
//         filename: fileName,
//       };
//       const apiResponse = await axios.post(
//         `${apiBaseUrl}query/`,
//         requestBody,
//         {
//           headers: {
//             Authorization: `Bearer ${token}`,
//           },
//         }
//       );
  
//       // Extract and clean the content text
//       if (apiResponse.data.answer) {
//         let content = apiResponse.data.answer;
//         content = content.replace(/\\n/g, '\n');
//         content = content.replace(/\\t/g, '\t');
//         content = content.replace(/\\'/g, "'");
//         content = content.replace(/\\"/g, '"');
//         setResponse(content);
//       } else {
//         setResponse("Answer not found or in unexpected format.");
//       }
//       setLoading(false);
//     } catch (error) {
//       console.error('Query failed:', error);
//       setLoading(false);
//       toast.error('Failed to get answer.');
//     }
//   };

//   return (
//     <div className="query-page-container">
//       <ToastContainer />
//       <h2>Ask a Question from {fileName} file</h2>
//       <div className="query-input">
//         <textarea
//           value={query}
//           onChange={handleQueryChange}
//           placeholder="Enter your question..."
//           disabled={loading}
//         />
//         <button onClick={handleSubmit} disabled={loading}>
//           Ask
//         </button>
//       </div>
//       {loading && <div className="loader">Loading...</div>}
//       {response && (
//         <div className="response-output">
//           <h3>Answer:</h3>
//           <p>{response}</p>
//         </div>
//       )}
//     </div>
//   );
// }

// export default QueryPage;


// src/components/Chat/Chat.js
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './querypage.css';

const apiBaseUrl = process.env.REACT_APP_API_BASE_URL;

function Chat({ fileName }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [displayedFileName, setDisplayedFileName] = useState(null);
  const isInitialRender = useRef(true);

  useEffect(() => {
    if (fileName !== displayedFileName) {
      if (isInitialRender.current) {
        setMessages((prevMessages) => [
          ...prevMessages,
          { text: `--- File selected: ${fileName} ---`, sender: 'system' },
        ]);
        isInitialRender.current = false;
      } else if (displayedFileName !== null) {
        setMessages((prevMessages) => [
          ...prevMessages,
          { text: `--- File changed to: ${fileName} ---`, sender: 'system' },
        ]);
      }
      setDisplayedFileName(fileName);
    }
  }, [fileName, displayedFileName]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const newMessage = { text: input, sender: 'user' };
    setMessages((prevMessages) => [...prevMessages, newMessage]);
    setInput('');

    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${apiBaseUrl}query/`,
        { query: input, filename: fileName },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMessages((prevMessages) => [
        ...prevMessages,
        { text: response.data.answer, sender: 'ai' },
      ]);
      setLoading(false);
    } catch (error) {
      console.error('Error sending message:', error);
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.sender}`}>
            {message.text}
          </div>
        ))}
        {loading && <div className="loader">Loading...</div>}
      </div>
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}

export default Chat;