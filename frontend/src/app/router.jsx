import {
  Navigate,
  createBrowserRouter,
} from "react-router-dom";

import ProtectedRoute from "../auth/ProtectedRoute";
import RoleRoute from "../auth/RoleRoute";
import AppShell from "../components/layout/AppShell";

import DashboardPage from "../pages/DashboardPage";
import FeaturePlaceholderPage from "../pages/FeaturePlaceholderPage";
import LoginPage from "../pages/LoginPage";
import NotFoundPage from "../pages/NotFoundPage";
import UnauthorizedPage from "../pages/UnauthorizedPage";

function placeholder(
  title,
  description,
) {
  return (
    <FeaturePlaceholderPage
      title={title}
      description={description}
    />
  );
}

const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <Navigate
        to="/dashboard"
        replace
      />
    ),
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/unauthorized",
    element: <UnauthorizedPage />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          {
            path: "/dashboard",
            element: <DashboardPage />,
          },
          {
            path: "/notifications",
            element: placeholder(
              "Notifications",
              "View reminders and workflow updates.",
            ),
          },
          {
            path: "/profile",
            element: placeholder(
              "Profile",
              "Manage your participant information.",
            ),
          },
          {
            path: "/analytics",
            element: placeholder(
              "Impact analytics",
              "Review redistribution activity and impact.",
            ),
          },

          {
            element: (
              <RoleRoute
                allowedRoles={["DONOR"]}
              />
            ),
            children: [
              {
                path: "/donations",
                element: placeholder(
                  "My donations",
                  "Create and manage food donations.",
                ),
              },
              {
                path: "/requests",
                element: placeholder(
                  "Receiver requests",
                  "Review incoming receiver requests.",
                ),
              },
            ],
          },

          {
            element: (
              <RoleRoute
                allowedRoles={["RECEIVER"]}
              />
            ),
            children: [
              {
                path: "/discover",
                element: placeholder(
                  "Discover donations",
                  "Find compatible food donations.",
                ),
              },
              {
                path: "/requests",
                element: placeholder(
                  "My requests",
                  "Track your donation requests.",
                ),
              },
              {
                path: "/received",
                element: placeholder(
                  "Food received",
                  "Review completed receipts.",
                ),
              },
            ],
          },

          {
            element: (
              <RoleRoute
                allowedRoles={["VOLUNTEER"]}
              />
            ),
            children: [
              {
                path: "/volunteer/tasks",
                element: placeholder(
                  "Available tasks",
                  "Find eligible transport tasks.",
                ),
              },
              {
                path: "/volunteer/deliveries",
                element: placeholder(
                  "My deliveries",
                  "Track accepted transport tasks.",
                ),
              },
            ],
          },

          {
            element: (
              <RoleRoute
                allowedRoles={["ADMIN"]}
              />
            ),
            children: [
              {
                path: "/admin/participants",
                element: placeholder(
                  "Participants",
                  "Manage SmartFood participants.",
                ),
              },
              {
                path: "/admin/verifications",
                element: placeholder(
                  "Verifications",
                  "Review verification submissions.",
                ),
              },
              {
                path: "/admin/operations",
                element: placeholder(
                  "Operations",
                  "Review operational issues.",
                ),
              },
            ],
          },
        ],
      },
    ],
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
]);

export default router;