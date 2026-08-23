import { LockKeyhole, Mail, Plane } from "lucide-react";
import { useState } from "react";
import { useAuth } from "../auth/AuthProvider";

export default function Login() {
  const { login, loading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    try {
      await login(email, password);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel">
        <div className="brand-mark">
          <Plane size={28} />
        </div>
        <h1>ParcelPilot</h1>
        <p className="subtitle">Secure support operations for shipment teams.</p>

        <form onSubmit={handleSubmit} className="login-form">
          <label>
            Email
            <span className="input-row">
              <Mail size={18} />
              <input
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
              />
            </span>
          </label>
          <label>
            Password
            <span className="input-row">
              <LockKeyhole size={18} />
              <input
                value={password}
                type="password"
                autoComplete="current-password"
                placeholder="Enter your password"
                onChange={(event) => setPassword(event.target.value)}
              />
            </span>
          </label>
          {error ? <p className="error-text">{error}</p> : null}
          <button type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}
