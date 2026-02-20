import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import api from '../../services/api';

import {
  MdNotifications, MdNotificationsNone, MdDoneAll,
  MdDeleteSweep, MdCircle
} from 'react-icons/md';
import { HiSun, HiMoon } from 'react-icons/hi2';
import { RiLogoutBoxLine } from 'react-icons/ri';
import { FiUser, FiChevronDown } from 'react-icons/fi';
import { TbSchool } from 'react-icons/tb';

// ── Role color/pill ───────────────────────────────────────────────────────────
const ROLE_STYLE = {
  teacher: 'bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300',
  student: 'bg-emerald-100 dark:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300',
};

// ── Avatar initials ───────────────────────────────────────────────────────────
function Avatar({ name, role }) {
  const initials = name?.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase() || '?';
  const color = role === 'teacher'
    ? 'bg-indigo-600 dark:bg-indigo-500'
    : 'bg-emerald-600 dark:bg-emerald-500';
  return (
    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-white text-xs font-bold select-none ${color}`}>
      {initials}
    </span>
  );
}

// ── Notification Bell ─────────────────────────────────────────────────────────
function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState({ unread_count: 0, notifications: [] });
  const ref = useRef(null);
  const navigate = useNavigate();

  const fetch = () => api.get('/v2/notifications').then(r => setData(r.data)).catch(() => { });

  useEffect(() => {
    fetch();
    const id = setInterval(fetch, 15000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const h = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  const markRead = async (id) => {
    await api.patch(`/v2/notifications/${id}/read`);
    setData(p => ({
      ...p,
      unread_count: Math.max(0, p.unread_count - 1),
      notifications: p.notifications.map(n => n.id === id ? { ...n, is_read: true } : n),
    }));
  };
  const markAll = async () => {
    await api.patch('/v2/notifications/read-all');
    setData(p => ({ ...p, unread_count: 0, notifications: p.notifications.map(n => ({ ...n, is_read: true })) }));
  };
  const clearAll = async () => {
    await api.delete('/v2/notifications/clear');
    setData({ unread_count: 0, notifications: [] });
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(o => !o)}
        className="relative p-2 rounded-xl text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 transition"
        aria-label="Notifications"
      >
        {data.unread_count > 0
          ? <MdNotifications size={20} className="text-indigo-500" />
          : <MdNotificationsNone size={20} />}
        {data.unread_count > 0 && (
          <span className="absolute top-1 right-1 bg-red-500 text-white text-[9px] font-bold min-w-[16px] h-4 flex items-center justify-center rounded-full px-0.5 leading-none">
            {data.unread_count > 9 ? '9+' : data.unread_count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-12 w-80 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-xl dark:shadow-slate-900/50 z-50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 dark:border-slate-700">
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">Notifications</span>
            <div className="flex gap-2 text-xs">
              {data.unread_count > 0 && (
                <button onClick={markAll} className="flex items-center gap-1 text-indigo-500 hover:text-indigo-700 dark:hover:text-indigo-300 transition">
                  <MdDoneAll size={14} /> Read all
                </button>
              )}
              {data.notifications.length > 0 && (
                <button onClick={clearAll} className="flex items-center gap-1 text-slate-400 hover:text-red-500 dark:hover:text-red-400 transition">
                  <MdDeleteSweep size={14} /> Clear
                </button>
              )}
            </div>
          </div>
          <div className="max-h-80 overflow-y-auto">
            {data.notifications.length === 0 ? (
              <div className="px-4 py-10 text-center text-slate-400 dark:text-slate-500 text-sm">
                <MdNotificationsNone className="mx-auto mb-2 opacity-40" size={32} />
                No notifications yet
              </div>
            ) : data.notifications.map(n => (
              <button
                key={n.id}
                onClick={() => { if (!n.is_read) markRead(n.id); if (n.link) { navigate(n.link); setOpen(false); } }}
                className={`w-full text-left px-4 py-3 border-b border-slate-50 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-700/40 transition ${!n.is_read ? 'bg-indigo-50/60 dark:bg-indigo-900/20' : ''}`}
              >
                <div className="flex items-start gap-2.5">
                  {!n.is_read
                    ? <MdCircle size={8} className="text-indigo-500 mt-1.5 shrink-0" />
                    : <span className="w-2 shrink-0" />}
                  <div>
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100 leading-snug">{n.title}</p>
                    {n.body && <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{n.body}</p>}
                    <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
                      {new Date(n.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true })}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── User Menu ─────────────────────────────────────────────────────────────────
function UserMenu({ user, logout }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const h = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-2 px-2 py-1.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 transition"
      >
        <Avatar name={user.full_name} role={user.role} />
        <div className="hidden sm:block text-left">
          <p className="text-xs font-semibold text-slate-900 dark:text-slate-100 leading-none">{user.full_name}</p>
          <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium mt-0.5 inline-block ${ROLE_STYLE[user.role] || 'bg-slate-100 text-slate-600'}`}>
            {user.role}
          </span>
        </div>
        <FiChevronDown size={14} className={`text-slate-400 hidden sm:block transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute right-0 top-12 w-52 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-xl dark:shadow-slate-900/50 z-50 overflow-hidden">
          {/* Profile info */}
          <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-700">
            <div className="flex items-center gap-2.5">
              <Avatar name={user.full_name} role={user.role} />
              <div className="min-w-0">
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">{user.full_name}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{user.email}</p>
              </div>
            </div>
          </div>

          {/* Menu items */}
          <div className="p-1.5">
            <button
              onClick={() => { logout(); setOpen(false); }}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition font-medium"
            >
              <RiLogoutBoxLine size={16} /> Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Navbar ────────────────────────────────────────────────────────────────────
export default function Navbar() {
  const { user, logout } = useAuth();
  const { dark, toggle } = useTheme();
  const navigate = useNavigate();

  return (
    <nav className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 transition-colors duration-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">

          {/* Logo */}
          <button
            onClick={() => navigate(user ? (user.role === 'teacher' ? '/teacher' : '/student') : '/login')}
            className="flex items-center gap-2 group"
          >
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center group-hover:bg-indigo-700 transition">
              <TbSchool size={18} className="text-white" />
            </div>
            <span className="text-lg font-bold text-slate-900 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition">
              K12 <span className="text-indigo-600 dark:text-indigo-400">Evaluator</span>
            </span>
          </button>

          {/* Right controls */}
          <div className="flex items-center gap-2">

            {/* Dark / Light toggle */}
            <button
              onClick={toggle}
              title={dark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              className="p-2 rounded-xl text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 transition"
            >
              {dark
                ? <HiSun size={20} className="text-amber-400" />
                : <HiMoon size={20} className="text-indigo-500" />}
            </button>

            {user ? (
              <>
                <NotificationBell />
                <div className="w-px h-6 bg-slate-200 dark:bg-slate-700" />
                <UserMenu user={user} logout={logout} />
              </>
            ) : (
              <>
                <Link to="/login"
                  className="flex items-center gap-1.5 text-sm text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 px-3 py-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 transition font-medium">
                  <FiUser size={15} /> Login
                </Link>
                <Link to="/register"
                  className="text-sm bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl transition font-medium">
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
