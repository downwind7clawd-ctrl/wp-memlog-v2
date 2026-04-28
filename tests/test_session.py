"""Tests for wp-memlog package"""
import pytest


def test_session_payload_creation():
    """Test SessionPayload creation"""
    from wp_memlog import SessionPayload
    
    payload = SessionPayload(
        agent="hermes",
        date="2026-04-28",
        content="Test content"
    )
    
    assert payload.agent == "hermes"
    assert payload.date == "2026-04-28"
    assert payload.content == "Test content"
    assert payload.idem_key  # UUID generated
    assert payload.category == "hermes"


def test_session_payload_title_default():
    """Test title auto-generation"""
    from wp_memlog import SessionPayload
    
    payload = SessionPayload(
        agent="macguffin",
        date="2026-04-28",
        content="Test"
    )
    
    assert payload.title == "[macguffin] 2026-04-28 세션"


def test_token_count_estimate():
    """Test token counting"""
    from wp_memlog import count_tokens
    
    text = "This is a test."
    count = count_tokens(text)
    
    assert count > 0
    assert isinstance(count, int)