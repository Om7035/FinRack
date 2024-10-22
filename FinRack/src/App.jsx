// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import LandingPage from './pages/LandingPage'; // Import the Landing Page
import Dashboard from './pages/Dashboard';
import Login from './pages/Login'; // If needed
import ContactUs from './pages/ContactUs'; // If needed
import Feedback from './pages/Feedback'; // If needed

const App = () => {
    return (
        <Router>
            <div className="App">
                <Routes>
                    {/* Route to the Landing Page */}
                    <Route path="/" element={<LandingPage />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/contact" element={<ContactUs />} />
                    <Route path="/feedback" element={<Feedback />} />
                </Routes>
            </div>
        </Router>
    );
};

export default App;
