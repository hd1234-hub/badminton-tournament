import client from "./client";

export interface LeaderboardEntry {
  id: number;
  name: string;
  level: number;
  win_rate: number;
  total_matches: number;
  wins: number;
  losses: number;
  point_diff: number;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
  total: number;
  skip: number;
  limit: number;
}

export async function getLeaderboard(clubId: number, skip = 0, limit = 50): Promise<LeaderboardResponse> {
  const { data } = await client.get(`/leaderboard?club_id=${clubId}&skip=${skip}&limit=${limit}`);
  return data;
}

export async function getGlobalLeaderboard(skip = 0, limit = 50): Promise<LeaderboardResponse> {
  const { data } = await client.get(`/leaderboard/global?skip=${skip}&limit=${limit}`);
  return data;
}
