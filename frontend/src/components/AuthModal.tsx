import { useState, type FormEvent } from "react";
import { api, authStorage } from "../api/client";
import type { User } from "../types";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: User) => void;
  initialMode?: "login" | "register" | "forgot";
}

export function AuthModal({
  isOpen,
  onClose,
  onSuccess,
  initialMode = "login",
}: AuthModalProps) {
  const [mode, setMode] = useState<"login" | "register" | "forgot">(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  if (!isOpen) return null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);

    try {
      if (mode === "login") {
        const res = await api.auth.login({ email, password });
        authStorage.setToken(res.access_token);
        onSuccess(res.user);
        onClose();
      } else if (mode === "register") {
        const res = await api.auth.register({ email, password, name });
        authStorage.setToken(res.access_token);
        onSuccess(res.user);
        onClose();
      } else if (mode === "forgot") {
        const res = await api.auth.forgotPassword(email);
        setMessage(res.message);
        if (res.reset_token) {
          setMessage(`${res.message} Reset token: ${res.reset_token}`);
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>
            {mode === "login"
              ? "Sign In to OpenTrace"
              : mode === "register"
              ? "Create Free Account"
              : "Reset Password"}
          </h3>
          <button className="btn-close" onClick={onClose} aria-label="Close modal">
            ×
          </button>
        </div>

        {error && <div className="auth-alert error">{error}</div>}
        {message && <div className="auth-alert success">{message}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          {mode === "register" && (
            <div className="form-group">
              <label htmlFor="auth-name">Full Name or Handle</label>
              <input
                id="auth-name"
                type="text"
                required
                placeholder="e.g. Alex Morgan"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="auth-email">Email Address</label>
            <input
              id="auth-email"
              type="email"
              required
              placeholder="you@domain.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          {mode !== "forgot" && (
            <div className="form-group">
              <label htmlFor="auth-password">Password</label>
              <input
                id="auth-password"
                type="password"
                required
                placeholder="Minimum 8 characters"
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          )}

          <button type="submit" className="btn-primary full-width" disabled={loading}>
            {loading
              ? "Processing..."
              : mode === "login"
              ? "Sign In"
              : mode === "register"
              ? "Create Account"
              : "Send Reset Token"}
          </button>
        </form>

        <div className="auth-footer">
          {mode === "login" ? (
            <>
              <button
                type="button"
                className="link-button"
                onClick={() => {
                  setMode("forgot");
                  setError("");
                }}
              >
                Forgot password?
              </button>
              <span> · </span>
              <button
                type="button"
                className="link-button"
                onClick={() => {
                  setMode("register");
                  setError("");
                }}
              >
                Don't have an account? Sign up
              </button>
            </>
          ) : (
            <button
              type="button"
              className="link-button"
              onClick={() => {
                setMode("login");
                setError("");
              }}
            >
              Already have an account? Sign in
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
