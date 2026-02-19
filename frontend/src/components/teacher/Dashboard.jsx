import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getMyPapers, deletePaper, getMyTextbooks, uploadTextbook, deleteTextbook } from '../../services/api';
import Navbar from '../common/Navbar';

export default function TeacherDashboard() {
  const [papers, setPapers] = useState([]);
  const [textbooks, setTextbooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploadingTextbook, setUploadingTextbook] = useState(false);
  const [activeTab, setActiveTab] = useState('papers');

  useEffect(() => {
    loadPapers();
    loadTextbooks();
  }, []);

  const loadPapers = async () => {
    try {
      const res = await getMyPapers();
      setPapers(res.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const loadTextbooks = async () => {
    try {
      const res = await getMyTextbooks();
      setTextbooks(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  const handleDelete = async (paperId) => {
    if (window.confirm('Are you sure you want to delete this paper? This action cannot be undone.')) {
      try {
        await deletePaper(paperId);
        setPapers(papers.filter(p => p.id !== paperId));
      } catch (error) {
        console.error(error);
        alert('Failed to delete paper');
      }
    }
  };

  const handleTextbookUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const title = prompt('Enter textbook title:');
    const subject = prompt('Enter subject (science/mathematics):');

    if (!title || !subject) return;

    setUploadingTextbook(true);
    try {
      await uploadTextbook(file, title, subject);
      loadTextbooks();
      alert('Textbook uploaded successfully! Processing in background...');
    } catch (error) {
      console.error(error);
      alert('Failed to upload textbook');
    } finally {
      setUploadingTextbook(false);
      e.target.value = '';
    }
  };

  const handleDeleteTextbook = async (textbookId) => {
    if (window.confirm('Delete this textbook? All chunks will be removed from vector database.')) {
      try {
        await deleteTextbook(textbookId);
        setTextbooks(textbooks.filter(t => t.id !== textbookId));
      } catch (error) {
        console.error(error);
        alert('Failed to delete textbook');
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
          <div className="flex gap-3">
            {activeTab === 'textbooks' && (
              <label className="text-sm bg-slate-900 text-white px-5 py-2.5 rounded-lg hover:bg-slate-800 transition font-medium cursor-pointer">
                {uploadingTextbook ? 'Uploading...' : 'Upload Textbook'}
                <input type="file" accept=".pdf" onChange={handleTextbookUpload} className="hidden" disabled={uploadingTextbook} />
              </label>
            )}
            {activeTab === 'papers' && (
              <Link
                to="/teacher/create-paper"
                className="text-sm bg-slate-900 text-white px-5 py-2.5 rounded-lg hover:bg-slate-800 transition font-medium"
              >
                Create Paper
              </Link>
            )}
          </div>
        </div>

        <div className="flex gap-4 mb-6 border-b border-slate-200">
          <button
            onClick={() => setActiveTab('papers')}
            className={`pb-3 px-1 font-medium transition ${
              activeTab === 'papers'
                ? 'text-slate-900 border-b-2 border-slate-900'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            Question Papers
          </button>
          <button
            onClick={() => setActiveTab('textbooks')}
            className={`pb-3 px-1 font-medium transition ${
              activeTab === 'textbooks'
                ? 'text-slate-900 border-b-2 border-slate-900'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            Textbooks
          </button>
        </div>

        {activeTab === 'papers' && (
          loading ? (
            <div className="text-center py-12 text-slate-500">Loading...</div>
          ) : papers.length === 0 ? (
            <div className="text-center py-16 bg-white border border-slate-200 rounded-xl">
              <p className="text-slate-500 mb-4">No question papers yet</p>
              <Link
                to="/teacher/create-paper"
                className="text-sm text-slate-900 hover:underline font-medium"
              >
                Create your first paper
              </Link>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {papers.map((paper) => (
                <div key={paper.id} className="bg-white border border-slate-200 rounded-xl p-5 hover:border-slate-300 transition">
                  <h3 className="font-medium text-slate-900 mb-3">{paper.title}</h3>
                  <div className="grid grid-cols-2 gap-3 text-sm mb-4">
                    <div>
                      <span className="text-slate-400">Subject</span>
                      <p className="font-medium text-slate-900 capitalize">{paper.subject}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">Marks</span>
                      <p className="font-medium text-slate-900">{paper.total_marks}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">Duration</span>
                      <p className="font-medium text-slate-900">{paper.duration_minutes}m</p>
                    </div>
                    <div>
                      <span className="text-slate-400">Questions</span>
                      <p className="font-medium text-slate-900">{paper.questions.length}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Link
                      to={`/teacher/papers/${paper.id}/submissions`}
                      className="flex-1 text-center text-sm bg-slate-900 text-white py-2 rounded-lg hover:bg-slate-800 transition"
                    >
                      View Submissions
                    </Link>
                    <button
                      onClick={() => handleDelete(paper.id)}
                      className="text-sm text-red-600 hover:text-red-700 px-3"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )
        )}

        {activeTab === 'textbooks' && (
          textbooks.length === 0 ? (
            <div className="text-center py-16 bg-white border border-slate-200 rounded-xl">
              <p className="text-slate-500 mb-4">No textbooks uploaded yet</p>
              <label className="text-sm text-slate-900 hover:underline font-medium cursor-pointer">
                Upload your first textbook
                <input type="file" accept=".pdf" onChange={handleTextbookUpload} className="hidden" />
              </label>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {textbooks.map((textbook) => (
                <div key={textbook.id} className="bg-white border border-slate-200 rounded-xl p-5 hover:border-slate-300 transition">
                  <h3 className="font-medium text-slate-900 mb-3">{textbook.title}</h3>
                  <div className="text-sm mb-4">
                    <div className="mb-2">
                      <span className="text-slate-400">Subject</span>
                      <p className="font-medium text-slate-900 capitalize">{textbook.subject}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">Chunks</span>
                      <p className="font-medium text-slate-900">{textbook.chunk_count || 'Processing...'}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteTextbook(textbook.id)}
                    className="w-full text-sm text-red-600 hover:text-red-700 py-2 border border-red-200 rounded-lg hover:bg-red-50 transition"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )
        )}
      </div>
    </div>
  );
}
