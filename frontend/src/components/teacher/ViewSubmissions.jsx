import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import Navbar from '../common/Navbar';
import api from '../../services/api';
import { useToast } from '../../context/ToastContext';
import {
  MdChevronLeft, MdPerson, MdMailOutline, MdEvent, MdCheckCircle,
  MdPendingActions, MdErrorOutline, MdAutoGraph, MdFilterList,
  MdAssignmentInd, MdBarChart, MdKeyboardArrowDown, MdKeyboardArrowUp,
  MdEdit, MdClose, MdInfoOutline
} from 'react-icons/md';
import { BiLoaderAlt } from 'react-icons/bi';

function toIST(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata', day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: true
  });
}

const statusConfig = {
  evaluated: {
    icon: <MdCheckCircle className="text-emerald-500" />,
    bg: 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 border-emerald-100 dark:border-emerald-800',
    label: 'Evaluated'
  },
  evaluating: {
    icon: <BiLoaderAlt className="text-amber-500 animate-spin" />,
    bg: 'bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 border-amber-100 dark:border-amber-800',
    label: 'Evaluating'
  },
  pending: {
    icon: <MdPendingActions className="text-slate-400" />,
    bg: 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700',
    label: 'Pending'
  },
  failed: {
    icon: <MdErrorOutline className="text-red-500" />,
    bg: 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border-red-100 dark:border-red-800',
    label: 'Failed'
  },
};

