"""Utility functions for the Smart Research Crew backend."""


def ask(prompt: str) -> str:
    """Helper function for CLI input."""
    return input(prompt).strip()
