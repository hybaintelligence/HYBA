import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { loginApi, registerApi, fetchProfileApi, logout as apiLogout, type AuthResponse } from "../apiClient";

interface AuthUser {
  id?: string;
  username: string;
  role: string;
  createdAt?: string;
}

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<AuthResponse>;
  register: (username: string, password: string) => Promise<AuthResponse>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = "hyba_auth_token";

function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY) || localStorage.getItem("quantum_token");
  } catch {
    return null;
  }
}

function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // noop
  }
}

function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem("quantum_token");
  } catch {
    // noop
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setTokenState] = useState<string | null>(() => getToken());
  const [isLoading, setIsLoading] = useState(true);

  const refreshProfile = useCallback(async () => {
    const currentToken = getToken();
    if (!currentToken) {
      setUser(null);
      setTokenState(null);
      setIsLoading(false);
      return;
    }

    try {
      const res = await fetchProfileApi();
      const data: AuthResponse = await res.json();
      if (data.success && data.user) {
        setUser(data.user);
        setTokenState(currentToken);
      } else {
        clearToken();
        setUser(null);
        setTokenState(null);
      }
    } catch {
      clearToken();
      setUser(null);
      setTokenState(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshProfile();
  }, [refreshProfile]);

  const login = async (username: string, password: string) => {
    const data = await loginApi({ username, password });
    if (data.success && data.token) {
      setToken(data.token);
      setTokenState(data.token);
      setUser(data.user || null);
    }
    return data;
  };

  const register = async (username: string, password: string) => {
    const data = await registerApi({ username, password });
    return data;
  };

  const logout = () => {
    apiLogout();
    clearToken();
    setUser(null);
    setTokenState(null);
  };

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated: !!token && !!user,
    login,
    register,
    logout,
    refreshProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
