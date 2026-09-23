import { Button } from "../ui/Button";
import styles from "./StateMessage.module.css";

interface ErrorStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
}

export function ErrorState({ title = "Something went wrong", description, onRetry }: ErrorStateProps) {
  return (
    <div className={styles.wrapper}>
      <div className={`${styles.title} ${styles.errorIcon}`}>{title}</div>
      {description ? <div className={styles.description}>{description}</div> : null}
      {onRetry ? (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}
