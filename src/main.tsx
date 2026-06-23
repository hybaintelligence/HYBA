import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { AuthProvider } from "./components/AuthProvider";
import { WebSocketProvider } from "./components/WebSocketProvider";
import { CustomerBoundaryEnforcer } from "./components/CustomerBoundaryEnforcer";

const ENABLE_WEBSOCKET = import.meta.env.VITE_ENABLE_WEBSOCKET !== "false";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary>
      <WebSocketProvider enabled={ENABLE_WEBSOCKET}>
        <AuthProvider>
          <CustomerBoundaryEnforcer />
          <App />
        </AuthProvider>
      </WebSocketProvider>
    </ErrorBoundary>
  </StrictMode>,
);
