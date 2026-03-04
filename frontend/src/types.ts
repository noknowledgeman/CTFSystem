export interface User {
  id: number
  username: string
  email: string
  role: string
  team_id: number | null
  is_active?: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Challenge {
  id: number
  name: string
  description: string | null
  category: string
  difficulty: string
  points: number
  vm_identifier: string | null
  upload_metadata: string | null
  grading_mode: string
  created_at: string
  updated_at: string
  solved?: boolean
}

export interface Hint {
  id: number
  challenge_id: number
  order: number
  content: string
  cost: number
  created_at: string
}

export interface Submission {
  id: number
  user_id: number | null
  team_id: number | null
  challenge_id: number
  correct: boolean
  status: string
  assigned_points: number | null
  feedback: string | null
  created_at: string
}

export interface LeaderboardEntry {
  rank: number
  user_id: number | null
  team_id: number | null
  username_or_team: string
  total_points: number
  solved_count: number
}

export interface EventStats {
  total_submissions: number
  correct_submissions: number
  unique_solvers: number
  challenges_count: number
}

export interface ProgressByCategory {
  category: string
  points: number
  solved_count: number
}

export interface PointsOverTimeEntry {
  date: string
  cumulative_points: number
}

export interface ProgressDetailed {
  total_points: number
  solved_count: number
  username: string
  team_id: number | null
  team_name: string | null
  by_category: ProgressByCategory[]
  points_over_time: PointsOverTimeEntry[]
}

export interface ValidationResult {
  challenge_id: number
  name: string
  vm_identifier: string | null
  status: string
  error: string | null
  checked_at: string
}
