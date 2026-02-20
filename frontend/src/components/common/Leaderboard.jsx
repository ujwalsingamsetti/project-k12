import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from './Navbar';
import api from '../../services/api';
import {
    MdChevronLeft, MdEvent, MdPeople, MdStars, MdCheckCircle,
    MdArrowUpward, MdBarChart, MdKeyboardArrowRight, MdAssignment
} from 'react-icons/md';
import { BiLoaderAlt, BiTrophy } from 'react-icons/bi';

const MEDAL = {
    1: { icon: '🥇', cls: 'text-amber-500 scale-125' },
    2: { icon: '🥈', cls: 'text-slate-400 scale-110' },
    3: { icon: '🥉', cls: 'text-amber-700 scale-105' }
};

function GradeChip({ grade }) {
    const colors = {
        'A+': 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800',
        'A': 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 border-emerald-100 dark:border-emerald-800',
        'B': 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-blue-100 dark:border-blue-800',
        'C': 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-800',
        'D': 'bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400 border-orange-100 dark:border-orange-800',
        'F': 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-100 dark:border-red-800',
    };
    return (
        <span className={`text-[10px] font-black px-3 py-1 rounded-lg border uppercase tracking-widest ${colors[grade] || 'bg-slate-100 text-slate-600'}`}>
            {grade}
        </span>
    );
}

