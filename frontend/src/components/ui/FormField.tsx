import type { PropsWithChildren, ReactNode } from "react";

import styles from "./FormControls.module.css";

interface FormFieldProps {
  label: string;
  htmlFor?: string;
  hint?: ReactNode;
  error?: string | null;
}

export function FormField({ label, htmlFor, hint, error, children }: PropsWithChildren<FormFieldProps>) {
  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor={htmlFor}>
        {label}
      </label>
      {children}
      {error ? <span className={styles.error}>{error}</span> : hint ? <span className={styles.hint}>{hint}</span> : null}
    </div>
  );
}
