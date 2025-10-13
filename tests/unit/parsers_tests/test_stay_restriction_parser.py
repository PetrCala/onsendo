"""
Tests for the stay restriction parser.
"""

from src.lib.parsers.stay_restriction import parse_stay_restriction


class TestStayRestrictionParser:
    """Test cases for stay restriction parsing."""

    def test_parse_stay_restriction_none(self):
        """Test parsing None value."""
        result = parse_stay_restriction(None)
        assert result.raw is None
        assert result.normalized is None
        assert result.is_stay_restricted is False
        assert result.requires_inquiry is False
        assert result.notes == []

    def test_parse_stay_restriction_empty(self):
        """Test parsing empty string."""
        result = parse_stay_restriction("")
        assert result.raw == ""
        assert result.normalized == ""
        assert result.is_stay_restricted is False
        assert result.requires_inquiry is False
        assert result.notes == []

    def test_parse_stay_restriction_whitespace(self):
        """Test parsing whitespace-only string."""
        result = parse_stay_restriction("   \n\t  ")
        assert result.raw == "   \n\t  "
        assert result.normalized == ""
        assert result.is_stay_restricted is False
        assert result.requires_inquiry is False
        assert result.notes == []

    def test_parse_stay_restriction_basic(self):
        """Test parsing basic stay restriction text."""
        result = parse_stay_restriction("宿泊限定")
        assert result.raw == "宿泊限定"
        assert result.normalized == "宿泊限定"
        assert result.is_stay_restricted is True
        assert result.requires_inquiry is False
        assert "Stay-restricted onsen (宿泊限定)" in result.notes

    def test_parse_stay_restriction_variations(self):
        """Test parsing various stay restriction patterns."""
        patterns = [
            "宿泊者限定",
            "宿泊客限定",
            "宿泊者のみ",
            "宿泊客のみ",
            "宿泊者専用",
            "宿泊客専用",
            "宿泊者向け",
            "宿泊客向け",
        ]

        for pattern in patterns:
            result = parse_stay_restriction(pattern)
            assert result.is_stay_restricted is True, f"Failed for pattern: {pattern}"
            assert "Stay-restricted onsen (宿泊限定)" in result.notes

    def test_parse_stay_restriction_mixed_case(self):
        """Test parsing with mixed case and spacing."""
        result = parse_stay_restriction("  宿泊限定  ")
        assert result.raw == "  宿泊限定  "
        assert result.normalized == "宿泊限定"
        assert result.is_stay_restricted is True

    def test_parse_stay_restriction_with_context(self):
        """Test parsing stay restriction with additional context."""
        text = "温泉施設。宿泊限定。日帰り不可。"
        result = parse_stay_restriction(text)
        assert result.is_stay_restricted is True
        assert "Stay-restricted onsen (宿泊限定)" in result.notes
        assert "Day-trip access may be available (日帰り)" in result.notes

    def test_parse_stay_restriction_requires_inquiry(self):
        """Test parsing text that requires inquiry."""
        text = "宿泊限定。要確認。"
        result = parse_stay_restriction(text)
        assert result.is_stay_restricted is True
        assert result.requires_inquiry is True
        assert "Confirmation required (要確認)" in result.notes

    def test_parse_stay_restriction_ambiguous_patterns(self):
        """Test parsing ambiguous patterns that require inquiry."""
        ambiguous_patterns = [
            "要確認",
            "要問合せ",
            "要相談",
            "要予約",
            "事前確認",
            "事前問合せ",
            "事前相談",
        ]

        for pattern in ambiguous_patterns:
            result = parse_stay_restriction(pattern)
            assert result.requires_inquiry is True, f"Failed for pattern: {pattern}"

    def test_parse_stay_restriction_no_restriction(self):
        """Test parsing text with no stay restrictions."""
        text = "日帰り可能。一般開放。"
        result = parse_stay_restriction(text)
        assert result.is_stay_restricted is False
        assert result.requires_inquiry is False
        assert result.notes == []

    def test_parse_stay_restriction_complex_text(self):
        """Test parsing complex text with multiple patterns."""
        text = "温泉施設。宿泊者限定。日帰り不可。要予約。"
        result = parse_stay_restriction(text)
        assert result.is_stay_restricted is True
        assert result.requires_inquiry is True
        assert "Stay-restricted onsen (宿泊限定)" in result.notes
        assert "Limited to facility guests only" in result.notes
        assert "Reservation required (要予約)" in result.notes

    def test_parse_stay_restriction_normalization(self):
        """Test text normalization."""
        text = "  宿泊  限定  \n  "
        result = parse_stay_restriction(text)
        assert result.normalized == "宿泊 限定"
        assert result.is_stay_restricted is True
