import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import TransactionAnalyzer from './components/TransactionAnalyzer';
import './index.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [userIds, setUserIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API_URL}/usuarios`);
      if (response.data.usuarios && response.data.usuarios.length > 0) {
        setUserIds(response.data.usuarios);
      } else {
        // Si no hay usuarios, usar IDs de ejemplo
        console.warn('No hay usuarios en la base de datos');
        setUserIds(['550e8400-e29b-41d4-a716-446655440000']);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      // Usar IDs de ejemplo en caso de error
      setUserIds(['550e8400-e29b-41d4-a716-446655440000']);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-2xl">Cargando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Tabs */}
        <div className="pt-6">
          <div className="border-b border-blue-700">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`${
                  activeTab === 'dashboard'
                    ? 'border-white text-white'
                    : 'border-transparent text-blue-300 hover:text-white hover:border-blue-400'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveTab('analyzer')}
                className={`${
                  activeTab === 'analyzer'
                    ? 'border-white text-white'
                    : 'border-transparent text-blue-300 hover:text-white hover:border-blue-400'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
              >
                Analizar Transacción
              </button>
            </nav>
          </div>
        </div>

        {/* Content */}
        <div className="py-8">
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'analyzer' && <TransactionAnalyzer userIds={userIds} />}
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-12 py-6 text-center text-blue-300 text-sm">
        <p>Sistema de Detección de Fraude v2.0 | Desarrollado con Apache Cassandra + FastAPI + React</p>
      </footer>
    </div>
  );
}

export default App;
