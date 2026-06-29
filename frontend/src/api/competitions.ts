import client from "./client";
import type { Competition, CompetitionSummary, MyCompetitionSummary } from "../types";

export async function createCompetition(req: {
  name: string; club_id: number | null; format: string; courts: number; player_ids?: number[]; scheduled_at?: string;
  open_signup?: boolean; is_public?: boolean; max_players?: number; signup_deadline?: string;
}): Promise<Competition> {
  const { data } = await client.post("/competitions", req);
  return data;
}

export async function getCompetition(id: number): Promise<Competition> {
  const { data } = await client.get(`/competitions/${id}`);
  return data;
}

export async function listClubCompetitions(clubId: number): Promise<CompetitionSummary[]> {
  const { data } = await client.get(`/clubs/${clubId}/competitions`);
  return data;
}

export async function listOpenCompetitions(q = ""): Promise<CompetitionSummary[]> {
  const { data } = await client.get("/competitions/open", { params: { q: q || undefined } });
  return data;
}

export async function listMyCompetitions(): Promise<MyCompetitionSummary[]> {
  const { data } = await client.get("/competitions/me");
  return data;
}

export async function joinCompetition(id: number): Promise<Competition> {
  const { data } = await client.post(`/competitions/${id}/join`);
  return data;
}

export async function leaveCompetition(id: number): Promise<Competition> {
  const { data } = await client.delete(`/competitions/${id}/join`);
  return data;
}

export async function startCompetition(id: number): Promise<Competition> {
  const { data } = await client.patch(`/competitions/${id}/start`);
  return data;
}

export async function recordScore(matchId: number, scoreA: number, scoreB: number) {
  const { data } = await client.post(`/matches/${matchId}/score`, { score_a: scoreA, score_b: scoreB });
  return data;
}

export async function finishCompetition(id: number): Promise<Competition> {
  const { data } = await client.patch(`/competitions/${id}/finish`);
  return data;
}
