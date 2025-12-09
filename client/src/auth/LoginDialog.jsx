
// src/auth/LoginDialog.jsx
import { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
} from "@mui/material";

function LoginDialog({ open, onClose, onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    setError(null);
    setSubmitting(true);
    try {
      await onLogin(username, password);
      // AuthProvider's login will close dialog on success
    } catch (err) {
      const detail =
        err?.response?.data?.detail ||
        err?.message ||
        "Login failed, please try again";
      setError(detail);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={submitting ? undefined : onClose}>
      <DialogTitle>Sign in</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 1, display: "flex", flexDirection: "column", gap: 2 }}>
          <TextField
            label="Username"
            fullWidth
            size="small"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoFocus
          />
          <TextField
            label="Password"
            type="password"
            fullWidth
            size="small"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error && (
            <Box sx={{ color: "error.main", fontSize: 13 }}>{error}</Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={submitting}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={submitting}
        >
          {submitting ? "Signing in..." : "Sign in"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default LoginDialog;
