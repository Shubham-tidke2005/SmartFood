import {
  StrictMode,
} from "react";

import {
  createRoot,
} from "react-dom/client";

import {
  RouterProvider,
} from "react-router-dom";

import * as RouterModule from "./app/router.jsx";

import * as AuthModule from "./auth/AuthProvider.jsx";

import "./index.css";


const router =
  RouterModule.default ||
  RouterModule.router;

const AuthProvider =
  AuthModule.default ||
  AuthModule.AuthProvider;


if (!router) {
  throw new Error(
    "router.jsx must export the router as default or as 'router'.",
  );
}


if (!AuthProvider) {
  throw new Error(
    "AuthProvider.jsx must export AuthProvider.",
  );
}


createRoot(
  document.getElementById("root"),
).render(
  <StrictMode>
    <AuthProvider>
      <RouterProvider
        router={router}
      />
    </AuthProvider>
  </StrictMode>,
);