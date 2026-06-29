import client from "./client";
import type { User } from "../types";

export interface AuthResponse {
  token: string;
  user: User;
}

export async function register(username: string, password: string, name: string): Promise<AuthResponse> {
  const { data } = await client.post("/auth/register", { username, password, name });
  return data;
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const { data } = await client.post("/auth/login", { username, password });
  return data;
}

export async function me() {
  const { data } = await client.get("/auth/me");
  return data;
}
