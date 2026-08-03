import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import Analyze from "./pages/Analyze";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import RepoReport from "./pages/RepoReport";
import Signup from "./pages/Signup";

function Private({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center text-slate-500 text-sm">Loading…</div>;
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/dashboard" element={<Private><Dashboard /></Private>} />
          <Route path="/analyze" element={<Private><Analyze /></Private>} />
          <Route path="/repos/:id" element={<Private><RepoReport /></Private>} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}
