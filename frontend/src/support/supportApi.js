import { apiFetch } from "../api/client";

export const supportApi = {
  overview: () => apiFetch("/support/overview"),
  tickets: () => apiFetch("/support/tickets"),
  ticket: (ticketId) => apiFetch(`/support/tickets/${ticketId}`),
  customers: () => apiFetch("/support/customers"),
  customer: (accountId) => apiFetch(`/support/customers/${accountId}`),
  orders: () => apiFetch("/support/orders"),
  order: (orderId) => apiFetch(`/support/orders/${orderId}`),
  policies: () => apiFetch("/support/policies"),
  issues: () => apiFetch("/support/issues"),
  investigate: (payload) =>
    apiFetch("/support/investigate", {
      method: "POST",
      body: JSON.stringify(payload)
    })
};