export default function Leaderboard() {
    const { paperId } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get(`/v2/papers/${paperId}/leaderboard`)
            .then(r => setData(r.data))
            .catch(e => console.error(e))
            .finally(() => setLoading(false));
    }, [paperId]);

    if (loading) return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
            <Navbar />
            <div className="flex flex-col items-center justify-center h-[60vh] text-slate-400 dark:text-slate-500 gap-4">
                <BiLoaderAlt size={48} className="animate-spin text-indigo-500" />
                <p className="font-medium">Fetching rankings...</p>
            </div>
        </div>
    );

    if (!data || data.entries?.length === 0) return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
            <Navbar />
            <div className="max-w-4xl mx-auto px-4 py-8 page-enter">
                <button onClick={() => navigate(-1)} className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-indigo-600 transition-colors mb-6">
                    <MdChevronLeft size={20} /> Back
                </button>
                <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border-4 border-dashed border-slate-100 dark:border-slate-800 rounded-[3rem] p-24 text-center">
                    <div className="w-24 h-24 bg-slate-50 dark:bg-slate-900 rounded-full flex items-center justify-center text-slate-200 dark:text-slate-700 mx-auto mb-8 shadow-inner">
                        <BiTrophy size={56} />
                    </div>
                    <h3 className="text-2xl font-black text-slate-900 dark:text-slate-100 mb-2">No Rankings Yet</h3>
                    <p className="text-slate-500 dark:text-slate-400 font-medium max-w-sm mx-auto">The leaderboard will appear once submissions are evaluated for this assessment.</p>
                </div>
            </div>
        </div>
    );

    const myEntry = data.entries.find(e => e.is_me);

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
            <Navbar />
            <div className="max-w-4xl mx-auto px-4 py-12 page-enter">
                <button onClick={() => navigate(-1)} className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-indigo-600 transition-colors mb-6">
                    <MdChevronLeft size={20} /> Back to Dashboard
                </button>

                {/* Header Section */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-8 mb-12">
                    <div>
                        <h1 className="text-4xl font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-4">
                            Elite Board <span className="w-12 h-1 bg-amber-500 rounded-full" />
                        </h1>
                        <div className="flex flex-wrap items-center gap-4 mt-3 text-sm font-medium text-slate-500">
                            <span className="flex items-center gap-1.5 bg-white dark:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                                <MdAssignment size={16} /> {data.paper_title}
                            </span>
                            <span className="flex items-center gap-1.5 bg-white dark:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                                <MdPeople size={16} /> {data.total_participants} Contenders
                            </span>
                        </div>
                    </div>

                    {myEntry && (
                        <div className="flex items-center gap-6 px-10 py-6 bg-indigo-600 rounded-[2.5rem] text-white shadow-2xl shadow-indigo-200 dark:shadow-none relative overflow-hidden group">
                            <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:scale-125 transition-transform duration-700">
                                <MdStars size={80} />
                            </div>
                            <div className="relative">
                                <p className="text-[10px] font-black uppercase tracking-widest opacity-60 mb-1">Your Standing</p>
                                <div className="flex items-baseline gap-2">
                                    <span className="text-4xl font-black">{MEDAL[myEntry.rank]?.icon || `#${myEntry.rank}`}</span>
                                    <span className="text-[10px] font-black uppercase tracking-widest bg-white/20 px-2 py-0.5 rounded-lg">Rank</span>
                                </div>
                            </div>
                            <div className="w-px h-12 bg-white/10" />
                            <div className="relative">
                                <p className="text-[10px] font-black uppercase tracking-widest opacity-60 mb-1">Total Score</p>
                                <div className="flex items-baseline gap-1">
                                    <span className="text-3xl font-black">{myEntry.score}</span>
                                    <span className="text-xs font-bold opacity-60">/{myEntry.max_marks}</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Leaderboard Body */}
                <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-[3rem] shadow-2xl dark:shadow-none overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="bg-slate-50/50 dark:bg-slate-900/50">
                                    <th className="px-8 py-6 text-left text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] w-24">Pos</th>
                                    <th className="px-8 py-6 text-left text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Competitor</th>
                                    <th className="px-8 py-6 text-right text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Result</th>
                                    <th className="px-8 py-6 text-center text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Efficiency</th>
                                    <th className="px-8 py-6 text-center text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Grade</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
                                {data.entries.map((e, i) => (
                                    <tr
                                        key={i}
                                        className={`group transition-all ${e.is_me ? 'bg-indigo-50/30 dark:bg-indigo-900/10' : 'hover:bg-slate-50/30 dark:hover:bg-slate-700/20'}`}
                                    >
                                        <td className="px-8 py-6">
                                            <div className={`w-10 h-10 rounded-2xl flex items-center justify-center text-sm font-black ${e.rank <= 3 ? (MEDAL[e.rank]?.cls + ' bg-white dark:bg-slate-900 shadow-sm border border-slate-100 dark:border-slate-800') : 'text-slate-400'
                                                }`}>
                                                {MEDAL[e.rank]?.icon || e.rank}
                                            </div>
                                        </td>
                                        <td className="px-8 py-6">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center font-black text-slate-400 group-hover:bg-indigo-100 group-hover:text-indigo-600 transition-colors">
                                                    {e.name.charAt(0)}
                                                </div>
                                                <div>
                                                    <p className="font-extrabold text-slate-900 dark:text-slate-100">
                                                        {e.name}
                                                        {e.is_me && <span className="ml-2 text-[8px] font-black bg-indigo-600 text-white px-1.5 py-0.5 rounded-lg uppercase tracking-widest">You</span>}
                                                    </p>
                                                    <p className="text-[10px] font-bold text-slate-400 group-hover:text-indigo-400/60 transition-colors">Verified Contender</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-8 py-6 text-right">
                                            <div className="flex items-baseline justify-end gap-1">
                                                <span className="text-lg font-black text-slate-900 dark:text-slate-100">{e.score}</span>
                                                <span className="text-[10px] font-bold text-slate-300 dark:text-slate-600">/{e.max_marks}</span>
                                            </div>
                                        </td>
                                        <td className="px-8 py-6 text-center">
                                            <div className="flex flex-col items-center gap-1.5">
                                                <span className={`text-sm font-black px-2 py-0.5 rounded-lg ${e.percentage >= 70 ? 'text-emerald-500 bg-emerald-50 dark:bg-emerald-900/20' :
                                                    e.percentage >= 40 ? 'text-amber-500 bg-amber-50 dark:bg-amber-900/20' :
                                                        'text-red-500 bg-red-50 dark:bg-red-900/20'
                                                    }`}>
                                                    {e.percentage}%
                                                </span>
                                                <div className="w-16 h-1 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                                                    <div className={`h-full rounded-full ${e.percentage >= 70 ? 'bg-emerald-500' : e.percentage >= 40 ? 'bg-amber-500' : 'bg-red-500'
                                                        }`} style={{ width: `${e.percentage}%` }} />
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-8 py-6 text-center">
                                            <GradeChip grade={e.grade} />
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
