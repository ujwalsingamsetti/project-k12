import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/common/ProtectedRoute';

// Auth
import Login from './components/auth/Login';
import Register from './components/auth/Register';

// Teacher
import TeacherDashboard from './components/teacher/Dashboard';
import CreatePaper from './components/teacher/CreatePaper';
import ViewSubmissions from './components/teacher/ViewSubmissions';

// Student
import StudentDashboard from './components/student/Dashboard';
import SubmitAnswer from './components/student/SubmitAnswer';
import ViewResults from './components/student/ViewResults';

function App() {
  return (
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
            path="/teacher/papers/:paperId/submissions"
            element={
              <ProtectedRoute role="teacher">
                <ViewSubmissions />
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

          <Route path="/" element={<Navigate to="/login" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
