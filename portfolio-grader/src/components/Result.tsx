import React from 'react';
import { CheckCircle, XCircle, Info } from 'lucide-react';

// Grouped checklist structure
const CHECKLIST_GROUPS: { [section: string]: { key: string; label: string }[] } = {
  About: [
    { key: 'about_section', label: 'Has About Me section' },
    { key: 'about_name', label: 'Name included' },
    { key: 'about_photo', label: 'Photo included' },
    { key: 'about_intro', label: 'Catchy introduction' },
    { key: 'about_professional_photo', label: 'Professional photo' },
  ],
  Projects: [
    { key: 'projects_section', label: 'Has Projects section' },
    { key: 'projects_minimum', label: 'Minimum 3 projects' },
    { key: 'projects_samples', label: 'Has project samples' },
    { key: 'projects_deployed', label: 'Projects deployed with links' },
    { key: 'projects_links', label: 'Project links included' },
    { key: 'projects_finished', label: 'Projects finished and working' },
    { key: 'projects_summary', label: 'Project summary included' },
    { key: 'projects_hero_image', label: 'Project hero image' },
    { key: 'projects_tech_stack', label: 'Project tech stack listed' },
  ],
  Skills: [
    { key: 'skills_section', label: 'Has Skills section' },
    { key: 'skills_highlighted', label: 'Skills/tech stack highlighted' },
  ],
  Contact: [
    { key: 'contact_section', label: 'Has Contact section' },
    { key: 'contact_linkedin', label: 'LinkedIn included' },
    { key: 'contact_github', label: 'GitHub included' },
  ],
  Other: [
    { key: 'links_correct', label: 'All links are correct' },
    { key: 'responsive_design', label: 'Responsive design' },
    { key: 'professional_url', label: 'Professional portfolio URL' },
    { key: 'grammar_checked', label: 'Grammar/spell checked' },
    { key: 'single_page_navbar', label: 'Single page with navbar' },
    { key: 'no_design_issues', label: 'No design issues' },
    { key: 'external_links_new_tab', label: 'External links open in new tab' },
  ],
};

type Checklist = { [key: string]: boolean };

interface ResultProps {
  result: { checklist: Checklist };
  onRestart: () => void;
}

function getSummary(checklist: Checklist) {
  const total = Object.keys(checklist).length;
  const passed = Object.values(checklist).filter(Boolean).length;
  if (passed === total) return { status: 'success', text: 'Excellent! All requirements met.' };
  if (passed > total * 0.8) return { status: 'info', text: 'Great job! Most requirements met.' };
  if (passed > total * 0.5) return { status: 'warning', text: 'Some improvements needed.' };
  return { status: 'danger', text: 'Significant improvements needed.' };
}

const BANNER_STYLES: any = {
  success: 'bg-green-100 text-green-800 border-green-300',
  info: 'bg-blue-100 text-blue-800 border-blue-300',
  warning: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  danger: 'bg-red-100 text-red-800 border-red-300',
};

