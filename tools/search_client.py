"""
PlanCraft Agent - Web Search Client

웹 검색 기능을 제공하는 모듈입니다.
Tavily API를 HTTP Request로 직접 호출하여 의존성을 최소화합니다.
"""

import os
import requests
from typing import List, Dict, Optional
from utils.config import Config

class SearchClient:
    """
    웹 검색 클라이언트 (Tavily API 기반)
    """
    
    def __init__(self):
        self.api_key = Config.TAVILY_API_KEY
        self.base_url = "https://api.tavily.com/search"
        
    def search(self, query: str, max_results: int = 3) -> str:
        """
        웹 검색을 수행하고 결과를 문자열로 반환합니다.
        
        Args:
            query: 검색어
            max_results: 최대 결과 수
            
        Returns:
            str: 마크다운 형식의 검색 결과 요약
        """
        if not self.api_key:
            return "[Web Search Skipped] TAVILY_API_KEY is not set."
            
        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": True,
                "max_results": max_results
            }
            
            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 답변이 있으면 우선 사용
            answer = data.get("answer", "")
            results = data.get("results", [])
            
            markdown_output = f"### 🔍 '{query}' 검색 결과\n\n"
            
            if answer:
                markdown_output += f"**AI 요약**: {answer}\n\n"
                
            markdown_output += "**상세 결과**:\n"
            for res in results:
                title = res.get("title", "No Title")
                url = res.get("url", "#")
                content = res.get("content", "")
                markdown_output += f"- **[{title}]({url})**: {content[:300]}...\n"
                
            return markdown_output
            
        except Exception as e:
            return f"[Web Search Failed] Error: {str(e)}"

# 전역 인스턴스
_search_client = None

def get_search_client() -> SearchClient:
    global _search_client
    if not _search_client:
        _search_client = SearchClient()
    return _search_client
