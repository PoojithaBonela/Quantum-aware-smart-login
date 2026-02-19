import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Otp.css';

function Otp() {
    const navigate = useNavigate();
    const location = useLocation();
    const [otp, setOtp] = useState('');
    const [error, setError] = useState('');

    // Get email from navigation state or fallback for testing
    const email = location.state?.email;

    // Redirect to login if email is missing (e.g. direct URL access)
    React.useEffect(() => {
        if (!email) {
            navigate('/login');
        }
    }, [email, navigate]);

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
                credentials: 'include',
                body: JSON.stringify({ email, otp }),
            });

            const data = await response.json();

            if (response.ok && data.status === 'success') {
                navigate('/dashboard');
            } else {
                setError(data.message || 'OTP verification failed. Please try again.');
            }
        } catch (err) {
            setError('Connection error. Please try again later.');
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
