import { useState } from 'react';
import { Download, CheckCircle, XCircle, AlertCircle, Clock, TrendingUp, ChevronDown, ChevronRight } from 'lucide-react';
import { api } from '../services/api';
import type { BatchGradingResponse, BatchResult, ChecklistItem } from '../services/api';

interface BatchResultsProps {
  results: BatchGradingResponse;
  onRestart: () => void;
}

export function BatchResults({ results, onRestart }: BatchResultsProps) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const toggleRow = (id: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  const handleExportCSV = async () => {
    try {
      const blob = await api.exportBatchResultsCSV(results);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `portfolio_results_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const getScoreColor = (score: number | null) => {
    if (score === null) return 'text-gray-400';
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getScoreBgColor = (score: number | null) => {
    if (score === null) return 'bg-gray-800';
    if (score >= 80) return 'bg-green-900/30';
    if (score >= 60) return 'bg-yellow-900/30';
    return 'bg-red-900/30';
  };

  const renderChecklistDetails = (checklist: { [key: string]: ChecklistItem }) => {
    const checklistArray = Object.entries(checklist);

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {checklistArray.map(([key, item]) => (
          <div
            key={key}
            className={`p-3 rounded-lg border ${
              item.pass
                ? 'bg-green-900/20 border-green-800'
                : 'bg-red-900/20 border-red-800'
            }`}
          >
            <div className="flex items-start gap-2 mb-2">
              {item.pass ? (
                <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${item.pass ? 'text-green-300' : 'text-red-300'}`}>
                  {key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                </p>
                {item.details.length > 0 && (
                  <div className="mt-1 space-y-0.5">
                    {item.details.map((detail, idx) => (
                      <p key={idx} className="text-xs text-gray-400">
                        {detail}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-950 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">
            Batch Grading Results
          </h1>
          <p className="text-gray-400">
            Analysis complete for {results.total} portfolios
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-900 rounded-lg p-6 shadow border border-gray-800">
            <div className="flex items-center gap-3 mb-2">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <span className="text-sm text-gray-400">Successful</span>
            </div>
            <p className="text-3xl font-bold text-white">
              {results.successful}
            </p>
          </div>

          <div className="bg-gray-900 rounded-lg p-6 shadow border border-gray-800">
            <div className="flex items-center gap-3 mb-2">
              <XCircle className="w-5 h-5 text-red-400" />
              <span className="text-sm text-gray-400">Failed</span>
            </div>
            <p className="text-3xl font-bold text-white">
              {results.failed}
            </p>
          </div>

          <div className="bg-gray-900 rounded-lg p-6 shadow border border-gray-800">
            <div className="flex items-center gap-3 mb-2">
              <TrendingUp className="w-5 h-5 text-blue-400" />
              <span className="text-sm text-gray-400">Avg Score</span>
            </div>
            <p className="text-3xl font-bold text-white">
              {results.avg_score !== null ? `${results.avg_score.toFixed(1)}%` : 'N/A'}
            </p>
          </div>

          <div className="bg-gray-900 rounded-lg p-6 shadow border border-gray-800">
            <div className="flex items-center gap-3 mb-2">
              <Clock className="w-5 h-5 text-purple-400" />
              <span className="text-sm text-gray-400">Total Time</span>
            </div>
            <p className="text-3xl font-bold text-white">
              {results.total_time.toFixed(1)}s
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            <Download className="w-5 h-5" />
            Export as CSV
          </button>
          <button
            onClick={onRestart}
            className="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg transition-colors border border-gray-700"
          >
            Grade More Portfolios
          </button>
        </div>

        {/* Results Table with Accordion */}
        <div className="bg-gray-900 rounded-lg shadow border border-gray-800 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-800 border-b border-gray-700">
                <tr>
                  <th className="w-10"></th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Portfolio
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {results.results.map((result: BatchResult) => (
                  <>
                    {/* Main Row */}
                    <tr
                      key={result.id}
                      className={`hover:bg-gray-800/50 transition-colors ${
                        result.status === 'success' && result.checklist ? 'cursor-pointer' : ''
                      }`}
                      onClick={() => {
                        if (result.status === 'success' && result.checklist) {
                          toggleRow(result.id);
                        }
                      }}
                    >
                      <td className="px-4 py-4">
                        {result.status === 'success' && result.checklist && (
                          <button
                            className="p-1 hover:bg-gray-700 rounded transition-colors"
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleRow(result.id);
                            }}
                          >
                            {expandedRows.has(result.id) ? (
                              <ChevronDown className="w-4 h-4 text-gray-400" />
                            ) : (
                              <ChevronRight className="w-4 h-4 text-gray-400" />
                            )}
                          </button>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                        {result.id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                        {result.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {result.score !== null ? (
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${getScoreBgColor(result.score)} ${getScoreColor(result.score)}`}>
                            {result.score}%
                          </span>
                        ) : (
                          <span className="text-gray-400 text-sm">N/A</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {result.status === 'success' && (
                          <span className="inline-flex items-center gap-1 text-sm text-green-400">
                            <CheckCircle className="w-4 h-4" />
                            Success
                          </span>
                        )}
                        {result.status === 'failed' && (
                          <span className="inline-flex items-center gap-1 text-sm text-red-400">
                            <XCircle className="w-4 h-4" />
                            Failed
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                        {result.analysis_time ? `${result.analysis_time.toFixed(1)}s` : '-'}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <a
                          href={result.portfolio_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-purple-400 hover:text-purple-300 hover:underline"
                          onClick={(e) => e.stopPropagation()}
                        >
                          View
                        </a>
                      </td>
                    </tr>

                    {/* Expanded Details Row */}
                    {expandedRows.has(result.id) && result.checklist && (
                      <tr key={`${result.id}-details`}>
                        <td colSpan={7} className="px-6 py-6 bg-gray-800/30">
                          <div className="space-y-6">
                            {/* Checklist Details */}
                            <div>
                              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                <CheckCircle className="w-5 h-5 text-purple-400" />
                                Detailed Checklist ({Object.values(result.checklist).filter(item => item.pass).length}/{Object.keys(result.checklist).length} passed)
                              </h3>
                              {renderChecklistDetails(result.checklist)}
                            </div>

                            {/* AI Analysis */}
                            {result.ai_analysis && (
                              <div className="pt-4 border-t border-gray-700">
                                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                                  <AlertCircle className="w-5 h-5 text-blue-400" />
                                  AI Feedback
                                </h3>
                                <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                                  <p className="text-sm text-gray-300 whitespace-pre-wrap">
                                    {result.ai_analysis}
                                  </p>
                                </div>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Failed Results Details */}
        {results.failed > 0 && (
          <div className="mt-6 bg-red-900/20 border border-red-800 rounded-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <h3 className="text-lg font-semibold text-red-300">
                Failed Analyses
              </h3>
            </div>
            <div className="space-y-3">
              {results.results
                .filter((r) => r.status === 'failed')
                .map((result) => (
                  <div
                    key={result.id}
                    className="bg-gray-900 p-4 rounded-lg border border-gray-800"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="font-semibold text-white">
                          {result.name} ({result.id})
                        </p>
                        <p className="text-sm text-gray-400">
                          {result.portfolio_url}
                        </p>
                      </div>
                    </div>
                    <p className="text-sm text-red-400">
                      Error: {result.error || 'Unknown error'}
                    </p>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
