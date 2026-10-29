import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Database, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

const API_URL = 'http://localhost:8000';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(false);

  // Se monta cada vez que se abre la pestaña, así que los números se refrescan solos
  useEffect(() => {
    axios.get(`${API_URL}/resumen`)
      .then((response) => setStats(response.data))
      .catch((err) => {
        console.error('Error obteniendo resumen:', err);
        setError(true);
      });
  }, []);

  const valor = (campo) => (stats && stats[campo] !== null ? stats[campo] : '-');

  const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className="bg-white rounded-lg shadow-md p-6 card-hover">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 font-medium">{title}</p>
          <p className={`text-3xl font-bold mt-2 ${color}`}>{value}</p>
        </div>
        <div className={`p-3 rounded-full ${color.replace('text-', 'bg-').replace('600', '100')}`}>
          <Icon className={`h-8 w-8 ${color}`} />
        </div>
      </div>
    </div>
  );

  return (
    <div className="py-8">
      <h2 className="text-3xl font-bold text-white mb-6">Dashboard</h2>

      {error && (
        <p className="mb-6 text-red-200">
          No se pudo obtener el resumen. Revisa que la API esté corriendo en {API_URL}.
        </p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Guardadas en Cassandra"
          value={valor('transacciones_guardadas')}
          icon={Database}
          color="text-blue-600"
        />

        <StatCard
          title="Aprobadas"
          value={valor('aprobadas')}
          icon={CheckCircle}
          color="text-green-600"
        />

        <StatCard
          title="Rechazadas"
          value={valor('rechazadas')}
          icon={XCircle}
          color="text-red-600"
        />

        <StatCard
          title="En Revisión"
          value={valor('en_revision')}
          icon={AlertTriangle}
          color="text-orange-600"
        />
      </div>

      <p className="mt-4 text-sm text-blue-200">
        Aprobadas, rechazadas y en revisión cuentan los análisis hechos desde que se inició la API.
      </p>
    </div>
  );
};

export default Dashboard;
