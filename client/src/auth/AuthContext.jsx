// src/auth/AuthContext.jsx
import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import axios from "axios";
import LoginDialog from "./LoginDialog";

const apiBase = import.meta.env.VITE_API_URL || "http://127.0.0.1:8001";

const AuthContext = createContext(undefined);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("auth_token"));
  const [loginOpen, setLoginOpen] = useState(false);

  const persistToken = (newToken) => {
    setToken(newToken);
    if (newToken) {
      localStorage.setItem("auth_token", newToken);
    } else {
      localStorage.removeItem("auth_token");
    }
  };

  const login = useCallback(async (username, password) => {
    const res = await axios.post(`${apiBase}/login`, {
      "email": username,
      "password": password,
    });

    // Adjust to match your FastAPI response
    const accessToken = res.data.access_token;
    persistToken(accessToken);
    setLoginOpen(false);

    window.location.reload();
  }, []);

  const logout = useCallback(() => {
    persistToken(null);
  }, []);

  /**
   * Generic wrapper for ANY axios request:
   * - JSON, multipart, whatever
   * - Only injects Authorization header
   */
  const authRequest = useCallback(
    async (config) => {
      if (!token) {
        setLoginOpen(true);
        throw new Error("Not authenticated");
      }

      try {
        const res = await axios.request({
          baseURL: apiBase,
          ...config,
          headers: {
            ...(config.headers || {}),
            // Only add this one header
            Authorization: `Bearer ${token}`,
          },
        });
        return res;
      } catch (err) {
        if (err?.response?.status === 401) {
          // Token invalid / expired
          persistToken(null);
          setLoginOpen(true);
        }
        throw err;
      }
    },
    [token]
  );

  const showLogin = useCallback(() => setLoginOpen(true), []);

  return (
    <AuthContext.Provider
      value={{
        token,
        login,
        logout,
        authRequest,
        showLogin,
      }}
    >
      {children}

      <LoginDialog
        open={loginOpen}
        onClose={() => setLoginOpen(false)}
        onLogin={login}
      />
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
