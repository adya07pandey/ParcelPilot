import {
  Bot,
  CircleAlert,
  Clock,
  CreditCard,
  FileText,
  HelpCircle,
  LayoutDashboard,
  MapPin,
  Package,
  PackageCheck,
  Plus,
  Settings,
  TicketCheck,
  Truck,
  User,
  XCircle
} from "lucide-react";

export const navItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "orders", label: "Orders", icon: Package },
  { id: "tickets", label: "Tickets", icon: TicketCheck },
  { id: "ai", label: "AI Support", icon: Bot }
];

export const priorityRank = { HIGH: 0, MEDIUM: 1, LOW: 2 };

export const orderStatusRank = {
  BOOKED: 0,
  PICKED_UP: 1,
  IN_TRANSIT: 2,
  OUT_FOR_DELIVERY: 3,
  DELIVERED: 4,
  CANCELLED: 5
};

export const ticketCategoryOptions = [
  {
    value: "SHIPMENT",
    label: "Shipment",
    subcategories: [
      ["SHIPMENT_LOCATION", "Where is my shipment?"],
      ["PICKUP_ISSUE", "Pickup issue"],
      ["PICKUP_DELAYED", "Pickup is delayed"],
      ["STATUS_WRONG", "Shipment status looks wrong"],
      ["DELIVERY_ISSUE", "Delivery issue"],
      ["OTHER", "Other"]
    ]
  },
  {
    value: "CANCELLATION",
    label: "Cancellation",
    subcategories: [
      ["CANCEL_SHIPMENT", "Cancel a shipment"],
      ["CANCELLATION_FEE", "Cancellation fee"],
      ["CANCELLATION_POLICY", "Cancellation policy"],
      ["CANCEL_AFTER_PICKUP", "Can I cancel after pickup?"],
      ["OTHER", "Other"]
    ]
  },
  {
    value: "SERVICE_CREDIT",
    label: "Service credit",
    subcategories: [
      ["CREDIT_ELIGIBILITY", "Am I eligible for a credit?"],
      ["PICKUP_DELAY_CREDIT", "Pickup delay credit"],
      ["CREDIT_AMOUNT", "How much credit will I receive?"],
      ["CREDIT_MISSING", "Credit hasn't appeared"],
      ["OTHER", "Other"]
    ]
  },
  {
    value: "TICKETS",
    label: "Tickets",
    subcategories: [
      ["CHECK_TICKET", "Check my ticket"],
      ["TICKET_DELAY", "Why is my ticket taking so long?"],
      ["ADD_TICKET_INFO", "Add information to a ticket"],
      ["ESCALATE_ISSUE", "Escalate my issue"],
      ["RAISE_TICKET", "Raise a new ticket"],
      ["OTHER", "Other"]
    ]
  },
  {
    value: "PRODUCT_HELP",
    label: "Product help",
    subcategories: [
      ["BULK_UPLOAD", "Bulk Upload"],
      ["SHIPMENT_STATUS", "Shipment Status"],
      ["SHIPMENT_CREATION", "Shipment Creation"],
      ["KNOWN_ISSUES", "Known Issues"],
      ["OTHER", "Other"]
    ]
  },
  {
    value: "ACCOUNT_SUPPORT",
    label: "Account & support",
    subcategories: [
      ["PLAN", "My plan"],
      ["SUPPORT_SLA", "My support SLA"],
      ["CUSTOMER_SUCCESS_MANAGER", "Customer success manager"],
      ["BILLING_ACCOUNT", "Billing / account"],
      ["SUPPORT_COVERAGE", "Support coverage"],
      ["OTHER", "Other"]
    ]
  },
  {
    value: "OTHER",
    label: "Other",
    subcategories: [["OTHER", "Other"]]
  }
];

