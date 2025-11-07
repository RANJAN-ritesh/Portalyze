import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import hashlib

class PortfolioCache:
    def __init__(self, cache_file: str = "portfolio_analysis_cache.json"):
        self.cache_file = cache_file
        self.cache: Dict[str, Any] = self._load_cache()
        
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from file or create new if doesn't exist."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"portfolios": {}, "analysis_patterns": {}}
        return {"portfolios": {}, "analysis_patterns": {}}
    
    def _save_cache(self):
        """Save cache to file."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def _generate_portfolio_id(self, github_url: str, deployed_url: str) -> str:
        """Generate unique ID for portfolio."""
        combined = f"{github_url}|{deployed_url}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get_portfolio_analysis(self, github_url: str, deployed_url: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis for portfolio if exists and not expired."""
        portfolio_id = self._generate_portfolio_id(github_url, deployed_url)
        portfolio_data = self.cache["portfolios"].get(portfolio_id)
        
        if portfolio_data:
            # Check if cache is expired (older than 24 hours)
            last_updated = datetime.fromisoformat(portfolio_data["last_updated"])
            if (datetime.now() - last_updated).days < 1:
                return portfolio_data["analysis"]
        return None
    
    def save_portfolio_analysis(self, github_url: str, deployed_url: str, analysis: Dict[str, Any]):
        """Save portfolio analysis to cache."""
        portfolio_id = self._generate_portfolio_id(github_url, deployed_url)
        self.cache["portfolios"][portfolio_id] = {
            "github_url": github_url,
            "deployed_url": deployed_url,
            "analysis": analysis,
            "last_updated": datetime.now().isoformat()
        }
        self._save_cache()
    
    def update_analysis_patterns(self, patterns: Dict[str, Any]):
        """Update common patterns found across portfolios."""
        self.cache["analysis_patterns"].update(patterns)
        self._save_cache()
    
    def get_analysis_patterns(self) -> Dict[str, Any]:
        """Get common patterns found across portfolios."""
        return self.cache["analysis_patterns"]
    
    def get_all_portfolios(self) -> List[Dict[str, Any]]:
        """Get all cached portfolio analyses."""
        return list(self.cache["portfolios"].values()) 