import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle } from 'lucide-react';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalTransactions: 0,
    approvedTransactions: 0,
    rejectedTransactions: 0,
    pendingReview: 0
  });

  useEffect(() => {
    setStats({
      totalTransactions: 90,
      approvedTransactions: 65,
      rejectedTransactions: 20,
      pendingReview: 5
    });
  }, []);

  const StatCard = ({ title, value, icon: Icon, color, trend }) => (
    <div className="bg-white rounded-lg shadow-md p-6 card-hover">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 font-medium">{title}</p>
          <p className={`text-3xl font-bold mt-2 ${color}`}>{value}</p>
          {trend && (
            <div className="flex items-center mt-2">
              {trend > 0 ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500" />
              )}
              <span className={`text-sm ml-1 ${trend > 0 ? 'text-green-500' : 'text-red-500'}`}>
                {Math.abs(trend)}%
              </span>
            </div>
          )}
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
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Transacciones"
          value={stats.totalTransactions}
          icon={TrendingUp}
          color="text-blue-600"
          trend={12}
        />
        
        <StatCard
          title="Aprobadas"
          value={stats.approvedTransactions}
          icon={CheckCircle}
          color="text-green-600"
          trend={8}
        />
        
        <StatCard
          title="Rechazadas"
          value={stats.rejectedTransactions}
          icon={AlertTriangle}
          color="text-red-600"
          trend={-3}
        />
        
        <StatCard
          title="En RevisiÃ³n"
          value={stats.pendingReview}
          icon={AlertTriangle}
          color="text-orange-600"
        />
      </div>
    </div>
  );
};

export default Dashboard;