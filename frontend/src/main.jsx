import React from "react";
import { createRoot } from "react-dom/client";
import { AuthProvider, useAuth } from "./auth/AuthProvider";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import SupportPortal from "./support/SupportPortal";
import "./styles.css";

function App() {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <main className="login-shell">
        <section className="login-panel">
          <h1>ParcelPilot</h1>
          <p className="subtitle">Restoring your session...</p>
        </section>
      </main>
    );
  }
  if (!user) {
    return <Login />;
  }
  if (user.role === "SUPPORT" || user.role === "ADMIN") {
    return <SupportPortal />;
  }
  return <Dashboard />;
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>
);
