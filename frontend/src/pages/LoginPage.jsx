import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';

export default function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
    } catch (err) {
      setError('Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex flex-col justify-center items-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <div className="mb-10 text-center">
          <div className="text-cyan-400 font-mono tracking-[0.3em] uppercase text-xs mb-3">Clinical AI System</div>
          <h1 className="text-4xl font-bold text-white tracking-tight">VitalWatch<span className="text-cyan-400">.</span></h1>
        </div>
        
        <div className="bg-gray-950 border border-gray-800 p-8 rounded-xl shadow-2xl relative overflow-hidden">
          {/* Subtle gradient background accent */}
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-400 to-blue-600"></div>
          
          <h2 className="text-white text-lg font-medium mb-6">System Authentication</h2>
          
          {error && (
            <div className="bg-red-950/40 border border-red-900/50 text-red-400 px-4 py-3 rounded text-sm mb-6 flex items-center">
              <span className="mr-2">⚠</span> {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-gray-400 text-xs uppercase tracking-wider mb-2 font-mono">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 text-white rounded px-4 py-3 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all font-mono text-sm"
                placeholder="Enter clinical ID"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-400 text-xs uppercase tracking-wider mb-2 font-mono">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 text-white rounded px-4 py-3 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all font-mono text-sm"
                placeholder="••••••••"
                required
              />
            </div>
            
            <button
              type="submit"
              disabled={loading}
              className={`w-full bg-cyan-500 hover:bg-cyan-400 text-black font-bold py-3 px-4 rounded transition-colors mt-4 flex items-center justify-center ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin"></div>
                  Authenticating...
                </span>
              ) : (
                'Secure Login'
              )}
            </button>
          </form>
          
          <div className="mt-8 pt-6 border-t border-gray-800 text-center">
            <p className="text-gray-500 text-xs font-mono">
              Use <span className="text-gray-300">admin / admin123</span> or <span className="text-gray-300">doctor / doctor123</span>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
