// // src/components/Home/Home.js
// import React, { useState, useEffect } from 'react';
// import { useNavigate } from 'react-router-dom';
// import axios from 'axios';
// import './home.css';
// import { ToastContainer, toast } from 'react-toastify';
// import 'react-toastify/dist/ReactToastify.css';
// import { FaEdit, FaTrash, FaSignOutAlt } from 'react-icons/fa'; // Import icons
// import Header from '../Header/header'; 


// const apiBaseUrl = process.env.REACT_APP_API_BASE_URL;

// function Home() {
//   const [files, setFiles] = useState([]);
//   const [selectedFile, setSelectedFile] = useState(null);
//   const [query, setQuery] = useState('');
//   const [showUploadOptions, setShowUploadOptions] = useState(false);
//   const navigate = useNavigate();
//   const [editDialog, setEditDialog] = useState({ open: false, fileId: null, fileName: '' });
//   const [editSelectedFile, setEditSelectedFile] = useState(null);
//   const [loading, setLoading] = useState(false);
//   const [deleteDialog, setDeleteDialog] = useState({ open: false, fileId: null, fileName: '' });

//   useEffect(() => {
//     fetchFiles();
//   }, []);

//   const fetchFiles = async () => {
//     try {
//       setLoading(true);
//       const token = localStorage.getItem('token');
//       const response = await axios.get(`${apiBaseUrl}all-files/`, {
//         headers: { Authorization: `Bearer ${token}` },
//       });
//       setFiles(response.data.Data);
//       setLoading(false);
//     } catch (error) {
//       console.error('Failed to fetch files:', error);
//       setLoading(false);
//       if (files.length > 0) {
//         toast.error('Failed to fetch files.');
//       }
//     }
//   };

//   const handleFileChange = (event) => {
//     setSelectedFile(event.target.files[0]);
//   };

//   const handleUpload = async () => {
//     if (!selectedFile) return;
//     try {
//       setLoading(true);
//       const token = localStorage.getItem('token');
//       const formData = new FormData();
//       formData.append('files', selectedFile);
//       await axios.post(`${apiBaseUrl}upload/`, formData, {
//         headers: {
//           Authorization: `Bearer ${token}`,
//           'Content-Type': 'multipart/form-data',
//         },
//       });
//       fetchFiles();
//       setShowUploadOptions(false);
//       setLoading(false);
//       toast.success('File uploaded successfully.');
//     } catch (error) {
//       console.error('Upload failed:', error);
//       setLoading(false);
//       toast.error('Upload failed.');
//     }
//   };

//   const handleDelete = (fileId, fileName) => {
//     setDeleteDialog({ open: true, fileId, fileName });
//   };

//   const confirmDelete = async () => {
//     try {
//       setLoading(true);
//       const token = localStorage.getItem('token');
//       await axios.delete(`${apiBaseUrl}delete-file/${deleteDialog.fileId}/`, {
//         headers: { Authorization: `Bearer ${token}` },
//       });

//       // Update files state immediately
//       setFiles(files.filter(file => file.id !== deleteDialog.fileId));

//       setLoading(false);
//       setDeleteDialog({ open: false, fileId: null, fileName: '' });
//       toast.success('File deleted successfully.');

//       // Refresh the list after the state update
//       fetchFiles();
//     } catch (error) {
//       console.error('Delete failed:', error);
//       setLoading(false);
//       setDeleteDialog({ open: false, fileId: null, fileName: '' });
//       toast.error('Delete failed.');
//     }
//   };

//   const cancelDelete = () => {
//     setDeleteDialog({ open: false, fileId: null, fileName: '' });
//   };

//   const handleEdit = (fileId, fileName) => {
//     setEditDialog({ open: true, fileId, fileName });
//   };

//   const handleEditFileChange = (event) => {
//     setEditSelectedFile(event.target.files[0]);
//   };

