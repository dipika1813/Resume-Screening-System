import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  initStorage,
  getActiveUser,
  setActiveUser,
  clearActiveUser,
  getUserById,
  getUserByEmail,
  loginUser,
  createUser,
  updateUser as updateStorageUser,
} from '../services/storageService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(() => getActiveUser());
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    // Load all data from MySQL before showing the app
    initStorage()
      .then(() => {
        const active = getActiveUser();
        if (active) {
          const fresh = getUserById(active.id);
          if (fresh) {
            setActiveUser(fresh);
            setCurrentUser(fresh);
          } else {
            clearActiveUser();
            setCurrentUser(null);
          }
        }
      })
      .catch(() => {
        setLoadError('Cannot connect to the backend. Start it with: cd backend, then npm start');
      })
      .finally(() => setLoading(false));
  }, []);

  // NOTE: login and register are now async (they talk to MySQL). Use await.
  const login = async (email, password) => {
    const user = await loginUser(email, password);
    setActiveUser(user);
    setCurrentUser(user);
    return user;
  };

  const register = async (userData) => {
    const newUser = await createUser(userData);
    setActiveUser(newUser);
    setCurrentUser(newUser);
    return newUser;
  };

  const logout = () => {
    clearActiveUser();
    setCurrentUser(null);
  };

  const updateProfile = (updates) => {
    if (!currentUser) return null;
    const updated = updateStorageUser(currentUser.id, updates);
    setCurrentUser(updated);
    return updated;
  };

  // Demo utility: switch between demo profiles instantly
  const switchDemoAccount = (email) => {
    const user = getUserByEmail(email);
    if (user) {
      setActiveUser(user);
      setCurrentUser(user);
      return user;
    }
    return null;
  };

  const isCandidate = currentUser?.role === 'candidate';
  const isRecruiter = currentUser?.role === 'recruiter';

  if (loading) {
    return <div style={{ padding: 40, fontFamily: 'sans-serif' }}>Loading data from database...</div>;
  }
  if (loadError) {
    return <div style={{ padding: 40, fontFamily: 'sans-serif', color: 'crimson' }}>{loadError}</div>;
  }

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        loading,
        login,
        register,
        logout,
        updateProfile,
        switchDemoAccount,
        isCandidate,
        isRecruiter,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}