import { MenuIcon } from "./icons";
import styles from "./AppHeader.module.css";

export function AppHeader({ onMenuClick }: { onMenuClick: () => void }) {
  return (
    <header className={styles.header}>
      <button className={styles.menuButton} onClick={onMenuClick} aria-label="Open navigation">
        <MenuIcon width={20} height={20} />
      </button>
      <span className={styles.title}>Pharmacy Ops</span>
    </header>
  );
}
