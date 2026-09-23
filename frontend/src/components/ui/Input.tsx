import type { InputHTMLAttributes } from "react";

import styles from "./FormControls.module.css";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

export function Input({ invalid, className, ...rest }: InputProps) {
  const classes = [styles.control, invalid ? styles.controlInvalid : "", className].filter(Boolean).join(" ");
  return <input className={classes} {...rest} />;
}
