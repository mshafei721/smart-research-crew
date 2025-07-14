import pytest
from pydantic import ValidationError
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models import ResearchRequest, ResearchSection, Report, HealthResponse, SettingsResponse

def test_research_request_model():
    # Valid data
    data = {
        "topic": "AI in Healthcare",
        "guidelines": "Focus on recent advancements.",
        "sections": "Introduction,Applications,Conclusion"
    }
    req = ResearchRequest(**data)
    assert req.topic == data["topic"]
    assert req.guidelines == data["guidelines"]
    assert req.sections == data["sections"]

    # Invalid data
    with pytest.raises(ValidationError):
        ResearchRequest(topic="AI", guidelines="", sections="") # topic too short, sections empty

def test_research_section_model():
    data = {
        "content": "This is a section about AI.",
        "sources": ["http://example.com/ai"]
    }
    section = ResearchSection(**data)
    assert section.content == data["content"]
    assert section.sources == data["sources"]

def test_report_model():
    section = ResearchSection(content="Content", sources=["source1"])
    data = {
        "topic": "AI Report",
        "sections": [section],
        "references": ["source1"]
    }
    report = Report(**data)
    assert report.topic == data["topic"]
    assert report.sections == data["sections"]
    assert report.references == data["references"]

def test_health_response_model():
    data = {
        "status": "healthy",
        "timestamp": "2025-07-15T10:00:00Z",
        "version": "1.0.0"
    }
    health = HealthResponse(**data)
    assert health.status == data["status"]
    assert health.timestamp == data["timestamp"]
    assert health.version == data["version"]

def test_settings_response_model():
    data = {
        "llm_model": "gpt-4",
        "max_concurrent_tasks": 10,
        "cache_enabled": True
    }
    settings = SettingsResponse(**data)
    assert settings.llm_model == data["llm_model"]
    assert settings.max_concurrent_tasks == data["max_concurrent_tasks"]
    assert settings.cache_enabled == data["cache_enabled"]
