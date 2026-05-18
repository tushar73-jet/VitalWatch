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
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

