import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

function Dashboard() {
    const navigate = useNavigate();
    const [securityData, setSecurityData] = useState(null);
    const [error, setError] = useState('');

    useEffect(() => {
        // Fetch security status from backend
        fetch('http://localhost:5000/api/user/security-status')
            .then(res => {
                if (!res.ok) throw new Error('Failed to fetch');
                return res.json();
            })
            .then(data => {
                // Support both nested and flat JSON structures for robustness
                const status = data.data || data;
                setSecurityData(status);
            })
            .catch(err => {
                console.error('Failed to fetch security status', err);
                setError('Unable to load security status.');
            });
    }, []);

    const handleLogout = () => {
        fetch('http://localhost:5000/api/logout', { method: 'POST' })
            .finally(() => navigate('/login'));
    };

    if (error) {
        return (
            <div className="dashboard-container">
                <div className="error-message-bg">
                    <p className="error-text">{error}</p>
                </div>
            </div>
        );
    }

    if (!securityData) {
        return (
            <div className="dashboard-container">
                <p className="loading-text">Loading security metrics...</p>
            </div>
        );
    }

    // Determine MFA display safely
    const mfaDisplay = (securityData.mfa_enabled === true || securityData.mfa_enabled === "MFA Enabled") ? "Yes" : "No";

    // Support either risk_level or last_login_risk
    const riskLevel = securityData.risk_level || securityData.last_login_risk || "Unknown";

    return (
        <div className="dashboard-container">
            <div className="dashboard-header">
                <h1>Account Security</h1>
                <p>Real-time monitoring and risk evaluation</p>
            </div>

            <div className="dashboard-grid">
                <div className="status-card">
                    <h3>Login Status</h3>
                    <div className="status-value">{securityData.login_status}</div>
                    <p className="status-meta">Current session authentication state</p>
                </div>

                <div className="status-card highlight">
                    <h3>Risk Level</h3>
                    <div className={`status-value risk-${riskLevel.toLowerCase()}`}>
                        {riskLevel}
                    </div>
                    <p className="status-meta">Adaptive evaluation of access context</p>
                </div>

                <div className="status-card">
                    <h3>MFA Enabled</h3>
                    <div className="status-value">{mfaDisplay}</div>
                    <p className="status-meta">Enhanced account protection active</p>
                </div>
            </div>

            <div className="recommendation-panel">
                <h3>Security Recommendation</h3>
                <p>{securityData.recommendation}</p>
            </div>

            <div className="dashboard-footer">
                <button className="logout-button" onClick={handleLogout}>Sign Out</button>
            </div>
        </div>
    );
}

export default Dashboard;
