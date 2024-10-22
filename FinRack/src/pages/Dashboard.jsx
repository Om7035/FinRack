// src/pages/Dashboard.jsx
import React, { useState } from 'react';
import { Bar, Doughnut } from 'react-chartjs-2';
import { FiMessageSquare } from 'react-icons/fi'; // Chat icon
import ChatBot from '../components/ChatBot'; // Import the ChatBot component
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

const Dashboard = () => {
  const [showChatBot, setShowChatBot] = useState(false); // State for toggling chatbot
  const [newExpense, setNewExpense] = useState({ category: '', amount: 0 });
  const [monthlyExpenses, setMonthlyExpenses] = useState([
    { category: "Rent", amount: 1200 },
    { category: "Groceries", amount: 300 },
    { category: "Utilities", amount: 150 },
    { category: "Transport", amount: 100 },
  ]);

  const [financialGoals, setFinancialGoals] = useState({
    goalAmount: 10000,
    currentSavings: 4000,
  });

  const [chatMessages, setChatMessages] = useState([]); // State for chat messages
  const [newChatMessage, setNewChatMessage] = useState(''); // State for new chat message

  const toggleChatBot = () => {
    setShowChatBot(!showChatBot); // Toggles chatbot visibility
  };

  const barChartData = {
    labels: monthlyExpenses.map(expense => expense.category),
    datasets: [
      {
        label: 'Monthly Expenses',
        data: monthlyExpenses.map(expense => expense.amount),
        backgroundColor: 'rgba(75, 192, 192, 0.7)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
      },
    ],
  };

  const doughnutChartData = {
    labels: ['Current Savings', 'Remaining to Goal'],
    datasets: [
      {
        label: 'Savings Progress',
        data: [
          financialGoals.currentSavings,
          financialGoals.goalAmount - financialGoals.currentSavings,
        ],
        backgroundColor: ['rgba(54, 162, 235, 0.7)', 'rgba(255, 99, 132, 0.7)'],
      },
    ],
  };

  const handleAddExpense = (e) => {
    e.preventDefault();
    if (newExpense.category && newExpense.amount > 0) {
      setMonthlyExpenses([...monthlyExpenses, newExpense]);
      setNewExpense({ category: '', amount: 0 });
    }
  };

  const handleDeleteExpense = (index) => {
    const updatedExpenses = monthlyExpenses.filter((_, i) => i !== index);
    setMonthlyExpenses(updatedExpenses);
  };

  const handleUpdateSavings = (e) => {
    const { name, value } = e.target;
    setFinancialGoals((prevGoals) => ({
      ...prevGoals,
      [name]: Number(value),
    }));
  };

  // Handle sending a chat message
  const handleSendMessage = (e) => {
    e.preventDefault(); // Prevent default form submission
    if (newChatMessage.trim()) {
      const userMessage = { sender: 'User', message: newChatMessage };
      setChatMessages([...chatMessages, userMessage]); // Add user message to chat
      setNewChatMessage(''); // Clear the input

      // Simulate chatbot response
      setTimeout(() => {
        const botResponse = { sender: 'ChatBot', message: `You said: ${newChatMessage}` }; // Example response
        setChatMessages((prevMessages) => [...prevMessages, botResponse]); // Add bot response to chat
      }, 1000);
    }
  };

  // Handle enter key press to send message
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage(e); // Call send message on Enter key press
    }
  };

  return (
    <div className="flex flex-col items-center justify-start p-8 bg-gray-900 text-gray-200 h-screen overflow-y-auto">
      <h1 className="text-5xl font-bold mb-6 text-blue-500">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-5xl mb-6">
        <div className="bg-gray-800 rounded-lg shadow-lg p-6 transition-shadow duration-300 hover:shadow-2xl">
          <h2 className="text-2xl font-semibold mb-4">User Info</h2>
          <p><strong>Name:</strong> John Doe</p>
          <p><strong>Email:</strong> johndoe@example.com</p>
        </div>

        <div className="bg-gray-800 rounded-lg shadow-lg p-6 transition-shadow duration-300 hover:shadow-2xl">
          <h2 className="text-2xl font-semibold mb-4">Financial Goals</h2>
          <div className="flex flex-col mb-4">
            <label>
              <strong>Goal Amount (INR):</strong>
              <input
                type="number"
                name="goalAmount"
                value={financialGoals.goalAmount}
                onChange={handleUpdateSavings}
                className="border border-gray-600 rounded-md p-2 mt-2 bg-gray-700 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-200"
              />
            </label>
            <label className="mt-2">
              <strong>Current Savings (INR):</strong>
              <input
                type="number"
                name="currentSavings"
                value={financialGoals.currentSavings}
                onChange={handleUpdateSavings}
                className="border border-gray-600 rounded-md p-2 mt-2 bg-gray-700 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-200"
              />
            </label>
            <p className="mt-2"><strong>Remaining:</strong> ₹{financialGoals.goalAmount - financialGoals.currentSavings}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-5xl mb-6">
        <div className="bg-gray-800 rounded-lg shadow-lg p-6 transition-shadow duration-300 hover:shadow-2xl">
          <h2 className="text-2xl font-semibold mb-4">Monthly Expenses</h2>
          <div className="h-64">
            <Bar 
              data={barChartData} 
              options={{
                maintainAspectRatio: false,
                scales: {
                  y: {
                    beginAtZero: true,
                    title: {
                      display: true,
                      text: 'Amount (INR)',
                      color: '#fff',
                    },
                    ticks: {
                      color: '#fff',
                    },
                  },
                },
                plugins: {
                  legend: {
                    position: 'top',
                    labels: {
                      color: '#fff',
                    },
                  },
                  title: {
                    display: true,
                    text: 'Monthly Expense Breakdown',
                    color: '#fff',
                  },
                },
              }} 
              height={300} 
            />
          </div>
          <ul className="mt-4">
            {monthlyExpenses.map((expense, index) => (
              <li key={index} className="flex justify-between items-center mb-2">
                <span>{expense.category}: ₹{expense.amount}</span>
                <button 
                  onClick={() => handleDeleteExpense(index)} 
                  className="text-red-500 hover:text-red-700 transition-all duration-200"
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-gray-800 rounded-lg shadow-lg p-6 transition-shadow duration-300 hover:shadow-2xl">
          <h2 className="text-2xl font-semibold mb-4">Savings Progress</h2>
          <div className="h-64">
            <Doughnut 
              data={doughnutChartData} 
              options={{
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'top',
                    labels: {
                      color: '#fff',
                    },
                  },
                  title: {
                    display: true,
                    text: 'Savings vs. Goal',
                    color: '#fff',
                  },
                },
              }} 
              height={300} 
            />
          </div>
        </div>
      </div>

      <form onSubmit={handleAddExpense} className="w-full max-w-5xl bg-gray-800 rounded-lg shadow-lg p-6 mb-8 transition-shadow duration-300 hover:shadow-2xl">
        <h2 className="text-2xl font-semibold mb-4">Add Expense</h2>
        <div className="flex mb-4">
          <input
            type="text"
            value={newExpense.category}
            onChange={(e) => setNewExpense({ ...newExpense, category: e.target.value })}
            placeholder="Category"
            className="border border-gray-600 rounded-md p-2 bg-gray-700 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-200 mr-2"
          />
          <input
            type="number"
            value={newExpense.amount}
            onChange={(e) => setNewExpense({ ...newExpense, amount: Number(e.target.value) })}
            placeholder="Amount (INR)"
            className="border border-gray-600 rounded-md p-2 bg-gray-700 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-200"
          />
        </div>
        <button 
          type="submit" 
          className="bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors duration-200"
        >
          Add Expense
        </button>
      </form>

      <button 
        onClick={toggleChatBot} 
        className="fixed bottom-4 right-4 bg-blue-500 text-white p-4 rounded-full shadow-lg hover:bg-blue-600 transition-all duration-200"
      >
        <FiMessageSquare size={24} />
      </button>

      {showChatBot && <ChatBot messages={chatMessages} onSend={handleSendMessage} onKeyPress={handleKeyPress} newChatMessage={newChatMessage} setNewChatMessage={setNewChatMessage} />}
    </div>
  );
};

export default Dashboard;
