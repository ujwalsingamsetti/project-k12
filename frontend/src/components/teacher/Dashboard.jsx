import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getMyPapers, deletePaper, getMyTextbooks, uploadTextbook, deleteTextbook } from '../../services/api';
import Navbar from '../common/Navbar';
import { useToast } from '../../context/ToastContext';
import {
  MdDelete, MdAdd, MdUpload, MdDescription, MdBook, MdGroup,
  MdBarChart, MdVisibility, MdAssignment, MdSchool, MdArrowForward,
  MdClose, MdOutlineLibraryBooks, MdOutlineDashboard, MdKeyboardArrowRight,
  MdCloudUpload, MdEditNote
} from 'react-icons/md';
import { BiLoaderAlt } from 'react-icons/bi';

// ─── Constants ────────────────────────────────────────────────────────────────
const SUBJECTS = [
  {
    group: 'Sciences', options: [
      { value: 'science', label: 'Science (General)' },
      { value: 'physics', label: 'Physics' },
      { value: 'chemistry', label: 'Chemistry' },
      { value: 'biology', label: 'Biology' },
      { value: 'environmental_science', label: 'Environmental Science' },
    ]
  },
  { group: 'Mathematics', options: [{ value: 'mathematics', label: 'Mathematics' }] },
  {
    group: 'Languages', options: [
      { value: 'english', label: 'English' },
      { value: 'hindi', label: 'Hindi' },
    ]
  },
  {
    group: 'Social Studies', options: [
      { value: 'social_science', label: 'Social Science (General)' },
      { value: 'history', label: 'History' },
      { value: 'geography', label: 'Geography' },
      { value: 'civics', label: 'Civics / Political Science' },
    ]
  },
  {
    group: 'Commerce / Humanities', options: [
      { value: 'economics', label: 'Economics' },
      { value: 'accountancy', label: 'Accountancy' },
      { value: 'business_studies', label: 'Business Studies' },
    ]
  },
  { group: 'Other', options: [{ value: 'general', label: 'General' }] },
];

