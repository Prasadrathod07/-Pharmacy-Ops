import type { SelectHTMLAttributes } from "react";

import styles from "./FormControls.module.css";

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  invalid?: boolean;
}

export function Select({ invalid, className, children, ...rest }: SelectProps) {
  const classes = [styles.control, invalid ? styles.controlInvalid : "", className].filter(Boolean).join(" ");
  return (
    <select className={classes} {...rest}>
      {children}
    </select>
  );
}
