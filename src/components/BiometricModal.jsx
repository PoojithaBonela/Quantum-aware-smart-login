import React, { useRef, useEffect, useState } from 'react';
import { loadModels, getFaceEmbedding } from '../utils/biometricUtils';
import './BiometricModal.css';

const BiometricModal = ({ mode, email, onComplete, onCancel, onCapture }) => {
    const videoRef = useRef(null);
    const [status, setStatus] = useState('Initializing camera...');
    const [capturedCount, setCapturedCount] = useState(0);
    const [embeddings, setEmbeddings] = useState([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const startVideo = async () => {
            try {
                await loadModels();
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                }
                setStatus(mode === 'enroll' ? 'Look at the camera (Front)' : 'Hold still for verification...');
            } catch (err) {
                console.error(err);
                setError('Could not access camera. Please check permissions.');
            }
        };
        startVideo();

        return () => {
            if (videoRef.current && videoRef.current.srcObject) {
                videoRef.current.srcObject.getTracks().forEach(track => track.stop());
            }
        };
    }, [mode]);

    const captureAngle = async () => {
        if (!videoRef.current || isProcessing) return;

        setIsProcessing(true);
        setStatus('Processing...');

        const embedding = await getFaceEmbedding(videoRef.current);

        if (embedding) {
            if (mode === 'enroll') {
                const newEmbeddings = [...embeddings, embedding];
                setEmbeddings(newEmbeddings);
                setCapturedCount(capturedCount + 1);

                if (capturedCount === 0) setStatus('Look to the Left');
                else if (capturedCount === 1) setStatus('Look to the Right');
                else {
                    setStatus('Capture complete. Processing...');
                    if (onCapture) {
                        onCapture(newEmbeddings);
                    } else {
                        await handleEnroll(newEmbeddings);
                    }
                }
            } else {
                setStatus('Verifying...');
                await handleVerify(embedding);
            }
        } else {
            setError('No face detected. Please adjust position.');
        }
        setIsProcessing(false);
    };

    const handleEnroll = async (finalEmbeddings) => {
        try {
            const response = await fetch('http://localhost:5000/api/biometric/enroll', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ email, embeddings: finalEmbeddings })
            });
            const data = await response.json();
            if (data.status === 'success') {
                onComplete();
            } else {
                setError(data.message || 'Enrollment failed');
            }
        } catch (err) {
            setError('Server connection failed');
        }
    };

    const handleVerify = async (embedding) => {
        try {
            const response = await fetch('http://localhost:5000/api/biometric/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ email, embedding })
            });
            const data = await response.json();
            if (response.ok) {
                onComplete(data);
            } else {
                setError(data.message || 'Verification failed');
            }
        } catch (err) {
            setError('Server connection failed');
        }
    };

    return (
        <div className="biometric-modal-overlay">
            <div className="biometric-modal">
                <h3>{mode === 'enroll' ? 'Biometric Enrollment' : 'Biometric Verification'}</h3>
                <p className="subtitle">{mode === 'enroll' ? 'Required for high-risk accounts' : 'Face ID security check'}</p>

                <div className="video-container">
                    <video ref={videoRef} autoPlay muted playsInline />
                    {isProcessing && <div className="spinner"></div>}
                </div>

                <div className="status-box">
                    {error ? <p className="error">{error}</p> : <p>{status}</p>}
                </div>

                <div className="modal-actions">
                    <button
                        className="capture-btn"
                        onClick={captureAngle}
                        disabled={isProcessing || !!error}
                    >
                        {mode === 'enroll' ? `Capture (${capturedCount + 1}/3)` : 'Verify Now'}
                    </button>
                    {!error && <button className="cancel-btn" onClick={onCancel}>Cancel</button>}
                    {error && <button className="retry-btn" onClick={() => window.location.reload()}>Retry</button>}
                </div>
            </div>
        </div>
    );
};

export default BiometricModal;
