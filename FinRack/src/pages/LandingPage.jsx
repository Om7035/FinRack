// src/pages/LandingPage.jsx
import React from 'react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
      <h1 className="text-4xl font-bold mb-8">Welcome to FinRack</h1>
      <p className="mb-4">Your personal financial advisor.</p>
      <div className="space-x-4">
        <Link to="/login">
          <button className="bg-blue-500 text-white px-4 py-2 rounded shadow hover:bg-blue-600">
            Login
          </button>
        </Link>
        <Link to="/register">
          <button className="bg-green-500 text-white px-4 py-2 rounded shadow hover:bg-green-600">
            Register
          </button>
        </Link>
        <Link to="/dashboard">
          <button className="bg-indigo-500 text-white px-4 py-2 rounded shadow hover:bg-indigo-600">
            Dashboard
          </button>
        </Link>
      </div>
    </div>
  );
};

export default LandingPage;