export default function Result({ result, onRestart }: ResultProps) {
  if (!result || !result.checklist) return <div>No results to display.</div>;
  const summary = getSummary(result.checklist);

  return (
    <div className="rounded-lg bg-background p-6 shadow-md w-full max-w-6xl mx-auto mt-8">
      <div className={`border-l-4 p-4 mb-6 rounded ${BANNER_STYLES[summary.status]}`}>
        <div className="flex items-center gap-2">
          <Info className="w-5 h-5" />
          <span className="font-semibold">{summary.text}</span>
        </div>
      </div>
      <h2 className="text-2xl font-bold mb-4 text-center">Portfolio Checklist</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {Object.entries(CHECKLIST_GROUPS).map(([section, items]) => (
          <div key={section} className="bg-white dark:bg-zinc-900 rounded-xl shadow border border-zinc-200 dark:border-zinc-700 p-4 flex flex-col min-h-[350px]">
            <h3 className="text-lg font-semibold mb-4 text-center border-b border-zinc-100 dark:border-zinc-800 pb-2">{section}</h3>
            <div className="flex-1 flex flex-col gap-3 justify-start">
              {items.map(({ key, label }) => (
                <div key={key} className="flex items-center gap-2 border rounded px-2 py-2 bg-zinc-50 dark:bg-zinc-800 border-zinc-100 dark:border-zinc-700 min-h-[40px]">
                  {result.checklist[key] ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-500" />
                  )}
                  <span className="font-medium text-sm">{label}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      {/* Suggestions Section */}
      <div className="mt-8 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-zinc-800 dark:to-zinc-900 rounded-xl shadow border border-blue-200 dark:border-zinc-700 p-6">
        <h2 className="text-xl font-bold mb-3 text-blue-800 dark:text-blue-200">Suggestions to Improve your Portfolio</h2>
        {(() => {
          // Group keys by section
          const sectionMap: { [section: string]: string[] } = {
            About: [
              'about_section', 'about_name', 'about_photo', 'about_intro', 'about_professional_photo'
            ],
            Projects: [
              'projects_section', 'projects_minimum', 'projects_samples', 'projects_deployed', 'projects_links', 'projects_finished', 'projects_summary', 'projects_hero_image', 'projects_tech_stack'
            ],
            Skills: [
              'skills_section', 'skills_highlighted'
            ],
            Contact: [
              'contact_section', 'contact_linkedin', 'contact_github'
            ],
            Technical: [
              'links_correct', 'responsive_design', 'professional_url', 'grammar_checked', 'single_page_navbar', 'no_design_issues', 'external_links_new_tab'
            ]
          };
          const checklist = result.checklist;
          const sectionSuggestions: { [section: string]: string[] } = {};
          Object.entries(sectionMap).forEach(([section, keys]) => {
            sectionSuggestions[section] = [];
            keys.forEach((key) => {
              const item = checklist[key];
              if (item && !(item === true || item.pass)) {
                if (item.details && item.details.length > 0) {
                  sectionSuggestions[section].push(item.details[0]);
                } else if (key === 'projects_minimum') sectionSuggestions[section].push('Add at least 3 projects.');
                else if (key === 'projects_hero_image') sectionSuggestions[section].push('Add a hero image or screenshot for your projects.');
                else if (key === 'projects_links') sectionSuggestions[section].push('Add GitHub repository links for your projects.');
                else if (key === 'projects_deployed') sectionSuggestions[section].push('Add deployed/live links for your projects.');
                else if (key === 'about_name') sectionSuggestions[section].push('Add your name to the About section.');
                else if (key === 'about_intro') sectionSuggestions[section].push('Add a short introduction in the About section.');
                else if (key === 'responsive_design') sectionSuggestions[section].push('Make your portfolio responsive for all devices.');
                else if (key === 'skills_highlighted') sectionSuggestions[section].push('Highlight your key skills and tech stack.');
                else if (key === 'contact_linkedin') sectionSuggestions[section].push('Add your LinkedIn link.');
                else if (key === 'contact_github') sectionSuggestions[section].push('Add your GitHub link.');
                else if (key === 'contact_section') sectionSuggestions[section].push('Add a Contact section.');
                else if (key === 'skills_section') sectionSuggestions[section].push('Add a Skills section.');
                else if (key === 'about_photo') sectionSuggestions[section].push('Add a professional photo.');
                else if (key === 'about_professional_photo') sectionSuggestions[section].push('Ensure your photo looks professional.');
                else if (key === 'projects_samples') sectionSuggestions[section].push('Add project samples.');
                else if (key === 'projects_summary') sectionSuggestions[section].push('Add a summary for each project.');
                else if (key === 'projects_finished') sectionSuggestions[section].push('Ensure your projects are finished and working.');
                else if (key === 'projects_tech_stack') sectionSuggestions[section].push('List the tech stack for each project.');
                else if (key === 'projects_section') sectionSuggestions[section].push('Add a Projects section.');
                else if (key === 'about_section') sectionSuggestions[section].push('Add an About section.');
                // For technical, only add actionable ones
                else if (key === 'links_correct') sectionSuggestions[section].push('Check that all links are correct.');
                else if (key === 'external_links_new_tab') sectionSuggestions[section].push('Make sure external links open in a new tab.');
                else if (key === 'no_design_issues') sectionSuggestions[section].push('Fix any design issues.');
                else if (key === 'single_page_navbar') sectionSuggestions[section].push('Add a single page navbar.');
                else if (key === 'grammar_checked') sectionSuggestions[section].push('Check your grammar and spelling.');
                else if (key === 'professional_url') sectionSuggestions[section].push('Use a professional portfolio URL.');
              }
            });
          });
          const paragraphParts: string[] = [];
          if (Object.values(sectionSuggestions).every(arr => arr.length === 0)) {
            return <p className="text-base text-zinc-700 dark:text-zinc-200">Your portfolio meets all the key requirements. Great job!</p>;
          }
          if (sectionSuggestions['About'].length > 0) {
            paragraphParts.push(`In the About section, ${sectionSuggestions['About'].join(' ')}`);
          }
          if (sectionSuggestions['Projects'].length > 0) {
            paragraphParts.push(`For your projects, ${sectionSuggestions['Projects'].join(' ')}`);
          }
          if (sectionSuggestions['Skills'].length > 0) {
            paragraphParts.push(`In the Skills section, ${sectionSuggestions['Skills'].join(' ')}`);
          }
          if (sectionSuggestions['Contact'].length > 0) {
            paragraphParts.push(`For Contact, ${sectionSuggestions['Contact'].join(' ')}`);
          }
          if (sectionSuggestions['Technical'].length > 0) {
            paragraphParts.push(`Additionally, ${sectionSuggestions['Technical'].join(' ')}`);
          }
          return <p className="text-base text-zinc-700 dark:text-zinc-200">{paragraphParts.join(' ')}</p>;
        })()}
      </div>
      <div className="flex justify-center mt-8">
        <button
          onClick={onRestart}
          className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors shadow"
        >
          Grade Another Portfolio
        </button>
      </div>
    </div>
  );
} 