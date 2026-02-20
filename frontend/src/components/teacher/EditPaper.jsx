import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getPaper, updatePaper } from '../../services/api';
import Navbar from '../common/Navbar';
import { useToast } from '../../context/ToastContext';
import {
  MdAdd, MdDelete, MdEditNote, MdCheckCircle,
  MdToggleOn, MdToggleOff, MdAccessTime, MdInfoOutline,
  MdFormatListNumbered, MdList, MdRadioButtonChecked, MdClose,
  MdOutlineDescription, MdSchool, MdArrowForward
} from 'react-icons/md';
import { BiLoaderAlt } from 'react-icons/bi';

export default function EditPaper() {
  const navigate = useNavigate();
  const { paperId } = useParams();
  const toast = useToast();

  const [formData, setFormData] = useState({
    title: '',
    subject: 'science',
    class_level: '12',
    total_marks: 0,
    duration_minutes: 60,
    instructions: '',
    is_exam_mode: false,
    exam_start_time: '',
    exam_end_time: '',
  });
  const [questions, setQuestions] = useState([
    { question_number: 1, question_text: '', question_type: 'short', marks: 5 },
  ]);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    loadPaper();
  }, [paperId]);

  const loadPaper = async () => {
    setFetching(true);
    try {
      const res = await getPaper(paperId);
      const paper = res.data;
      setFormData({
        title: paper.title,
        subject: paper.subject,
        class_level: paper.class_level,
        total_marks: paper.total_marks,
        duration_minutes: paper.duration_minutes,
        instructions: paper.instructions || '',
        is_exam_mode: paper.is_exam_mode || false,
        exam_start_time: paper.exam_start_time ? new Date(paper.exam_start_time).toISOString().slice(0, 16) : '',
        exam_end_time: paper.exam_end_time ? new Date(paper.exam_end_time).toISOString().slice(0, 16) : '',
      });
      if (paper.questions && paper.questions.length > 0) {
        setQuestions(paper.questions);
      }
    } catch (error) {
      toast.error('Failed to load paper details.');
      navigate('/teacher');
    } finally {
      setFetching(false);
    }
  };

  const addQuestion = () => {
    setQuestions([
      ...questions,
      {
        question_number: questions.length + 1,
        question_text: '',
        question_type: 'short',
        marks: 5,
      },
    ]);
  };

  const updateQuestion = (index, field, value) => {
    const updated = [...questions];
    updated[index][field] = value;

    if (field === 'question_type' && value === 'mcq') {
      updated[index].options = { A: '', B: '', C: '', D: '' };
      updated[index].correct_answer = 'A';
      updated[index].marks = 1;
    } else if (field === 'question_type' && updated[index].options) {
      delete updated[index].options;
      delete updated[index].correct_answer;
    }

    if (field === 'marks') {
      updated[index][field] = parseInt(value) || 0;
    }

    setQuestions(updated);
  };

  const updateMCQOption = (index, option, value) => {
    const updated = [...questions];
    if (!updated[index].options) {
      updated[index].options = { A: '', B: '', C: '', D: '' };
    }
    updated[index].options[option] = value;
    setQuestions(updated);
  };

  const removeQuestion = (index) => {
    setQuestions(questions.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const totalMarks = questions.reduce((sum, q) => sum + (parseInt(q.marks) || 0), 0);
    const payload = {
      ...formData,
      total_marks: totalMarks,
      questions,
      exam_start_time: formData.is_exam_mode && formData.exam_start_time ? new Date(formData.exam_start_time).toISOString() : null,
      exam_end_time: formData.is_exam_mode && formData.exam_end_time ? new Date(formData.exam_end_time).toISOString() : null,
    };
    try {
      await updatePaper(paperId, payload);
      toast.success('Question paper updated successfully!');
      navigate('/teacher');
    } catch (error) {
      toast.error('Failed to update paper. Please check all fields.');
    } finally {
      setLoading(false);
    }
  };

  const totalMarks = questions.reduce((sum, q) => sum + (parseInt(q.marks) || 0), 0);

  if (fetching) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <BiLoaderAlt className="animate-spin text-indigo-500" size={48} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 py-12 page-enter">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10">
          <div>
            <h1 className="text-4xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">Edit Paper</h1>
            <p className="text-slate-500 dark:text-slate-400 font-medium mt-2">Modify the assessment details and questions below.</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Header Settings Card */}
          <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-3xl p-8 shadow-xl dark:shadow-none space-y-8">
            <div className="grid md:grid-cols-3 gap-6">
              <div className="md:col-span-2">
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2.5 ml-1">Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-5 py-3.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2.5 ml-1">Subject</label>
                <select
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                  className="w-full px-5 py-3.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-bold cursor-pointer"
                >
                  <option value="science">Science</option>
                  <option value="physics">Physics</option>
                  <option value="chemistry">Chemistry</option>
                  <option value="mathematics">Mathematics</option>
                  <option value="english">English</option>
                </select>
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2.5 ml-1">Class Level</label>
                <select
                  value={formData.class_level}
                  onChange={(e) => setFormData({ ...formData, class_level: e.target.value })}
                  className="w-full px-5 py-3.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-bold cursor-pointer"
                >
                  {[8, 9, 10, 11, 12].map(g => <option key={g} value={String(g)}>Grade {g}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2.5 ml-1 flex items-center gap-2">
                  <MdAccessTime size={18} className="text-indigo-500" /> Duration <span className="text-xs text-slate-400 font-normal">(mins)</span>
                </label>
                <input
                  type="number"
                  value={formData.duration_minutes}
                  onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) || 60 })}
                  className="w-full px-5 py-3.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-bold"
                />
              </div>
              <div className="flex items-end px-1 pb-1">
                <div className="flex items-center gap-3 bg-slate-100 dark:bg-slate-900/50 p-2 rounded-2xl flex-1 justify-center border border-slate-200 dark:border-slate-700">
                  <span className="text-xs font-black uppercase text-indigo-500 tracking-wider">Total Marks</span>
                  <span className="text-2xl font-black text-slate-900 dark:text-slate-100">{totalMarks}</span>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2.5 ml-1 flex items-center gap-2">
                <MdInfoOutline className="text-indigo-500" /> Instructions
              </label>
              <textarea
                value={formData.instructions}
                onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
                className="w-full px-5 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium"
                rows="2"
              />
            </div>

            {/* Exam Mode Toggle */}
            <div className={`p-6 rounded-3xl border-2 transition-all duration-300 ${formData.is_exam_mode ? 'border-indigo-500 bg-indigo-50/20 dark:bg-indigo-900/10' : 'border-slate-100 dark:border-slate-700'}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-2xl ${formData.is_exam_mode ? 'bg-indigo-600 text-white' : 'bg-slate-100 dark:bg-slate-900 text-slate-400'}`}>
                    <MdAccessTime size={24} />
                  </div>
                  <div>
                    <p className="font-bold text-slate-900 dark:text-slate-100">Scheduled Exam Mode</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Auto-lock paper submission outside specified time window</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setFormData(f => ({ ...f, is_exam_mode: !f.is_exam_mode }))}
                  className="text-indigo-600 focus:outline-none"
                >
                  {formData.is_exam_mode ? <MdToggleOn size={52} /> : <MdToggleOff className="text-slate-300 dark:text-slate-600" size={52} />}
                </button>
              </div>
              {formData.is_exam_mode && (
                <div className="grid sm:grid-cols-2 gap-6 mt-6 animate-in fade-in zoom-in-95 duration-200">
                  <div>
                    <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase mb-2 ml-1">Start Time (IST)</label>
                    <input
                      type="datetime-local"
                      value={formData.exam_start_time}
                      onChange={e => setFormData(f => ({ ...f, exam_start_time: e.target.value }))}
                      className="w-full px-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl text-sm font-bold focus:ring-2 focus:ring-indigo-500/20 outline-none dark:text-slate-100 transition-all"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase mb-2 ml-1">End Time (IST)</label>
                    <input
                      type="datetime-local"
                      value={formData.exam_end_time}
                      onChange={e => setFormData(f => ({ ...f, exam_end_time: e.target.value }))}
                      className="w-full px-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl text-sm font-bold focus:ring-2 focus:ring-indigo-500/20 outline-none dark:text-slate-100 transition-all"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Questions Section */}
          <div className="space-y-6">
            <div className="flex justify-between items-center px-4">
              <h3 className="text-2xl font-black text-slate-900 dark:text-slate-100">Questions</h3>
              <button
                type="button"
                onClick={addQuestion}
                className="inline-flex items-center gap-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-6 py-2.5 rounded-2xl font-black text-xs text-indigo-600 dark:text-indigo-400 hover:bg-slate-50 dark:hover:bg-slate-700 shadow-sm transition-all active:scale-95"
              >
                <MdAdd size={18} /> Add New Question
              </button>
            </div>

            <div className="space-y-6">
              {questions.map((q, index) => (
                <div key={index} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-[2.5rem] p-8 shadow-lg dark:shadow-none hover:shadow-2xl dark:hover:shadow-indigo-500/5 transition-all duration-300 group">
                  <div className="flex justify-between items-center mb-6">
                    <div className="flex items-center gap-3">
                      <span className="w-10 h-10 bg-indigo-600 text-white rounded-2xl flex items-center justify-center font-black text-lg shadow-lg shadow-indigo-200 dark:shadow-none">
                        {index + 1}
                      </span>
                      <span className="text-sm font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">Question</span>
                    </div>
                    {questions.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeQuestion(index)}
                        className="p-2.5 text-slate-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-2xl transition-all"
                      >
                        <MdDelete size={24} />
                      </button>
                    )}
                  </div>

                  <div className="space-y-6">
                    <textarea
                      value={q.question_text}
                      onChange={(e) => updateQuestion(index, 'question_text', e.target.value)}
                      className="w-full px-6 py-5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-3xl text-lg font-medium focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none dark:text-slate-100"
                      rows="3"
                      required
                    />

                    <div className="grid sm:grid-cols-2 gap-6">
                      <div className="relative">
                        <label className="block text-xs font-black text-slate-400 uppercase mb-2 ml-1">Response Type</label>
                        <select
                          value={q.question_type}
                          onChange={(e) => updateQuestion(index, 'question_type', e.target.value)}
                          className="w-full px-6 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl font-bold focus:ring-2 focus:ring-indigo-500/20 outline-none dark:text-slate-100 appearance-none cursor-pointer"
                        >
                          <option value="short">Short Answer</option>
                          <option value="long">Detailed Explanation</option>
                          <option value="mcq">Multiple Choice (MCQ)</option>
                        </select>
                        <div className="absolute right-6 bottom-4 text-slate-400 pointer-events-none">
                          {q.question_type === 'short' ? <MdList size={20} /> : q.question_type === 'long' ? <MdFormatListNumbered size={20} /> : <MdRadioButtonChecked size={20} />}
                        </div>
                      </div>
                      <div>
                        <label className="block text-xs font-black text-slate-400 uppercase mb-2 ml-1">Maximum Marks</label>
                        <input
                          type="number"
                          value={q.marks}
                          onChange={(e) => updateQuestion(index, 'marks', e.target.value)}
                          className="w-full px-6 py-4 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl font-black focus:ring-2 focus:ring-indigo-500/20 outline-none dark:text-slate-100"
                          placeholder="Marks"
                          required
                        />
                      </div>
                    </div>

                    {q.question_type === 'mcq' && (
                      <div className="space-y-4 pt-4 border-t border-slate-100 dark:border-slate-700 animate-in fade-in slide-in-from-top-2 duration-300">
                        <label className="text-sm font-black text-slate-900 dark:text-slate-100 mb-2 block ml-1 flex items-center gap-2">
                          <MdRadioButtonChecked className="text-indigo-500" /> Options Setup
                        </label>
                        <div className="grid sm:grid-cols-2 gap-4">
                          {['A', 'B', 'C', 'D'].map(opt => (
                            <div key={opt} className="relative group/opt">
                              <span className={`absolute left-4 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg flex items-center justify-center font-black text-sm transition-colors ${q.correct_answer === opt ? 'bg-emerald-600 text-white' : 'bg-slate-200 dark:bg-slate-700 text-slate-500'}`}>
                                {opt}
                              </span>
                              <input
                                type="text"
                                value={q.options?.[opt] || ''}
                                onChange={(e) => updateMCQOption(index, opt, e.target.value)}
                                className={`w-full pl-16 pr-4 py-4 bg-slate-50 dark:bg-slate-900 border rounded-2xl font-medium focus:ring-2 focus:ring-indigo-500/20 outline-none dark:text-slate-100 transition-all ${q.correct_answer === opt ? 'border-emerald-500 ring-2 ring-emerald-500/10' : 'border-slate-200 dark:border-slate-700'}`}
                                placeholder={`Option ${opt} text`}
                                required
                              />
                              <button
                                type="button"
                                onClick={() => updateQuestion(index, 'correct_answer', opt)}
                                className={`absolute right-4 top-1/2 -translate-y-1/2 p-2 rounded-xl transition-all ${q.correct_answer === opt ? 'text-emerald-500' : 'text-slate-300 group-hover/opt:text-slate-500'}`}
                              >
                                <MdCheckCircle size={24} />
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-4 pt-10">
              <button
                type="submit"
                disabled={loading}
                className="flex-[2] bg-indigo-600 hover:bg-indigo-700 text-white py-5 rounded-[2rem] font-black text-lg shadow-xl shadow-indigo-100 dark:shadow-none transition-all flex items-center justify-center gap-3 transform active:scale-95 disabled:opacity-70"
              >
                {loading ? <BiLoaderAlt className="animate-spin" size={28} /> : (
                  <>
                    <span>Update Question Paper</span>
                    <MdCheckCircle size={24} />
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={() => navigate('/teacher')}
                className="flex-1 bg-white dark:bg-slate-800 border-2 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 py-5 rounded-[2.5rem] font-black hover:bg-slate-50 dark:hover:bg-slate-700 transition-all text-lg"
              >
                Discard
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
