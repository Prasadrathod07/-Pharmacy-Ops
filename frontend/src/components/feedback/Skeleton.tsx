import styles from "./Skeleton.module.css";

export function Skeleton({ height = 14, width = "100%" }: { height?: number | string; width?: number | string }) {
  return <div className={styles.skeleton} style={{ height, width }} />;
}

export function SkeletonStack({ rows = 4 }: { rows?: number }) {
  return (
    <div className={styles.stack}>
      {Array.from({ length: rows }).map((_, index) => (
        <Skeleton key={index} height={16} width={index === rows - 1 ? "60%" : "100%"} />
      ))}
    </div>
  );
}
