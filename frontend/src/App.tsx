import { Routes, Route } from "react-router-dom";
import { useAuthProvider, AuthContext } from "./hooks/useAuth";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import Dashboard from "./pages/Dashboard";
import ClubPage from "./pages/ClubPage";
import CreateCompetition from "./pages/CreateCompetition";
import CompetitionBoard from "./pages/CompetitionBoard";
import ProfilePage from "./pages/ProfilePage";
import LeaderboardPage from "./pages/LeaderboardPage";
import CreateActivity from "./pages/CreateActivity";
import ActivityPage from "./pages/ActivityPage";
import ClubDashboardPage from "./pages/ClubDashboardPage";
import AdminPage from "./pages/AdminPage";
import AdminRoute from "./components/AdminRoute";
import MyCompetitionsPage from "./pages/MyCompetitionsPage";
import CreateLobbyCompetition from "./pages/CreateLobbyCompetition";

export default function App() {
  const auth = useAuthProvider();

  return (
    <AuthContext.Provider value={auth}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/clubs/:id" element={<ClubPage />} />
          <Route path="/clubs/:id/dashboard" element={<ClubDashboardPage />} />
          <Route path="/clubs/:id/create-activity" element={<CreateActivity />} />
          <Route path="/activities/:id" element={<ActivityPage />} />
          <Route path="/clubs/:id/create-competition" element={<CreateCompetition />} />
          <Route path="/competitions/:id" element={<CompetitionBoard />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/leaderboard" element={<LeaderboardPage />} />
          <Route path="/my-competitions" element={<MyCompetitionsPage />} />
          <Route path="/create-lobby-competition" element={<CreateLobbyCompetition />} />
          <Route path="/admin" element={<AdminRoute><AdminPage /></AdminRoute>} />
        </Route>
      </Routes>
    </AuthContext.Provider>
  );
}
