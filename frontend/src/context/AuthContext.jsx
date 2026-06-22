import { createContext, useContext, useEffect, useState } from "react";
import api from "../api/client";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access");
    if (!token) return setLoading(false);
    api
      .get("/auth/me/")
      .then(({ data }) => setUser(data))
      .catch(() => localStorage.clear())
      .finally(() => setLoading(false));
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login/", { email, password });
    localStorage.setItem("access", data.access);
    localStorage.setItem("refresh", data.refresh);
    setUser(data.user);
    return data.user;
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
  };

  const refreshUser = () => api.get("/auth/me/").then(({ data }) => setUser(data));

  // Layer 3 helper: can the current user do `action` on `module`?
  const can = (module, action = "view") => {
    if (!user) return false;
    if (user.is_admin_view && user.dashboard === "admin") return true; // super admin / founder
    return !!user.modules?.[module]?.[action];
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, can, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}
