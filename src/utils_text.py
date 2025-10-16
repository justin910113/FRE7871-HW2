
import re
from dataclasses import dataclass
from typing import List, Tuple

WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)

def word_count(text: str) -> int:
    if not isinstance(text, str): return 0
    return max(1, len(WORD_RE.findall(text)))

def compile_vocab(words: List[str]):
    return [re.compile(re.escape(w.strip()), re.I) for w in words if w.strip()]

def count_weighted(text: str, pats, weight=1.0) -> float:
    if not isinstance(text, str) or not text.strip(): return 0.0
    return sum(weight * len(p.findall(text)) for p in pats)

@dataclass
class DictScorer:
    hawk_terms: List[str]
    dove_terms: List[str]
    hawk_weight: float = 1.0
    dove_weight: float = 1.0
    def __post_init__(self):
        self._hawk = compile_vocab(self.hawk_terms)
        self._dove = compile_vocab(self.dove_terms)
    def score_doc(self, text: str) -> Tuple[float, int]:
        wc = word_count(text)
        hawk = count_weighted(text, self._hawk, self.hawk_weight)
        dove = count_weighted(text, self._dove, self.dove_weight)
        return ((hawk - dove) / wc, wc)
