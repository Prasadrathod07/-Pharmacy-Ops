import type { PropsWithChildren } from "react";

import styles from "./Badge.module.css";

export type BadgeTone = "success" | "warning" | "danger" | "info" | "neutral";

interface BadgeProps {
  tone?: BadgeTone;
  dot?: boolean;
  className?: string;
}

export function Badge({ tone = "neutral", dot = true, className, children }: PropsWithChildren<BadgeProps>) {
  const classes = [styles.badge, styles[tone], className].filter(Boolean).join(" ");
  return (
    <span className={classes}>
      {dot ? <span className={styles.dot} /> : null}
      {children}
    </span>
  );
}
