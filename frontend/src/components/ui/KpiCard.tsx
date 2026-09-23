import type { ReactNode } from "react";

import { Skeleton } from "../feedback/Skeleton";
import styles from "./KpiCard.module.css";

interface KpiCardProps {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: "default" | "warning" | "danger" | "success";
  isLoading?: boolean;
}

const ACCENT_CLASS: Record<NonNullable<KpiCardProps["tone"]>, string> = {
  default: styles.accentDefault,
  warning: styles.accentWarning,
  danger: styles.accentDanger,
  success: styles.accentSuccess,
};

export function KpiCard({ label, value, hint, tone = "default", isLoading }: KpiCardProps) {
  return (
    <div className={styles.card}>
      <span className={styles.label}>{label}</span>
      {isLoading ? (
        <Skeleton height={26} width={64} />
      ) : (
        <div className={styles.valueRow}>
          <span className={`${styles.accent} ${ACCENT_CLASS[tone]}`} />
          <span className={styles.value}>{value}</span>
        </div>
      )}
      {hint ? <span className={styles.hint}>{hint}</span> : null}
    </div>
  );
}
