import type { ReactNode } from "react";

import { EmptyState } from "../feedback/EmptyState";
import { ErrorState } from "../feedback/ErrorState";
import { SkeletonStack } from "../feedback/Skeleton";
import styles from "./DataTable.module.css";

export interface DataTableColumn<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  align?: "left" | "right";
  /** Value used as sort_by when this column's header is clicked. */
  sortKey?: string;
}

interface SortState {
  sortBy: string;
  sortOrder: "asc" | "desc";
  onSortChange: (sortBy: string) => void;
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  onRowClick?: (row: T) => void;
  isLoading?: boolean;
  isError?: boolean;
  onRetry?: () => void;
  emptyTitle?: string;
  emptyDescription?: string;
  sort?: SortState;
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  onRowClick,
  isLoading,
  isError,
  onRetry,
  emptyTitle = "No results",
  emptyDescription,
  sort,
}: DataTableProps<T>) {
  return (
    <div className={styles.tableWrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            {columns.map((column) => {
              const isSortable = Boolean(sort && column.sortKey);
              const isActive = isSortable && sort!.sortBy === column.sortKey;
              return (
                <th
                  key={column.key}
                  className={[
                    column.align === "right" ? styles.alignRight : "",
                    isSortable ? styles.sortableHeader : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={isSortable ? () => sort!.onSortChange(column.sortKey!) : undefined}
                >
                  {column.header}
                  {isActive ? <span className={styles.sortArrow}>{sort!.sortOrder === "asc" ? " ▲" : " ▼"}</span> : null}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            <tr>
              <td className={styles.padded} colSpan={columns.length}>
                <SkeletonStack rows={4} />
              </td>
            </tr>
          ) : isError ? (
            <tr>
              <td colSpan={columns.length}>
                <ErrorState description="Could not load this data." onRetry={onRetry} />
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length}>
                <EmptyState title={emptyTitle} description={emptyDescription} />
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr
                key={rowKey(row)}
                className={onRowClick ? styles.clickableRow : undefined}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
              >
                {columns.map((column) => (
                  <td key={column.key} className={column.align === "right" ? styles.alignRight : undefined}>
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
