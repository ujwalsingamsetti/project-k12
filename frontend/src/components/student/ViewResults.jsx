import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getSubmissionDetails } from '../../services/api';
import Navbar from '../common/Navbar';

export default function ViewResults() {
  const { submissionId } = useParams();
  const navigate = useNavigate();
  const [submission, setSubmission] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSubmission();
  }, [submissionId]);

  const loadSubmission = async () => {
    try {
      const res = await getSubmissionDetails(submissionId);
      setSubmission(res.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const parseFeedback = (feedbackStr) => {
    try {
      return JSON.parse(feedbackStr);
    } catch {
      return null;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <div className="flex items-center justify-center py-12 text-slate-500">Loading...</div>
      </div>
    );
  }

  if (!submission) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <div className="flex items-center justify-center py-12 text-slate-500">Submission not found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 py-8">
        <button
          onClick={() => navigate('/student')}
          className="mb-4 text-sm text-slate-600 hover:text-slate-900 flex items-center gap-1"
        >
          ← Back to Dashboard
        </button>
        
        <h1 className="text-2xl font-semibold text-slate-900 mb-2">Evaluation Results</h1>
        <p className="text-slate-600 mb-8">
          Submitted: {new Date(submission.submitted_at).toLocaleString()}
        </p>

        {/* Uploaded Images */}
        {submission.image_path && (
          <div className="bg-white border border-slate-200 rounded-xl p-6 mb-6">
            <h2 className="text-lg font-medium text-slate-900 mb-4">Your Uploaded Answer Sheet</h2>
            <div className="grid gap-4 md:grid-cols-2">
              {submission.image_path.split(',').map((path, idx) => (
                <div key={idx} className="border border-slate-200 rounded-lg overflow-hidden">
                  <img 
                    src={`http://localhost:8000${path.replace('/app', '')}`}
                    alt={`Answer sheet page ${idx + 1}`}
                    className="w-full h-auto"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'block';
                    }}
                  />
                  <div style={{display: 'none'}} className="p-4 text-center text-slate-500 text-sm">
                    Image not available
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="bg-white border border-slate-200 rounded-xl p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-medium text-slate-900">Total Score</h2>
              <p className="text-sm text-slate-600">Status: <span className="capitalize font-medium">{submission.status}</span></p>
            </div>
            <div className="text-right">
              <p className="text-4xl font-semibold text-slate-900">
                {submission.total_marks}/{submission.max_marks}
              </p>
              <p className="text-slate-600">
                {((submission.total_marks / submission.max_marks) * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <h2 className="text-lg font-medium text-slate-900">Question-wise Results</h2>
          {submission.evaluations && submission.evaluations.map((evaluation) => {
            const feedback = parseFeedback(evaluation.feedback);
            
            return (
              <div key={evaluation.question_id} className="bg-white border border-slate-200 rounded-xl p-6">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-base font-medium text-slate-900">Question {evaluation.question_number}</h3>
                  <span className="text-xl font-semibold text-slate-900">
                    {evaluation.marks_obtained}/{evaluation.max_marks}
                  </span>
                </div>
                
                <div className="mb-4">
                  <p className="text-sm font-medium text-slate-700 mb-2">Your Answer:</p>
                  <p className="text-sm text-slate-800 bg-slate-50 p-3 rounded-lg border border-slate-200">
                    {evaluation.student_answer || 'No answer provided'}
                  </p>
                </div>

                {feedback ? (
                  <div className="space-y-4">
                    {feedback.overall_feedback && (
                      <div>
                        <p className="text-sm font-medium text-slate-700 mb-2">Overall Feedback:</p>
                        <p className="text-sm text-slate-800 bg-blue-50 p-3 rounded-lg border border-blue-200">
                          {feedback.overall_feedback}
                        </p>
                      </div>
                    )}

                    {feedback.correct_points && feedback.correct_points.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-emerald-700 mb-2">✓ What You Got Right:</p>
                        <ul className="text-sm text-slate-800 bg-emerald-50 p-3 rounded-lg border border-emerald-200 space-y-1">
                          {feedback.correct_points.map((point, idx) => (
                            <li key={idx} className="flex items-start">
                              <span className="text-emerald-600 mr-2">•</span>
                              <span>{point}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {feedback.errors && feedback.errors.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-red-700 mb-2">✗ What is Wrong:</p>
                        <div className="space-y-2">
                          {feedback.errors.map((error, idx) => (
                            <div key={idx} className="bg-red-50 p-3 rounded-lg border border-red-200">
                              <p className="text-sm font-medium text-red-900 mb-1">{error.what}</p>
                              <p className="text-sm text-red-800"><span className="font-medium">Why:</span> {error.why}</p>
                              {error.impact && (
                                <p className="text-sm text-red-700 mt-1"><span className="font-medium">Impact:</span> {error.impact}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {feedback.missing_concepts && feedback.missing_concepts.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-amber-700 mb-2">⚠ Missing Concepts:</p>
                        <ul className="text-sm text-slate-800 bg-amber-50 p-3 rounded-lg border border-amber-200 space-y-1">
                          {feedback.missing_concepts.map((concept, idx) => (
                            <li key={idx} className="flex items-start">
                              <span className="text-amber-600 mr-2">•</span>
                              <span>{concept}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {feedback.correct_answer_should_include && feedback.correct_answer_should_include.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-blue-700 mb-2">📝 Correct Answer Should Include:</p>
                        <ul className="text-sm text-slate-800 bg-blue-50 p-3 rounded-lg border border-blue-200 space-y-1">
                          {feedback.correct_answer_should_include.map((point, idx) => (
                            <li key={idx} className="flex items-start">
                              <span className="text-blue-600 mr-2">•</span>
                              <span>{point}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {feedback.improvement_guidance && feedback.improvement_guidance.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-purple-700 mb-2">💡 How to Improve:</p>
                        <div className="space-y-2">
                          {feedback.improvement_guidance.map((guide, idx) => (
                            <div key={idx} className="bg-purple-50 p-3 rounded-lg border border-purple-200">
                              <p className="text-sm font-medium text-purple-900 mb-1">{guide.suggestion}</p>
                              {guide.resource && (
                                <p className="text-sm text-purple-800"><span className="font-medium">Resource:</span> {guide.resource}</p>
                              )}
                              {guide.practice && (
                                <p className="text-sm text-purple-700 mt-1"><span className="font-medium">Practice:</span> {guide.practice}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div>
                    <p className="text-sm font-medium text-slate-700 mb-2">Feedback:</p>
                    <p className="text-sm text-slate-800 bg-slate-50 p-3 rounded-lg border border-slate-200">
                      {evaluation.feedback || 'Evaluation in progress...'}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
