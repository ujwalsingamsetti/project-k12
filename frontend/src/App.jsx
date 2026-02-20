import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './context/ToastContext';
import ProtectedRoute from './components/common/ProtectedRoute';

// Auth
import Login from './components/auth/Login';
import Register from './components/auth/Register';

// Teacher
import TeacherDashboard from './components/teacher/Dashboard';
import CreatePaper from './components/teacher/CreatePaper';
import EditPaper from './components/teacher/EditPaper';
import ViewSubmissions from './components/teacher/ViewSubmissions';
import Analytics from './components/teacher/Analytics';
import AssignPaper from './components/teacher/AssignPaper';
import Sections from './components/teacher/Sections';

// Student
import StudentDashboard from './components/student/Dashboard';
import SubmitAnswer from './components/student/SubmitAnswer';
import ViewResults from './components/student/ViewResults';

// Shared
import Leaderboard from './components/common/Leaderboard';

function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* Teacher Routes */}
              <Route
                path="/teacher"
                element={
                  <ProtectedRoute role="teacher">
                    <TeacherDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/create-paper"
                element={
                  <ProtectedRoute role="teacher">
                    <CreatePaper />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/papers/:paperId/edit"
                element={
                  <ProtectedRoute role="teacher">
                    <EditPaper />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/papers/:paperId/submissions"
                element={
                  <ProtectedRoute role="teacher">
                    <ViewSubmissions />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/papers/:paperId/analytics"
                element={
                  <ProtectedRoute role="teacher">
                    <Analytics />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/papers/:paperId/assign"
                element={
                  <ProtectedRoute role="teacher">
                    <AssignPaper />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/sections"
                element={
                  <ProtectedRoute role="teacher">
                    <Sections />
                  </ProtectedRoute>
                }
              />

              {/* Student Routes */}
              <Route
                path="/student"
                element={
                  <ProtectedRoute role="student">
                    <StudentDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/student/submit/:paperId"
                element={
                  <ProtectedRoute role="student">
                    <SubmitAnswer />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/student/submissions/:submissionId"
                element={
                  <ProtectedRoute role="student">
                    <ViewResults />
                  </ProtectedRoute>
                }
              />

              {/* Shared Routes */}
              <Route
                path="/leaderboard/:paperId"
                element={
                  <ProtectedRoute>
                    <Leaderboard />
                  </ProtectedRoute>
                }
              />

              <Route path="/" element={<Navigate to="/login" />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
