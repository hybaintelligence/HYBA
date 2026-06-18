import React, { createContext, useContext, useEffect, useState } from "react";
import { onAuthStateChanged, User } from "firebase/auth";
import { auth } from "../firebase";

interface BackendUser {
  id?: string;
  username: string;
  role: string;
  createdAt?: string;
}

interface AuthContextType {
  user: User | null;
  backendUser: BackendUser | null;
  loading: boolean;
  isAdmin: boolean;
  isExecutive: boolean;
  hasRole: (role: string) => boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  backendUser: null,
  loading: true,
  isAdmin: false,
  isExecutive: false,
  hasRole: () => false,
});

const EXECUTIVE_ROLES = ["ceo_heir_apparent", "chairman", "cto", "cfo", "legal", "chief_of_staff"];

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [backendUser, setBackendUser] = useState<BackendUser | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchBackendProfile = async (token: string | null) => {
    if (!token) {
      setBackendUser(null);
      return;
    }
    try {
      const response = await fetch("/api/auth/profile", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.user) {
          setBackendUser(data.user);
        }
      }
    } catch (error) {
      console.error("Failed to fetch backend profile:", error);
    }
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser);
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("hyba_auth_token") || localStorage.getItem("quantum_token");
    fetchBackendProfile(token);
  }, [user]);

  const isAdmin = backendUser?.role === "admin";
  const isExecutive = EXECUTIVE_ROLES.includes(backendUser?.role || "");
  const hasRole = (role: string) => backendUser?.role === role;

  return (
    <AuthContext.Provider value={{ user, backendUser, loading, isAdmin, isExecutive, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
