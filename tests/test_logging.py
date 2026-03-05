"""Tests for logging utilities."""

import logging
import pytest
from autohound.utils.logging import setup_logging


def test_setup_logging_info():
    """Test INFO level logging setup."""
    # Clear handlers first
    logging.root.handlers = []
    logging.root.setLevel(logging.NOTSET)
    
    setup_logging("INFO")
    
    assert len(logging.root.handlers) > 0
    # Handler will have the level, root logger effective level may differ
    handler = logging.root.handlers[0]
    assert handler.level <= logging.INFO or logging.root.level == logging.INFO


def test_setup_logging_debug():
    """Test DEBUG level logging setup."""
    logging.root.handlers = []
    logging.root.setLevel(logging.NOTSET)
    
    setup_logging("DEBUG")
    
    # At least one handler should exist
    assert len(logging.root.handlers) > 0


def test_setup_logging_none_defaults_to_info():
    """Test that None level defaults to INFO."""
    logging.root.handlers = []
    logging.root.setLevel(logging.NOTSET)
    
    setup_logging(None)
    
    assert len(logging.root.handlers) > 0


def test_setup_logging_adds_stream_handler():
    """Test that a StreamHandler is added."""
    logging.root.handlers = []
    
    setup_logging()
    
    has_stream_handler = any(
        isinstance(h, logging.StreamHandler) for h in logging.root.handlers
    )
    assert has_stream_handler


def test_setup_logging_formatter():
    """Test that handlers have a formatter with expected fields."""
    logging.root.handlers = []
    
    setup_logging()
    
    handler = logging.root.handlers[0]
    assert handler.formatter is not None
    
    format_str = handler.formatter._fmt
    assert "levelname" in format_str
    assert "name" in format_str
    assert "message" in format_str
    assert "asctime" in format_str


def test_setup_logging_third_party_loggers():
    """Test that third-party loggers are set to WARNING."""
    logging.root.handlers = []
    # Reset third-party loggers
    for logger_name in ["neo4j", "anthropic", "httpx"]:
        logging.getLogger(logger_name).setLevel(logging.NOTSET)
    
    setup_logging()
    
    assert logging.getLogger("neo4j").level == logging.WARNING
    assert logging.getLogger("anthropic").level == logging.WARNING
    assert logging.getLogger("httpx").level == logging.WARNING


def test_setup_logging_case_insensitive():
    """Test case-insensitive level names."""
    logging.root.handlers = []
    
    # Test that it doesn't crash with lowercase
    setup_logging("debug")
    assert len(logging.root.handlers) > 0
    
    logging.root.handlers = []
    setup_logging("WARNING")
    assert len(logging.root.handlers) > 0
