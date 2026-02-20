import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../common/Navbar';
import api from '../../services/api';
import { useToast } from '../../context/ToastContext';
import {
    MdChevronLeft, MdPerson, MdSearch, MdEvent,
    MdCheckCircle, MdRemoveCircleOutline, MdAssignmentInd,
    MdMailOutline
} from 'react-icons/md';
import { BiLoaderAlt } from 'react-icons/bi';

function toIST(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: '2-digit', year: 'numeric' });
}

export default function AssignPaper() {
    const { paperId } = useParams();
    const navigate = useNavigate();
    const toast = useToast();

    const [paper, setPaper] = useState(null);
    const [students, setStudents] = useState([]);
    const [assignments, setAssignments] = useState([]);
    const [selected, setSelected] = useState(new Set());
    const [dueDate, setDueDate] = useState('');
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [search, setSearch] = useState('');

    useEffect(() => {
        Promise.all([
            api.get(`/teacher/papers/${paperId}`),
            api.get('/teacher/students'),
            api.get(`/teacher/papers/${paperId}/assignments`),
        ]).then(([paperRes, studentsRes, assignRes]) => {
            setPaper(paperRes.data);
            setStudents(studentsRes.data);
            setAssignments(assignRes.data);
            const assignedIds = new Set(assignRes.data.map(a => a.student_id));
            setSelected(assignedIds);
        }).catch(() => toast.error('Failed to load data'))
            .finally(() => setLoading(false));
    }, [paperId]);

    const assignedIds = new Set(assignments.map(a => a.student_id));

    const toggleStudent = (id) => {
        setSelected(prev => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id); else next.add(id);
            return next;
        });
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            await api.post(`/teacher/papers/${paperId}/assign`, {
                student_ids: [...selected],
                due_date: dueDate || null,
            });
            const res = await api.get(`/teacher/papers/${paperId}/assignments`);
            setAssignments(res.data);
            toast.success(`Successfully assigned to ${selected.size} student(s)`);
        } catch {
            toast.error('Failed to assign paper');
        } finally {
            setSaving(false);
        }
    };

    const handleRemove = async (studentId) => {
        if (!confirm('Remove assignment for this student?')) return;
        try {
            await api.delete(`/teacher/papers/${paperId}/assignments/${studentId}`);
            setAssignments(prev => prev.filter(a => a.student_id !== studentId));
            setSelected(prev => { const n = new Set(prev); n.delete(studentId); return n; });
            toast.success('Assignment removed');
        } catch {
            toast.error('Failed to remove assignment');
        }
    };

    const filteredStudents = students.filter(s =>
        s.name.toLowerCase().includes(search.toLowerCase()) ||
        s.email.toLowerCase().includes(search.toLowerCase())
    );

    if (loading) return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
            <Navbar />
            <div className="flex flex-col items-center justify-center h-[60vh] text-slate-400 dark:text-slate-500 gap-4">
                <BiLoaderAlt size={48} className="animate-spin text-indigo-500" />
                <p className="font-medium">Loading paper details...</p>
            </div>
        </div>
    );

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
            <Navbar />
            <div className="max-w-7xl mx-auto px-4 py-8 page-enter">

                {/* Header */}
                <div className="mb-10">
                    <button onClick={() => navigate(-1)} className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors mb-2">
                        <MdChevronLeft size={20} /> Back
                    </button>
                    <h1 className="text-3xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-3">
                        <MdAssignmentInd className="text-indigo-600 dark:text-indigo-400" size={32} /> Assign Paper
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400 font-bold mt-1 text-lg">{paper?.title}</p>
                </div>

                <div className="grid lg:grid-cols-5 gap-8">
                    {/* Left Column: Student Selection */}
                    <div className="lg:col-span-3 space-y-6">
                        <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-3xl p-8 shadow-xl dark:shadow-none">
                            <div className="flex items-center justify-between mb-6">
                                <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                                    <MdPerson className="text-indigo-500" /> Select Students
                                </h2>
                                <div className="flex gap-4">
                                    <button onClick={() => setSelected(new Set(students.map(s => s.id)))}
                                        className="text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline">Select all</button>
                                    <button onClick={() => setSelected(new Set())}
                                        className="text-xs font-bold text-slate-500 hover:underline">Clear all</button>
                                </div>
                            </div>

                            <div className="relative group mb-6">
                                <MdSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors" size={20} />
                                <input
                                    value={search}
                                    onChange={e => setSearch(e.target.value)}
                                    placeholder="Search by name or email..."
                                    className="w-full pl-12 pr-4 py-3.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl text-sm font-medium outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all dark:text-slate-100"
                                />
                            </div>

                            <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                                {filteredStudents.length === 0 && (
                                    <div className="text-center py-20 bg-slate-50/50 dark:bg-slate-900/50 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-700">
                                        <MdPerson className="mx-auto text-slate-300 dark:text-slate-600 mb-2" size={40} />
                                        <p className="text-slate-400 dark:text-slate-500 font-medium">No students found matching your search</p>
                                    </div>
                                )}
                                {filteredStudents.map(s => (
                                    <label key={s.id} className={`flex items-center gap-4 p-4 rounded-2xl border transition-all cursor-pointer ${selected.has(s.id)
                                            ? 'border-indigo-200 bg-indigo-50/30 dark:border-indigo-900/50 dark:bg-indigo-900/10'
                                            : 'border-transparent hover:border-slate-200 dark:hover:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-900/30'
                                        }`}>
                                        <div className="relative flex items-center justify-center">
                                            <input
                                                type="checkbox"
                                                checked={selected.has(s.id)}
                                                onChange={() => toggleStudent(s.id)}
                                                className="w-6 h-6 rounded-lg border-slate-300 text-indigo-600 focus:ring-indigo-500/20 cursor-pointer"
                                            />
                                            {selected.has(s.id) && <MdCheckCircle className="absolute pointer-events-none text-indigo-600" size={22} />}
                                        </div>
                                        <div className="min-w-0 flex-1">
                                            <p className="font-bold text-slate-900 dark:text-slate-100 truncate">{s.name}</p>
                                            <div className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400">
                                                <MdMailOutline size={14} />
                                                <p className="text-xs font-medium truncate">{s.email}</p>
                                            </div>
                                        </div>
                                        {assignedIds.has(s.id) && (
                                            <span className="shrink-0 inline-flex items-center gap-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 px-3 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-tight">
                                                <MdCheckCircle size={12} /> Assigned
                                            </span>
                                        )}
                                    </label>
                                ))}
                            </div>

                            <div className="mt-8 grid md:grid-cols-5 gap-6 items-end pt-8 border-t border-slate-100 dark:border-slate-700">
                                <div className="md:col-span-3">
                                    <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2 ml-1">Due Date <span className="text-xs text-slate-400 font-normal ml-1">(Optional)</span></label>
                                    <div className="relative">
                                        <MdEvent className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" size={20} />
                                        <input
                                            type="datetime-local"
                                            value={dueDate}
                                            onChange={e => setDueDate(e.target.value)}
                                            className="w-full pl-12 pr-4 py-3.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl text-sm font-medium outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 dark:text-slate-100 transition-all"
                                        />
                                    </div>
                                </div>
                                <div className="md:col-span-2">
                                    <button
                                        onClick={handleSave}
                                        disabled={saving || selected.size === 0}
                                        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-4 rounded-2xl font-bold shadow-lg shadow-indigo-100 dark:shadow-none transition-all flex items-center justify-center gap-2 disabled:opacity-50 h-[52px]"
                                    >
                                        {saving ? <BiLoaderAlt className="animate-spin" size={24} /> : (
                                            <>
                                                <MdAssignmentInd size={20} />
                                                <span>Save Assignment ({selected.size})</span>
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Current Assignments Stats */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-3xl p-8 shadow-xl dark:shadow-none h-fit">
                            <div className="flex items-center justify-between mb-8">
                                <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">Currently Assigned</h2>
                                <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 text-xs font-black px-3 py-1 rounded-full">
                                    {assignments.length}
                                </span>
                            </div>

                            {assignments.length === 0 ? (
                                <div className="text-center py-16 px-4 bg-slate-50/50 dark:bg-slate-900/50 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-700">
                                    <p className="text-slate-400 dark:text-slate-500 font-medium text-sm">No assignments found for this paper yet.</p>
                                </div>
                            ) : (
                                <div className="space-y-3 max-h-[700px] overflow-y-auto pr-2 custom-scrollbar">
                                    {assignments.map(a => (
                                        <div key={a.assignment_id}
                                            className="group flex items-center justify-between p-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-700 hover:border-indigo-200 dark:hover:border-indigo-900 shadow-sm transition-all duration-300">
                                            <div className="min-w-0">
                                                <p className="font-bold text-slate-900 dark:text-slate-100 text-sm truncate">{a.student_name}</p>
                                                <p className="text-[10px] font-medium text-slate-400 dark:text-slate-500 truncate mb-1">{a.student_email}</p>
                                                {a.due_date && (
                                                    <div className="flex items-center gap-1.5 text-amber-600 dark:text-amber-500 text-[10px] font-bold">
                                                        <MdEvent size={12} />
                                                        <span>Due: {toIST(a.due_date)}</span>
                                                    </div>
                                                )}
                                            </div>
                                            <button
                                                onClick={() => handleRemove(a.student_id)}
                                                className="p-2 text-slate-300 hover:text-red-500 dark:hover:text-red-400 transition-colors rounded-xl hover:bg-red-50 dark:hover:bg-red-900/20"
                                                title="Remove Assignment"
                                            >
                                                <MdRemoveCircleOutline size={20} />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
