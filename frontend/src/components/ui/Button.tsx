import type { ButtonHTMLAttributes } from "react";

import styles from "./Button.module.css";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md";
}

export function Button({ variant = "primary", size = "md", className, ...rest }: ButtonProps) {
  const variantClass = styles[variant];
  const sizeClass = size === "sm" ? styles.sizeSm : styles.sizeMd;
  const classes = [styles.button, variantClass, sizeClass, className].filter(Boolean).join(" ");
  return <button className={classes} {...rest} />;
}
