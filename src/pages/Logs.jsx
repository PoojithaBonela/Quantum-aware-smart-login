import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Logs.css';

function Logs() {
    const navigate = useNavigate();
    const [readiness, setReadiness] = useState(null);
    const [logs, setLogs] = useState([]);
    const [readinessError, setReadinessError] = useState('');
    const [logsError, setLogsError] = useState('');

    const fetchData = () => {
        // Fetch readiness metrics
        fetch('http://localhost:5000/api/admin/readiness')
            .then(res => {
                if (!res.ok) throw new Error('API failed');
                return res.json();
            })
            .then(data => {
                const readinessData = data.data || data;
                setReadiness(readinessData);
                setReadinessError('');
            })
            .catch(err => {
                console.error('Readiness fetch error:', err);
                setReadinessError('Unable to load readiness metrics');
            });

        // Fetch security logs
        fetch('http://localhost:5000/api/admin/logs')
            .then(res => {
                if (!res.ok) throw new Error('API failed');
                return res.json();
            })
            .then(data => {
                const logsData = data.data || data;
                setLogs(logsData);
                setLogsError('');
            })
            .catch(err => {
                console.error('Logs fetch error:', err);
                setLogsError('Unable to load security logs');
            });
    };

    useEffect(() => {
        fetchData();
    }, []);

    return (
        <div className="admin-container">
            <div className="admin-header">
                <h1>Administrative Oversight</h1>
                <p>Organization-wide security health and audit logs</p>
            </div>

            {readinessError ? (
                <div className="error-message-bg admin-error">
                    <p>{readinessError}</p>
                </div>
            ) : readiness ? (
                <div className="readiness-summary">
                    <div className="metric-box">
                        <span className="metric-label">Total Users</span>
                        <span className="metric-value">{readiness.total_users}</span>
                    </div>
                    <div className="metric-box border-x">
                        <span className="metric-label">Quantum Safe</span>
                        <span className="metric-value safe">{readiness.quantum_safe}{typeof readiness.quantum_safe === 'number' ? '%' : ''}</span>
                    </div>
                    <div className="metric-box border-x">
                        <span className="metric-label">Partially Safe</span>
                        <span className="metric-value warning">{readiness.partially_safe}{typeof readiness.partially_safe === 'number' ? '%' : ''}</span>
                    </div>
                    <div className="metric-box">
                        <span className="metric-label">Critical Risk</span>
                        <span className="metric-value danger">{readiness.critical}{typeof readiness.critical === 'number' ? '%' : ''}</span>
                    </div>
                </div>
            ) : (
                <div className="loading-metrics">Loading metrics...</div>
            )}

            <div className="log-section">
                <div className="section-title">
                    <h2>Security Audit Logs</h2>
                    <div className="admin-actions">
                        <button className="download-button" onClick={() => window.open('http://localhost:5000/api/admin/logs/download', '_blank')}>
                            Download security Report
                        </button>
                        <button className="refresh-button" onClick={fetchData}>Refresh Logs</button>
                    </div>
                </div>

                {logsError ? (
                    <div className="error-message-bg admin-error">
                        <p>{logsError}</p>
                    </div>
                ) : (
                    <div className="table-wrapper">
                        <table className="log-table">
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Email</th>
                                    <th>IP Address</th>
                                    <th>Device</th>
                                    <th>Result</th>
                                    <th>Risk Level</th>
                                    <th>MFA</th>
                                    <th>Details</th>
                                </tr>
                            </thead>
                            <tbody>
                                {logs.length > 0 ? (
                                    logs.map((log, index) => (
                                        <tr key={index}>
                                            <td className="time-col">{log.timestamp}</td>
                                            <td>{log.email}</td>
                                            <td className="ip-col">{log.ip}</td>
                                            <td className="device-col" title={log.device}>
                                                {log.device.length > 20 ? log.device.substring(0, 20) + '...' : log.device}
                                            </td>
                                            <td>
                                                <span className={`pill ${(log.result || '').toLowerCase().replace(' ', '-')}`}>
                                                    {log.result}
                                                </span>
                                            </td>
                                            <td>{log.risk}</td>
                                            <td>{log.mfa}</td>
                                            <td className="reason-col">{log.reason || '-'}</td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="8" className="empty-logs">No security logs available.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            <div className="admin-footer">
                <button className="exit-button" onClick={() => navigate('/')}>Exit Administrator Mode</button>
            </div>
        </div>
    );
}

export default Logs;
