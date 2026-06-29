import client from "./client";
import type { DashboardData } from "../types";

export async function getClubDashboard(clubId: number): Promise<DashboardData> {
  const { data } = await client.get(`/dashboard/clubs/${clubId}`);
  return data;
}
