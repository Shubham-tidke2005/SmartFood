import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router-dom";

import router from "./app/router.jsx";
import AuthProvider from "./auth/AuthProvider.jsx";

import "./index.css";

//main
const rootElement =
  document.getElementById("root");

if (!rootElement) {
  throw new Error(
    'Root element with id "root" was not found.',
  );
}

createRoot(rootElement).render(
  <StrictMode>
    <AuthProvider>
      <RouterProvider
        router={router}
      />
    </AuthProvider>
  </StrictMode>,
);