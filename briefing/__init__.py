"""Public package surface for the research brief generator."""

from .core.agent import ResearchPipeline, build_default_pipeline, research_agent

__all__ = ["ResearchPipeline", "build_default_pipeline", "research_agent"]
