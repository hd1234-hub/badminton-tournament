import client from "./client";

export interface AdminOverviewStats {
  total_users: number;
  today_registrations: number;
  week_registrations: number;
  total_clubs: number;
  total_competitions: number;
  competitions_in_progress: number;
  completed_competitions: number;
  agent_messages_total: number;
  agent_messages_today: number;
  active_users_7d: number;
}

export interface RegistrationTrendItem {
  date: string;
  count: number;
}

export interface AdminUserItem {
  id: number;
  username: string;
  name: string;
  is_admin: boolean;
  created_at: string | null;
  club_count: number;
  agent_messages: number;
}

export interface AdminUserListResponse {
  items: AdminUserItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface AdminCompetitionItem {
  id: number;
  name: string;
  club_id: number;
  status: string;
  player_count: number;
  created_at: string | null;
}

export async function getAdminStats(): Promise<AdminOverviewStats> {
  const { data } = await client.get("/admin/stats");
  return data;
}

export async function getRegistrationTrend(days = 30): Promise<RegistrationTrendItem[]> {
  const { data } = await client.get("/admin/stats/registrations", { params: { days } });
  return data;
}

export async function listAdminUsers(page = 1, pageSize = 20, search = ""): Promise<AdminUserListResponse> {
  const { data } = await client.get("/admin/users", {
    params: { page, page_size: pageSize, search: search || undefined },
  });
  return data;
}

export async function listRecentCompetitions(limit = 10) {
  const { data } = await client.get("/admin/competitions/recent", { params: { limit } });
  return data.items as AdminCompetitionItem[];
}
