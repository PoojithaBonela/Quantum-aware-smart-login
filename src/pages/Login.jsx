import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BiometricModal from '../components/BiometricModal';
import './Register.css'; // Using the same base styling as Register

function Login() {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        email: '',
        password: ''
    });
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showBiometricVerify, setShowBiometricVerify] = useState(false);

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
        setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!formData.email || !formData.password) {
            setError('Please fill in all fields');
            return;
        }

        try {
            const response = await fetch('http://localhost:5000/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    email: formData.email,
                    password: formData.password
                }),
            });

            const data = await response.json();

<<<<<<< HEAD
            if (data.status === 'success') {
                localStorage.setItem('userEmail', formData.email); // Persist for dashboard
                navigate('/dashboard');
            } else if (data.status === 'mfa_required') {
                localStorage.setItem('userEmail', formData.email); // Persist for OTP page
                navigate('/otp', { state: { email: formData.email } });
=======
            if (response.ok) {
                if (data.status === 'success') {
                    navigate('/dashboard');
                } else if (data.status === 'mfa_required') {
                    navigate('/otp', { state: { email: formData.email } });
                } else if (data.status === 'biometric_required') {
                    setShowBiometricVerify(true);
                }
>>>>>>> second-version
            } else {
                setError(data.message || 'Login failed. Please try again.');
            }
        } catch (err) {
<<<<<<< HEAD
            setError(err.message || 'Login failed. Please try again.');
=======
            setError('Connection error. Please try again later.');
>>>>>>> second-version
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-box">
                <h2 className="auth-title">Welcome Back</h2>
                <p className="auth-subtitle">Signed in with your secure account</p>

                {error && <div className="error-message">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Email Address</label>
                        <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            placeholder="name@example.com"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Password</label>
                        <div className="password-input-wrapper">
                            <input
                                type={showPassword ? "text" : "password"}
                                name="password"
                                value={formData.password}
                                onChange={handleChange}
                                placeholder="••••••••"
                                required
                            />
                            <button
                                type="button"
                                className="toggle-password"
                                onClick={() => setShowPassword(!showPassword)}
                            >
                                {showPassword ? "Hide" : "Show"}
                            </button>
                        </div>
                    </div>

                    <button type="submit" className="auth-button">Sign In</button>
                </form>

                <p className="auth-footer">
                    Don't have an account? <span onClick={() => navigate('/register')}>Sign up</span>
                </p>
            </div>

            {showBiometricVerify && (
                <BiometricModal
                    mode="verify"
                    email={formData.email}
                    onComplete={(data) => {
                        if (data.status === 'mfa_required') {
                            navigate('/otp', { state: { email: formData.email } });
                        } else {
                            navigate('/dashboard');
                        }
                    }}
                    onCancel={() => setShowBiometricVerify(false)}
                />
            )}
        </div>
    );
}

export default Login;
