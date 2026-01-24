# Quantum-Aware Smart Login Security System

A modern, high-security authentication system designed for the post-quantum era. This project features a React-based frontend and a Flask-based backend, implementing adaptive multi-factor authentication (MFA) and quantum readiness monitoring.

![Project Screenshot](file:///C:/Users/LENOVO/.gemini/antigravity/brain/10f60fdb-97f9-4839-86a9-04cbfca9b5b2/frontend_home_page_1769249964420.png)

## 🚀 Overview

QuantumSecure is an adaptive security platform that evaluates login risks in real-time. It provides a seamless user experience for low-risk scenarios while enforcing strict MFA for high-risk attempts, preparing organizations for future quantum computing threats.

## 🛠️ Tech Stack

- **Frontend**: React, Vite, CSS (Vanilla)
- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-CORS
- **Database**: SQLite
- **Security**: BCrypt hashing, Adaptive MFA, Quantum-ready metrics

## 🚦 Getting Started

### Prerequisites
- Node.js (v18+)
- Python (v3.9+)

### Backend Setup
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment:
   ```bash
   copy .env.example .env
   ```
5. Run the server:
   ```bash
   python app.py
   ```
   The backend will run on `http://localhost:5000`.

### Frontend Setup
1. return to the root directory:
   ```bash
   cd ..
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173`.

## ✨ Key Features

- **Adaptive MFA**: Risk-based authentication triggers (Low/Medium/High risk).
- **Quantum Readiness Dashboard**: Monitor your infrastructure's preparedness for quantum-level threats.
- **Security Event Logging**: Real-time auditing of login attempts and security events.
- **Rich Aesthetics**: Premium dark-mode UI with smooth micro-animations.

## 📁 Project Structure

- `backend/`: Flask API, database models, and security logic.
- `src/`: React components and frontend application logic.
- `public/`: Static assets.
- `vite.config.js`: Vite configuration for the React app.

---
Developed with focus on post-quantum security.
