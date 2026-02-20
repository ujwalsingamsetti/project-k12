import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../common/Navbar';
import { useToast } from '../../context/ToastContext';
import api from '../../services/api';

import {
    MdPeople as PeopleIcon, MdTrendingUp as TrendingIcon, MdEmojiEvents as AwardIcon,
    MdCheckCircle as CheckIcon, MdArrowBack as BackIcon, MdFileDownload as DownloadIcon,
    MdInsertChart as ChartIcon, MdLayers as TableIcon, MdSentimentVeryDissatisfied as SadIcon,
    MdInfo as InfoIcon, MdStar as StarIcon,
    MdCheckCircleOutline, MdChevronLeft, MdDownload, MdBarChart, MdTableChart,
    MdSentimentDissatisfied, MdOutlineAnalytics, MdInfoOutline,
    MdStars, MdFiberManualRecord
} from 'react-icons/md';
import { BiLoaderAlt } from 'react-icons/bi';
import { FiAlertTriangle, FiTarget } from 'react-icons/fi';

// ── Grade colour map ──────────────────────────────────────────────────────────
const GRADE_COLORS = {
    'A+': '#10b981', A: '#34d399', B: '#3b82f6', C: '#f59e0b', D: '#f97316', F: '#ef4444',
};
const gradeOf = (pct) => {
    if (pct >= 90) return 'A+';
    if (pct >= 75) return 'A';
    if (pct >= 60) return 'B';
    if (pct >= 45) return 'C';
    if (pct >= 33) return 'D';
    return 'F';
};