// ── Override Modal ─────────────────────────────────────────────────────────────
function OverrideModal({ evaluation, onClose, onSaved }) {
  const [marks, setMarks] = useState(String(evaluation.marks_obtained));
  const [comment, setComment] = useState(evaluation.override_feedback || '');
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  const handleSave = async () => {
    const m = parseFloat(marks);
    if (isNaN(m) || m < 0 || m > evaluation.max_marks) {
      toast.error(`Marks must be between 0 and ${evaluation.max_marks}`);
      return;
    }
    setSaving(true);
    try {
      await api.patch(`/teacher/evaluations/${evaluation.question_id}/override`, {
        marks: m, comment
      });
      onSaved(evaluation.question_id, m, comment);
      toast.success('Evaluation overridden');
      onClose();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-[60] p-4">
      <div className="bg-white dark:bg-slate-800 rounded-3xl shadow-2xl w-full max-w-md p-8 border border-slate-200 dark:border-slate-700 scale-enter">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <MdEdit className="text-indigo-500" /> Override Marks
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
            <MdClose size={24} />
          </button>
        </div>

        <div className="p-4 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-700 mb-6 font-medium text-xs text-slate-500 dark:text-slate-400">
          Editing evaluation for <span className="text-indigo-600 dark:text-indigo-400 font-bold">Question {evaluation.question_number}</span>
        </div>

        <div className="space-y-6">
          <div>
            <label className="text-sm font-bold text-slate-700 dark:text-slate-300 block mb-2 ml-1">
              Revised Marks <span className="text-xs text-slate-400 font-normal">(Maximum {evaluation.max_marks})</span>
            </label>
            <input
              type="number" min={0} max={evaluation.max_marks} step={0.5}
              value={marks}
              onChange={e => setMarks(e.target.value)}
              className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl text-lg font-black focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none dark:text-slate-100 transition-all text-center"
            />
          </div>
          <div>
            <label className="text-sm font-bold text-slate-700 dark:text-slate-300 block mb-2 ml-1">Teacher Feedback</label>
            <textarea
              value={comment} onChange={e => setComment(e.target.value)}
              rows={4}
              className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl text-sm font-medium focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none dark:text-slate-100 transition-all"
              placeholder="Explain the reason for mark adjustment..."
            />
          </div>
        </div>
        <div className="flex gap-4 mt-8">
          <button
            onClick={handleSave} disabled={saving}
            className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white py-4 rounded-2xl font-bold shadow-lg shadow-indigo-100 dark:shadow-none transition-all flex items-center justify-center gap-2"
          >
            {saving ? <BiLoaderAlt className="animate-spin" size={24} /> : 'Save Changes'}
          </button>
          <button onClick={onClose} className="px-6 py-4 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 font-bold text-sm rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-all">Cancel</button>
        </div>
      </div>
    </div>
  );
}

// ── Submission Row ─────────────────────────────────────────────────────────────
function SubmissionRow({ sub, paperId }) {
  const [open, setOpen] = useState(false);
  const [overrideTarget, setOverrideTarget] = useState(null);
  const [evals, setEvals] = useState(sub.evaluations || []);

  const handleOverrideSaved = (questionId, newMarks, comment) => {
    setEvals(prev => prev.map(e =>
      e.question_id === questionId
        ? { ...e, marks_obtained: newMarks, override_feedback: comment, teacher_override: true }
        : e
    ));
  };

  const config = statusConfig[sub.status] || statusConfig.pending;

  return (
    <>
      {overrideTarget && (
        <OverrideModal
          evaluation={overrideTarget}
          onClose={() => setOverrideTarget(null)}
          onSaved={handleOverrideSaved}
        />
      )}
      <tr
        className={`hover:bg-slate-50 dark:hover:bg-slate-900/50 cursor-pointer transition-colors ${open ? 'bg-slate-50/50 dark:bg-slate-900/30' : ''}`}
        onClick={() => setOpen(o => !o)}
      >
        <td className="px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400 dark:text-slate-500">
              <MdPerson size={24} />
            </div>
            <div>
              <p className="font-bold text-slate-900 dark:text-slate-100">{sub.student_name}</p>
              <div className="flex items-center gap-1 text-[10px] text-slate-400 font-medium">
                <MdMailOutline size={12} /> {sub.student_email}
              </div>
            </div>
          </div>
        </td>
        <td className="px-6 py-5">
          <div className="flex items-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400">
            <MdEvent size={14} className="text-slate-300" /> {toIST(sub.submitted_at)}
          </div>
        </td>
        <td className="px-6 py-5">
          <span className={`inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider px-3 py-1 rounded-full border ${config.bg}`}>
            {config.icon} {config.label}
          </span>
        </td>
        <td className="px-6 py-5">
          {sub.status === 'evaluated' ? (
            <div className="flex items-baseline gap-1">
              <span className={`text-lg font-black ${(sub.total_marks / sub.max_marks) >= 0.7 ? 'text-emerald-600' : (sub.total_marks / sub.max_marks) >= 0.4 ? 'text-amber-600' : 'text-red-600'
                }`}>
                {sub.total_marks}
              </span>
              <span className="text-xs font-medium text-slate-400">/{sub.max_marks}</span>
            </div>
          ) : (
            <span className="text-slate-300 dark:text-slate-600 font-black">—</span>
          )}
        </td>
        <td className="px-6 py-5 text-right">
          <div className="flex justify-end p-2 text-slate-300 dark:text-slate-600 group-hover:text-slate-400 transition-colors">
            {open ? <MdKeyboardArrowUp size={24} /> : <MdKeyboardArrowDown size={24} />}
          </div>
        </td>
      </tr>

      {/* Expandable detail */}
      {open && (
        <tr>
          <td colSpan={5} className="bg-slate-50 dark:bg-slate-900/50 px-6 py-6 border-t border-slate-100 dark:border-slate-800 animate-in slide-in-from-top-2 duration-300">
            {evals.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 opacity-40">
                <MdInfoOutline size={48} className="text-slate-300" />
                <p className="text-sm font-bold mt-2">No question evaluation available.</p>
              </div>
            ) : (
              <div className="flex flex-col gap-4 max-w-5xl mx-auto">
                {evals
                  .slice()
                  .sort((a, b) => a.question_number - b.question_number)
                  .map(ev => (
                    <div key={ev.id || ev.question_id} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-[2rem] p-6 shadow-sm flex flex-col md:flex-row gap-6">
                      <div className="shrink-0 flex flex-col items-center justify-center w-24 border-r border-slate-50 dark:border-slate-700 pr-6">
                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Q {ev.question_number}</span>
                        <div className="flex items-baseline gap-0.5">
                          <span className={`text-2xl font-black ${ev.marks_obtained >= ev.max_marks ? 'text-emerald-600' : ev.marks_obtained === 0 ? 'text-red-600' : 'text-amber-600'}`}>
                            {ev.marks_obtained}
                          </span>
                          <span className="text-xs font-bold text-slate-400">/{ev.max_marks}</span>
                        </div>
                        {ev.teacher_override && (
                          <span className="text-[9px] font-black bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-400 px-2 py-0.5 rounded-full mt-2 uppercase tracking-tighter">Override</span>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-1.5">
                          <MdKeyboardArrowDown size={14} /> Student Response
                        </p>
                        <div className="text-sm text-slate-800 dark:text-slate-100 font-medium bg-slate-50 dark:bg-slate-900/50 p-4 rounded-2xl border border-slate-100 dark:border-slate-700 leading-relaxed italic">
                          {ev.student_answer || <span className="text-slate-400">Not answered</span>}
                        </div>
                        {ev.override_feedback && (
                          <div className="mt-3 flex items-start gap-2 text-indigo-600 dark:text-indigo-400">
                            <MdInfoOutline size={16} className="mt-0.5 shrink-0" />
                            <p className="text-xs font-bold leading-tight">Teacher Remark: <span className="font-medium text-slate-500 dark:text-slate-400 font-italic italic">{ev.override_feedback}</span></p>
                          </div>
                        )}
                      </div>
                      <div className="shrink-0 flex items-center">
                        <button
                          onClick={e => { e.stopPropagation(); setOverrideTarget(ev); }}
                          className="inline-flex items-center gap-2 text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest px-4 py-2 border-2 border-slate-100 dark:border-slate-700 rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-700 hover:text-indigo-600 transition-all dark:hover:text-indigo-400"
                        >
                          <MdEdit size={16} /> Adjust Marks
                        </button>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function ViewSubmissions() {
  const { paperId } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [paper, setPaper] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get(`/teacher/papers/${paperId}`),
      api.get(`/teacher/papers/${paperId}/submissions`),
    ]).then(([paperRes, subsRes]) => {
      setPaper(paperRes.data);
      setSubmissions(subsRes.data);
    }).catch(() => toast.error('Failed to load submissions'))
      .finally(() => setLoading(false));
  }, [paperId]);

  if (loading) return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      <Navbar />
      <div className="flex flex-col items-center justify-center h-[60vh] text-slate-400 dark:text-slate-500 gap-4">
        <BiLoaderAlt size={48} className="animate-spin text-indigo-500" />
        <p className="font-medium">Fetching class performance...</p>
      </div>
    </div>
  );

  const evaluated = submissions.filter(s => s.status === 'evaluated');
  const avgScore = evaluated.length > 0
    ? (evaluated.reduce((s, sub) => s + sub.total_marks, 0) / evaluated.length).toFixed(1)
    : null;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 py-12 page-enter">
        <button onClick={() => navigate('/teacher')} className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors mb-4">
          <MdChevronLeft size={20} /> Back to Dashboard
        </button>

        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8 mb-10">
          <div>
            <h1 className="text-4xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">{paper?.title}</h1>
            <div className="flex flex-wrap items-center gap-3 mt-3">
              <span className="bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-lg border border-slate-200 dark:border-slate-700">
                {paper?.subject?.replace('_', ' ')}
              </span>
              <span className="bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-lg border border-indigo-100 dark:border-indigo-800">
                {paper?.total_marks} Marks
              </span>
              <span className="bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-lg border border-blue-100 dark:border-blue-800">
                {paper?.duration_minutes} Mins
              </span>
            </div>
          </div>
          <div className="flex gap-4">
            <Link
              to={`/teacher/papers/${paperId}/assign`}
              className="inline-flex items-center gap-2 px-6 py-3.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-all font-bold text-sm shadow-sm"
            >
              <MdAssignmentInd size={20} className="text-indigo-500" /> Assign Students
            </Link>
            <Link
              to={`/teacher/papers/${paperId}/analytics`}
              className="inline-flex items-center gap-2 px-6 py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl transition-all font-bold text-sm shadow-xl shadow-indigo-100 dark:shadow-none"
            >
              <MdBarChart size={20} /> Advanced Analytics
            </Link>
          </div>
        </div>

        {/* Performance Overview Chips */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-10">
          <div className="bg-white dark:bg-slate-800 p-6 rounded-3xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden relative group">
            <div className="absolute right-[-10px] top-[-10px] opacity-5 group-hover:scale-110 transition-transform duration-500">
              <MdPerson size={80} />
            </div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Total Submissions</p>
            <p className="text-3xl font-black text-slate-900 dark:text-slate-100">{submissions.length}</p>
          </div>
          <div className="bg-emerald-50/30 dark:bg-emerald-900/10 p-6 rounded-3xl border border-emerald-100/50 dark:border-emerald-800 shadow-sm overflow-hidden relative group">
            <div className="absolute right-[-10px] top-[-10px] opacity-10 text-emerald-500">
              <MdCheckCircle size={80} />
            </div>
            <p className="text-[10px] font-black text-emerald-600 dark:text-emerald-400 uppercase tracking-widest mb-1">Evaluated</p>
            <p className="text-3xl font-black text-emerald-600 dark:text-emerald-400">{evaluated.length}</p>
          </div>
          {avgScore && (
            <div className="bg-blue-50/30 dark:bg-blue-900/10 p-6 rounded-3xl border border-blue-100/50 dark:border-blue-800 shadow-sm overflow-hidden relative group md:col-span-2">
              <div className="absolute right-0 top-[-20px] opacity-10 text-blue-500">
                <MdAutoGraph size={120} />
              </div>
              <p className="text-[10px] font-black text-blue-600 dark:text-blue-400 uppercase tracking-widest mb-1">Class Average Performance</p>
              <div className="flex items-baseline gap-2">
                <p className="text-3xl font-black text-blue-600 dark:text-blue-400">{avgScore}</p>
                <p className="text-lg font-bold text-blue-400">/ {paper?.total_marks}</p>
                <span className="ml-4 text-xs font-black text-blue-500 bg-blue-100/50 dark:bg-blue-900/50 px-3 py-1 rounded-full border border-blue-200/50 dark:border-blue-800">
                  {((avgScore / paper?.total_marks) * 100).toFixed(0)}% Score Rate
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Submissions Table Section */}
        <div className="flex items-center justify-between mb-6 px-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">Submission History</h2>
          <button className="flex items-center gap-2 text-xs font-black text-slate-400 uppercase tracking-widest hover:text-indigo-600 transition-colors">
            <MdFilterList size={18} /> Filter Listings
          </button>
        </div>

        <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-[2.5rem] shadow-2xl dark:shadow-none overflow-hidden">
          {submissions.length === 0 ? (
            <div className="text-center py-24 flex flex-col items-center opacity-30">
              <MdPendingActions size={80} />
              <p className="text-2xl font-black mt-4">Waiting for initial submissions...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-slate-100/50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
                    <th className="px-6 py-4 text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em]">Student Profile</th>
                    <th className="px-6 py-4 text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em]">Time of Submission</th>
                    <th className="px-6 py-4 text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em]">Evaluation Status</th>
                    <th className="px-6 py-4 text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em]">Final Score</th>
                    <th className="px-6 py-4"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                  {submissions.map(sub => (
                    <SubmissionRow key={sub.id} sub={sub} paperId={paperId} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
