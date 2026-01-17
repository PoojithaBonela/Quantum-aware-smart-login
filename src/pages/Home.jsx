import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Home.css';

function Home() {
  const navigate = useNavigate();

  return (
    <div className="home-container">
      <div className="home-content">
        <h1 className="home-title">Quantum-Aware Smart Login</h1>
        <p className="home-description">
          A security system designed for the post-quantum era, evaluating risks and protecting user access with adaptive MFA.
        </p>

        <div className="home-actions">
          <div className="action-card" onClick={() => navigate('/login')}>
            <h3>User Portal</h3>
            <p>Access your secure dashboard and security metrics.</p>
            <button className="nav-button">Get Started</button>
          </div>

          <div className="action-card" onClick={() => navigate('/logs')}>
            <h3>Admin Portal</h3>
            <p>Monitor organization health and security logs.</p>
            <button className="nav-button secondary">Logs Dashboard</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;
