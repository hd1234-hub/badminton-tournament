import client from "./client";
import type { Notification } from "../types";

export async function listNotifications(unreadOnly = false): Promise<Notification[]> {
  const { data } = await client.get("/notifications", { params: { unread_only: unreadOnly } });
  return data;
}

export async function markRead(notificationId: number): Promise<Notification> {
  const { data } = await client.post(`/notifications/${notificationId}/read`);
  return data;
}

export async function markAllRead(): Promise<{ updated: number }> {
  const { data } = await client.post("/notifications/read-all");
  return data;
}