//   const handleEditSubmit = async () => {
//     if (!editSelectedFile) return;
//     try {
//       setLoading(true);
//       const token = localStorage.getItem('token');
//       const formData = new FormData();
//       formData.append('file', editSelectedFile);
//       await axios.put(`${apiBaseUrl}update-file/${editDialog.fileId}/`, formData, {
//         headers: {
//           Authorization: `Bearer ${token}`,
//           'Content-Type': 'multipart/form-data',
//         },
//       });
//       setEditDialog({ open: false, fileId: null, fileName: '' });
//       fetchFiles();
//       setLoading(false);
//       toast.success('File edited successfully.');
//     } catch (error) {
//       console.error('Edit failed:', error);
//       setLoading(false);
//       setEditDialog({ open: false, fileId: null, fileName: '' });
//       toast.error('Edit failed.');
//     }
//   };

//   const handleEditCancel = () => {
//     setEditDialog({ open: false, fileId: null, fileName: '' });
//   };

//   const handleSearch = () => {
//     console.log(`Search query: ${query}`);
//   };

//   const handleLogout = () => {
//     localStorage.clear();
//     navigate('/');
//   };

//   const handleFileClick = (fileId, fileName) => {
//     const fileNameWithoutExtension = fileName.replace(/\.[^/.]+$/, "");
//     navigate(`/querypage/${fileNameWithoutExtension}`);
//   };

//   return (
//     <div className="home-container">
//       <Header /> {/* Use the Header component here */}
//       <h2>Your Uploaded Files</h2>
//       {/* <button onClick={handleLogout} className="logout-button" disabled={loading}><FaSignOutAlt /> Sign Out</button> */}
//       {loading && <div className="loader">Loading...</div>}
//       {files.length === 0 && !loading ? (
//         <p>No files uploaded.</p>
//       ) : (
//         <ul className="file-list">
//           {files.map((file) => (
//             <li key={file.id} className="file-item">
//               <span className="file-name" onClick={() => handleFileClick(file.id, file.file_name)} style={{cursor: 'pointer'}}>{file.file_name}</span>
//               <div className="file-actions">
//                 <button onClick={() => handleEdit(file.id, file.file_name)} disabled={loading}> <FaEdit /></button>
//                 <button onClick={() => handleDelete(file.id, file.file_name)} disabled={loading}><FaTrash /></button>
//               </div>
//             </li>
//           ))}
//         </ul>
//       )}
//       <div className="upload-section">
//         <button onClick={() => setShowUploadOptions(!showUploadOptions)} disabled={loading}>
//           Upload File
//         </button>
//         {showUploadOptions && (
//           <div className="upload-options">
//             <input type="file" onChange={handleFileChange} disabled={loading}/>
//             <button onClick={handleUpload} disabled={loading}>Upload</button>
//           </div>
//         )}
//       </div>

//       {editDialog.open && (
//         <div className="edit-dialog-overlay">
//           <div className="edit-dialog">
//             <h3>Edit File: {editDialog.fileName}</h3>
//             <input type="file" onChange={handleEditFileChange} disabled={loading}/>
//             <button onClick={handleEditSubmit} disabled={loading}>OK</button>
//             <button onClick={handleEditCancel} disabled={loading}>Cancel</button>
//           </div>
//         </div>
//       )}

//       {deleteDialog.open && (
//         <div className="edit-dialog-overlay">
//           <div className="edit-dialog">
//             <h3>Are you sure you want to delete {deleteDialog.fileName}?</h3>
//             <button onClick={confirmDelete} disabled={loading}>Yes</button>
//             <button onClick={cancelDelete} disabled={loading}>No</button>
//           </div>
//         </div>
//       )}
//     </div>
//   );
// }

// export default Home;

// src/components/Home/Home.js
import React, { useState } from 'react';
import './home.css';
import Header from '../Header/header';
import DocumentList from '../DocumentList/documentList';
import Chat from '../QueryPage/querypage';

function Home() {
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileSelect = (fileName) => {
    setSelectedFile(fileName);
  };

  return (
    <div className="home-container">
      <Header />
      <div className="content-area">
        <DocumentList onFileSelect={handleFileSelect} />
        <div className="chat-area">
          {selectedFile && <Chat fileName={selectedFile} />}
          {!selectedFile && <p>Select a file to start a conversation.</p>}
        </div>
      </div>
    </div>
  );
}

export default Home;