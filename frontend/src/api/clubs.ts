import client from "./client";
import type { Club, Player, ClubSearchResult } from "../types";

export async function listClubs(): Promise<Club[]> {
  const { data } = await client.get("/clubs");
  return data;
}

export async function createClub(name: string): Promise<Club> {
  const { data } = await client.post("/clubs", { name });
  return data;
}

export async function searchClubs(q: string): Promise<ClubSearchResult[]> {
  const { data } = await client.get("/clubs/search", { params: { q } });
  return data;
}

export async function joinClub(clubId: number): Promise<void> {
  await client.post(`/clubs/${clubId}/join`);
}

export async function getClubPlayers(clubId: number): Promise<Player[]> {
  const { data } = await client.get(`/clubs/${clubId}/players`);
  return data;
}
