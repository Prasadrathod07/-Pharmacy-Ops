import { NavLink } from "react-router-dom";

import { DashboardIcon, InventoryIcon, NewOrderIcon, OrdersIcon } from "./icons";
import styles from "./Sidebar.module.css";

const navItems = [
  { to: "/", label: "Dashboard", end: true, icon: DashboardIcon },
  { to: "/orders", label: "Orders", icon: OrdersIcon },
  { to: "/orders/new", label: "New Order", icon: NewOrderIcon },
  { to: "/inventory", label: "Inventory", icon: InventoryIcon },
];

interface SidebarProps {
  open: boolean;
  onNavigate: () => void;
}

export function Sidebar({ open, onNavigate }: SidebarProps) {
  const classes = [styles.sidebar, open ? styles.sidebarOpen : ""].filter(Boolean).join(" ");

  return (
    <nav className={classes}>
      <div className={styles.brand}>
        <span className={styles.brandMark}>Rx</span>
        <div>
          <div className={styles.brandName}>Pharmacy Ops</div>
          <div className={styles.brandSubtitle}>Order &amp; Inventory</div>
        </div>
      </div>

      {navItems.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={onNavigate}
            className={({ isActive }) => [styles.navLink, isActive ? styles.navLinkActive : ""].filter(Boolean).join(" ")}
          >
            <Icon className={styles.navIcon} />
            {item.label}
          </NavLink>
        );
      })}
    </nav>
  );
}
