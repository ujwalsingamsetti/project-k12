import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createPaper, createPaperFromImage } from '../../services/api';
import Navbar from '../common/Navbar';

export default function CreatePaper() {
  const navigate = useNavigate();
  const [mode, setMode] = useState('manual'); // 'manual' or 'image'
  const [formData, setFormData] = useState({
    title: '',
    subject: 'science',
    total_marks: 0,
    duration_minutes: 60,
    instructions: '',
  });
  const [questions, setQuestions] = useState([
    { question_number: 1, question_text: '', question_type: 'short', marks: 5 },
  ]);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadFiles, setUploadFiles] = useState([]);

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
    
    // Handle MCQ options
    if (field === 'question_type' && value === 'mcq') {
      updated[index].options = { A: '', B: '', C: '', D: '' };
      updated[index].correct_answer = 'A';
      updated[index].marks = 1;
    } else if (field === 'question_type' && updated[index].options) {
      delete updated[index].options;
      delete updated[index].correct_answer;
    }
    
    // Handle marks field to prevent NaN
    if (field === 'marks') {
      updated[index][field] = parseInt(value) || 0;
    }
    
    setQuestions(updated);
  };

  const updateMCQOption = (index, option, value) => {
    const updated = [...questions];
    updated[index].options[option] = value;
    setQuestions(updated);
  };

  const removeQuestion = (index) => {
    setQuestions(questions.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const totalMarks = questions.reduce((sum, q) => sum + parseInt(q.marks), 0);
    try {
      await createPaper({ ...formData, total_marks: totalMarks, questions });
      navigate('/teacher');
    } catch (error) {
      setError('Failed to create paper');
    }
  };

  const handleImageUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setUploading(true);
    setError('');

    try {
      const res = await createPaperFromImage(files, formData.title, formData.subject, formData.duration_minutes);
      alert(`Paper created successfully! ${res.data.questions_count} questions extracted. ${res.data.diagrams_detected || 0} diagrams detected.`);
      navigate('/teacher');
    } catch (error) {
      setError('Failed to process file(s). Please ensure images/PDF are clear and contain question numbers with marks.');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setUploadFiles(files);
  };

  const removeFile = (index) => {
    setUploadFiles(uploadFiles.filter((_, i) => i !== index));
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-semibold text-slate-900 mb-8">Create Question Paper</h1>
        
        {/* Mode Selection */}
        <div className="flex gap-4 mb-6 border-b border-slate-200">
          <button
            onClick={() => setMode('manual')}
            className={`pb-3 px-1 font-medium transition ${
              mode === 'manual'
                ? 'text-slate-900 border-b-2 border-slate-900'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            Manual Entry
          </button>
          <button
            onClick={() => setMode('image')}
            className={`pb-3 px-1 font-medium transition ${
              mode === 'image'
                ? 'text-slate-900 border-b-2 border-slate-900'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            Upload Question Paper
          </button>
        </div>
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
            {error}
          </div>
        )}

        {mode === 'image' ? (
          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <div className="grid md:grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent transition"
                  placeholder="Optional"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Subject</label>
                <select
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent transition"
                >
                  <option value="science">Science</option>
                  <option value="mathematics">Mathematics</option>
                </select>
              </div>
            </div>
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-700 mb-1">Duration (minutes)</label>
              <input
                type="number"
                value={formData.duration_minutes}
                onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) || 60 })}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent transition"
              />
            </div>
            <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center">
              <p className="text-slate-600 mb-2">Upload question paper images or PDF</p>
              <p className="text-sm text-slate-500 mb-4">Supported: JPG, PNG, PDF. Multiple pages supported. Format: "Q1. Question text [5 marks]"</p>
              
              {uploadFiles.length > 0 && (
                <div className="mb-4 space-y-2">
                  {uploadFiles.map((file, idx) => (
                    <div key={idx} className="flex items-center justify-between bg-slate-50 p-2 rounded">
                      <span className="text-sm text-slate-700">{file.name}</span>
                      <button
                        type="button"
                        onClick={() => removeFile(idx)}
                        className="text-red-600 hover:text-red-700 text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              )}
              
              <div className="flex gap-3 justify-center">
                <label className="inline-block bg-slate-900 text-white px-6 py-2.5 rounded-lg hover:bg-slate-800 transition font-medium cursor-pointer">
                  Choose Files
                  <input type="file" accept="image/*,.pdf" multiple onChange={handleFileSelect} className="hidden" />
                </label>
                
                {uploadFiles.length > 0 && (
                  <button
                    type="button"
                    onClick={(e) => {
                      const fakeEvent = { target: { files: uploadFiles, value: '' } };
                      handleImageUpload(fakeEvent);
                    }}
                    disabled={uploading}
                    className="bg-green-600 text-white px-6 py-2.5 rounded-lg hover:bg-green-700 transition font-medium disabled:opacity-50"
                  >
                    {uploading ? 'Processing...' : 'Upload & Extract'}
                  </button>
                )}
              </div>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="bg-white border border-slate-200 rounded-xl p-6 space-y-6">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent transition"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Subject</label>
                <select
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent transition"
                >
                  <option value="science">Science</option>
                  <option value="mathematics">Mathematics</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Duration (minutes)</label>
              <input
                type="number"
                value={formData.duration_minutes}
                onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) || 60 })}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent transition"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Instructions</label>
              <textarea
                value={formData.instructions}
                onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent transition"
                rows="3"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-medium text-slate-900">Questions</h3>
                <button
                  type="button"
                  onClick={addQuestion}
                  className="text-sm text-slate-900 hover:text-slate-700 font-medium"
                >
                  + Add Question
                </button>
              </div>

              {questions.map((q, index) => (
                <div key={index} className="border border-slate-200 rounded-lg p-4 mb-3">
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-sm font-medium text-slate-900">Question {index + 1}</span>
                    {questions.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeQuestion(index)}
                        className="text-sm text-red-600 hover:text-red-700"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                  <textarea
                    value={q.question_text}
                    onChange={(e) => updateQuestion(index, 'question_text', e.target.value)}
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg mb-3 focus:ring-2 focus:ring-slate-900 focus:border-transparent transition"
                    placeholder="Enter question text"
                    rows="2"
                    required
                  />
                  <div className="grid grid-cols-2 gap-3">
                    <select
                      value={q.question_type}
                      onChange={(e) => updateQuestion(index, 'question_type', e.target.value)}
                      className="px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent transition"
                    >
                      <option value="short">Short Answer</option>
                      <option value="long">Long Answer</option>
                      <option value="mcq">MCQ</option>
                    </select>
                    <input
                      type="number"
                      value={q.marks}
                      onChange={(e) => updateQuestion(index, 'marks', e.target.value)}
                      className="px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent transition"
                      placeholder="Marks"
                      required
                    />
                  </div>
                  
                  {q.question_type === 'mcq' && (
                    <div className="mt-3 space-y-2">
                      <p className="text-sm font-medium text-slate-700">Options:</p>
                      {['A', 'B', 'C', 'D'].map(opt => (
                        <input
                          key={opt}
                          type="text"
                          value={q.options?.[opt] || ''}
                          onChange={(e) => updateMCQOption(index, opt, e.target.value)}
                          className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent transition"
                          placeholder={`Option ${opt}`}
                          required
                        />
                      ))}
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Correct Answer:</label>
                        <select
                          value={q.correct_answer || 'A'}
                          onChange={(e) => updateQuestion(index, 'correct_answer', e.target.value)}
                          className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent transition"
                        >
                          <option value="A">A</option>
                          <option value="B">B</option>
                          <option value="C">C</option>
                          <option value="D">D</option>
                        </select>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="submit"
                className="flex-1 bg-slate-900 text-white py-2.5 rounded-lg hover:bg-slate-800 transition font-medium"
              >
                Create Paper
              </button>
              <button
                type="button"
                onClick={() => navigate('/teacher')}
                className="px-6 text-slate-600 hover:text-slate-900 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