const CLASS_LEVELS = [
  { value: 'kg', label: 'Kindergarten (KG)' },
  ...[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(g => ({ value: String(g), label: `Grade ${g}` })),
];

const labelForSubject = (val) => {
  for (const g of SUBJECTS) for (const o of g.options) if (o.value === val) return o.label;
  return val;
};
const labelForClass = (val) => {
  const found = CLASS_LEVELS.find(c => c.value === val);
  return found ? found.label : (val ? `Grade ${val}` : '—');
};

const SUBJECT_COLORS = {
  mathematics: 'bg-indigo-500', science: 'bg-emerald-500', physics: 'bg-blue-500',
  chemistry: 'bg-amber-500', biology: 'bg-green-600', english: 'bg-violet-500',
  hindi: 'bg-pink-500', history: 'bg-orange-500', geography: 'bg-cyan-500',
  social_science: 'bg-lime-500',
};
const colorClassFor = (s) => SUBJECT_COLORS[s?.toLowerCase()] || 'bg-slate-400';

const INPUT_STYLE = "w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium outline-none";

// ─── Upload Modal ─────────────────────────────────────────────────────────────
function UploadTextbookModal({ onClose, onSuccess }) {
  const [form, setForm] = useState({ title: '', subject: 'science', class_level: '12' });
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const toast = useToast();
  const fileRef = useRef();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) { toast.error('Please select a PDF file.'); return; }
    setUploading(true);
    try {
      await uploadTextbook(file, form.title || file.name.replace('.pdf', ''), form.subject, form.class_level);
      onSuccess();
    } catch { toast.error('Upload failed. Please try again.'); }
    finally { setUploading(false); }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-[2.5rem] shadow-2xl w-full max-w-md p-10 border border-slate-200 dark:border-slate-700 scale-enter">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-2xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-3">
            <MdUpload className="text-indigo-600" /> Add Textbook
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
            <MdClose size={28} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-3 ml-1">
              Source PDF <span className="text-red-500">*</span>
            </label>
            {file ? (
              <div className="flex items-center justify-between bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800 rounded-2xl px-5 py-4">
                <span className="text-sm font-bold text-slate-700 dark:text-slate-300 truncate flex items-center gap-3">
                  <MdDescription className="text-indigo-600 shrink-0" size={20} /> {file.name}
                </span>
                <button type="button" onClick={() => { setFile(null); fileRef.current.value = ''; }}
                  className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-all">
                  <MdDelete size={20} />
                </button>
              </div>
            ) : (
              <label className="flex flex-col items-center justify-center border-4 border-dashed border-slate-100 dark:border-slate-700 rounded-3xl p-10 cursor-pointer hover:border-indigo-200 dark:hover:border-indigo-900 transition-all group">
                <MdCloudUpload className="w-12 h-12 text-slate-300 dark:text-slate-600 group-hover:text-indigo-500 mb-3 transition" />
                <span className="text-sm text-slate-500 dark:text-slate-400 font-bold">Select PDF file</span>
                <input ref={fileRef} type="file" accept=".pdf" className="hidden"
                  onChange={(e) => setFile(e.target.files[0] || null)} />
              </label>
            )}
          </div>

          <div>
            <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2 ml-1">Title</label>
            <input type="text" value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className={INPUT_STYLE} placeholder="e.g. Physics Class 12" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2 ml-1">Subject</label>
              <select value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} className={INPUT_STYLE + " appearance-none cursor-pointer"}>
                {SUBJECTS.map(g => (
                  <optgroup key={g.group} label={g.group}>
                    {g.options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </optgroup>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2 ml-1">Class</label>
              <select value={form.class_level} onChange={(e) => setForm({ ...form, class_level: e.target.value })} className={INPUT_STYLE + " appearance-none cursor-pointer"}>
                {CLASS_LEVELS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
          </div>

          <button type="submit" disabled={uploading}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-5 rounded-[2rem] font-black text-lg shadow-xl shadow-indigo-100 dark:shadow-none transition-all flex items-center justify-center gap-3 active:scale-95 disabled:opacity-50 mt-4">
            {uploading ? <><BiLoaderAlt className="animate-spin" size={24} /> Uploading…</> : <><MdUpload size={24} /> Upload for AI Analysis</>}
          </button>
        </form>
      </div>
    </div>
  );
}

// ─── Paper Card ───────────────────────────────────────────────────────────────
function PaperCard({ paper, onDelete }) {
  const colorClass = colorClassFor(paper.subject);
  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-[2.5rem] p-6 flex flex-col gap-6 hover:shadow-2xl dark:hover:shadow-indigo-500/5 transition-all duration-500 group relative overflow-hidden">
      {/* Subject Line Decor */}
      <div className={`absolute top-0 left-0 w-full h-1.5 ${colorClass} opacity-60`} />

      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap gap-2 mb-3">
            <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest text-white ${colorClass}`}>
              {paper.subject?.replace('_', ' ')}
            </span>
            {paper.is_exam_mode && (
              <span className="bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border border-amber-200 dark:border-amber-800">
                Exam
              </span>
            )}
          </div>
          <h3 className="font-extrabold text-slate-900 dark:text-slate-100 text-lg leading-tight group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-2">{paper.title}</h3>
        </div>
        <button onClick={() => onDelete(paper.id)}
          className="text-slate-200 hover:text-red-500 transition-colors p-2 rounded-2xl hover:bg-red-50 dark:hover:bg-red-900/20">
          <MdDelete size={22} />
        </button>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Marks', value: paper.total_marks },
          { label: 'Minutes', value: paper.duration_minutes },
          { label: 'Level', value: labelForClass(paper.class_level).replace('Grade ', '') },
        ].map(({ label, value }) => (
          <div key={label} className="bg-slate-50 dark:bg-slate-900/50 rounded-2xl py-3 px-1 text-center border border-slate-100/50 dark:border-slate-700/50">
            <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-0.5">{label}</p>
            <p className="font-black text-slate-900 dark:text-slate-100 text-sm">{value}</p>
          </div>
        ))}
      </div>

      <div className="space-y-2 mt-auto">
        <div className="flex gap-2">
          <Link to={`/teacher/papers/${paper.id}/submissions`}
            className="flex-1 flex items-center justify-center gap-2 text-xs bg-indigo-600 hover:bg-indigo-700 text-white py-3.5 rounded-2xl transition-all font-black shadow-lg shadow-indigo-100 dark:shadow-none active:scale-95">
            <MdVisibility size={18} /> Submissions
          </Link>
          <Link to={`/teacher/papers/${paper.id}/edit`}
            className="flex items-center justify-center bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 p-3.5 rounded-2xl transition-all hover:bg-blue-100 dark:hover:bg-blue-800 shadow-sm border border-blue-100 dark:border-blue-800/50"
            title="Edit Paper">
            <MdEditNote size={20} />
          </Link>
          <Link to={`/teacher/papers/${paper.id}/analytics`}
            className="flex items-center justify-center bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 p-3.5 rounded-2xl transition-all hover:bg-emerald-100 dark:hover:bg-emerald-800 shadow-sm border border-emerald-100 dark:border-emerald-800/50"
            title="View Analytics">
            <MdBarChart size={20} />
          </Link>
          <Link to={`/teacher/papers/${paper.id}/assign`}
            className="flex items-center justify-center bg-slate-50 dark:bg-slate-900 text-slate-500 dark:text-slate-400 p-3.5 rounded-2xl transition-all hover:bg-slate-100 dark:hover:bg-slate-700 shadow-sm border border-slate-200 dark:border-slate-700"
            title="Assign Paper">
            <MdGroup size={20} />
          </Link>
        </div>
      </div>
    </div>
  );
}

// ─── Textbook Card ────────────────────────────────────────────────────────────
function TextbookCard({ textbook, onDelete }) {
  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-[2.5rem] p-6 flex flex-col gap-6 hover:shadow-2xl dark:hover:shadow-indigo-500/5 transition-all duration-500 group relative">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap gap-2 mb-3">
            <span className="bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border border-emerald-200 dark:border-emerald-800">
              {labelForSubject(textbook.subject)}
            </span>
            {textbook.class_level && (
              <span className="bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border border-blue-200 dark:border-blue-800">
                Grade {textbook.class_level}
              </span>
            )}
          </div>
          <h3 className="font-extrabold text-slate-900 dark:text-slate-100 text-lg leading-tight group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors line-clamp-2">{textbook.title}</h3>
        </div>
        <button onClick={() => onDelete(textbook.id)}
          className="text-slate-200 hover:text-red-500 transition-colors p-2 rounded-2xl hover:bg-red-50 dark:hover:bg-red-900/20">
          <MdDelete size={22} />
        </button>
      </div>

      <div className="flex justify-between items-center bg-slate-50 dark:bg-slate-900/50 rounded-2xl px-5 py-4 border border-slate-100/50 dark:border-slate-700/50">
        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Chapters Indexed</span>
        <span className="font-black text-slate-900 dark:text-slate-100 flex items-center gap-2">
          {textbook.chunk_count > 0 ? textbook.chunk_count : (
            <span className="text-amber-500 flex items-center gap-1.5 text-[10px] uppercase font-black tracking-tighter">
              <BiLoaderAlt className="animate-spin" /> AI Training…
            </span>
          )}
        </span>
      </div>

      <div className="mt-auto">
        <button className="w-full flex items-center justify-center gap-2 text-xs font-black uppercase tracking-widest text-slate-400 group-hover:text-emerald-500 transition-colors">
          View Source <MdArrowForward size={16} />
        </button>
      </div>
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
export default function TeacherDashboard() {
  const [papers, setPapers] = useState([]);
  const [textbooks, setTextbooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('papers');
  const [showUpload, setShowUpload] = useState(false);
  const toast = useToast();
  const navigate = useNavigate();

  useEffect(() => { loadPapers(); loadTextbooks(); }, []);

  const loadPapers = async () => {
    try { const res = await getMyPapers(); setPapers(res.data); }
    catch { toast.error('Failed to load papers'); }
    finally { setLoading(false); }
  };

  const loadTextbooks = async () => {
    try { const res = await getMyTextbooks(); setTextbooks(res.data); }
    catch { toast.error('Failed to load textbooks'); }
  };

  const handleDelete = async (paperId) => {
    if (!window.confirm('Delete this paper? This cannot be undone.')) return;
    try {
      await deletePaper(paperId);
      setPapers(p => p.filter(x => x.id !== paperId));
      toast.success('Paper deleted successfully');
    } catch { toast.error('Failed to delete paper'); }
  };

  const handleDeleteTextbook = async (id) => {
    if (!window.confirm('Delete this textbook from AI library?')) return;
    try {
      await deleteTextbook(id);
      setTextbooks(t => t.filter(x => x.id !== id));
      toast.success('Library updated');
    } catch { toast.error('Failed to update library'); }
  };

  const TABS = [
    { key: 'papers', label: 'Papers', icon: <MdAssignment />, count: papers.length },
    { key: 'textbooks', label: 'Library', icon: <MdOutlineLibraryBooks />, count: textbooks.length },
  ];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-200">
      <Navbar />

      {showUpload && (
        <UploadTextbookModal
          onClose={() => setShowUpload(false)}
          onSuccess={() => { setShowUpload(false); loadTextbooks(); toast.success('Textbook added to AI library!'); }}
        />
      )}

      <div className="max-w-7xl mx-auto px-4 py-12 page-enter">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-8 mb-12">
          <div>
            <h1 className="text-4xl font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-4">
              Dashboard <span className="w-12 h-1 bg-indigo-600 rounded-full" />
            </h1>
            <p className="text-slate-500 dark:text-slate-400 font-bold mt-2 uppercase text-[10px] tracking-[0.3em] flex items-center gap-2">
              <MdOutlineDashboard className="text-indigo-500" /> Professional Educator Suite
            </p>
          </div>

          <div className="flex gap-4">
            <>
              <Link to="/teacher/sections"
                className="inline-flex items-center gap-2 text-sm bg-white dark:bg-slate-800 border-2 border-slate-100 dark:border-slate-700 text-slate-700 dark:text-slate-300 px-6 py-3.5 rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-all font-bold shadow-sm active:scale-95">
                <MdGroup size={20} className="text-indigo-500" /> Class Sections
              </Link>
              <Link to="/teacher/create-paper"
                className="inline-flex items-center gap-2 text-sm bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3.5 rounded-2xl transition-all font-black shadow-xl shadow-indigo-100 dark:shadow-none active:scale-95">
                <MdAdd size={24} /> New Paper
              </Link>
            </>
          </div>
        </div>

        {/* Dynamic Navigation Tabs */}
        <div className="flex items-center justify-between mb-8 border-b border-slate-200 dark:border-slate-800">
          <div className="flex gap-8">
            {TABS.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`relative pb-4 text-sm font-black uppercase tracking-widest transition-all px-2 ${activeTab === tab.key
                  ? 'text-indigo-600 dark:text-indigo-400'
                  : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
                  }`}
              >
                <div className="flex items-center gap-2">
                  {tab.icon} {tab.label}
                  {tab.count > 0 && (
                    <span className={`text-[10px] font-black px-2 py-0.5 rounded-lg ${activeTab === tab.key ? 'bg-indigo-100 dark:bg-indigo-900/50' : 'bg-slate-50 dark:bg-slate-900'
                      }`}>
                      {tab.count}
                    </span>
                  )}
                </div>
                {activeTab === tab.key && (
                  <div className="absolute bottom-[-1px] left-0 w-full h-1 bg-indigo-600 dark:bg-indigo-400 rounded-full animate-in fade-in zoom-in-95 duration-300" />
                )}
              </button>
            ))}
          </div>

          {activeTab === 'textbooks' && (
            <button onClick={() => setShowUpload(true)}
              className="text-xs font-black text-indigo-600 dark:text-indigo-400 flex items-center gap-1.5 hover:underline mb-4">
              <MdUpload size={18} /> Add to AI Library
            </button>
          )}
        </div>

        {/* Papers Tab */}
        {activeTab === 'papers' && (
          loading ? (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-[2.5rem] p-8 h-64 animate-pulse">
                  <div className="h-6 bg-slate-100 dark:bg-slate-700 rounded-2xl w-3/4 mb-6" />
                  <div className="h-3 bg-slate-50 dark:bg-slate-700 rounded-full w-1/2 mb-10" />
                  <div className="grid grid-cols-3 gap-3">
                    {[...Array(3)].map((_, j) => <div key={j} className="h-14 bg-slate-50 dark:bg-slate-700 rounded-2xl" />)}
                  </div>
                </div>
              ))}
            </div>
          ) : papers.length === 0 ? (
            <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border-4 border-dashed border-slate-100 dark:border-slate-800 rounded-[3rem] p-24 text-center mt-4">
              <div className="w-24 h-24 bg-slate-50 dark:bg-slate-900 rounded-full flex items-center justify-center text-slate-200 dark:text-slate-700 mx-auto mb-8 shadow-inner">
                <MdAssignment size={56} />
              </div>
              <h3 className="text-2xl font-black text-slate-900 dark:text-slate-100 mb-2">Build your first exam</h3>
              <p className="text-slate-500 dark:text-slate-400 font-medium mb-10 max-w-sm mx-auto">Create beautiful question papers with AI-assisted grading in minutes.</p>
              <Link to="/teacher/create-paper"
                className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-10 py-4 rounded-[2rem] font-black shadow-xl shadow-indigo-100 dark:shadow-none transition-all active:scale-95">
                <MdAdd size={24} /> Get Started Now
              </Link>
            </div>
          ) : (
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              {papers.map(p => <PaperCard key={p.id} paper={p} onDelete={handleDelete} />)}
            </div>
          )
        )}

        {/* Textbooks Tab */}
        {activeTab === 'textbooks' && (
          textbooks.length === 0 ? (
            <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border-4 border-dashed border-slate-100 dark:border-slate-800 rounded-[3rem] p-24 text-center mt-4">
              <div className="w-24 h-24 bg-slate-50 dark:bg-slate-900 rounded-full flex items-center justify-center text-slate-200 dark:text-slate-700 mx-auto mb-8 shadow-inner">
                <MdOutlineLibraryBooks size={56} />
              </div>
              <p className="text-2xl font-black text-slate-900 dark:text-slate-100 mb-2">No AI Resources</p>
              <p className="text-slate-500 dark:text-slate-400 font-medium mb-10 max-w-sm mx-auto">Upload textbooks to train the AI on your specific curriculum for more accurate grading.</p>
              <button onClick={() => setShowUpload(true)}
                className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-10 py-4 rounded-[2rem] font-black shadow-xl shadow-emerald-100 dark:shadow-none transition-all active:scale-95">
                <MdUpload size={24} /> Upload Textbook
              </button>
            </div>
          ) : (
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              {textbooks.map(t => <TextbookCard key={t.id} textbook={t} onDelete={handleDeleteTextbook} />)}
            </div>
          )
        )}
      </div>
    </div>
  );
}
