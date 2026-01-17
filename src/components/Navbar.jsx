import React from 'react';
import { NavLink } from 'react-router-dom';
import './Navbar.css';

function Navbar() {
    return (
        <nav className="navbar">
            <div className="nav-container">
                <NavLink to="/" className="nav-logo">
                    QuantumSecure
                </NavLink>
                <ul className="nav-links">
                    <li>
                        <NavLink to="/" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
                            Home
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/login" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
                            Login
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/register" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
                            Register
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/dashboard" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
                            Dashboard
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/logs" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
                            Admin
                        </NavLink>
                    </li>
                </ul>
            </div>
        </nav>
    );
}

export default Navbar;
