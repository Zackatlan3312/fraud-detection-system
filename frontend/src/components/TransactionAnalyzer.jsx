import React, { useState } from 'react';
import { Send, Loader, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import axios from 'axios';

const TransactionAnalyzer = ({ userIds }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [formData, setFormData] = useState({
    id_usuario: userIds[0] || '',
    monto: '',
    moneda: 'MXN',
    comercio: '',
    ciudad: '',
    pais: 'Mexico',
    mcc: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const response = await axios.post('http://localhost:8000/analizar-transaccion', {
        ...formData,
        monto: parseFloat(formData.monto),
        mcc: parseInt(formData.mcc)
      });
      setResult(response.data);
    } catch (error) {
      console.error('Error:', error);
      setResult({ 
        status: 'ERROR', 
        motivo: 'Error al conectar con el servidor',
        score_riesgo: 0,
        banderas_rojas: []
      });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'APROBADO':
        return <CheckCircle className="h-12 w-12 text-green-500" />;
      case 'RECHAZADO':
        return <XCircle className="h-12 w-12 text-red-500" />;
      case 'REVISION_MANUAL':
        return <AlertCircle className="h-12 w-12 text-orange-500" />;
      default:
        return <AlertCircle className="h-12 w-12 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'APROBADO':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'RECHAZADO':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'REVISION_MANUAL':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      <h3 className="text-2xl font-bold text-gray-800 mb-6">Analizar TransacciÃ³n</h3>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ID Usuario
            </label>
            <select
              name="id_usuario"
              value={formData.id_usuario}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              {userIds.map((id) => (
                <option key={id} value={id}>{id.substring(0, 8)}...</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Monto
            </label>
            <input
              type="number"
              name="monto"
              value={formData.monto}
              onChange={handleChange}
              step="0.01"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="0.00"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Moneda
            </label>
            <select
              name="moneda"
              value={formData.moneda}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              <option value="MXN">MXN</option>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Comercio
            </label>
            <input
              type="text"
              name="comercio"
              value={formData.comercio}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Nombre del comercio"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Ciudad
            </label>
            <input
              type="text"
              name="ciudad"
              value={formData.ciudad}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Ciudad"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              PaÃ­s
            </label>
            <input
              type="text"
              name="pais"
              value={formData.pais}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="PaÃ­s"
              required
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              MCC (CategorÃ­a)
            </label>
            <select
              name="mcc"
              value={formData.mcc}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              <option value="">Seleccionar...</option>
              <option value="5411">5411 - Supermercados</option>
              <option value="5812">5812 - Restaurantes</option>
              <option value="5814">5814 - CafeterÃ­as</option>
              <option value="5541">5541 - Gasolineras</option>
              <option value="5999">5999 - Comercio en lÃ­nea</option>
              <option value="7995">7995 - Apuestas (Alto Riesgo)</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <Loader className="h-5 w-5 animate-spin" />
              <span>Analizando...</span>
            </>
          ) : (
            <>
              <Send className="h-5 w-5" />
              <span>Analizar TransacciÃ³n</span>
            </>
          )}
        </button>
      </form>

      {result && (
        <div className="mt-8 space-y-4">
          <div className={`border-2 rounded-lg p-6 ${getStatusColor(result.status)}`}>
            <div className="flex items-center space-x-4">
              {getStatusIcon(result.status)}
              <div className="flex-1">
                <h4 className="text-2xl font-bold">{result.status}</h4>
                <p className="text-sm mt-1">{result.motivo}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium">Score de Riesgo</p>
                <p className="text-3xl font-bold">{result.score_riesgo}%</p>
              </div>
            </div>
          </div>

          {result.banderas_rojas && result.banderas_rojas.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-6">
              <h5 className="font-semibold text-gray-800 mb-3">Banderas Rojas Detectadas:</h5>
              <ul className="space-y-2">
                {result.banderas_rojas.map((bandera, index) => (
                  <li key={index} className="flex items-center space-x-2">
                    <AlertCircle className="h-5 w-5 text-red-500" />
                    <span className="text-gray-700">{bandera}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TransactionAnalyzer;