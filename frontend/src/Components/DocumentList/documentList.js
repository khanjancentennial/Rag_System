// src/components/DocumentList/DocumentList.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './documentList.css';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { FaEdit, FaTrash } from 'react-icons/fa';

const apiBaseUrl = process.env.REACT_APP_API_BASE_URL;

function DocumentList({ onFileSelect }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editDialog, setEditDialog] = useState({ open: false, fileId: null, fileName: '' });
  const [editSelectedFile, setEditSelectedFile] = useState(null);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, fileId: null, fileName: '' });
  const [selectedFile, setSelectedFile] = useState(null);
  const [showUploadOptions, setShowUploadOptions] = useState(false);

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${apiBaseUrl}all-files/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setFiles(response.data.Data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch files:', error);
      setLoading(false);
      if (files.length > 0) {
        toast.error('Failed to fetch files.');
      }
    }
  };

  const handleDelete = (fileId, fileName) => {
    setDeleteDialog({ open: true, fileId, fileName });
  };

  const confirmDelete = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      await axios.delete(`${apiBaseUrl}delete-file/${deleteDialog.fileId}/`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      setFiles(files.filter(file => file.id !== deleteDialog.fileId));

      setLoading(false);
      setDeleteDialog({ open: false, fileId: null, fileName: '' });
      toast.success('File deleted successfully.');

      fetchFiles();
    } catch (error) {
      console.error('Delete failed:', error);
      setLoading(false);
      setDeleteDialog({ open: false, fileId: null, fileName: '' });
      toast.error('Delete failed.');
    }
  };

  const cancelDelete = () => {
    setDeleteDialog({ open: false, fileId: null, fileName: '' });
  };

  const handleEdit = (fileId, fileName) => {
    setEditDialog({ open: true, fileId, fileName });
  };

  const handleEditFileChange = (event) => {
    setEditSelectedFile(event.target.files[0]);
  };

  const handleEditSubmit = async () => {
    if (!editSelectedFile) return;
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', editSelectedFile);
      await axios.put(`${apiBaseUrl}update-file/${editDialog.fileId}/`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });
      setEditDialog({ open: false, fileId: null, fileName: '' });
      fetchFiles();
      setLoading(false);
      toast.success('File edited successfully.');
    } catch (error) {
      console.error('Edit failed:', error);
      setLoading(false);
      setEditDialog({ open: false, fileId: null, fileName: '' });
      toast.error('Edit failed.');
    }
  };

  const handleEditCancel = () => {
    setEditDialog({ open: false, fileId: null, fileName: '' });
  };

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handelCloseUploadOptions = () => {
    setShowUploadOptions(false);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('files', selectedFile);
      await axios.post(`${apiBaseUrl}upload/`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });
      fetchFiles();
      setShowUploadOptions(false);
      setLoading(false);
      toast.success('File uploaded successfully.');
    } catch (error) {
      console.error('Upload failed:', error);
      setLoading(false);
      toast.error('Upload failed.');
    }
  };

  return (
    <div className="document-list">
      <ToastContainer />
      <h2>Your Uploaded Files</h2>
      {loading && <div className="loader">Loading...</div>}
      {files.length === 0 && !loading ? (
        <p>No files uploaded.</p>
      ) : (
        <ul className="file-list">
          {files.map((file) => (
            <li key={file.id} className="file-item">
              <span className="file-name" onClick={() => onFileSelect(file.file_name)} style={{cursor: 'pointer'}}>{file.file_name}</span>
              <div className="file-actions">
                <button className="edit" onClick={() => handleEdit(file.id, file.file_name)} disabled={loading}>
                  <FaEdit />
                </button>
                <button className="delete" onClick={() => handleDelete(file.id, file.file_name)} disabled={loading}>
                  <FaTrash />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="upload-section">
        <button onClick={() => setShowUploadOptions(!showUploadOptions)} disabled={loading}>
          Upload File
        </button>
        {showUploadOptions && (
          <div className="upload-options">
            <input type="file" onChange={handleFileChange} disabled={loading}/>
            <button onClick={handleUpload} disabled={loading}>Upload</button>
            <button className="cancel" onClick={handelCloseUploadOptions} disabled={loading}>Cancel</button>
          </div>
        )}
      </div>

      {editDialog.open && (
        <div className="edit-dialog-overlay">
          <div className="edit-dialog">
            <h3>Edit File: {editDialog.fileName}</h3>
            <input type="file" onChange={handleEditFileChange} disabled={loading} />
            <button className="delete-yes" onClick={handleEditSubmit} disabled={loading}>OK</button>
            <button className="delete-no" onClick={handleEditCancel} disabled={loading}>Cancel</button>
          </div>
        </div>
      )}

      {deleteDialog.open && (
        <div className="edit-dialog-overlay">
          <div className="edit-dialog">
            <h3>Are you sure you want to delete {deleteDialog.fileName}?</h3>
            <button className="delete-yes" onClick={confirmDelete} disabled={loading}>Yes</button>
            <button className="delete-no" onClick={cancelDelete} disabled={loading}>No</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default DocumentList;