import {
  Navigate,
  createBrowserRouter,
} from "react-router-dom";

import ProtectedRoute from "../auth/ProtectedRoute";
import RoleRoute from "../auth/RoleRoute";
import AppShell from "../components/layout/AppShell";

import DashboardPage from "../pages/DashboardPage";
import LoginPage from "../pages/LoginPage";
import NotFoundPage from "../pages/NotFoundPage";
import UnauthorizedPage from "../pages/UnauthorizedPage";

import {
  CreateDonationPage,
  DonorDonationDetailPage,
  DonorHistoryPage,
  DonorRequestsPage,
} from "../pages/donor/DonorPages";

import {
  BrowseDonationsPage,
  ReceiptConfirmationPage,
  ReceiverDonationDetailPage,
  ReceiverRequestsPage,
  ReceiverRequirementsPage,
} from "../pages/receiver/ReceiverPages";

import {
  ActiveTaskPage,
  AvailableTasksPage,
  VolunteerTaskHistoryPage,
} from "../pages/volunteer/VolunteerPages";

import {
  AdminAnalyticsPage,
  AdminComplaintsPage,
  AdminDonationsPage,
  AdminUsersPage,
  VerificationQueuePage,
} from "../pages/admin/AdminPages";

import {
  HelpReportingPage,
  NotificationsPage,
  PasswordResetPage,
  ProfilePage,
  RegistrationPage,
} from "../pages/shared/SharedPages";

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
    path: "/register",
    element: <RegistrationPage />,
  },
  {
    path: "/password-reset",
    element: <PasswordResetPage />,
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
            path: "/profile",
            element: <ProfilePage />,
          },
          {
            path: "/notifications",
            element: <NotificationsPage />,
          },
          {
            path: "/help",
            element: <HelpReportingPage />,
          },

          {
            element: (
              <RoleRoute
                allowedRoles={["DONOR"]}
              />
            ),
            children: [
              {
                path: "/donor/donations/new",
                element: <CreateDonationPage />,
              },
              {
                path: "/donor/donations/:donationId",
                element: <DonorDonationDetailPage />,
              },
              {
                path: "/donor/requests",
                element: <DonorRequestsPage />,
              },
              {
                path: "/donor/history",
                element: <DonorHistoryPage />,
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
                path: "/receiver/donations",
                element: <BrowseDonationsPage />,
              },
              {
                path: "/receiver/donations/:donationId",
                element: <ReceiverDonationDetailPage />,
              },
              {
                path: "/receiver/requirements",
                element: <ReceiverRequirementsPage />,
              },
              {
                path: "/receiver/requests",
                element: <ReceiverRequestsPage />,
              },
              {
                path: "/receiver/receipts/:donationId",
                element: <ReceiptConfirmationPage />,
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
                element: <AvailableTasksPage />,
              },
              {
                path: "/volunteer/tasks/:taskId",
                element: <ActiveTaskPage />,
              },
              {
                path: "/volunteer/history",
                element: <VolunteerTaskHistoryPage />,
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
                path: "/admin/verifications",
                element: <VerificationQueuePage />,
              },
              {
                path: "/admin/users",
                element: <AdminUsersPage />,
              },
              {
                path: "/admin/donations",
                element: <AdminDonationsPage />,
              },
              {
                path: "/admin/complaints",
                element: <AdminComplaintsPage />,
              },
              {
                path: "/admin/analytics",
                element: <AdminAnalyticsPage />,
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