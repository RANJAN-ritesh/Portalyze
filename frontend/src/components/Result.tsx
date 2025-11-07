import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  ChevronDown,
  ChevronUp,
  CheckCircle,
  XCircle,
  AlertCircle,
  User,
  FolderKanban,
  Code2,
  Mail,
  Settings,
  Sparkles,
  Camera,
  BookOpen,
  Monitor,
  Tablet,
  Smartphone,
  Clock,
  Database,
  ExternalLink,
  RotateCcw,
  RefreshCw,
  Copy,
  Check
} from 'lucide-react';
import type { GradingResult } from '../services/api';
import type { LucideIcon } from 'lucide-react';

interface ResultProps {
  result: GradingResult;
  onRestart: () => void;
}

// Grouped checklist structure
type ChecklistKey = keyof GradingResult['checklist'];

interface ChecklistGroupItem {
  key: ChecklistKey;
  label: string;
  icon: LucideIcon;
}

const CHECKLIST_GROUPS: Record<string, ChecklistGroupItem[]> = {
  About: [
    { key: 'about_section', label: 'Has About Me section', icon: User },
    { key: 'about_name', label: 'Name included', icon: User },
    { key: 'about_photo', label: 'Photo included', icon: Camera },
    { key: 'about_intro', label: 'Catchy introduction', icon: Sparkles },
    { key: 'about_professional_photo', label: 'Professional photo', icon: Camera },
  ],
  Projects: [
    { key: 'projects_section', label: 'Has Projects section', icon: FolderKanban },
    { key: 'projects_minimum', label: 'Minimum 3 projects', icon: FolderKanban },
    { key: 'projects_samples', label: 'Has project samples', icon: FolderKanban },
    { key: 'projects_deployed', label: 'Projects deployed with links', icon: ExternalLink },
    { key: 'projects_links', label: 'Project links included', icon: ExternalLink },
    { key: 'projects_finished', label: 'Projects finished and working', icon: CheckCircle },
    { key: 'projects_summary', label: 'Project summary included', icon: BookOpen },
    { key: 'projects_hero_image', label: 'Project hero image', icon: Camera },
    { key: 'projects_tech_stack', label: 'Project tech stack listed', icon: Code2 },
  ],
  Skills: [
    { key: 'skills_section', label: 'Has Skills section', icon: Code2 },
    { key: 'skills_highlighted', label: 'Skills/tech stack highlighted', icon: Sparkles },
  ],
  Contact: [
    { key: 'contact_section', label: 'Has Contact section', icon: Mail },
    { key: 'contact_linkedin', label: 'LinkedIn included', icon: ExternalLink },
    { key: 'contact_github', label: 'GitHub included', icon: ExternalLink },
  ],
  Other: [
    { key: 'links_correct', label: 'All links are correct', icon: CheckCircle },
    { key: 'responsive_design', label: 'Responsive design', icon: Monitor },
    { key: 'professional_url', label: 'Professional portfolio URL', icon: ExternalLink },
    { key: 'grammar_checked', label: 'Grammar/spell checked', icon: CheckCircle },
    { key: 'single_page_navbar', label: 'Single page with navbar', icon: Settings },
    { key: 'no_design_issues', label: 'No design issues', icon: Sparkles },
    { key: 'external_links_new_tab', label: 'External links open in new tab', icon: ExternalLink },
  ],
};

const SECTION_ICONS: Record<string, LucideIcon> = {
  About: User,
  Projects: FolderKanban,
  Skills: Code2,
  Contact: Mail,
  Other: Settings,
};

interface AccordionSectionProps {
  title: string;
  items: ChecklistGroupItem[];
  checklist: GradingResult['checklist'];
  defaultOpen?: boolean;
}

