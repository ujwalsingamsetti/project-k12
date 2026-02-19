import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getAvailablePapers, getMySubmissions, getTeachers } from '../../services/api';
import Navbar from '../common/Navbar';

export default function StudentDashboard() {
  const [papers, setPapers] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [selectedTeacher, setSelectedTeacher] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTeachers();
    loadData();
  }, []);

  useEffect(() => {
    loadPapers();
  }, [selectedTeacher]);

  const loadTeachers = async () => {
    try {
      const res = await getTeachers();
      setTeachers(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  const loadPapers = async () => {
    try {
      const res = await getAvailablePapers(selectedTeacher || null);
      setPapers(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  const loadData = async () => {
    try {
      const submissionsRes = await getMySubmissions();
      setSubmissions(submissionsRes.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-semibold text-slate-900 mb-8">Dashboard</h1>

        <div className="grid lg:grid-cols-2 gap-8">
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-medium text-slate-900">Available Papers</h2>
              {teachers.length > 0 && (
                <select
                  value={selectedTeacher}
                  onChange={(e) => setSelectedTeacher(e.target.value)}
                  className="text-sm px-3 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                >
                  <option value="">All Teachers</option>
                  {teachers.map((teacher) => (
                    <option key={teacher.id} value={teacher.id}>
                      {teacher.full_name}
                    </option>
                  ))}
                </select>
              )}
            </div>
            {loading ? (
              <div className="text-center py-12 text-slate-500">Loading...</div>
            ) : papers.length === 0 ? (
              <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-500">
                {selectedTeacher ? 'No papers from this teacher' : 'No papers available'}
              </div>
            ) : (
              <div className="space-y-3">
                {papers.map((paper) => (
                  <div key={paper.id} className="bg-white border border-slate-200 rounded-xl p-5 hover:border-slate-300 transition">
                    <h3 className="font-medium text-slate-900 mb-3">{paper.title}</h3>
                    <div className="grid grid-cols-3 gap-3 text-sm text-slate-600 mb-4">
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
                    </div>
                    <Link
                      to={`/student/submit/${paper.id}`}
                      className="block text-center text-sm bg-slate-900 text-white py-2 rounded-lg hover:bg-slate-800 transition"
                    >
                      Submit Answer
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <h2 className="text-lg font-medium text-slate-900 mb-4">My Submissions</h2>
            {loading ? (
              <div className="text-center py-12 text-slate-500">Loading...</div>
            ) : submissions.length === 0 ? (
              <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-500">
                No submissions yet
              </div>
            ) : (
              <div className="space-y-3">
                {submissions.map((sub) => (
                  <Link
                    key={sub.id}
                    to={`/student/submissions/${sub.id}`}
                    className="block bg-white border border-slate-200 rounded-xl p-5 hover:border-slate-300 transition"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm font-medium text-slate-900">Submission</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        sub.status === 'evaluated' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                        sub.status === 'pending' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                        'bg-red-50 text-red-700 border border-red-200'
                      }`}>
                        {sub.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mb-3">
                      {new Date(sub.submitted_at).toLocaleString()}
                    </p>
                    {sub.status === 'evaluated' && (
                      <p className="text-lg font-semibold text-slate-900">
                        {sub.total_marks}/{sub.max_marks}
                      </p>
                    )}
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
