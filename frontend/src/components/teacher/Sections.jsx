import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../common/Navbar';
import api from '../../services/api';
import { useToast } from '../../context/ToastContext';
import {
    MdGroup, MdAdd, MdDelete, MdChevronLeft, MdSave,
    MdAssignment, MdEvent, MdSearch, MdClose, MdCheckCircle
} from 'react-icons/md';
import { RiExpandUpDownLine } from 'react-icons/ri';
import { BiLoaderAlt } from 'react-icons/bi';

export default function Sections() {
    const navigate = useNavigate();
    const toast = useToast();
    const [sections, setSections] = useState([]);
    const [students, setStudents] = useState([]);
    const [papers, setPapers] = useState([]);
    const [loading, setLoading] = useState(true);

    // Create section form
    const [showCreate, setShowCreate] = useState(false);
    const [form, setForm] = useState({ name: '', class_level: '', subject: '' });
    const [creating, setCreating] = useState(false);

    // Manage members modal
    const [activeSection, setActiveSection] = useState(null);
    const [memberIds, setMemberIds] = useState(new Set());
    const [searchStudent, setSearchStudent] = useState('');
    const [savingMembers, setSavingMembers] = useState(false);

    // Assign section to paper modal
    const [assignPaper, setAssignPaper] = useState(null); // section object
    const [selectedPaper, setSelectedPaper] = useState('');
    const [dueDate, setDueDate] = useState('');
    const [assigning, setAssigning] = useState(false);

    useEffect(() => {
        Promise.all([
            api.get('/teacher/sections'),
            api.get('/teacher/students'),
            api.get('/teacher/papers'),
        ]).then(([s, st, p]) => {
            setSections(s.data);
            setStudents(st.data);
            setPapers(p.data);
        }).catch(() => toast.error('Failed to load data'))
            .finally(() => setLoading(false));
    }, []);

    const createSection = async () => {
        if (!form.name.trim()) return;
        setCreating(true);
        try {
            const res = await api.post('/teacher/sections', form);
            setSections(prev => [...prev, res.data]);
            setShowCreate(false);
            setForm({ name: '', class_level: '', subject: '' });
            toast.success('Section created!');
        } catch {
            toast.error('Failed to create section');
        } finally {
            setCreating(false);
        }
    };

    const deleteSection = async (id) => {
        if (!confirm('Delete this section?')) return;
        try {
            await api.delete(`/teacher/sections/${id}`);
            setSections(prev => prev.filter(s => s.id !== id));
            if (activeSection?.id === id) setActiveSection(null);
            toast.success('Section deleted');
        } catch {
            toast.error('Failed to delete section');
        }
    };

    const openMembers = async (section) => {
        setActiveSection(section);
        setSearchStudent('');
        try {
            const res = await api.get(`/teacher/sections/${section.id}/members`);
            setMemberIds(new Set(res.data.map(m => m.student_id)));
        } catch {
            toast.error('Failed to load members');
        }
    };

    const saveMembers = async () => {
        setSavingMembers(true);
        try {
            await api.put(`/teacher/sections/${activeSection.id}/members`, { student_ids: [...memberIds] });
            setSections(prev => prev.map(s => s.id === activeSection.id ? { ...s, member_count: memberIds.size } : s));
            toast.success(`Saved ${memberIds.size} members`);
            setActiveSection(null);
        } catch {
            toast.error('Failed to save members');
        } finally {
            setSavingMembers(false);
        }
    };

    const doAssign = async () => {
        if (!selectedPaper) return;
        setAssigning(true);
        try {
            const res = await api.post(`/teacher/sections/${assignPaper.id}/assign-paper/${selectedPaper}`, null, {
                params: dueDate ? { due_date: new Date(dueDate).toISOString() } : {}
            });
            toast.success(res.data.message || 'Paper assigned successfully!');
            setAssignPaper(null);
        } catch {
            toast.error('Failed to assign paper');
        } finally {
            setAssigning(false);
        }
    };

    const filtered = students.filter(s =>
        s.name.toLowerCase().includes(searchStudent.toLowerCase()) ||
        s.email.toLowerCase().includes(searchStudent.toLowerCase())
    );

    if (loading) return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
            <Navbar />
            <div className="flex flex-col items-center justify-center h-[60vh] text-slate-400 dark:text-slate-500 gap-4">
                <BiLoaderAlt size={48} className="animate-spin text-indigo-500" />
                <p className="font-medium">Loading sections...</p>
            </div>
        </div>
    );

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
            <Navbar />
            <div className="max-w-7xl mx-auto px-4 py-8 page-enter">

                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <button onClick={() => navigate('/teacher')} className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors mb-2">
                            <MdChevronLeft size={20} /> Back to Dashboard
                        </button>
                        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-3">
                            <MdGroup className="text-indigo-600 dark:text-indigo-400" size={32} /> Class Sections
                        </h1>
                        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1 font-medium">Group students and manage paper assignments collectively</p>
                    </div>
                    <button
                        onClick={() => setShowCreate(true)}
                        className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-2xl shadow-lg shadow-indigo-200 dark:shadow-none transition-all duration-200 font-bold text-sm transform active:scale-95"
                    >
                        <MdAdd size={20} /> New Section
                    </button>
                </div>

                {/* Create Section Modal */}
                {showCreate && (
                    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="bg-white dark:bg-slate-800 rounded-3xl shadow-2xl w-full max-w-md p-8 border border-slate-200 dark:border-slate-700 scale-enter">
                            <div className="flex items-center justify-between mb-6">
                                <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">Create Section</h3>
                                <button onClick={() => setShowCreate(false)} className="text-slate-400 hover:text-slate-600 transition-colors">
                                    <MdClose size={24} />
                                </button>
                            </div>
                            <div className="space-y-5">
                                <div>
                                    <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Section Name</label>
                                    <input
                                        value={form.name}
                                        onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                                        placeholder="e.g. Grade 10 - Science A"
                                        className="w-full px-4 py-3 border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 rounded-2xl text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none dark:text-slate-100"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Grade Level</label>
                                        <input
                                            value={form.class_level}
                                            onChange={e => setForm(f => ({ ...f, class_level: e.target.value }))}
                                            placeholder="e.g. 10"
                                            className="w-full px-4 py-3 border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 rounded-2xl text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none dark:text-slate-100"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Subject</label>
                                        <input
                                            value={form.subject}
                                            onChange={e => setForm(f => ({ ...f, subject: e.target.value }))}
                                            placeholder="e.g. Biology"
                                            className="w-full px-4 py-3 border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 rounded-2xl text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none dark:text-slate-100"
                                        />
                                    </div>
                                </div>
                            </div>
                            <div className="flex gap-4 mt-8">
                                <button
                                    onClick={createSection}
                                    disabled={creating}
                                    className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-2xl text-sm font-bold shadow-lg shadow-indigo-100 dark:shadow-none transition-all flex items-center justify-center gap-2"
                                >
                                    {creating ? <BiLoaderAlt className="animate-spin" size={20} /> : 'Create Section'}
                                </button>
                                <button
                                    onClick={() => setShowCreate(false)}
                                    className="px-6 py-3 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 font-bold text-sm rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Section Grid */}
                {sections.length === 0 ? (
                    <div className="bg-white dark:bg-slate-800 border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-3xl p-20 text-center flex flex-col items-center gap-4">
                        <div className="w-20 h-20 bg-slate-50 dark:bg-slate-900 rounded-full flex items-center justify-center text-slate-300 dark:text-slate-600">
                            <MdGroup size={48} />
                        </div>
                        <div>
                            <p className="text-xl font-bold text-slate-900 dark:text-slate-100">No sections yet</p>
                            <p className="text-slate-500 dark:text-slate-400 mt-1 max-w-sm mx-auto">Create sections to easily assign papers to entire classes at once.</p>
                        </div>
                        <button
                            onClick={() => setShowCreate(true)}
                            className="mt-2 text-indigo-600 dark:text-indigo-400 font-bold hover:underline"
                        >
                            + Create your first section
                        </button>
                    </div>
                ) : (
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
                        {sections.map(s => (
                            <div key={s.id} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-3xl p-6 shadow-sm hover:shadow-xl dark:shadow-indigo-500/5 transition-all duration-300 group">
                                <div className="flex justify-between items-start mb-6">
                                    <div>
                                        <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">{s.name}</h3>
                                        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400 mt-1.5 uppercase tracking-wider">
                                            {s.class_level && <span className="bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded-md">Grade {s.class_level}</span>}
                                            {s.subject && <span className="bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded-md">{s.subject}</span>}
                                        </div>
                                    </div>
                                    <span className="inline-flex items-center gap-1.5 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 px-3 py-1 rounded-full text-xs font-bold">
                                        <MdPerson size={14} /> {s.member_count}
                                    </span>
                                </div>

                                <div className="space-y-2">
                                    <div className="flex gap-2">
                                        <button onClick={() => openMembers(s)}
                                            className="flex-1 inline-flex items-center justify-center gap-2 py-2.5 border border-slate-200 dark:border-slate-700 rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-900 text-slate-700 dark:text-slate-300 font-bold text-sm transition-all">
                                            <MdGroup size={18} /> Members
                                        </button>
                                        <button onClick={() => { setAssignPaper(s); setSelectedPaper(''); setDueDate(''); }}
                                            className="flex-1 inline-flex items-center justify-center gap-2 py-2.5 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-400 rounded-2xl hover:bg-indigo-100 dark:hover:bg-indigo-900/40 font-bold text-sm transition-all">
                                            <MdAssignment size={18} /> Assign
                                        </button>
                                    </div>
                                    <button onClick={() => deleteSection(s.id)}
                                        className="w-full inline-flex items-center justify-center gap-2 py-2.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-2xl font-bold text-sm transition-all opacity-0 group-hover:opacity-100">
                                        <MdDelete size={18} /> Delete Section
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Manage Members Side Panel */}
                {activeSection && (
                    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex justify-end z-50">
                        <div className="bg-white dark:bg-slate-800 w-full max-w-md h-full shadow-2xl flex flex-col page-enter">
                            <div className="p-8 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center">
                                <div>
                                    <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">{activeSection.name}</h2>
                                    <p className="text-sm text-slate-500 dark:text-slate-400 font-medium mt-1">Manage members in this section</p>
                                </div>
                                <button onClick={() => setActiveSection(null)} className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
                                    <MdClose size={28} />
                                </button>
                            </div>

                            <div className="p-8 pb-4">
                                <div className="relative group">
                                    <MdSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors" size={20} />
                                    <input
                                        value={searchStudent}
                                        onChange={e => setSearchStudent(e.target.value)}
                                        placeholder="Search by name or email..."
                                        className="w-full pl-12 pr-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl text-sm outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all dark:text-slate-100"
                                    />
                                </div>
                                <div className="flex items-center justify-between mt-6 px-1">
                                    <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">{students.length} Total Students</span>
                                    <div className="flex gap-4">
                                        <button onClick={() => setMemberIds(new Set(students.map(s => s.id)))} className="text-xs font-bold text-indigo-600 hover:underline">Select all</button>
                                        <button onClick={() => setMemberIds(new Set())} className="text-xs font-bold text-slate-500 hover:underline">Deselect all</button>
                                    </div>
                                </div>
                            </div>

                            <div className="flex-1 overflow-y-auto px-8 py-2">
                                <div className="space-y-2">
                                    {filtered.map(st => (
                                        <label key={st.id} className="flex items-center gap-4 p-4 rounded-2xl border border-transparent hover:border-slate-200 dark:hover:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-900/50 cursor-pointer transition-all">
                                            <input
                                                type="checkbox"
                                                checked={memberIds.has(st.id)}
                                                onChange={() => setMemberIds(prev => { const n = new Set(prev); n.has(st.id) ? n.delete(st.id) : n.add(st.id); return n; })}
                                                className="w-5 h-5 rounded-md border-slate-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                                            />
                                            <div className="flex-1 min-w-0">
                                                <p className="font-bold text-slate-900 dark:text-slate-100 truncate">{st.name}</p>
                                                <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{st.email}</p>
                                            </div>
                                            {memberIds.has(st.id) && <MdCheckCircle size={20} className="text-indigo-500" />}
                                        </label>
                                    ))}
                                    {filtered.length === 0 && (
                                        <div className="text-center py-10">
                                            <p className="text-sm text-slate-400">No students found.</p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="p-8 border-t border-slate-100 dark:border-slate-700">
                                <button
                                    onClick={saveMembers}
                                    disabled={savingMembers}
                                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-4 rounded-2xl font-bold transition-all shadow-lg shadow-indigo-100 dark:shadow-none flex items-center justify-center gap-2"
                                >
                                    {savingMembers ? <BiLoaderAlt className="animate-spin" size={24} /> : (
                                        <>
                                            <MdSave size={20} />
                                            <span>Update Members ({memberIds.size})</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Assign Paper Modal */}
                {assignPaper && (
                    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="bg-white dark:bg-slate-800 rounded-3xl shadow-2xl w-full max-w-md p-8 border border-slate-200 dark:border-slate-700 scale-enter">
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">Assign Paper</h3>
                                <button onClick={() => setAssignPaper(null)} className="text-slate-400 hover:text-slate-600 transition-colors">
                                    <MdClose size={24} />
                                </button>
                            </div>
                            <p className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-8 flex items-center gap-1.5">
                                to <span className="text-indigo-600 dark:text-indigo-400 font-bold">{assignPaper.name}</span> · {assignPaper.member_count} students
                            </p>

                            <div className="space-y-6">
                                <div className="relative group">
                                    <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2 ml-1">Select Paper</label>
                                    <div className="relative">
                                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
                                            <MdAssignment size={20} />
                                        </div>
                                        <select
                                            value={selectedPaper}
                                            onChange={e => setSelectedPaper(e.target.value)}
                                            className="w-full pl-12 pr-10 py-3.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl text-sm font-medium outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 appearance-none cursor-pointer dark:text-slate-100 transition-all"
                                        >
                                            <option value="">Choose a paper...</option>
                                            {papers.map(p => <option key={p.id} value={p.id}>{p.title}</option>)}
                                        </select>
                                        <div className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
                                            <RiExpandUpDownLine size={18} />
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2 ml-1">Due Date <span className="text-xs text-slate-400 font-normal ml-1">(Optional)</span></label>
                                    <div className="relative">
                                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
                                            <MdEvent size={20} />
                                        </div>
                                        <input
                                            type="datetime-local"
                                            value={dueDate}
                                            onChange={e => setDueDate(e.target.value)}
                                            className="w-full pl-12 pr-4 py-3.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl text-sm font-medium outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 dark:text-slate-100 transition-all"
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="flex gap-4 mt-10">
                                <button
                                    onClick={doAssign}
                                    disabled={!selectedPaper || assigning}
                                    className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white py-4 rounded-2xl font-bold shadow-lg shadow-indigo-100 dark:shadow-none transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                                >
                                    {assigning ? <BiLoaderAlt className="animate-spin" size={20} /> : 'Assign Now'}
                                </button>
                                <button
                                    onClick={() => setAssignPaper(null)}
                                    className="px-6 py-4 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 font-bold text-sm rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
