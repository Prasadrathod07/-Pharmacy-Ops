import { useState } from "react";
import { Outlet } from "react-router-dom";

import { useRealtimeEvents } from "../../hooks/useRealtimeEvents";
import { AppHeader } from "./AppHeader";
import styles from "./AppLayout.module.css";
import { Sidebar } from "./Sidebar";

export function AppLayout() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  useRealtimeEvents();

  return (
    <div className={styles.shell}>
      <Sidebar open={mobileNavOpen} onNavigate={() => setMobileNavOpen(false)} />

      {mobileNavOpen ? (
        <button
          type="button"
          aria-label="Close navigation"
          className={`${styles.backdrop} ${styles.backdropVisible}`}
          onClick={() => setMobileNavOpen(false)}
        />
      ) : null}

      <div className={styles.main}>
        <AppHeader onMenuClick={() => setMobileNavOpen(true)} />
        <div className={styles.content}>
          <Outlet />
        </div>
      </div>
    </div>
  );
}
