import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Otp.css'; // Reuse OTP styling

function BiometricVerification() {
    const navigate = useNavigate();
    const location = useLocation();
    const [status, setStatus] = useState('Scanning...');
    const [error, setError] = useState('');

    // Get email from storage
    const email = localStorage.getItem('userEmail');

    useEffect(() => {
        if (!email) {
            navigate('/login');
            return;
        }

        // Auto-start simulation
        simulateBiometricScan();
    }, [email, navigate]);

    const simulateBiometricScan = async () => {
        try {
            // Wait 2 seconds to simulate scanning
            await new Promise(resolve => setTimeout(resolve, 2000));

            setStatus('Verifying...');

            const response = await fetch('http://localhost:5000/api/verify-biometric', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });

            const data = await response.json();

            if (data.status === 'success') {
                setStatus('Verified!');
                setTimeout(() => {
                    navigate('/dashboard');
                }, 1000);
            } else {
                setError(data.message || 'Biometric verification failed.');
                setStatus('Failed');
            }
        } catch (err) {
            setError('System error during verification.');
            setStatus('Error');
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-box">
                <h2 className="auth-title">Biometric Verification</h2>
                <p className="auth-subtitle">High Security Access Required</p>

                <div style={{ margin: '30px 0', textAlign: 'center' }}>
                    <div className="biometric-icon" style={{ fontSize: '48px', marginBottom: '20px' }}>
                        {status === 'Scanning...' ? '👆' : status === 'Verified!' ? '✅' : '❌'}
                    </div>
                    <h3>{status}</h3>
                </div>

                {error && <div className="error-message">{error}</div>}

                {error && (
                    <button onClick={simulateBiometricScan} className="auth-button">
                        Retry Scan
                    </button>
                )}
            </div>
        </div>
    );
}

export default BiometricVerification;
