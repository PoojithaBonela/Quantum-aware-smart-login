import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Otp.css';

function Otp() {
    const navigate = useNavigate();
    const location = useLocation();
    const [otp, setOtp] = useState('');
    const [error, setError] = useState('');

    // Get email from navigation state or localStorage or fallback
    const email = location.state?.email || localStorage.getItem('userEmail') || "user@example.com";

    const handleChange = (e) => {
        // Only allow numeric input
        const value = e.target.value.replace(/\D/g, '');
        setOtp(value);
        setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!otp) {
            setError('OTP is required');
            return;
        }

        try {
            const response = await fetch('http://localhost:5000/api/verify-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, otp }),
            });

            const data = await response.json();

            if (data.status === 'success') {
                localStorage.setItem('userEmail', email); // Persist for dashboard
                navigate('/dashboard');
            } else if (data.status === 'biometric_required') {
                navigate('/biometric-verification');
            } else {
                setError(data.message || 'OTP verification failed. Please try again.');
            }
        } catch (err) {
            setError('OTP verification failed. Please try again.');
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-box">
                <h2 className="auth-title">Verify Access</h2>
                <p className="auth-subtitle">High-risk activity detected. Enter the OTP sent to your email.</p>

                {error && <div className="error-message">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group otp-group">
                        <input
                            type="text"
                            name="otp"
                            value={otp}
                            onChange={handleChange}
                            placeholder="000000"
                            maxLength="6"
                            className="otp-input"
                            required
                        />
                    </div>

                    <button type="submit" className="auth-button">Verify OTP</button>
                </form>

                <div className="auth-footer">
                    <p>Didn't receive a code? <span>Resend</span></p>
                    <span className="back-to-login" onClick={() => navigate('/login')}>Back to login</span>
                </div>
            </div>
        </div>
    );
}

export default Otp;
