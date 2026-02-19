import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

function Dashboard() {
    const navigate = useNavigate();
    const [securityData, setSecurityData] = useState(null);
    const [error, setError] = useState('');

    useEffect(() => {
        // Fetch security status from backend with cache-busting
        fetch('http://localhost:5000/api/user/security-status', {
            credentials: 'include',
            cache: 'no-store'
        })
            .then(res => {
                if (res.status === 401) {
                    navigate('/login');
                    throw new Error('Please log in again.');
                }
                if (!res.ok) throw new Error('Failed to fetch');
                return res.json();
            })
            .then(data => {
                const status = data.data || data;
                setSecurityData(status);
            })
            .catch(err => {
                console.error('Security status error:', err);
                setError(err.message || 'Unable to load security status.');
            });
    }, [navigate]);

    const handleLogout = () => {
        fetch('http://localhost:5000/api/logout', {
            method: 'POST',
            credentials: 'include'
        })
            .finally(() => {
                setSecurityData(null);
                navigate('/login');
            });
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
                <p className="user-email">Logged in as: <strong>{securityData.email}</strong></p>
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
                <p className="recommendation-text">{securityData.recommendation}</p>
            </div>

            <div className="dashboard-footer">
                <button className="logout-button" onClick={handleLogout}>Sign Out</button>
            </div>
        </div>
    );
}

export default Dashboard;
