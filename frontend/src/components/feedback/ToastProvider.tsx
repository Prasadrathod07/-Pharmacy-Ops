import { useCallback, useMemo, useState, type PropsWithChildren } from "react";
import { createPortal } from "react-dom";

import { ToastContext, type ToastKind } from "./toastContext";
import styles from "./Toast.module.css";

interface Toast {
  id: number;
  kind: ToastKind;
  message: string;
}

const ACCENT_CLASS: Record<ToastKind, string> = {
  success: styles.accentSuccess,
  error: styles.accentError,
  info: styles.accentInfo,
};

const AUTO_DISMISS_MS = 4000;

export function ToastProvider({ children }: PropsWithChildren) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback(
    (message: string, kind: ToastKind = "success") => {
      const id = Date.now() + Math.random();
      setToasts((current) => [...current, { id, kind, message }]);
      window.setTimeout(() => dismiss(id), AUTO_DISMISS_MS);
    },
    [dismiss],
  );

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      {createPortal(
        <div className={styles.viewport}>
          {toasts.map((toast) => (
            <div key={toast.id} className={`${styles.toast} ${ACCENT_CLASS[toast.kind]}`}>
              <span>{toast.message}</span>
              <button className={styles.closeButton} onClick={() => dismiss(toast.id)} aria-label="Dismiss">
                ×
              </button>
            </div>
          ))}
        </div>,
        document.body,
      )}
    </ToastContext.Provider>
  );
}
