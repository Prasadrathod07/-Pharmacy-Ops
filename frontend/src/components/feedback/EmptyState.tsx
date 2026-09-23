import type { ReactNode } from "react";

import styles from "./StateMessage.module.css";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className={styles.wrapper}>
      <div className={styles.title}>{title}</div>
      {description ? <div className={styles.description}>{description}</div> : null}
      {action}
    </div>
  );
}
