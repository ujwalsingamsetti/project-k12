import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getPaperDetails, submitAnswer } from '../../services/api';
import Navbar from '../common/Navbar';

export default function SubmitAnswer() {
  const { paperId } = useParams();
  const navigate = useNavigate();
  const [paper, setPaper] = useState(null);
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadPaper();
  }, [paperId]);

  const loadPaper = async () => {
    try {
      const res = await getPaperDetails(paperId);
      setPaper(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length > 0) {
      // Append new files to existing ones
      const newFiles = [...files, ...selectedFiles];
      setFiles(newFiles);
      
      // Generate previews for new files only
      const newPreviews = [...previews];
      let loadedCount = 0;
      
      selectedFiles.forEach((file) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          newPreviews.push(reader.result);
          loadedCount++;
          if (loadedCount === selectedFiles.length) {
            setPreviews(newPreviews);
          }
        };
        reader.readAsDataURL(file);
      });
    }
    // Reset input to allow selecting same file again
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
      setError('Please select at least one image');
      return;
    }

    setSubmitting(true);
    setError('');
    try {
      await submitAnswer(paperId, files);
      navigate('/student');
    } catch (error) {
      setError('Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (!paper) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <div className="flex items-center justify-center py-12 text-slate-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-8">
        <button
          onClick={() => navigate('/student')}
          className="mb-4 text-sm text-slate-600 hover:text-slate-900 flex items-center gap-1"
        >
          ← Back to Dashboard
        </button>
        
        <h1 className="text-2xl font-semibold text-slate-900 mb-2">{paper.title}</h1>
        <p className="text-slate-600 mb-4">
          {paper.subject} · {paper.total_marks} marks · {paper.duration_minutes} minutes
        </p>
        
        {paper.pdf_path && (
          <div className="mb-6">
            <a
              href={`http://localhost:8000/api/student/papers/${paperId}/pdf`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              📄 View Question Paper PDF
            </a>
          </div>
        )}

        <div className="bg-white border border-slate-200 rounded-xl p-6 mb-6">
          <h2 className="text-lg font-medium text-slate-900 mb-4">Questions</h2>
          <div className="space-y-4">
            {paper.questions.map((q) => (
              <div key={q.id} className="border-l-2 border-slate-900 pl-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">Q{q.question_number}. {q.question_text}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <p className="text-sm text-slate-500">({q.marks} marks · {q.question_type})</p>
                      {q.section && <span className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded">Section {q.section}</span>}
                      {q.has_or_option && <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded">OR Option</span>}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-white border border-slate-200 rounded-xl p-6">
          <h2 className="text-lg font-medium text-slate-900 mb-4">Upload Answer Sheet</h2>
          
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
              {error}
            </div>
          )}

          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Select Images (JPG, PNG) - Add multiple pages
            </label>
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={handleFileChange}
              className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent transition"
            />
            <p className="text-xs text-slate-500 mt-1">
              Click "Choose Files" multiple times to add more pages. Arrange them in order below.
            </p>
          </div>

          {previews.length > 0 && (
            <div className="mb-6">
              <p className="text-sm font-medium text-slate-700 mb-3">Preview ({files.length} page{files.length > 1 ? 's' : ''}):</p>
              <div className="space-y-3">
                {previews.map((preview, index) => (
                  <div key={index} className="border border-slate-200 rounded-lg p-3 flex gap-3">
                    <img src={preview} alt={`Page ${index + 1}`} className="w-32 h-32 object-cover rounded" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-900 mb-2">Page {index + 1}</p>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => moveUp(index)}
                          disabled={index === 0}
                          className="text-xs px-2 py-1 border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          ↑ Move Up
                        </button>
                        <button
                          type="button"
                          onClick={() => moveDown(index)}
                          disabled={index === files.length - 1}
                          className="text-xs px-2 py-1 border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          ↓ Move Down
                        </button>
                        <button
                          type="button"
                          onClick={() => removeFile(index)}
                          className="text-xs px-2 py-1 text-red-600 border border-red-300 rounded hover:bg-red-50"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 bg-slate-900 text-white py-2.5 rounded-lg hover:bg-slate-800 transition font-medium disabled:bg-slate-400"
            >
              {submitting ? 'Submitting...' : `Submit ${files.length} Page${files.length > 1 ? 's' : ''}`}
            </button>
            <button
              type="button"
              onClick={() => navigate('/student')}
              className="px-6 text-slate-600 hover:text-slate-900 transition"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
