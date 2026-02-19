import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogoClick = () => {
    if (user) {
      navigate(user.role === 'teacher' ? '/teacher' : '/student');
    } else {
      navigate('/login');
    }
  };

  return (
    <nav className="bg-white border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <button onClick={handleLogoClick} className="text-xl font-semibold text-slate-900 hover:text-slate-700 transition">
              K12 Evaluator
            </button>
          </div>
          <div className="flex items-center gap-4">
            {user ? (
              <>
                <span className="text-sm text-slate-600">
                  {user.full_name} <span className="text-slate-400">·</span> <span className="capitalize">{user.role}</span>
                </span>
                <button
                  onClick={logout}
                  className="text-sm text-slate-600 hover:text-slate-900 transition"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-sm text-slate-600 hover:text-slate-900 transition"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="text-sm bg-slate-900 text-white px-4 py-2 rounded-lg hover:bg-slate-800 transition"
                >
                  Register
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
