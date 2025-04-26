// src/components/Header/Header.js
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FaSignOutAlt } from 'react-icons/fa';
import './header.css'; // Create Header.css

function Header() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.clear();
    navigate('/');
  };

  return (
    <header className="home-header">
      <h2>AI Agent</h2>
      <button onClick={handleLogout} className="logout-button">
        <FaSignOutAlt /> Sign Out
      </button>
    </header>
  );
}

export default Header;