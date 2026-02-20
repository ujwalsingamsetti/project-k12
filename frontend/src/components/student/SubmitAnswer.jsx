import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getPaperDetails, submitAnswer } from '../../services/api';
import Navbar from '../common/Navbar';
import { useToast } from '../../context/ToastContext';
import {
  MdChevronLeft, MdOutlineDescription, MdAccessTime, MdInfoOutline,
  MdCloudUpload, MdImage, MdDelete, MdArrowUpward, MdArrowDownward,
  MdCheckCircle, MdOutlineSchool, MdPictureAsPdf
} from 'react-icons/md';
import { BiLoaderAlt } from 'react-icons/bi';

export default function SubmitAnswer() {
  const { paperId } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [paper, setPaper] = useState(null);
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPaper();
  }, [paperId]);

  const loadPaper = async () => {
    try {
      const res = await getPaperDetails(paperId);
      setPaper(res.data);
    } catch (error) {
      toast.error('Failed to load paper details');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length > 0) {
      const newFiles = [...files, ...selectedFiles];
      setFiles(newFiles);

      const newPreviews = [...previews];
      let loadedCount = 0;

      selectedFiles.forEach((file) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          newPreviews.push(reader.result);
          loadedCount++;
          if (loadedCount === selectedFiles.length) {
            setPreviews(newPreviews);
            toast.success(`Added ${selectedFiles.length} page(s)`);
          }
        };
        reader.readAsDataURL(file);
      });
    }
    e.target.value = '';
  };

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
    setPreviews(previews.filter((_, i) => i !== index));
  };

  const moveUp = (index) => {
    if (index === 0) return;
    const newFiles = [...files];
    const newPreviews = [...previews];
    [newFiles[index], newFiles[index - 1]] = [newFiles[index - 1], newFiles[index]];
    [newPreviews[index], newPreviews[index - 1]] = [newPreviews[index - 1], newPreviews[index]];
    setFiles(newFiles);
    setPreviews(newPreviews);
  };

  const moveDown = (index) => {
    if (index === files.length - 1) return;
    const newFiles = [...files];
    const newPreviews = [...previews];
    [newFiles[index], newFiles[index + 1]] = [newFiles[index + 1], newFiles[index]];
    [newPreviews[index], newPreviews[index + 1]] = [newPreviews[index + 1], newPreviews[index]];
    setFiles(newFiles);
    setPreviews(newPreviews);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (files.length === 0) {
      toast.error('Please upload at least one page of your answer sheet');
      return;
    }

    setSubmitting(true);
    try {
      await submitAnswer(paperId, files);
      toast.success('Your answer sheet has been submitted for evaluation!');
      navigate('/student');
    } catch (error) {
      toast.error('Submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
        <Navbar />
        <div className="flex flex-col items-center justify-center h-[60vh] text-slate-400 dark:text-slate-500 gap-4">
          <BiLoaderAlt size={48} className="animate-spin text-indigo-500" />
          <p className="font-medium">Loading paper...</p>
        </div>
      </div>
    );
  }

  if (!paper) return null;

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

        <div className="flex flex-col md:flex-row justify-between md:items-end gap-6 mb-10">
          <div>
            <h1 className="text-4xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">{paper.title}</h1>
            <div className="flex flex-wrap items-center gap-3 mt-3">
              <span className="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-lg border border-slate-200 dark:border-slate-700">
                {paper.subject}
              </span>
              <span className="bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-lg border border-indigo-100 dark:border-indigo-800">
                {paper.total_marks} Marks
              </span>
              <span className="flex items-center gap-1.5 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-lg border border-blue-100 dark:border-blue-800">
                <MdAccessTime size={14} /> {paper.duration_minutes} Mins
              </span>
            </div>
          </div>

          {paper.pdf_path && (
            <a
              href={`http://localhost:8000/api/student/papers/${paperId}/pdf`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3.5 rounded-2xl font-bold text-sm shadow-xl shadow-indigo-100 dark:shadow-none transition-all transform active:scale-95"
            >
              <MdPictureAsPdf size={20} /> View Question Paper
            </a>
          )}
        </div>

        <div className="grid lg:grid-cols-5 gap-8">
          {/* Questions Panel */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-3xl p-8 shadow-xl dark:shadow-none h-fit sticky top-24">
              <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-6 flex items-center gap-2">
                <MdOutlineDescription className="text-indigo-500" /> Exam Questions
              </h2>
              <div className="space-y-6 max-h-[60vh] overflow-y-auto pr-2 custom-scrollbar">
                {paper.questions.map((q) => (
                  <div key={q.id} className="group border-l-4 border-slate-100 dark:border-slate-700 hover:border-indigo-500 pl-4 py-1 transition-all">
                    <p className="text-sm font-bold text-slate-800 dark:text-slate-100 leading-relaxed mb-2">
                      Q{q.question_number}. {q.question_text}
                    </p>
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] font-black text-slate-400 uppercase tracking-tighter">
                        {q.marks} Marks
                      </span>
                      <span className="text-[10px] font-black text-indigo-400 dark:text-indigo-500 uppercase tracking-tighter">
                        {q.question_type}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Submission Form */}
          <div className="lg:col-span-3">
            <form onSubmit={handleSubmit} className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-3xl p-8 shadow-2xl dark:shadow-none space-y-8">
              <div>
                <h2 className="text-2xl font-black text-slate-900 dark:text-slate-100 mb-2">Submit Answer Sheet</h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">Capture or upload your written answers. Multiple pages supported.</p>
              </div>

              <div className="border-4 border-dashed border-slate-100 dark:border-slate-700 rounded-3xl p-12 text-center group hover:border-indigo-200 dark:hover:border-indigo-900 transition-colors">
                <div className="w-20 h-20 bg-indigo-50 dark:bg-indigo-900/30 rounded-full flex items-center justify-center text-indigo-600 dark:text-indigo-400 mx-auto mb-6 group-hover:scale-110 transition-transform duration-300">
                  <MdCloudUpload size={40} />
                </div>
                <label className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-10 py-4 rounded-2xl font-black shadow-xl shadow-indigo-100 dark:shadow-none transition-all cursor-pointer transform active:scale-95">
                  Select Images
                  <input type="file" accept="image/*" multiple onChange={handleFileChange} className="hidden" />
                </label>
                <p className="text-xs text-slate-400 font-bold mt-4 uppercase tracking-widest">JPG or PNG only</p>
              </div>

              {previews.length > 0 && (
                <div className="space-y-4 animate-in fade-in slide-in-from-top-4 duration-300">
                  <div className="flex items-center justify-between px-2">
                    <p className="text-sm font-black text-slate-400 uppercase tracking-widest">Uploaded Pages ({previews.length})</p>
                    <button type="button" onClick={() => { setFiles([]); setPreviews([]); }} className="text-xs font-bold text-red-500 hover:underline">Clear all</button>
                  </div>
                  <div className="grid gap-4">
                    {previews.map((preview, index) => (
                      <div key={index} className="group relative flex gap-6 p-4 bg-slate-50 dark:bg-slate-900 rounded-[2rem] border border-slate-100 dark:border-slate-700 hover:border-indigo-200 transition-all">
                        <div className="relative shrink-0">
                          <img src={preview} alt={`Page ${index + 1}`} className="w-28 h-28 object-cover rounded-2xl shadow-md" />
                          <span className="absolute -top-3 -left-3 w-8 h-8 bg-indigo-600 text-white rounded-xl flex items-center justify-center font-black text-sm shadow-lg">
                            {index + 1}
                          </span>
                        </div>
                        <div className="flex-1 py-1">
                          <p className="font-bold text-slate-900 dark:text-slate-100 mb-1">Answer Page {index + 1}</p>
                          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mb-4">Arrange pages in chronological order.</p>
                          <div className="flex gap-2">
                            <button
                              type="button"
                              onClick={() => moveUp(index)}
                              disabled={index === 0}
                              className="p-2 bg-white dark:bg-slate-800 text-slate-400 hover:text-indigo-600 rounded-xl border border-slate-100 dark:border-slate-700 disabled:opacity-20 shadow-sm transition-all"
                            >
                              <MdArrowUpward size={18} />
                            </button>
                            <button
                              type="button"
                              onClick={() => moveDown(index)}
                              disabled={index === files.length - 1}
                              className="p-2 bg-white dark:bg-slate-800 text-slate-400 hover:text-indigo-600 rounded-xl border border-slate-100 dark:border-slate-700 disabled:opacity-20 shadow-sm transition-all"
                            >
                              <MdArrowDownward size={18} />
                            </button>
                            <button
                              type="button"
                              onClick={() => removeFile(index)}
                              className="p-2 bg-white dark:bg-slate-800 text-slate-300 hover:text-red-500 rounded-xl border border-slate-100 dark:border-slate-700 shadow-sm transition-all ml-auto"
                            >
                              <MdDelete size={18} />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-6">
                <button
                  type="submit"
                  disabled={submitting || files.length === 0}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-5 rounded-[2rem] font-black text-lg shadow-xl shadow-indigo-100 dark:shadow-none transition-all flex items-center justify-center gap-3 transform active:scale-95 disabled:opacity-50"
                >
                  {submitting ? <BiLoaderAlt className="animate-spin" size={28} /> : (
                    <>
                      <span>Submit Answer Sheet</span>
                      <MdCheckCircle size={24} />
                    </>
                  )}
                </button>
                <p className="text-center text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mt-6">
                  Evaluation will begin automatically after upload
                </p>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
