import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, useNavigate } from 'react-router-dom'
import { Auth0Provider } from '@auth0/auth0-react'
import './index.css'
import App from './App.jsx'

const AUTH0_DOMAIN = import.meta.env.VITE_AUTH0_DOMAIN
const AUTH0_CLIENT_ID = import.meta.env.VITE_AUTH0_CLIENT_ID

/**
 * Auth0ProviderWithNavigate
 * A wrapper that enables using useNavigate() inside onRedirectCallback.
 * IMPORTANT: Skipped on public /passport/ routes so they work from any origin
 * (e.g., NFC scans via network IP) without needing Auth0 configuration.
 */
const Auth0ProviderWithNavigate = ({ children }) => {
  const navigate = useNavigate();

  // Public routes that don't need Auth0 — skip the provider entirely
  const isPublicRoute = window.location.pathname.startsWith('/passport/');

  if (isPublicRoute) {
    return <>{children}</>;
  }

  const onRedirectCallback = (appState) => {
    // Navigate to the 'returnTo' path or current path
    navigate(appState?.returnTo || window.location.pathname);
  };

  return (
    <Auth0Provider
      domain={AUTH0_DOMAIN || "dev-placeholder.auth0.com"}
      clientId={AUTH0_CLIENT_ID || "dev-placeholder-client-id"}
      authorizationParams={{
        redirect_uri: window.location.origin,
        audience: import.meta.env.VITE_AUTH0_AUDIENCE || "https://fair-hiring-api",
        scope: "openid profile email",
      }}
      onRedirectCallback={onRedirectCallback}
      cacheLocation="localstorage"
    >
      {children}
    </Auth0Provider>
  );
};

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Auth0ProviderWithNavigate>
        <App />
      </Auth0ProviderWithNavigate>
    </BrowserRouter>
  </StrictMode>,
)