// ── Difficulty chip ───────────────────────────────────────────────────────────
const diffChip = (pct) => {
    if (pct >= 70) return { label: 'Accessible', cls: 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 border-emerald-100 dark:border-emerald-800' };
    if (pct >= 40) return { label: 'Moderate', cls: 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-800' };
    return { label: 'Challenging', cls: 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-100 dark:border-red-800' };
};

// ── Stat Card ─────────────────────────────────────────────────────────────────
function StatCard({ icon, label, value, sub, accentClass = 'text-slate-900 dark:text-slate-100' }) {
    return (
        <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-3xl p-8 shadow-xl dark:shadow-none hover:shadow-2xl transition-all group overflow-hidden relative">
            <div className="absolute top-0 right-0 p-4 opacity-[0.03] group-hover:scale-125 transition-transform duration-700">
                {icon}
            </div>
            <div className="relative">
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">{label}</p>
                <div className="flex items-baseline gap-2">
                    <p className={`text-3xl font-black ${accentClass}`}>{value}</p>
                </div>
                {sub && <p className="text-xs font-bold text-slate-500 dark:text-slate-400 mt-2 flex items-center gap-1.5"><MdFiberManualRecord size={8} className="text-indigo-500" /> {sub}</p>}
            </div>
        </div>
    );
}

// ── Bar Chart ─────────────────────────────────────────────────────────────────
function BarChart({ data, valueKey, labelKey, maxValue, colorFn }) {
    if (!data?.length) return <p className="text-slate-400 dark:text-slate-500 text-sm italic py-10 text-center">Waiting for score data...</p>;
    return (
        <div className="space-y-6">
            {data.map((item, i) => {
                const pct = maxValue > 0 ? (item[valueKey] / maxValue) * 100 : 0;
                const color = colorFn ? colorFn(item) : '#6366f1';
                return (
                    <div key={i} className="group">
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-[10px] font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">{item[labelKey]}</span>
                            <span className="text-xs font-black text-slate-900 dark:text-slate-100">{item[valueKey]}</span>
                        </div>
                        <div className="bg-slate-50 dark:bg-slate-900 rounded-full h-4 overflow-hidden border border-white dark:border-slate-800 shadow-inner">
                            <div className="h-full rounded-full transition-all duration-1000 ease-out shadow-sm" style={{ width: `${pct}%`, backgroundColor: color }} />
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

// ── Grade Donut ───────────────────────────────────────────────────────────────
function GradeDonut({ distribution }) {
    if (!distribution?.length) return null;
    const total = distribution.reduce((s, d) => s + d.count, 0);
    if (!total) return null;
    let cum = 0;
    const segments = distribution.filter(d => d.count > 0).map(d => {
        const pct = (d.count / total) * 100;
        const seg = { grade: d.grade, count: d.count, pct, start: cum, color: GRADE_COLORS[d.grade] || '#94a3b8' };
        cum += pct;
        return seg;
    });
    const gradient = segments.map(s => `${s.color} ${s.start}% ${s.start + s.pct}%`).join(', ');

    return (
        <div className="flex flex-col xl:flex-row items-center gap-10">
            <div className="relative w-48 h-48 shrink-0">
                <div className="w-full h-full rounded-full shadow-2xl" style={{ background: `conic-gradient(${gradient})` }} />
                <div className="absolute inset-8 rounded-full bg-white dark:bg-slate-800 shadow-inner" />
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-3xl font-black text-slate-900 dark:text-slate-100">{total}</span>
                    <span className="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">Graded</span>
                </div>
            </div>
            <div className="grid grid-cols-2 gap-4 w-full">
                {segments.map(s => (
                    <div key={s.grade} className="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-2xl border border-slate-100/50 dark:border-slate-700/50 flex flex-col">
                        <div className="flex items-center gap-2 mb-1">
                            <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: s.color }} />
                            <span className="text-sm font-black text-slate-900 dark:text-slate-100">{s.grade}</span>
                        </div>
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">{s.count} Students · {s.pct.toFixed(0)}%</p>
                    </div>
                ))}
            </div>
        </div>
    );
}

// ── Skeleton ──────────────────────────────────────────────────────────────────
function Skeleton({ className }) {
    return <div className={`bg-slate-100 dark:bg-slate-800 rounded-3xl animate-pulse ${className}`} />;
}

function LoadingSkeleton() {
    return (
        <div className="space-y-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-3xl p-8 h-40">
                        <Skeleton className="h-3 w-20 mb-6" />
                        <Skeleton className="h-10 w-32" />
                    </div>
                ))}
            </div>
            <div className="grid md:grid-cols-2 gap-8">
                {[...Array(2)].map((_, i) => (
                    <div key={i} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-[2.5rem] p-10 h-80">
                        <Skeleton className="h-6 w-48 mb-10" />
                        <div className="space-y-6">{[...Array(4)].map((_, j) => <Skeleton key={j} className="h-8 w-full" />)}</div>
                    </div>
                ))}
            </div>
        </div>
    );
}

// ── Main Analytics ────────────────────────────────────────────────────────────
export default function Analytics() {
    const { paperId } = useParams();
    const navigate = useNavigate();
    const toast = useToast();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [exporting, setExporting] = useState(false);

    useEffect(() => {
        api.get(`/teacher/papers/${paperId}/analytics`)
            .then(r => setData(r.data))
            .catch(() => toast.error('Failed to load analytics'))
            .finally(() => setLoading(false));
    }, [paperId]);

    const exportCSV = () => {
        if (!data?.student_scores?.length) { toast.warning('No data to export yet.'); return; }
        setExporting(true);
        try {
            const header = ['Student', 'Score', 'Max Marks', 'Percentage', 'Grade'];
            const rows = data.student_scores.map(s => [
                s.name ?? 'Student', s.score, s.max_marks,
                `${((s.score / s.max_marks) * 100).toFixed(1)}%`,
                gradeOf((s.score / s.max_marks) * 100),
            ]);
            const csv = [header, ...rows].map(r => r.join(',')).join('\n');
            const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
            const a = Object.assign(document.createElement('a'), { href: url, download: `${data.paper_title?.replace(/\s+/g, '_') || 'analytics'}_scores.csv` });
            a.click();
            URL.revokeObjectURL(url);
            toast.success('Analytics exported successfully');
        } catch { toast.error('Export failed'); }
        finally { setExporting(false); }
    };

    const avgPct = data?.max_marks > 0 ? ((data.class_average / data.max_marks) * 100).toFixed(1) : '0.0';
    const highPct = data?.max_marks > 0 ? ((data.highest_score / data.max_marks) * 100).toFixed(1) : '0.0';
    const passPct = data?.evaluated > 0 && data?.student_scores
        ? ((data.student_scores.filter(s => (s.score / s.max_marks) * 100 >= 33).length / data.evaluated) * 100).toFixed(0)
        : null;

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
            <Navbar />
            <div className="max-w-7xl mx-auto px-4 py-12 page-enter">

                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-8 mb-12">
                    <div>
                        <button onClick={() => navigate(-1)}
                            className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-indigo-600 transition-colors mb-4">
                            <BackIcon size={20} /> Dashboard
                        </button>
                        <h1 className="text-4xl font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-4">
                            Class Metrics <span className="w-12 h-1 bg-indigo-600 rounded-full" />
                        </h1>
                        <div className="flex flex-wrap items-center gap-4 mt-3 text-sm font-medium text-slate-500">
                            <span className="flex items-center gap-1.5 bg-white dark:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                                {data?.paper_title || 'Loading analysis...'}
                            </span>
                        </div>
                    </div>

                    {data?.evaluated > 0 && (
                        <button onClick={exportCSV} disabled={exporting}
                            className="inline-flex items-center gap-2 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 px-8 py-3.5 rounded-2xl font-black text-sm shadow-xl transition-all active:scale-95 disabled:opacity-50">
                            {exporting ? <BiLoaderAlt className="animate-spin" size={20} /> : <DownloadIcon size={20} />}
                            Export Analytics
                        </button>
                    )}
                </div>

                {loading ? <LoadingSkeleton /> : !data || data.evaluated === 0 ? (
                    <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border-4 border-dashed border-slate-100 dark:border-slate-800 rounded-[3rem] p-24 text-center">
                        <div className="w-24 h-24 bg-slate-50 dark:bg-slate-900 rounded-full flex items-center justify-center text-slate-200 dark:text-slate-700 mx-auto mb-8 shadow-inner">
                            <SadIcon size={56} />
                        </div>
                        <h3 className="text-2xl font-black text-slate-900 dark:text-slate-100 mb-2">Awaiting Data</h3>
                        <p className="text-slate-500 dark:text-slate-400 font-medium max-w-sm mx-auto">Metrics will unlock as soon as your students' submissions are processed and graded by the AI.</p>
                    </div>
                ) : (
                    <>
                        {/* Stat Highlights */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
                            <StatCard
                                icon={<PeopleIcon size={96} />}
                                label="Engagement"
                                value={data.total_submissions}
                                sub={`${data.evaluated} evaluations final`}
                            />
                            <StatCard
                                icon={<TrendingIcon size={96} />}
                                label="Academic Mean"
                                value={`${data.class_average}/${data.max_marks}`}
                                sub={`${avgPct}% Class Performance`}
                                accentClass="text-indigo-600 dark:text-indigo-400"
                            />
                            <StatCard
                                icon={<StarIcon size={96} />}
                                label="Highest Achievement"
                                value={`${data.highest_score}/${data.max_marks}`}
                                sub={`${highPct}% Benchmark`}
                                accentClass="text-emerald-600 dark:text-emerald-400"
                            />
                            <StatCard
                                icon={<CheckIcon size={96} />}
                                label="Pass Threshold"
                                value={passPct !== null ? `${passPct}%` : '—'}
                                sub="Students above 33%"
                                accentClass={passPct >= 75 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}
                            />
                        </div>

                        {/* Top Perspective Row */}
                        <div className="grid lg:grid-cols-5 gap-10 mb-12">
                            <div className="lg:col-span-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-[3rem] p-10 shadow-xl dark:shadow-none">
                                <h2 className="text-xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-3 mb-10">
                                    <ChartIcon className="text-indigo-600" /> Mastery Distribution
                                </h2>
                                <BarChart
                                    data={data.score_distribution}
                                    labelKey="range"
                                    valueKey="count"
                                    maxValue={data.evaluated}
                                    colorFn={() => '#6366f1'}
                                />
                            </div>

                            <div className="lg:col-span-2 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-[3rem] p-10 shadow-xl dark:shadow-none">
                                <h2 className="text-xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-3 mb-10">
                                    <AwardIcon className="text-amber-500" /> Grade Archetypes
                                </h2>
                                {data.grade_distribution ? (
                                    <GradeDonut distribution={data.grade_distribution} />
                                ) : (
                                    <p className="text-slate-400 dark:text-slate-500 text-sm italic py-20 text-center">Incomplete grade profile.</p>
                                )}
                            </div>
                        </div>

                        {/* Question difficulty landscape */}
                        <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-[3rem] p-10 shadow-xl dark:shadow-none mb-12 overflow-hidden relative">
                            <div className="absolute top-0 right-0 p-8 opacity-[0.03] scale-150 rotate-12">
                                <FiTarget size={120} />
                            </div>
                            <h2 className="text-xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-3 mb-10 relative">
                                <ChartIcon className="text-indigo-600" /> Curriculum Calibration
                                <span className="text-[10px] font-black uppercase bg-slate-50 dark:bg-slate-900 px-3 py-1 rounded-lg text-slate-400 ml-auto">Avg. Points per Prompt</span>
                            </h2>
                            <BarChart
                                data={data.per_question.map(q => ({
                                    label: `Q${q.question_number}`,
                                    avg: parseFloat(q.avg_marks),
                                    max: q.max_marks,
                                }))}
                                labelKey="label"
                                valueKey="avg"
                                maxValue={Math.max(...data.per_question.map(q => q.max_marks), 1)}
                                colorFn={(item) => {
                                    const p = item.max > 0 ? (item.avg / item.max) * 100 : 0;
                                    return p >= 70 ? '#10b981' : p >= 40 ? '#f59e0b' : '#ef4444';
                                }}
                            />
                        </div>

                        {/* Detailed Drill-down */}
                        <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-[3rem] shadow-xl dark:shadow-none overflow-hidden">
                            <div className="flex items-center justify-between px-10 py-8 border-b border-slate-100 dark:border-slate-700/50">
                                <h2 className="text-xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-3">
                                    <TableIcon className="text-indigo-600" /> Question-wise Intel
                                </h2>
                                <span className="text-[10px] font-black uppercase text-slate-400 tracking-widest">{data.per_question.length} Items Evaluated</span>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="bg-slate-50/50 dark:bg-slate-900/50">
                                            {['Ref', 'Prompt Content', 'Bench', 'Avg', 'Performance', '100%', '0%', 'Difficulty'].map(h => (
                                                <th key={h} className="px-8 py-5 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest whitespace-nowrap">{h}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
                                        {data.per_question.map(q => {
                                            const pct = q.max_marks > 0 ? +((q.avg_marks / q.max_marks) * 100).toFixed(0) : 0;
                                            const { label, cls } = diffChip(pct);
                                            const barColor = pct >= 70 ? '#10b981' : pct >= 40 ? '#f59e0b' : '#ef4444';
                                            return (
                                                <tr key={q.question_number} className="hover:bg-indigo-50/30 dark:hover:bg-indigo-900/10 transition-colors group">
                                                    <td className="px-8 py-5 font-black text-indigo-600">Q{q.question_number}</td>
                                                    <td className="px-8 py-5">
                                                        <p className="text-sm font-bold text-slate-800 dark:text-slate-200 max-w-xs truncate group-hover:text-indigo-700 dark:group-hover:text-indigo-400 transition-colors">{q.question_text}</p>
                                                    </td>
                                                    <td className="px-8 py-5 text-[10px] font-black text-slate-300">{q.max_marks}</td>
                                                    <td className="px-8 py-5 font-black text-slate-900 dark:text-slate-100">{q.avg_marks}</td>
                                                    <td className="px-8 py-5">
                                                        <div className="flex items-center gap-3">
                                                            <div className="w-24 bg-slate-100 dark:bg-slate-900 rounded-full h-2 border border-white dark:border-slate-800 shadow-inner">
                                                                <div className="h-full rounded-full transition-all duration-1000 group-hover:scale-y-110" style={{ width: `${pct}%`, backgroundColor: barColor }} />
                                                            </div>
                                                            <span className="text-[10px] font-black text-slate-400">{pct}%</span>
                                                        </div>
                                                    </td>
                                                    <td className="px-8 py-5">
                                                        <span className="flex items-center gap-1.5 text-xs font-black text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 px-2 py-1 rounded-lg">
                                                            <CheckIcon size={14} /> {q.full_marks_count ?? '0'}
                                                        </span>
                                                    </td>
                                                    <td className="px-8 py-5">
                                                        <span className="flex items-center gap-1.5 text-xs font-black text-red-500 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded-lg">
                                                            <FiAlertTriangle size={14} /> {q.zero_marks_count ?? '0'}
                                                        </span>
                                                    </td>
                                                    <td className="px-8 py-5">
                                                        <span className={`text-[10px] font-black uppercase tracking-tighter px-3 py-1 rounded-xl border ${cls}`}>{label}</span>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
