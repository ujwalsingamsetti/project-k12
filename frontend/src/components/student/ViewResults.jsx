import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getSubmissionDetails } from '../../services/api';
import Navbar from '../common/Navbar';
import { useToast } from '../../context/ToastContext';
import {
  MdChevronLeft, MdEvent, MdAccessTime, MdCheckCircle, MdPendingActions,
  MdErrorOutline, MdInfoOutline, MdDownload, MdFormatListNumbered,
  MdBarChart, MdKeyboardArrowRight, MdStars, MdCheck, MdClose, MdLightbulbOutline
} from 'react-icons/md';
import { BiLoaderAlt, BiTrophy } from 'react-icons/bi';

const API_BASE = 'http://localhost:8000';

function toIST(dateStr) {
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return { date: '—', time: '—' };
  const opts = { timeZone: 'Asia/Kolkata' };
  const date = d.toLocaleDateString('en-IN', { ...opts, day: '2-digit', month: '2-digit', year: 'numeric' });
  const time = d.toLocaleTimeString('en-IN', { ...opts, hour: '2-digit', minute: '2-digit', hour12: true });
  return { date, time };
}

function AnswerSheetPage({ submissionId, pageIndex, totalPages }) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const [blobUrl, setBlobUrl] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    const apiBase = typeof API_BASE !== 'undefined' ? API_BASE : '';
    const url = `${apiBase}/api/student/submissions/${submissionId}/image?page=${pageIndex + 1}`;
    let objectUrl = null;

    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then(res => {
        if (!res.ok) throw new Error('Image load failed');
        return res.blob();
      })
      .then(blob => {
        objectUrl = URL.createObjectURL(blob);
        setBlobUrl(objectUrl);
        setLoaded(true);
      })
      .catch(() => setError(true));

    return () => { if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [submissionId, pageIndex]);

  return (
    <div className="relative border border-slate-200 dark:border-slate-700 rounded-3xl overflow-hidden bg-white dark:bg-slate-800 min-h-64 shadow-sm group">
      <div className="absolute top-4 left-4 z-10 bg-black/70 backdrop-blur-md text-white text-[10px] font-black px-3 py-1.5 rounded-xl uppercase tracking-widest">
        Page {pageIndex + 1} / {totalPages}
      </div>

      {!loaded && !error && (
        <div className="flex flex-col items-center justify-center h-64 text-slate-400 gap-3">
          <BiLoaderAlt size={32} className="animate-spin text-indigo-500" />
          <p className="text-xs font-bold uppercase tracking-wider">Loading Page...</p>
        </div>
      )}

      {error && (
        <div className="flex flex-col items-center justify-center h-64 text-slate-400 gap-2">
          <MdErrorOutline size={32} />
          <p className="text-xs font-bold uppercase tracking-wider">Image Not Found</p>
        </div>
      )}

      {blobUrl && (
        <div className="overflow-hidden">
          <img
            src={blobUrl}
            alt={`Answer sheet page ${pageIndex + 1}`}
            className="w-full h-auto block group-hover:scale-[1.02] transition-transform duration-700"
            onLoad={() => setLoaded(true)}
          />
        </div>
      )}
    </div>
  );
}

