import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { evaluateSecurityMetrics } from '../utils/passwordAnalysis';
import PasswordStrengthModal from '../components/PasswordStrengthModal';
import BiometricModal from '../components/BiometricModal';
import './Register.css';

function Register() {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: ''
    });
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    const [evaluationMetrics, setEvaluationMetrics] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [isConfirmed, setIsConfirmed] = useState(false);
    const [showBiometricEnroll, setShowBiometricEnroll] = useState(false);
    const [capturedBiometrics, setCapturedBiometrics] = useState(null);

    const validatePassword = (password) => {
        const minLength = 8;
        const hasUpperCase = /[A-Z]/.test(password);
        const hasLowerCase = /[a-z]/.test(password);
        const hasNumber = /[0-9]/.test(password);
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

        if (password.length < minLength) return "Password must be at least 8 characters long";
        if (!hasUpperCase) return "Password must contain at least one uppercase letter";
        if (!hasLowerCase) return "Password must contain at least one lowercase letter";
        if (!hasNumber) return "Password must contain at least one number";
        if (!hasSpecialChar) return "Password must contain at least one special character";
        return null;
    };

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
        setError('');
    };

    const handleSubmit = async (e) => {
        if (e) e.preventDefault();

        if (!formData.email || !formData.password || !formData.confirmPassword) {
            setError('All fields are required');
            return;
        }

        const passwordError = validatePassword(formData.password);
        if (passwordError) {
            setError(passwordError);
            return;
        }

        if (formData.password !== formData.confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        // 1. Trigger evaluation if not yet confirmed
        if (!isConfirmed) {
            const metrics = evaluateSecurityMetrics(formData.password, formData.email);
            setEvaluationMetrics(metrics);
            setShowModal(true);
            return;
        }

        // 2. Trigger biometric enrollment if high risk and not yet captured
        if (evaluationMetrics?.riskLabel === 'HIGH' && !capturedBiometrics) {
            setShowBiometricEnroll(true);
            return;
        }

        try {
            const response = await fetch('http://localhost:5000/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    email: formData.email,
                    password: formData.password,
                    biometricData: capturedBiometrics // Send if available
                }),
            });

            const data = await response.json();

            if (data.status === 'success') {
                setMessage('Registration successful! Redirecting to login...');
                setTimeout(() => navigate('/login'), 2000);
            } else {
                setError(data.message || 'Registration failed');
            }
        } catch (err) {
            setError('Connection to server failed');
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-box">
                <h2 className="auth-title">Create Account</h2>
                <p className="auth-subtitle">Join the quantum-secure network</p>

                {error && <div className="error-message">{error}</div>}
                {message && <div className="success-message">{message}</div>}

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

                    <div className="form-group">
                        <label>Confirm Password</label>
                        <div className="password-input-wrapper">
                            <input
                                type={showConfirmPassword ? "text" : "password"}
                                name="confirmPassword"
                                value={formData.confirmPassword}
                                onChange={handleChange}
                                placeholder="••••••••"
                                required
                            />
                            <button
                                type="button"
                                className="toggle-password"
                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                            >
                                {showConfirmPassword ? "Hide" : "Show"}
                            </button>
                        </div>
                    </div>

                    <button type="submit" className="auth-button">Sign Up</button>
                </form>

                <p className="auth-footer">
                    Already have an account? <span onClick={() => navigate('/login')}>Sign in</span>
                </p>
            </div>

            {showModal && (
                <PasswordStrengthModal
                    metrics={evaluationMetrics}
                    onCancel={() => {
                        setShowModal(false);
                        setIsConfirmed(false);
                    }}
                    onConfirm={() => {
                        setShowModal(false);
                        setIsConfirmed(true);
                        // Using setTimeout to ensure state is updated before next submission
                        setTimeout(() => {
                            const submitBtn = document.querySelector('.auth-button');
                            if (submitBtn) submitBtn.click();
                        }, 100);
                    }}
                />
            )}
            {showBiometricEnroll && (
                <BiometricModal
                    mode="enroll"
                    email={formData.email}
                    onCapture={(embeddings) => {
                        setCapturedBiometrics(embeddings);
                        setShowBiometricEnroll(false);
                        // Now trigger the final submission
                        setTimeout(() => {
                            const btn = document.querySelector('.auth-button');
                            if (btn) btn.click();
                        }, 100);
                    }}
                    onCancel={() => setShowBiometricEnroll(false)}
                />
            )}
        </div>
    );
}

export default Register;
