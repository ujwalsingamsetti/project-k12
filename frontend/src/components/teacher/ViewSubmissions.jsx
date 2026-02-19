import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getPaperSubmissions, getPaper } from '../../services/api';
import Navbar from '../common/Navbar';

export default function ViewSubmissions() {
  const { paperId } = useParams();
  const [paper, setPaper] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [paperId]);

  const loadData = async () => {
    try {
      const [paperRes, submissionsRes] = await Promise.all([
        getPaper(paperId),
        getPaperSubmissions(paperId),
      ]);
      setPaper(paperRes.data);
      setSubmissions(submissionsRes.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'evaluated':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex items-center justify-center py-12">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">{paper?.title}</h1>
        <p className="text-gray-600 mb-8">
          {paper?.subject} | {paper?.total_marks} marks | {paper?.duration_minutes} minutes
        </p>

        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b">
            <h2 className="text-xl font-semibold">Student Submissions ({submissions.length})</h2>
          </div>

          {submissions.length === 0 ? (
            <div className="text-center py-12 text-gray-600">No submissions yet</div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Student
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Submitted At
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Score
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {submissions.map((sub) => (
                  <tr key={sub.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap font-medium">{sub.student_name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-600">{sub.student_email}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                      {new Date(sub.submitted_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(sub.status)}`}>
                        {sub.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap font-semibold">
                      {sub.status === 'evaluated' ? `${sub.total_marks}/${sub.max_marks}` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
