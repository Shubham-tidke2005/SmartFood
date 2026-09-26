import {
  AlertTriangle,
  X,
} from "lucide-react";

import {
  useEffect,
  useRef,
} from "react";

import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "motion/react";

import Button from "./Button";

export default function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  danger = false,
  isLoading = false,
  onConfirm,
  onClose,
}) {
  const cancelButtonRef = useRef(null);

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    const previousOverflow =
      document.body.style.overflow;

    document.body.style.overflow = "hidden";

    const focusTimer = window.setTimeout(() => {
      cancelButtonRef.current?.focus();
    }, 0);

    function handleKeyDown(event) {
      if (event.key === "Escape" && !isLoading) {
        onClose();
      }
    }

    document.addEventListener(
      "keydown",
      handleKeyDown,
    );

    return () => {
      window.clearTimeout(focusTimer);
      document.body.style.overflow =
        previousOverflow;

      document.removeEventListener(
        "keydown",
        handleKeyDown,
      );
    };
  }, [open, isLoading, onClose]);

  return createPortal(
    <AnimatePresence>
      {open && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center sm:items-center sm:p-6"
          role="presentation"
        >
          <motion.button
            type="button"
            aria-label="Close confirmation dialog"
            className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => {
              if (!isLoading) {
                onClose();
              }
            }}
          />

          <motion.div
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="confirm-dialog-title"
            aria-describedby="confirm-dialog-description"
            initial={{
              opacity: 0,
              y: 30,
              scale: 0.98,
            }}
            animate={{
              opacity: 1,
              y: 0,
              scale: 1,
            }}
            exit={{
              opacity: 0,
              y: 30,
              scale: 0.98,
            }}
            transition={{
              duration: 0.18,
            }}
            className="relative w-full rounded-t-3xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-700 dark:bg-slate-800 sm:max-w-md sm:rounded-3xl"
          >
            <button
              type="button"
              aria-label="Close dialog"
              className="focus-ring absolute right-4 top-4 rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700"
              disabled={isLoading}
              onClick={onClose}
            >
              <X
                aria-hidden="true"
                className="size-5"
              />
            </button>

            <div className="flex size-11 items-center justify-center rounded-2xl bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300">
              <AlertTriangle
                aria-hidden="true"
                className="size-5"
              />
            </div>

            <h2
              id="confirm-dialog-title"
              className="mt-4 pr-8 text-xl font-bold text-slate-950 dark:text-white"
            >
              {title}
            </h2>

            <p
              id="confirm-dialog-description"
              className="mt-2 leading-6 text-slate-600 dark:text-slate-300"
            >
              {description}
            </p>

            <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <Button
                ref={cancelButtonRef}
                variant="secondary"
                disabled={isLoading}
                onClick={onClose}
              >
                {cancelLabel}
              </Button>

              <Button
                variant={
                  danger
                    ? "danger"
                    : "primary"
                }
                isLoading={isLoading}
                onClick={onConfirm}
              >
                {confirmLabel}
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body,
  );
}