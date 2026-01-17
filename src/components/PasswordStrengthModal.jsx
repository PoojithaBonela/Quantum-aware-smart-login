import React, { useState } from 'react';
import { formatTime } from '../utils/passwordAnalysis';
import '../pages/StrengthModal.css';

function PasswordStrengthModal({ metrics, onCancel, onConfirm }) {
    const [showDetails, setShowDetails] = useState(false);

    if (!metrics) return null;

    const {
        patterns,
        spaceMetrics,
        classicalCrackTimeSeconds,
        quantumCrackTimeSeconds,
        riskScore,
        riskLabel,
        decision
    } = metrics;

    const getRiskClass = (label) => {
        if (label === 'HIGH') return 'high';
        if (label === 'MEDIUM') return 'medium';
        return 'low';
    };

    const riskClass = getRiskClass(riskLabel);

    return (
        <div className="modal-overlay">
            <div className="strength-modal">
                <div className="modal-header">
                    <h3 className="modal-title">Password Security Analysis</h3>
                    <p className="auth-subtitle">Evaluation based on patterns and search space</p>
                </div>

                <div className="metrics-grid">
                    <div className="metric-card">
                        <span className="metric-val">{formatTime(classicalCrackTimeSeconds)}</span>
                        <span className="metric-name">Classical Crack Time</span>
                    </div>
                    <div className="metric-card">
                        <span className="metric-val">{formatTime(quantumCrackTimeSeconds)}</span>
                        <span className="metric-name">Quantum Crack Time</span>
                    </div>
                </div>

                <div className="risk-level-container">
                    <div className="detail-item">
                        <span>Risk Threat Level</span>
                        <span style={{ fontWeight: 700, color: riskClass === 'high' ? '#F44336' : riskClass === 'medium' ? '#FFC107' : '#4CAF50' }}>
                            {riskLabel}
                        </span>
                    </div>
                    <div className="risk-score-bar">
                        <div className={`risk-fill ${riskClass}`} style={{ width: `${riskScore}%` }}></div>
                    </div>
                </div>

                <div className="decision-box">
                    <span className="decision-label">Security Protocol Decision</span>
                    <span className="decision-value">{decision}</span>
                </div>

                <div className="details-panel">
                    <button className="details-toggle" onClick={() => setShowDetails(!showDetails)}>
                        {showDetails ? 'Hide Detailed Metrics ↑' : 'Show Detailed Metrics ↓'}
                    </button>

                    {showDetails && (
                        <div className="details-content">
                            <div className="detail-item">
                                <span>Charset Size:</span>
                                <span>{spaceMetrics.charset_size}</span>
                            </div>
                            <div className="detail-item">
                                <span>Password Length:</span>
                                <span>{spaceMetrics.password_length}</span>
                            </div>
                            <div className="detail-item">
                                <span>Entropy Transformation:</span>
                                <span>{spaceMetrics.effective_search_space > 1e15 ? 'High' : 'Low'}</span>
                            </div>

                            <p style={{ marginTop: '12px', marginBottom: '8px', fontSize: '0.75rem', fontWeight: 600 }}>Pattern Detection:</p>
                            <div className="detail-item">
                                <span>Dictionary Words:</span>
                                <span className={`pattern-chip ${patterns.dictionary_word ? 'found' : 'not-found'}`}>
                                    {patterns.dictionary_word ? 'DETECTED' : 'CLEAR'}
                                </span>
                            </div>
                            <div className="detail-item">
                                <span>Name/Email Reuse:</span>
                                <span className={`pattern-chip ${patterns.name_reuse ? 'found' : 'not-found'}`}>
                                    {patterns.name_reuse ? 'DETECTED' : 'CLEAR'}
                                </span>
                            </div>
                            <div className="detail-item">
                                <span>Keyboard Patterns:</span>
                                <span className={`pattern-chip ${patterns.keyboard_pattern ? 'found' : 'not-found'}`}>
                                    {patterns.keyboard_pattern ? 'DETECTED' : 'CLEAR'}
                                </span>
                            </div>
                            <div className="detail-item">
                                <span>Sequential Characters:</span>
                                <span className={`pattern-chip ${patterns.sequential_pattern ? 'found' : 'not-found'}`}>
                                    {patterns.sequential_pattern ? 'DETECTED' : 'CLEAR'}
                                </span>
                            </div>
                            <div className="detail-item">
                                <span>Repeated Characters:</span>
                                <span className={`pattern-chip ${patterns.repeated_pattern ? 'found' : 'not-found'}`}>
                                    {patterns.repeated_pattern ? 'DETECTED' : 'CLEAR'}
                                </span>
                            </div>
                            <div className="detail-item">
                                <span>Year Pattern:</span>
                                <span className={`pattern-chip ${patterns.year_pattern ? 'found' : 'not-found'}`}>
                                    {patterns.year_pattern ? 'DETECTED' : 'CLEAR'}
                                </span>
                            </div>
                            <div className="detail-item">
                                <span>Date Pattern:</span>
                                <span className={`pattern-chip ${patterns.date_pattern ? 'found' : 'not-found'}`}>
                                    {patterns.date_pattern ? 'DETECTED' : 'CLEAR'}
                                </span>
                            </div>
                        </div>
                    )}
                </div>

                <div className="modal-actions">
                    <button className="modal-btn" onClick={onCancel}>Adjust Password</button>
                    <button className="modal-btn primary" onClick={onConfirm}>Confirm Security</button>
                </div>
            </div>
        </div>
    );
}

export default PasswordStrengthModal;
