import styles from "./Pagination.module.css";

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, pageSize, total, totalPages, onPageChange }: PaginationProps) {
  if (total === 0) return null;

  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  return (
    <div className={styles.wrapper}>
      <span>
        Showing {start}-{end} of {total}
      </span>
      <div className={styles.controls}>
        <button
          className={styles.pageButton}
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          aria-label="Previous page"
        >
          ‹
        </button>
        <span>
          Page {page} of {Math.max(totalPages, 1)}
        </span>
        <button
          className={styles.pageButton}
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          aria-label="Next page"
        >
          ›
        </button>
      </div>
    </div>
  );
}
