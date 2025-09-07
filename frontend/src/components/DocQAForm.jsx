import { useState } from 'react';

export default function DocQAForm() {
  const [docLink, setDocLink] = useState('');
  const [questions, setQuestions] = useState('');
  const [answers, setAnswers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setAnswers([]);
    try {
      const response = await fetch('/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          documents: docLink,
          questions: questions.split('\n').filter(q => q.trim())
        })
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'API error');
      }
      const data = await response.json();
      setAnswers(data.answer.answers || []);
    } catch (err) {
      setError(err.message || 'Failed to fetch answers.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white/10 backdrop-blur-xl rounded-2xl p-8 shadow-xl border border-white/20 max-w-xl mx-auto mt-10 flex flex-col gap-6">
      <label className="font-semibold text-white">Document Link</label>
      <input
        type="text"
        value={docLink}
        onChange={e => setDocLink(e.target.value)}
        className="p-3 rounded-lg bg-white/30 text-white border border-white/30 focus:outline-none focus:ring-2 focus:ring-purple-500"
        placeholder="Paste document link here..."
        required
      />
      <label className="font-semibold text-white">Questions (one per line)</label>
      <textarea
        value={questions}
        onChange={e => setQuestions(e.target.value)}
        className="p-3 rounded-lg bg-white/30 text-white border border-white/30 focus:outline-none focus:ring-2 focus:ring-purple-500 min-h-[100px]"
        placeholder="Type your questions here..."
        required
      />
      <button
        type="submit"
        disabled={loading}
        className="py-3 px-6 rounded-full font-semibold shadow-lg transition-all duration-300 bg-gradient-to-r from-purple-600 to-blue-500 text-white hover:scale-105 hover:shadow-xl"
      >
        {loading ? 'Getting Answers...' : 'Get Answers'}
      </button>
      {error && <div className="text-red-400 font-medium">{error}</div>}
      {answers.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-bold text-white mb-2">Answers:</h3>
          <ul className="list-disc pl-6 text-white/90">
            {answers.map((ans, idx) => (
              <li key={idx}>{ans}</li>
            ))}
          </ul>
        </div>
      )}
    </form>
  );
}
