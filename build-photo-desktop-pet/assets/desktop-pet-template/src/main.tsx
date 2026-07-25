import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import IdlePreview from "./IdlePreview";
import "./styles.css";

if (!window.__TAURI_INTERNALS__) {
  document.documentElement.classList.add("browser-preview");
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <IdlePreview />
  </StrictMode>,
);
