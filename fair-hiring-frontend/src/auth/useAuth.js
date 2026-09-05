/**
 * useAuth — Custom Auth0 hook for Fair Hiring Network
 *
 * Wraps useAuth0 and adds:
 *  - syncWithBackend()  -> sends Auth0 user info to create/retrieve the DB row
 */
import { useAuth0 } from "@auth0/auth0-react";
import { useCallback } from "react";

const BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL || "http://localhost:8012";

export function useAuth() {
  const {
    user,
    isAuthenticated,
    isLoading,
    loginWithRedirect,
    logout,
  } = useAuth0();

  /**
   * Calls POST /auth/candidate/auth0-sync with the Auth0 user info.
   * The backend creates or retrieves the DB Candidate row.
   * Returns { anon_id, email, name, … }
   */
  const syncWithBackend = useCallback(async () => {
    if (!user) throw new Error("Not authenticated");

    const res = await fetch(`${BACKEND_URL}/auth/candidate/auth0-sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sub:   user.sub,
        email: user.email || "",
        name:  user.name || user.nickname || user.email?.split("@")[0] || "candidate",
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Sync failed: HTTP ${res.status}`);
    }

    return res.json(); // { anon_id, email, name, … }
  }, [user]);

  return {
    user,
    isAuthenticated,
    isLoading,
    loginWithRedirect,
    logout,
    syncWithBackend,
  };
}