export default function ViewResults() {
  const { submissionId } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [submission, setSubmission] = useState(null);
  const [loading, setLoading] = useState(true);

  const isProcessing = (status) => status === 'pending' || status === 'evaluating';

  useEffect(() => {
    let pollInterval = null;

    const fetchSubmission = async (isInitial = false) => {
      try {
        const res = await getSubmissionDetails(submissionId);
        const data = res.data;
        setSubmission(data);

        // If evaluation is done or failed, stop polling
        if (!isProcessing(data.status)) {
          if (pollInterval) clearInterval(pollInterval);
        }
      } catch (error) {
        if (pollInterval) clearInterval(pollInterval);
      } finally {
        setLoading(false);
      }
    };

    fetchSubmission(true);
    pollInterval = setInterval(() => fetchSubmission(), 5000);

    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [submissionId]);

  const parseFeedback = (feedbackStr) => {
    try { return JSON.parse(feedbackStr); } catch { return null; }
  };

  const handleDownload = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE}/api/v2/submissions/${submissionId}/report`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
    } catch {
      toast.error('Could not generate PDF report');
    }
  };

  if (loading) return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      <Navbar />
      <div className="flex flex-col items-center justify-center h-[60vh] text-slate-400 dark:text-slate-500 gap-4">
        <BiLoaderAlt size={48} className="animate-spin text-indigo-500" />
        <p className="font-medium">Opening evaluation...</p>
      </div>
    </div>
  );

  if (!submission) return null;

  const { date: submittedDate, time: submittedTime } = toIST(submission.submitted_at);
  const pageCount = (submission.uploaded_files && Array.isArray(submission.uploaded_files) && submission.uploaded_files.length > 0)
    ? submission.uploaded_files.length
    : (submission.page_count || (submission.image_path ? 1 : 0));
  const scorePercent = submission.max_marks > 0
    ? ((submission.total_marks / submission.max_marks) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 py-8 page-enter">
        <button
          onClick={() => navigate('/student')}
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors mb-6"
        >
          <MdChevronLeft size={20} /> Back to Dashboard
        </button>

        {/* Header Section */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8 mb-10">
          <div>
            <h1 className="text-4xl font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-3">
              Evaluation Report <MdStars className="text-amber-500" />
            </h1>
            <div className="flex flex-wrap items-center gap-4 mt-3 text-sm font-medium text-slate-500">
              <span className="flex items-center gap-1.5 bg-white dark:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <MdEvent size={16} /> {submittedDate}
              </span>
              <span className="flex items-center gap-1.5 bg-white dark:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <MdAccessTime size={16} /> {submittedTime} IST
              </span>
            </div>
          </div>

          {submission.status === 'evaluated' && (
            <div className="flex gap-4">
              <button
                onClick={handleDownload}
                className="inline-flex items-center gap-2 bg-slate-900 dark:bg-slate-700 text-white px-6 py-3.5 rounded-2xl font-bold text-sm shadow-xl transition-all transform active:scale-95"
              >
                <MdDownload size={20} /> Download Report
              </button>
              {submission.paper_id && (
                <button
                  onClick={() => navigate(`/leaderboard/${submission.paper_id}`)}
                  className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3.5 rounded-2xl font-bold text-sm shadow-xl shadow-indigo-100 dark:shadow-none transition-all transform active:scale-95"
                >
                  <BiTrophy size={20} /> Leaderboard
                </button>
              )}
            </div>
          )}
        </div>

        {/* Status Banners */}
        {isProcessing(submission.status) && (
          <div className="flex items-start gap-4 bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-900/50 rounded-3xl px-6 py-6 mb-8 animate-pulse text-amber-800 dark:text-amber-400">
            <BiLoaderAlt className="animate-spin mt-1 shrink-0" size={24} />
            <div>
              <p className="font-black text-lg">Evaluation in Progress...</p>
              <p className="text-sm font-medium opacity-90 leading-relaxed">
                {submission.status === 'evaluating'
                  ? 'Our AI is currently grading each of your responses. This usually takes between 30 to 90 seconds depending on the length of your sheet.'
                  : 'Your submission is in the queue for OCR processing. We are converting your handwriting into text.'}
                {' '}This page will automatically refresh with your results.
              </p>
            </div>
          </div>
        )}

        {submission.status === 'failed' && (
          <div className="flex items-start gap-4 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-900/50 rounded-3xl px-6 py-6 mb-8 text-red-800 dark:text-red-400">
            <MdErrorOutline className="mt-1 shrink-0" size={28} />
            <div>
              <p className="font-black text-lg">Evaluation Failed</p>
              <p className="text-sm font-medium opacity-90 leading-relaxed">
                We encountered an error while processing your answer sheet. Please ensure the images are clear and readable, then try re-uploading. Contact your teacher if the issue persists.
              </p>
            </div>
          </div>
        )}

        <div className="grid lg:grid-cols-3 gap-8 mb-10">
          {/* Score Hub */}
          <div className="lg:col-span-1">
            <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-[2.5rem] p-8 shadow-xl dark:shadow-none h-full flex flex-col items-center justify-center text-center">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em] mb-4">Final Assessment</p>
              <div className="relative mb-6">
                <div className="w-32 h-32 rounded-full border-[10px] border-slate-50 dark:border-slate-900 flex items-center justify-center">
                  <p className="text-4xl font-black text-slate-900 dark:text-slate-100">{submission.total_marks}</p>
                </div>
                <div className="absolute -bottom-2 -right-2 bg-indigo-600 text-white w-12 h-12 rounded-2xl flex items-center justify-center shadow-lg transform rotate-12">
                  <span className="font-black text-xs">/{submission.max_marks}</span>
                </div>
              </div>
              <div className="space-y-1">
                <p className={`text-2xl font-black ${parseFloat(scorePercent) >= 75 ? 'text-emerald-500' : parseFloat(scorePercent) >= 40 ? 'text-amber-500' : 'text-red-500'}`}>
                  {scorePercent}%
                </p>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Aggregate Score</p>
              </div>

              <div className="w-full mt-10 pt-10 border-t border-slate-100 dark:border-slate-700">
                <div className="flex items-center justify-between px-2">
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Status</span>
                  <span className={`inline-flex items-center gap-1.5 text-xs font-black uppercase ${submission.status === 'evaluated' ? 'text-emerald-600' : submission.status === 'failed' ? 'text-red-600' : 'text-amber-600'
                    }`}>
                    {submission.status === 'evaluated' ? <MdCheckCircle /> : <MdPendingActions />} {submission.status}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Answer Sheet Preview */}
          <div className="lg:col-span-2">
            <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-[2.5rem] p-8 shadow-xl dark:shadow-none h-full">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-3">
                  <MdBarChart className="text-indigo-500" /> Answer Sheets
                </h2>
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">{pageCount} Pages Loaded</span>
              </div>
              <div className={`grid gap-6 ${pageCount > 1 ? 'md:grid-cols-2' : ''} max-h-[400px] overflow-y-auto pr-2 custom-scrollbar`}>
                {Array.from({ length: pageCount }, (_, i) => (
                  <AnswerSheetPage key={i} submissionId={submissionId} pageIndex={i} totalPages={pageCount} />
                ))}
                {pageCount === 0 && (
                  <div className="py-20 flex flex-col items-center justify-center opacity-30 italic font-medium col-span-2">
                    <MdInfoOutline size={48} />
                    <p className="mt-2 text-sm">No images uploaded for this submission.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Question-wise Breakdown */}
        {submission.evaluations && submission.evaluations.length > 0 && (
          <div className="space-y-8">
            <div className="flex items-center gap-4 px-4">
              <h2 className="text-2xl font-black text-slate-900 dark:text-slate-100">Detailed Feedback</h2>
              <div className="h-0.5 flex-1 bg-slate-200 dark:bg-slate-800 rounded-full" />
            </div>

            {submission.evaluations.map((ev) => {
              const feedback = parseFeedback(ev.feedback);
              return (
                <div key={ev.question_id} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-[2.5rem] p-10 shadow-lg dark:shadow-none group overflow-hidden relative transition-all hover:shadow-2xl dark:hover:shadow-indigo-500/5">
                  {/* Score pill in background */}
                  <div className={`absolute top-0 right-0 p-8 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity uppercase font-black text-9xl pointer-events-none ${ev.marks_obtained === ev.max_marks ? 'text-emerald-500' : 'text-slate-500'
                    }`}>
                    {Math.round((ev.marks_obtained / ev.max_marks) * 100)}%
                  </div>

                  <div className="flex flex-col md:flex-row justify-between items-start gap-6 mb-10 relative">
                    <div className="flex items-center gap-4">
                      <div className="w-14 h-14 bg-indigo-600 text-white rounded-2xl flex items-center justify-center text-xl font-black shadow-lg shadow-indigo-100 dark:shadow-none">
                        {ev.question_number}
                      </div>
                      <div>
                        <p className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">Question Analysis</p>
                        <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">Performance on Question {ev.question_number}</h3>
                      </div>
                    </div>
                    <div className={`flex items-baseline gap-1 px-6 py-3 rounded-2xl border-2 ${ev.marks_obtained === ev.max_marks ? 'bg-emerald-50 dark:bg-emerald-900/10 border-emerald-200 dark:border-emerald-800 text-emerald-600' :
                      ev.marks_obtained === 0 ? 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800 text-red-600' : 'bg-amber-50 dark:bg-amber-900/10 border-amber-200 dark:border-amber-800 text-amber-600'
                      }`}>
                      <span className="text-3xl font-black">{ev.marks_obtained}</span>
                      <span className="text-sm font-bold opacity-60">/{ev.max_marks} Marks</span>
                    </div>
                  </div>

                  <div className="space-y-8 relative">
                    {/* Student Answer */}
                    <div>
                      <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3 block ml-1 flex items-center gap-2">
                        <MdKeyboardArrowRight size={16} /> Decoded Student Response
                      </label>
                      <div className="text-base text-slate-800 dark:text-slate-100 font-medium bg-slate-50 dark:bg-slate-900 p-6 rounded-3xl border border-slate-100 dark:border-slate-800 italic leading-relaxed">
                        {ev.student_answer || 'No answer decoded'}
                      </div>
                    </div>

                    {/* Feedback content */}
                    {feedback ? (
                      <div className="grid md:grid-cols-2 gap-8">
                        {/* Points & Improvements */}
                        <div className="space-y-6">
                          {feedback.correct_points?.length > 0 && (
                            <div className="bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-700/60 rounded-3xl p-6">
                              <p className="text-xs font-black text-emerald-600 dark:text-emerald-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                <MdCheck size={18} /> Points of Accuracy
                              </p>
                              <ul className="space-y-3">
                                {feedback.correct_points.map((p, i) => (
                                  <li key={i} className="text-sm font-semibold text-slate-700 dark:text-emerald-200 flex items-start gap-3">
                                    <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full mt-1.5 shrink-0" />
                                    {p}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {feedback.overall_feedback && (
                            <div className="bg-blue-50 dark:bg-slate-800 border border-blue-200 dark:border-slate-600 rounded-3xl p-6">
                              <p className="text-xs font-black text-blue-600 dark:text-blue-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                                <MdInfoOutline size={18} /> Overall Feedback
                              </p>
                              <p className="text-sm font-medium text-slate-700 dark:text-slate-200 leading-relaxed italic">{feedback.overall_feedback}</p>
                            </div>
                          )}

                          {feedback.improvement_guidance?.length > 0 && (
                            <div className="bg-purple-50 dark:bg-purple-950/60 border border-purple-200 dark:border-purple-700/60 rounded-3xl p-6">
                              <p className="text-xs font-black text-purple-600 dark:text-purple-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                <MdLightbulbOutline size={18} /> Growth Guidance
                              </p>
                              <div className="space-y-4">
                                {feedback.improvement_guidance.map((g, i) => (
                                  <div key={i} className="border-l-2 border-purple-300 dark:border-purple-600 pl-4 py-1">
                                    <p className="text-sm font-bold text-slate-800 dark:text-purple-100 mb-1">{g.suggestion}</p>
                                    {g.resource && <p className="text-xs text-purple-500 dark:text-purple-400 font-bold underline cursor-pointer">Ref: {g.resource}</p>}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Errors & Concepts */}
                        <div className="space-y-6">
                          {feedback.errors?.length > 0 && (
                            <div className="bg-red-50 dark:bg-red-950/60 border border-red-200 dark:border-red-700/60 rounded-3xl p-6">
                              <p className="text-xs font-black text-red-600 dark:text-red-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                <MdClose size={18} /> Errors Identified
                              </p>
                              <div className="space-y-4">
                                {feedback.errors.map((err, i) => (
                                  <div key={i} className="p-4 bg-red-100 dark:bg-slate-800 rounded-2xl border border-red-200 dark:border-red-800/50">
                                    <p className="text-sm font-black text-red-900 dark:text-red-300 mb-1">{err.what}</p>
                                    <p className="text-xs font-medium text-red-700 dark:text-red-400 leading-relaxed"><span className="font-black italic mr-1">Root Cause:</span> {err.why}</p>
                                    {err.impact && <p className="text-xs font-medium text-red-700 dark:text-red-400 mt-1 opacity-70">Impact: {err.impact}</p>}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {feedback.missing_concepts?.length > 0 && (
                            <div className="bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-700/60 rounded-3xl p-6">
                              <p className="text-xs font-black text-amber-600 dark:text-amber-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                <MdBarChart size={18} /> Concept Gaps
                              </p>
                              <div className="flex flex-wrap gap-2">
                                {feedback.missing_concepts.map((c, i) => (
                                  <span key={i} className="bg-amber-100 dark:bg-slate-800 text-[10px] font-black text-amber-700 dark:text-amber-400 px-3 py-1.5 rounded-lg border border-amber-300 dark:border-amber-700">
                                    {c}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {feedback.correct_answer_should_include?.length > 0 && (
                            <div className="bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-700/60 rounded-3xl p-6">
                              <p className="text-xs font-black text-indigo-600 dark:text-indigo-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                <MdFormatListNumbered size={18} /> Correct Answer Should Include
                              </p>
                              <ul className="space-y-2">
                                {feedback.correct_answer_should_include.map((p, i) => (
                                  <li key={i} className="text-xs font-semibold text-slate-700 dark:text-indigo-200 flex items-start gap-2">
                                    <span className="text-indigo-500 dark:text-indigo-400 mt-1">•</span>
                                    {p}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      <div className="bg-slate-50 dark:bg-slate-900 p-8 rounded-3xl border border-slate-200 dark:border-slate-800 text-center flex flex-col items-center gap-4">
                        <BiLoaderAlt size={32} className="animate-spin text-slate-300" />
                        <p className="text-sm font-bold text-slate-400 uppercase tracking-[0.2em]">Detailed Analytics Pending</p>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
