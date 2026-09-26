import {
  LogOut,
  Menu,
  X,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { AnimatePresence, motion } from "motion/react";

import { useAuth } from "../../auth/AuthProvider";
import { getNavigationForRole } from "../../config/navigation";
import { cn } from "../../lib/cn";
import Button from "../ui/Button";
import ConfirmDialog from "../ui/ConfirmDialog";
import StatusBadge from "../ui/StatusBadge";

function SmartFoodLogo() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex size-10 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-sky-500 font-black text-white shadow-lg shadow-blue-500/20">
        S
      </div>

      <div>
        <p className="text-lg font-black tracking-tight text-slate-950 dark:text-white">
          SmartFood
        </p>

        <p className="text-xs text-slate-500 dark:text-slate-400">
          Better redistribution
        </p>
      </div>
    </div>
  );
}

function NavigationLink({
  item,
  mobile = false,
  onNavigate,
}) {
  const Icon = item.icon;

  return (
    <NavLink
      to={item.path}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          "focus-ring flex items-center rounded-xl",
          "font-semibold transition-all duration-200",
          mobile
            ? "min-w-16 flex-col gap-1 px-2 py-2 text-[11px]"
            : "gap-3 px-3 py-2.5 text-sm",
          isActive
            ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
            : "text-slate-600 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white",
        )
      }
    >
      <Icon
        aria-hidden="true"
        className={
          mobile
            ? "size-5"
            : "size-4.5"
        }
      />

      <span>{item.label}</span>
    </NavLink>
  );
}

export default function AppShell() {
  const { user, logout } = useAuth();

  const location = useLocation();
  const navigate = useNavigate();

  const [mobileMenuOpen, setMobileMenuOpen] =
    useState(false);

  const [logoutDialogOpen, setLogoutDialogOpen] =
    useState(false);

  const [loggingOut, setLoggingOut] =
    useState(false);

  const navigation = useMemo(
    () => getNavigationForRole(user?.role),
    [user?.role],
  );

  const mobileNavigation = navigation.slice(0, 4);

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  async function handleLogout() {
    setLoggingOut(true);

    try {
      await logout();
      navigate("/login", {
        replace: true,
      });
    } finally {
      setLoggingOut(false);
      setLogoutDialogOpen(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <header className="glass-surface sticky top-0 z-30 border-b lg:hidden">
        <div className="flex h-16 items-center justify-between px-4">
          <SmartFoodLogo />

          <button
            type="button"
            aria-label={
              mobileMenuOpen
                ? "Close navigation"
                : "Open navigation"
            }
            aria-expanded={mobileMenuOpen}
            className="focus-ring rounded-xl p-2 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
            onClick={() =>
              setMobileMenuOpen((current) => !current)
            }
          >
            {mobileMenuOpen ? (
              <X
                aria-hidden="true"
                className="size-6"
              />
            ) : (
              <Menu
                aria-hidden="true"
                className="size-6"
              />
            )}
          </button>
        </div>
      </header>

      <aside className="fixed inset-y-0 left-0 z-40 hidden w-72 border-r border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900 lg:flex lg:flex-col">
        <SmartFoodLogo />

        <nav
          aria-label="Main navigation"
          className="mt-8 flex flex-1 flex-col gap-1.5"
        >
          {navigation.map((item) => (
            <NavigationLink
              key={item.path}
              item={item}
            />
          ))}
        </nav>

        <div className="border-t border-slate-200 pt-4 dark:border-slate-700">
          <div className="mb-4 rounded-2xl bg-slate-50 p-3 dark:bg-slate-800">
            <p className="truncate text-sm font-bold text-slate-950 dark:text-white">
              {user?.display_name ||
                user?.name ||
                user?.email}
            </p>

            <div className="mt-2 flex flex-wrap gap-2">
              <StatusBadge status={user?.role} />
              <StatusBadge
                status={
                  user?.verification_status ||
                  "PENDING"
                }
              />
            </div>
          </div>

          <Button
            variant="ghost"
            className="w-full justify-start"
            onClick={() =>
              setLogoutDialogOpen(true)
            }
          >
            <LogOut
              aria-hidden="true"
              className="size-4"
            />

            Sign out
          </Button>
        </div>
      </aside>

      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            <motion.button
              type="button"
              aria-label="Close mobile navigation"
              className="fixed inset-0 z-30 bg-slate-950/50 lg:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() =>
                setMobileMenuOpen(false)
              }
            />

            <motion.aside
              className="fixed inset-y-0 right-0 z-40 flex w-[min(86vw,22rem)] flex-col bg-white p-5 shadow-2xl dark:bg-slate-900 lg:hidden"
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{
                type: "spring",
                damping: 28,
                stiffness: 300,
              }}
            >
              <div className="flex items-center justify-between">
                <SmartFoodLogo />

                <button
                  type="button"
                  aria-label="Close navigation"
                  className="focus-ring rounded-xl p-2"
                  onClick={() =>
                    setMobileMenuOpen(false)
                  }
                >
                  <X
                    aria-hidden="true"
                    className="size-5"
                  />
                </button>
              </div>

              <nav
                aria-label="Mobile navigation"
                className="mt-8 flex flex-1 flex-col gap-2"
              >
                {navigation.map((item) => (
                  <NavigationLink
                    key={item.path}
                    item={item}
                    onNavigate={() =>
                      setMobileMenuOpen(false)
                    }
                  />
                ))}
              </nav>

              <Button
                variant="secondary"
                className="w-full"
                onClick={() =>
                  setLogoutDialogOpen(true)
                }
              >
                <LogOut
                  aria-hidden="true"
                  className="size-4"
                />

                Sign out
              </Button>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <main className="pb-24 lg:ml-72 lg:pb-0">
        <div className="mx-auto w-full max-w-[1600px] p-4 sm:p-6 lg:p-8">
          <Outlet />
        </div>
      </main>

      <nav
        aria-label="Bottom navigation"
        className="glass-surface fixed inset-x-0 bottom-0 z-20 grid grid-cols-4 border-t px-2 pb-[env(safe-area-inset-bottom)] lg:hidden"
      >
        {mobileNavigation.map((item) => (
          <NavigationLink
            key={item.path}
            item={item}
            mobile
          />
        ))}
      </nav>

      <ConfirmDialog
        open={logoutDialogOpen}
        title="Sign out of SmartFood?"
        description="You will need to sign in again to access your dashboard."
        confirmLabel="Sign out"
        danger
        isLoading={loggingOut}
        onConfirm={handleLogout}
        onClose={() =>
          setLogoutDialogOpen(false)
        }
      />
    </div>
  );
}