"""
Unit tests for source quality scoring.
"""

import sys
import unittest
from pathlib import Path

src_path = str(Path(__file__).resolve().parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cognisynth.schemas.evidence import Source, SourceType, Document
from cognisynth.evidence.scorer import score_source, score_source_authority, score_extraction_quality


class TestSourceScoring(unittest.TestCase):
    def test_academic_authority(self):
        src_academic = Source(url="https://arxiv.org/abs/2301.0000", domain="arxiv.org", source_type=SourceType.ACADEMIC)
        doc = Document(source_id=src_academic.source_id, text="A" * 2000)

        score = score_source(src_academic, doc)
        self.assertGreaterEqual(score, 0.85)

    def test_general_web_scoring(self):
        src_blog = Source(url="https://some-random-blog.xyz/post", domain="some-random-blog.xyz", source_type=SourceType.BLOG)
        doc = Document(source_id=src_blog.source_id, text="Short text.")

        score = score_source(src_blog, doc)
        self.assertLess(score, 0.65)


if __name__ == "__main__":
    unittest.main()
