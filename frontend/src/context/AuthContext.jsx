import { createContext, useContext, useState, useEffect } from 'react';
import { login as apiLogin, checkAuth, apiLogout } from '../lib/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in via cookies on mount
    checkAuth()
      .then(data => {
        setUser({ role: data.role, full_name: data.full_name, username: data.username });
      })
      .catch(() => {
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const login = async (username, password) => {
    const data = await apiLogin(username, password);
    setUser({ role: data.role, full_name: data.full_name, username });
  };

  const logout = async () => {
    try {
      await apiLogout();
    } catch (e) {
      console.error('Logout failed', e);
    }
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {loading ? (
        <div className="min-h-screen bg-black flex flex-col items-center justify-center text-mono">
          <div className="w-12 h-12 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin mb-4 shadow-[0_0_15px_rgba(0,229,255,0.5)]"></div>
          <div className="text-cyan-400 font-bold tracking-widest text-sm animate-pulse">CONNECTING TO VITALWATCH CORE...</div>
          <div className="text-gray-600 text-xs mt-2 font-mono">Verifying secure session & backend health</div>
        </div>
      ) : (
        children
      )}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

