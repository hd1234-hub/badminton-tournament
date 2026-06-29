import client from "./client";
import type { Activity, CompetitionFormat, Competition } from "../types";

export interface ActivityCreateRequest {
  title: string;
  club_id: number;
  format: CompetitionFormat;
  courts: number;
  min_players: number;
  max_players: number;
  start_time: string;
  signup_deadline: string;
  location?: string;
  description?: string;
}

export async function createActivity(req: ActivityCreateRequest): Promise<Activity> {
  const { data } = await client.post("/activities", req);
  return data;
}

export async function listClubActivities(clubId: number): Promise<Activity[]> {
  const { data } = await client.get(`/activities/club/${clubId}`);
  return data;
}

export async function getActivity(activityId: number): Promise<Activity> {
  const { data } = await client.get(`/activities/${activityId}`);
  return data;
}

export async function signup(activityId: number): Promise<Activity> {
  const { data } = await client.post(`/activities/${activityId}/signup`);
  return data;
}

export async function cancelSignup(activityId: number): Promise<Activity> {
  const { data } = await client.post(`/activities/${activityId}/cancel`);
  return data;
}

export async function generateCompetition(activityId: number): Promise<Competition> {
  const { data } = await client.post(`/activities/${activityId}/generate`);
  return data;
}
