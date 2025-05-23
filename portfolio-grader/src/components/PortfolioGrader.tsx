import { useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { CheckCircle2, XCircle, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChecklistItem {
  pass: boolean;
  details: string[];
}

interface Checklist {
  about_section: ChecklistItem;
  about_name: ChecklistItem;
  about_photo: ChecklistItem;
  about_intro: ChecklistItem;
  about_professional_photo: ChecklistItem;
  projects_section: ChecklistItem;
  projects_samples: ChecklistItem;
  projects_deployed: ChecklistItem;
  projects_links: ChecklistItem;
  projects_finished: ChecklistItem;
  projects_summary: ChecklistItem;
  projects_hero_image: ChecklistItem;
  projects_tech_stack: ChecklistItem;
  skills_section: ChecklistItem;
  skills_highlighted: ChecklistItem;
  contact_section: ChecklistItem;
  contact_linkedin: ChecklistItem;
  contact_github: ChecklistItem;
  links_correct: ChecklistItem;
  responsive_design: ChecklistItem;
  professional_url: ChecklistItem;
  grammar_checked: ChecklistItem;
  single_page_navbar: ChecklistItem;
  no_design_issues: ChecklistItem;
  external_links_new_tab: ChecklistItem;
  projects_minimum: ChecklistItem;
}

interface GradingResult {
  checklist: Checklist;
  mode: string;
}

const sectionGroups = {
  "About Section": [
    "about_section",
    "about_name",
    "about_photo",
    "about_intro",
    "about_professional_photo",
  ],
  "Projects": [
    "projects_section",
    "projects_minimum",
    "projects_samples",
    "projects_deployed",
    "projects_links",
    "projects_finished",
    "projects_summary",
    "projects_hero_image",
    "projects_tech_stack",
  ],
  "Skills": [
    "skills_section",
    "skills_highlighted",
  ],
  "Contact": [
    "contact_section",
    "contact_linkedin",
    "contact_github",
  ],
  "Technical": [
    "links_correct",
    "responsive_design",
    "professional_url",
    "grammar_checked",
    "single_page_navbar",
    "no_design_issues",
    "external_links_new_tab",
  ],
};

const formatKey = (key: string) => {
  return key
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

export function PortfolioGrader() {
  const [repoUrl, setRepoUrl] = useState("");
  const [result, setResult] = useState<GradingResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  const toggleItem = (key: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedItems(newExpanded);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setExpandedItems(new Set());

    try {
      const response = await fetch("http://localhost:8000/grade", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ repoUrl }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to grade portfolio");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6 text-center">Portfolio Grader</h1>
      
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="flex gap-2">
          <Input
            type="text"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="Enter GitHub repository URL"
            className="flex-1"
          />
          <Button type="submit" disabled={loading}>
            {loading ? "Grading..." : "Grade Portfolio"}
          </Button>
        </div>
      </form>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-6">
          <div className="text-center">
            <span className="inline-block px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              {result.mode === "react" ? "React/SPA Portfolio" : "Static HTML Portfolio"}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Object.entries(sectionGroups).map(([sectionName, items]) => (
              <div key={sectionName} className="bg-white dark:bg-zinc-900 rounded-xl shadow border border-zinc-200 dark:border-zinc-700 p-4 flex flex-col min-h-[350px]">
                <h2 className="text-lg font-semibold mb-4 text-center border-b border-zinc-100 dark:border-zinc-800 pb-2">{sectionName}</h2>
                <div className="flex-1 flex flex-col gap-3 justify-between">
                  {items.map((key) => {
                    const item = result.checklist[key as keyof Checklist];
                    return (
                      <div key={key} className="flex items-center gap-2 border rounded px-2 py-1 bg-zinc-50 dark:bg-zinc-800 border-zinc-100 dark:border-zinc-700">
                        {item.pass ? (
                          <CheckCircle2 className="h-5 w-5 text-green-500" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-500" />
                        )}
                        <span className="font-medium text-sm">{formatKey(key)}</span>
                        {item.details && item.details.length > 0 && (
                          <span className="ml-2 text-xs text-zinc-500">{item.details[0]}</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
          {/* Suggestions Section */}
          <div className="mt-8 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-zinc-800 dark:to-zinc-900 rounded-xl shadow border border-blue-200 dark:border-zinc-700 p-6">
            <h2 className="text-xl font-bold mb-3 text-blue-800 dark:text-blue-200">AI Suggestions</h2>
            <ul className="list-disc pl-6 space-y-2 text-base text-zinc-700 dark:text-zinc-200">
              {Object.entries(result.checklist).map(([key, item]) => {
                if (item.pass) return null;
                // Custom suggestions for key fails
                if (key === "projects_minimum") return <li key={key}>Add at least 3 projects to your portfolio to meet the minimum requirement.</li>;
                if (key === "projects_hero_image") return <li key={key}>Add a hero image or screenshot for each project to make them visually appealing.</li>;
                if (key === "projects_links") return <li key={key}>Include GitHub repository links for each project.</li>;
                if (key === "projects_deployed") return <li key={key}>Add deployed/live links for your projects if available.</li>;
                if (key === "about_name") return <li key={key}>Make sure your name is clearly visible in the About section.</li>;
                if (key === "about_intro") return <li key={key}>Add a short, catchy introduction about yourself in the About section.</li>;
                if (key === "responsive_design") return <li key={key}>Make your portfolio responsive for all devices using CSS media queries or frameworks.</li>;
                if (key === "skills_highlighted") return <li key={key}>Highlight your key skills and tech stack with badges or icons.</li>;
                // Generic fallback
                return <li key={key}>Improve: {formatKey(key).replace(/_/g, ' ')}. {item.details && item.details[0]}</li>;
              })}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
} 