function AccordionSection({ title, items, checklist, defaultOpen = false }: AccordionSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const Icon = SECTION_ICONS[title] || Settings;

  const passedItems = items.filter(item => checklist[item.key]?.pass).length;

  const totalItems = items.length;
  const allPassed = passedItems === totalItems;

  return (
    <div className="border border-gray-800 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 bg-gray-900 hover:bg-gray-800 transition-colors flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <Icon className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          <span className={`text-sm px-3 py-1 rounded-full ${
            allPassed
              ? 'bg-green-900/30 text-green-400'
              : 'bg-gray-800 text-gray-400'
          }`}>
            {passedItems}/{totalItems}
          </span>
        </div>
        {isOpen ? (
          <ChevronUp className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        )}
      </button>

      {isOpen && (
        <div className="px-6 py-4 bg-gray-900/50 border-t border-gray-800">
          <div className="space-y-2">
            {items.map(({ key, label }) => {
              const checkItem = checklist[key];
              const passed = checkItem?.pass ?? false;
              const details = checkItem?.details ?? [];

              return (
                <div key={key} className="flex items-start gap-3 p-3 bg-gray-800 rounded-lg">
                  <div className="flex-shrink-0 mt-0.5">
                    {passed ? (
                      <CheckCircle className="w-5 h-5 text-green-400" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white">{label}</p>
                    {details.length > 0 && (
                      <div className="mt-1 space-y-1">
                        {details.map((detail: string, idx: number) => (
                          <p key={idx} className="text-xs text-gray-400">
                            {detail}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function getScoreColor(score: number) {
  if (score >= 80) return 'text-green-400';
  if (score >= 60) return 'text-yellow-400';
  return 'text-red-400';
}

export default function Result({ result, onRestart }: ResultProps) {
  const [copied, setCopied] = useState(false);

  if (!result || !result.checklist) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950 p-4">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <p className="text-gray-400">No results to display.</p>
        </div>
      </div>
    );
  }

  const totalChecks = Object.keys(result.checklist).length;
  const passedChecks = Object.values(result.checklist).filter(item => item?.pass).length;

  const handleCopyFeedback = async () => {
    try {
      await navigator.clipboard.writeText(result.ai_analysis);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err: unknown) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 py-8 px-4">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header with Score */}
        <div className="bg-gray-900 rounded-2xl shadow-xl p-8 border border-gray-800">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                Portfolio Analysis Complete
              </h1>
              <p className="text-gray-400">
                <a
                  href={result.portfolio_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-purple-400 hover:underline inline-flex items-center gap-1"
                >
                  {result.portfolio_url}
                  <ExternalLink className="w-4 h-4" />
                </a>
              </p>
            </div>
            <button
              onClick={onRestart}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors flex items-center gap-2"
            >
              <RotateCcw className="w-5 h-5" />
              Grade Another
            </button>
          </div>

          {/* Score Display */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-6 bg-purple-900/20 border border-purple-800 rounded-xl">
              <div className="text-sm font-medium text-gray-400 mb-2">Overall Score</div>
              <div className={`text-5xl font-bold ${getScoreColor(result.score)}`}>
                {result.score}%
              </div>
            </div>
            <div className="text-center p-6 bg-gray-800 border border-gray-700 rounded-xl">
              <div className="text-sm font-medium text-gray-400 mb-2">Checks Passed</div>
              <div className="text-5xl font-bold text-white">
                {passedChecks}/{totalChecks}
              </div>
            </div>
            <div className="text-center p-6 bg-gray-800 border border-gray-700 rounded-xl">
              <div className="text-sm font-medium text-gray-400 mb-2">Analysis Time</div>
              <div className="text-5xl font-bold text-white flex items-center justify-center gap-2">
                <Clock className="w-10 h-10" />
                {result.analysis_time.toFixed(1)}s
              </div>
            </div>
          </div>

          {/* Metadata */}
          <div className="mt-6 flex flex-wrap items-center gap-4 text-sm">
            <div className="flex items-center gap-2 text-gray-400">
              <Sparkles className="w-4 h-4" />
              <span>AI Provider: {result.ai_provider}</span>
            </div>
            {result.from_cache && (
              <div className="flex items-center gap-2 px-3 py-1 bg-yellow-900/30 border border-yellow-800 rounded-full text-yellow-400">
                <Database className="w-4 h-4" />
                <span className="font-medium">Cached Result</span>
              </div>
            )}
            {!result.from_cache && (
              <div className="flex items-center gap-2 px-3 py-1 bg-green-900/30 border border-green-800 rounded-full text-green-400">
                <RefreshCw className="w-4 h-4" />
                <span className="font-medium">Fresh Analysis</span>
              </div>
            )}
          </div>
        </div>

        {/* Professional Photo Analysis */}
        {result.professional_photo && (
          <div className="bg-gray-900 rounded-xl shadow p-6 border border-gray-800">
            <div className="flex items-center gap-3 mb-4">
              <Camera className="w-6 h-6 text-purple-400" />
              <h2 className="text-xl font-bold text-white">
                Professional Photo Analysis
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                {result.professional_photo.exists ? (
                  <CheckCircle className="w-5 h-5 text-green-400" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-400" />
                )}
                <span className="text-gray-300">
                  Photo {result.professional_photo.exists ? 'Found' : 'Not Found'}
                </span>
              </div>
              {result.professional_photo.exists && (
                <>
                  <div className="flex items-center gap-2">
                    {result.professional_photo.has_face ? (
                      <CheckCircle className="w-5 h-5 text-green-400" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-400" />
                    )}
                    <span className="text-gray-300">
                      Face {result.professional_photo.has_face ? 'Detected' : 'Not Detected'}
                    </span>
                  </div>
                  {result.professional_photo.confidence !== null && (
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-purple-400" />
                      <span className="text-gray-300">
                        Confidence: {(result.professional_photo.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                  <div className="flex items-center gap-2">
                    {result.professional_photo.is_professional ? (
                      <CheckCircle className="w-5 h-5 text-green-400" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-yellow-400" />
                    )}
                    <span className="text-gray-300">
                      {result.professional_photo.is_professional ? 'Looks Professional' : 'Could Be More Professional'}
                    </span>
                  </div>
                </>
              )}
            </div>
            <p className="mt-4 text-sm text-gray-400">
              {result.professional_photo.details}
            </p>
          </div>
        )}

        {/* Responsive Design Check */}
        {result.responsive_check && (
          <div className="bg-gray-900 rounded-xl shadow p-6 border border-gray-800">
            <div className="flex items-center gap-3 mb-4">
              <Monitor className="w-6 h-6 text-purple-400" />
              <h2 className="text-xl font-bold text-white">
                Responsive Design Check
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {result.responsive_check.mobile && (
                <div className="flex items-center gap-3 p-4 bg-gray-800 border border-gray-700 rounded-lg">
                  <Smartphone className="w-8 h-8 text-purple-400" />
                  <div>
                    <div className="font-medium text-white">Mobile</div>
                    <div className="flex items-center gap-1 text-sm">
                      {result.responsive_check.mobile.passes ? (
                        <>
                          <CheckCircle className="w-4 h-4 text-green-400" />
                          <span className="text-green-400">Passes</span>
                        </>
                      ) : (
                        <>
                          <XCircle className="w-4 h-4 text-red-400" />
                          <span className="text-red-400">Fails</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )}
              {result.responsive_check.tablet && (
                <div className="flex items-center gap-3 p-4 bg-gray-800 border border-gray-700 rounded-lg">
                  <Tablet className="w-8 h-8 text-purple-400" />
                  <div>
                    <div className="font-medium text-white">Tablet</div>
                    <div className="flex items-center gap-1 text-sm">
                      {result.responsive_check.tablet.passes ? (
                        <>
                          <CheckCircle className="w-4 h-4 text-green-400" />
                          <span className="text-green-400">Passes</span>
                        </>
                      ) : (
                        <>
                          <XCircle className="w-4 h-4 text-red-400" />
                          <span className="text-red-400">Fails</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )}
              {result.responsive_check.desktop && (
                <div className="flex items-center gap-3 p-4 bg-gray-800 border border-gray-700 rounded-lg">
                  <Monitor className="w-8 h-8 text-purple-400" />
                  <div>
                    <div className="font-medium text-white">Desktop</div>
                    <div className="flex items-center gap-1 text-sm">
                      {result.responsive_check.desktop.passes ? (
                        <>
                          <CheckCircle className="w-4 h-4 text-green-400" />
                          <span className="text-green-400">Passes</span>
                        </>
                      ) : (
                        <>
                          <XCircle className="w-4 h-4 text-red-400" />
                          <span className="text-red-400">Fails</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Checklist Accordion */}
        <div className="bg-gray-900 rounded-xl shadow p-6 border border-gray-800">
          <h2 className="text-2xl font-bold text-white mb-6">
            Detailed Checklist
          </h2>
          <div className="space-y-3">
            {Object.entries(CHECKLIST_GROUPS).map(([section, items], index) => (
              <AccordionSection
                key={section}
                title={section}
                items={items}
                checklist={result.checklist}
                defaultOpen={index === 0}
              />
            ))}
          </div>
        </div>

        {/* AI Analysis */}
        <div className="bg-purple-900/20 rounded-xl shadow p-6 border border-purple-800">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Sparkles className="w-6 h-6 text-purple-400" />
              <h2 className="text-2xl font-bold text-white">
                AI-Powered Feedback
              </h2>
            </div>
            <button
              onClick={handleCopyFeedback}
              className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors border border-gray-700"
              title="Copy feedback to clipboard"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 text-green-400" />
                  <span className="text-sm text-green-400">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  <span className="text-sm">Copy</span>
                </>
              )}
            </button>
          </div>
          <div className="prose prose-sm prose-invert max-w-none markdown-content">
            <ReactMarkdown
              className="text-gray-300 leading-relaxed"
              components={{
                h2: ({ node, ...props }) => {
                  void node;
                  return <h2 className="text-xl font-bold text-purple-300 mt-6 mb-3" {...props} />;
                },
                h3: ({ node, ...props }) => {
                  void node;
                  return <h3 className="text-lg font-semibold text-purple-400 mt-4 mb-2" {...props} />;
                },
                p: ({ node, ...props }) => {
                  void node;
                  return <p className="mb-3 text-gray-300" {...props} />;
                },
                ul: ({ node, ...props }) => {
                  void node;
                  return <ul className="list-disc list-inside mb-3 space-y-1" {...props} />;
                },
                ol: ({ node, ...props }) => {
                  void node;
                  return <ol className="list-decimal list-inside mb-3 space-y-1" {...props} />;
                },
                li: ({ node, ...props }) => {
                  void node;
                  return <li className="text-gray-300" {...props} />;
                },
                strong: ({ node, ...props }) => {
                  void node;
                  return <strong className="font-semibold text-white" {...props} />;
                },
                code: ({ node, ...props }) => {
                  void node;
                  return <code className="bg-gray-800 px-1 py-0.5 rounded text-purple-300 text-sm" {...props} />;
                },
              }}
            >
              {result.ai_analysis}
            </ReactMarkdown>
          </div>
        </div>

        {/* Learning Resources */}
        {result.learning_resources && result.learning_resources.length > 0 && (
          <div className="bg-gray-900 rounded-xl shadow p-6 border border-gray-800">
            <div className="flex items-center gap-3 mb-6">
              <BookOpen className="w-6 h-6 text-purple-400" />
              <h2 className="text-2xl font-bold text-white">
                Learning Resources
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {result.learning_resources.map((resource, index) => (
                <div key={index} className="border border-gray-800 rounded-lg p-5 bg-gray-800/50">
                  <h3 className="text-lg font-semibold text-white mb-2">
                    {resource.title}
                  </h3>
                  <p className="text-sm text-gray-400 mb-3">
                    {resource.description}
                  </p>
                  {resource.tips && resource.tips.length > 0 && (
                    <ul className="space-y-1">
                      {resource.tips.map((tip, tipIndex) => (
                        <li key={tipIndex} className="flex items-start gap-2 text-sm text-gray-300">
                          <CheckCircle className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
                          <span>{tip}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Share Button (if available) */}
        {result.share_url && (
          <div className="bg-blue-900/20 border border-blue-800 rounded-xl p-6 text-center">
            <p className="text-gray-300 mb-3">
              Share your portfolio analysis results:
            </p>
            <a
              href={result.share_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <ExternalLink className="w-5 h-5" />
              View Shareable Link
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
