import { useState, useRef } from 'react';
import { Upload, FileText, X, AlertCircle, CheckCircle2, ClipboardPaste } from 'lucide-react';
import { api } from '../services/api';
import type { BatchPortfolioItem } from '../services/api';

interface BatchUploadProps {
  onPortfoliosLoaded: (portfolios: BatchPortfolioItem[]) => void;
}

type UploadMode = 'file' | 'paste';

export function BatchUpload({ onPortfoliosLoaded }: BatchUploadProps) {
  const [mode, setMode] = useState<UploadMode>('file');
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [csvText, setCsvText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const parseCsvText = (text: string): BatchPortfolioItem[] => {
    const lines = text.trim().split('\n').filter(line => line.trim());
    if (lines.length < 2) {
      throw new Error('CSV must have at least a header row and one data row');
    }

    // Parse header
    const header = lines[0].split(/[,\t]/).map(h => h.trim().toLowerCase());

    // Find column indices (flexible column names)
    const idIndex = header.findIndex(h => ['id', 'student id', 'roll'].includes(h));
    const nameIndex = header.findIndex(h => ['name', 'student name'].includes(h));
    const urlIndex = header.findIndex(h => ['portfolio link', 'url', 'portfolio url', 'link', 'portfolio'].includes(h));

    if (idIndex === -1 || nameIndex === -1 || urlIndex === -1) {
      throw new Error('CSV must have columns: Id, Name, Portfolio Link (or similar)');
    }

    // Parse data rows
    const portfolios: BatchPortfolioItem[] = [];
    for (let i = 1; i < lines.length; i++) {
      const cols = lines[i].split(/[,\t]/).map(c => c.trim());
      if (cols.length > Math.max(idIndex, nameIndex, urlIndex)) {
        portfolios.push({
          id: cols[idIndex],
          name: cols[nameIndex],
          portfolio_url: cols[urlIndex]
        });
      }
    }

    return portfolios;
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.name.endsWith('.csv')) {
      setFile(droppedFile);
      setError(null);
    } else {
      setError('Please upload a CSV file');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.name.endsWith('.csv')) {
        setFile(selectedFile);
        setError(null);
      } else {
        setError('Please upload a CSV file');
      }
    }
  };

  const handleFileUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const result = await api.uploadCSV(file);
      setSuccess(true);
      setTimeout(() => {
        onPortfoliosLoaded(result.portfolios);
      }, 500);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || 'Failed to upload CSV');
      } else {
        setError('Failed to upload CSV');
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePasteProcess = async () => {
    if (!csvText.trim()) {
      setError('Please paste CSV data');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const portfolios = parseCsvText(csvText);
      if (portfolios.length === 0) {
        throw new Error('No valid portfolio entries found in CSV');
      }
      setSuccess(true);
      setTimeout(() => {
        onPortfoliosLoaded(portfolios);
      }, 500);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || 'Failed to parse CSV');
      } else {
        setError('Failed to parse CSV');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
    setError(null);
    setSuccess(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleModeChange = (newMode: UploadMode) => {
    setMode(newMode);
    setFile(null);
    setCsvText('');
    setError(null);
    setSuccess(false);
  };

  return (
    <div className="space-y-6">
      {/* Tab Toggle */}
      <div className="flex gap-2 bg-gray-800 p-1 rounded-lg border border-gray-700">
        <button
          onClick={() => handleModeChange('file')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${
            mode === 'file'
              ? 'bg-purple-600 text-white'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          <Upload className="w-4 h-4" />
          Upload File
        </button>
        <button
          onClick={() => handleModeChange('paste')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${
            mode === 'paste'
              ? 'bg-purple-600 text-white'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          <ClipboardPaste className="w-4 h-4" />
          Paste CSV
        </button>
      </div>

      {/* Upload File Mode */}
      {mode === 'file' && (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            border-2 border-dashed rounded-xl p-12 text-center transition-all
            ${isDragging
              ? 'border-purple-500 bg-purple-900/20'
              : 'border-gray-700 hover:border-purple-500'
            }
            ${file ? 'bg-gray-800' : 'bg-gray-800/50'}
          `}
        >
          {!file ? (
            <>
              <Upload className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h3 className="text-xl font-semibold text-gray-200 mb-2">
                Upload CSV File
              </h3>
              <p className="text-gray-400 mb-4">
                Drag and drop your CSV file here, or click to browse
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="hidden"
                id="csv-upload"
              />
              <label
                htmlFor="csv-upload"
                className="inline-block px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg cursor-pointer transition-colors"
              >
                Choose File
              </label>
            </>
          ) : (
            <div className="flex items-center justify-center gap-4">
              <FileText className="w-12 h-12 text-purple-400" />
              <div className="text-left">
                <p className="font-semibold text-white">{file.name}</p>
                <p className="text-sm text-gray-400">
                  {(file.size / 1024).toFixed(2)} KB
                </p>
              </div>
              <button
                onClick={handleRemoveFile}
                className="p-2 hover:bg-gray-700 rounded-full transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Paste CSV Mode */}
      {mode === 'paste' && (
        <div className="space-y-4">
          <div>
            <label htmlFor="csv-textarea" className="block text-sm font-medium text-gray-300 mb-2">
              Paste CSV Data
            </label>
            <textarea
              id="csv-textarea"
              value={csvText}
              onChange={(e) => setCsvText(e.target.value)}
              placeholder={`Id,Name,Portfolio Link
fw16_484,Pratik Uttam Ganjale,https://github.com/pratikganjale55
fw11_156,S Naveed,https://naveed476.github.io/portfolio/`}
              rows={10}
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 font-mono text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
            />
            <p className="mt-2 text-xs text-gray-400">
              Paste your CSV data here with tab or comma-separated values
            </p>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-900/20 border border-red-800 rounded-lg">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="flex items-center gap-3 p-4 bg-green-900/20 border border-green-800 rounded-lg">
          <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
          <p className="text-sm text-green-300">
            CSV processed successfully!
          </p>
        </div>
      )}

      {/* Process Button */}
      {((mode === 'file' && file && !success) || (mode === 'paste' && csvText.trim() && !success)) && (
        <button
          onClick={mode === 'file' ? handleFileUpload : handlePasteProcess}
          disabled={loading}
          className="w-full py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:text-gray-500 text-white font-semibold rounded-lg transition-colors disabled:cursor-not-allowed"
        >
          {loading ? 'Processing...' : `Process ${mode === 'file' ? 'CSV File' : 'CSV Data'}`}
        </button>
      )}

      {/* CSV Format Info */}
      <div className="bg-purple-900/20 border border-purple-800 rounded-lg p-4">
        <h4 className="font-semibold text-purple-300 mb-2">CSV Format:</h4>
        <pre className="text-xs text-purple-200 font-mono bg-gray-800 p-3 rounded overflow-x-auto border border-gray-700">
{`Id,Name,Portfolio Link
fw16_484,John Doe,https://johndoe.com
fw13_042,Jane Smith,https://janesmith.com`}
        </pre>
        <p className="text-xs text-purple-400 mt-2">
          Columns can be named: Id/ID/id, Name/name, Portfolio Link/URL/url
        </p>
        <p className="text-xs text-purple-400 mt-1">
          Supports both comma (,) and tab-separated values
        </p>
      </div>
    </div>
  );
}
