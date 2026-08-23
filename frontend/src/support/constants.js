import { ClipboardList, FileText, Home, Package, ShieldAlert, Ticket, Users } from "lucide-react";

export const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard", icon: Home },
  { key: "tickets", label: "Tickets", icon: Ticket },
  { key: "issues", label: "Issues & Incidents", icon: ShieldAlert },
  { key: "customers", label: "Customers", icon: Users },
  { key: "orders", label: "Orders", icon: Package },
  { key: "policies", label: "Policies & Agreements", icon: FileText }
];

export const SUPPORT_BRAND_ICON = ClipboardList;

export const priorityRank = { HIGH: 0, MEDIUM: 1, LOW: 2 };

export const orderStatusRank = {
  BOOKED: 0,
  PICKED_UP: 1,
  IN_TRANSIT: 2,
  OUT_FOR_DELIVERY: 3,
  DELIVERED: 4,
  CANCELLED: 5
};
