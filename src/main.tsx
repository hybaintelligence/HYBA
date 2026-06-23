import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { AuthProvider } from "./components/AuthProvider";
import { WebSocketProvider } from "./components/WebSocketProvider";

const ENABLE_WEBSOCKET = import.meta.env.VITE_ENABLE_WEBSOCKET !== "false";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary>
      <WebSocketProvider enabled={ENABLE_WEBSOCKET}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </WebSocketProvider>
    </ErrorBoundary>
  </StrictMode>,
);