export const supportCategories = [
  {
    id: "shipment",
    label: "Shipment",
    description: "Track, pickup, delivery, or status issues",
    icon: Package,
    otherPrompt: "Tell me what is happening with your shipment.",
    subcategories: [
      { id: "shipment_location", label: "Where is my shipment?", icon: MapPin },
      { id: "pickup_issue", label: "Pickup issue", icon: Truck },
      { id: "pickup_delayed", label: "Pickup is delayed", icon: Clock },
      { id: "status_wrong", label: "Shipment status looks wrong", icon: CircleAlert },
      { id: "delivery_issue", label: "Delivery issue", icon: PackageCheck },
      { id: "other_shipment", label: "Other shipment issue", icon: HelpCircle }
    ]
  },
  {
    id: "cancellation",
    label: "Cancellation",
    description: "Cancel shipments or understand fees",
    icon: XCircle,
    otherPrompt: "Tell me what you need help with for cancellation.",
    subcategories: [
      { id: "cancel_shipment", label: "Cancel a shipment", icon: XCircle },
      { id: "cancellation_fee", label: "Cancellation fee", icon: CreditCard },
      { id: "cancellation_policy", label: "Cancellation policy", icon: FileText },
      { id: "cancel_after_pickup", label: "Can I cancel after pickup?", icon: Truck },
      { id: "other_cancellation", label: "Other cancellation issue", icon: HelpCircle }
    ]
  },
  {
    id: "service-credit",
    label: "Service Credit",
    description: "Check eligibility or credit amount",
    icon: CreditCard,
    otherPrompt: "Tell me what service-credit question you have.",
    subcategories: [
      { id: "credit_eligibility", label: "Am I eligible for a credit?", icon: CreditCard },
      { id: "pickup_delay_credit", label: "Pickup delay credit", icon: Clock },
      { id: "credit_amount", label: "How much credit will I receive?", icon: FileText },
      { id: "credit_missing", label: "Credit hasn't appeared", icon: CircleAlert },
      { id: "other_service_credit", label: "Other service-credit issue", icon: HelpCircle }
    ]
  },
  {
    id: "tickets",
    label: "Tickets",
    description: "Check or get help with your tickets",
    icon: TicketCheck,
    otherPrompt: "Tell me what ticket issue you need help with.",
    subcategories: [
      { id: "check_ticket", label: "Check my ticket", icon: TicketCheck },
      { id: "ticket_delay", label: "Why is my ticket taking so long?", icon: Clock },
      { id: "add_ticket_info", label: "Add information to a ticket", icon: Plus },
      { id: "escalate_issue", label: "Escalate my issue", icon: CircleAlert },
      { id: "raise_ticket", label: "Raise a new ticket", icon: Plus },
      { id: "other_ticket", label: "Other ticket issue", icon: HelpCircle }
    ]
  },
  {
    id: "product-help",
    label: "Product Help",
    description: "Bulk upload, shipment creation, and known issues",
    icon: Settings,
    otherPrompt: "Tell me what product area you need help with.",
    subcategories: [
      { id: "bulk_upload", label: "Bulk Upload", icon: FileText },
      { id: "shipment_status", label: "Shipment Status", icon: PackageCheck },
      { id: "shipment_creation", label: "Shipment Creation", icon: Package },
      { id: "known_issues", label: "Known Issues", icon: CircleAlert },
      { id: "other_product", label: "Other product question", icon: HelpCircle }
    ]
  },
  {
    id: "account-support",
    label: "Account & Support",
    description: "Plans, SLA, coverage, and contract terms",
    icon: User,
    otherPrompt: "Tell me what account or support question you have.",
    subcategories: [
      { id: "plan", label: "My plan", icon: User },
      { id: "support_sla", label: "My support SLA", icon: Clock },
      { id: "customer_success_manager", label: "Customer success manager", icon: User },
      { id: "billing_account", label: "Billing / account", icon: CreditCard },
      { id: "support_coverage", label: "Support coverage", icon: HelpCircle },
      { id: "other_account", label: "Other account issue", icon: HelpCircle }
    ]
  }
];
