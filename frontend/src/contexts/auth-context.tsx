"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError, clearAuthToken, getCurrentUser, getStoredAuthToken, login, setAuthToken, type UserResponse } from "@/lib/api-client";

type AuthStatus = "loading" | "ready";

type AuthContextValue = {
  user: UserResponse | null;
  isAuthenticated: boolean;
  status: AuthStatus;
  signIn: (payload: { organization_code: string; email: string; password: string }) => Promise<void>;
  signOut: () => void;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");
  const router = useRouter();

  const refreshUser = async () => {
    const token = getStoredAuthToken();
    if (!token) {
      setUser(null);
      setStatus("ready");
      return;
    }

    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      setStatus("ready");
    } catch (error) {
      clearAuthToken();
      setUser(null);
      setStatus("ready");
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
        router.replace("/login");
      }
    }
  };

  useEffect(() => {
    void refreshUser();
  }, []);

  const signIn = async (payload: { organization_code: string; email: string; password: string }) => {
    const response = await login(payload);
    setAuthToken(response.access_token);
    setUser(response.user);
    setStatus("ready");
    router.replace("/");
  };

  const signOut = () => {
    clearAuthToken();
    setUser(null);
    setStatus("ready");
    router.replace("/login");
  };

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      status,
      signIn,
      signOut,
      refreshUser,
    }),
    [user, status, router],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
