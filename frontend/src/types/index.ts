export type CompetitionFormat = "singles_rotation" | "doubles_rotation" | "eight_player_rotation" | "four_player_rotation" | "knockout";

export const FORMAT_LABELS: Record<CompetitionFormat, string> = {
  singles_rotation: "单打轮转",
  doubles_rotation: "双打轮转",
  eight_player_rotation: "八人转",
  four_player_rotation: "四人转",
  knockout: "淘汰赛",
};

export const FORMAT_PLAYER_COUNTS: Record<CompetitionFormat, number[]> = {
  singles_rotation: [2, 3, 4, 5, 6, 7, 8],
  doubles_rotation: [4, 6, 8],
  eight_player_rotation: [8],
  four_player_rotation: [4],
  knockout: [4, 8, 16],
};

export type CompetitionStatus = "open" | "pending" | "in_progress" | "completed";

export interface User {
  id: number;
  username: string;
  name: string;
  gender: string;
  skill_level: number;
  birth_year: number;
  bio: string;
  is_admin?: boolean;
}

export interface Player {
  id: number;
  name: string;
  level: number;
  handedness: string;
  gender: string;
}

export interface Club {
  id: number;
  name: string;
  owner_id: number;
  owner_name?: string;
  member_count?: number;
}

export interface ClubSearchResult {
  id: number;
  name: string;
  owner_name: string;
  member_count: number;
  is_joined: boolean;
}

export interface CompetitionSummary {
  id: number;
  name: string;
  club_id: number | null;
  format: CompetitionFormat;
  status: CompetitionStatus;
  is_public: boolean;
  max_players: number | null;
  signup_deadline: string | null;
  creator_name: string | null;
  my_joined: boolean;
  player_count: number;
  created_at: string;
}

export interface MyCompetitionSummary {
  id: number;
  name: string;
  club_id: number | null;
  format: CompetitionFormat;
  status: CompetitionStatus;
  created_at: string;
  scheduled_at: string | null;
  my_matches: number;
  my_wins: number;
  my_losses: number;
  my_win_rate: number;
}

export interface Match {
  id: number;
  round_id: number;
  court: number;
  team_a: number[];
  team_b: number[];
  score_a: number | null;
  score_b: number | null;
}

export interface Round {
  id: number;
  competition_id: number;
  round_number: number;
  matches: Match[];
}

export interface Competition {
  id: number;
  name: string;
  club_id: number | null;
  format: CompetitionFormat;
  status: CompetitionStatus;
  courts: number;
  is_public: boolean;
  max_players: number | null;
  signup_deadline: string | null;
  scheduled_at: string | null;
  players: Player[];
  rounds: Round[];
}

export interface ActivitySignup {
  id: number;
  activity_id: number;
  player_id: number;
  status: "confirmed" | "waitlisted" | "cancelled";
  signed_up_at: string;
  player: Player;
}

export interface Activity {
  id: number;
  club_id: number;
  title: string;
  description: string | null;
  location: string | null;
  format: CompetitionFormat;
  courts: number;
  min_players: number;
  max_players: number;
  start_time: string;
  signup_deadline: string;
  status: "open" | "scheduled" | "closed";
  competition_id: number | null;
  created_at: string;
  signups: ActivitySignup[];
  confirmed_count: number;
  waitlist_count: number;
  my_signup_status: string | null;
}

export interface Notification {
  id: number;
  type: string;
  title: string;
  message: string;
  severity: string;
  club_id: number | null;
  activity_id: number | null;
  competition_id: number | null;
  match_id: number | null;
  read_at: string | null;
  created_at: string;
}

export interface DashboardData {
  club_id: number;
  player_id: number;
  summary: { matches: number; wins: number; losses: number; win_rate: number; avg_score: number };
  recent_trend: Array<{
    match_id: number;
    competition_id: number | null;
    competition_name: string;
    round_number: number | null;
    team_score: number;
    opponent_score: number;
    won: boolean;
    recorded_at: string | null;
  }>;
  win_rate_curve: Array<{ match_id: number; recorded_at: string | null; win_rate: number; wins: number; total: number }>;
  opponent_relationships: Array<{
    player_id: number;
    player_name: string;
    matches: number;
    wins: number;
    points_for: number;
    points_against: number;
    win_rate: number;
    avg_point_diff: number;
  }>;
  partner_matrix: Array<{
    player_a_id: number;
    player_a_name: string;
    player_b_id: number;
    player_b_name: string;
    matches: number;
    wins: number;
    win_rate: number;
  }>;
}

export interface Prediction {
  id: string;
  competitionId: number;
  competitionName: string;
  playerAId: number;
  playerAName: string;
  playerBId: number;
  playerBName: string;
  predictedWinner: string;
  predictedText: string;
  matchId: number | null;
  actualWinner: string | null;
  verdict: "correct" | "wrong" | "pending";
  createdAt: string;
}
