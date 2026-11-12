"""Generalized Notation Notation track.

The project-owned parser (``gnn.parser``) and concordance checks
(``gnn.concordance``) are the public surface. Conformance tooling is imported
by module path: :mod:`gnn.upstream` holds the upstream checkout selection and
the parser-digest conformance support used by
``tests/test_gnn_upstream_conformance.py``. The pin itself
(``gnn/upstream.json``) is read and validated by the estate's shared reader,
``gnn.importers``, from the pinned release.
"""

from gnn.concordance import BERNOULLI_SYMBOL_MAP, concordance_holds, parity_gaps
from gnn.model import GnnConnection, GnnModel, GnnVariable
from gnn.parser import GNNParseError, parse_gnn, parse_gnn_file

__all__ = [
    "BERNOULLI_SYMBOL_MAP",
    "GNNParseError",
    "GnnConnection",
    "GnnModel",
    "GnnVariable",
    "concordance_holds",
    "parse_gnn",
    "parse_gnn_file",
    "parity_gaps",
]
