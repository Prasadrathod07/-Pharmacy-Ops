import { useEffect, type PropsWithChildren } from "react";
import { createPortal } from "react-dom";

import styles from "./Modal.module.css";

interface ModalProps {
  title: string;
  onClose: () => void;
  size?: "sm" | "lg";
}

export function Modal({ title, onClose, size = "sm", children }: PropsWithChildren<ModalProps>) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return createPortal(
    <div className={styles.overlay} onClick={onClose}>
      <div
        className={`${styles.dialog} ${size === "lg" ? styles.dialogLg : ""}`}
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <div className={styles.header}>
          <span className={styles.title}>{title}</span>
          <button className={styles.closeButton} onClick={onClose} aria-label="Close dialog">
            ×
          </button>
        </div>
        <div className={styles.body}>{children}</div>
      </div>
    </div>,
    document.body,
  );
}
