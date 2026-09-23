import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "../components/layout/AppLayout";
import { DashboardPage } from "../pages/DashboardPage";
import { InventoryPage } from "../pages/InventoryPage";
import { NewOrderPage } from "../pages/NewOrderPage";
import { OrderDetailsPage } from "../pages/OrderDetailsPage";
import { OrdersPage } from "../pages/OrdersPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "orders", element: <OrdersPage /> },
      { path: "orders/new", element: <NewOrderPage /> },
      { path: "orders/:orderId", element: <OrderDetailsPage /> },
      { path: "inventory", element: <InventoryPage /> },
    ],
  },
]);
