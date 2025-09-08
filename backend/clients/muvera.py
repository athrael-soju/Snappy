import logging
from typing import Optional, List

import numpy as np

from config import (
    MUVERA_ENABLED,
    MUVERA_K_SIM,
    MUVERA_DIM_PROJ,
    MUVERA_R_REPS,
    MUVERA_RANDOM_SEED,
)

logger = logging.getLogger(__name__)


class MuveraPostprocessor:
    """
    Thin wrapper around fastembed.postprocess.Muvera for transforming
    multi-vector embeddings (e.g., ColPali/ColBERT-style) into a single-vector
    Fixed Dimensional Encoding (FDE) for fast initial retrieval.
    """

    def __init__(self, input_dim: int):
        self.enabled = bool(MUVERA_ENABLED)
        self._muvera = None
        self._embedding_size: Optional[int] = None

        if not self.enabled:
            logger.info("MUVERA disabled via config; postprocessor will not be used")
            return

        try:
            # Lazy import to avoid dependency issues if disabled
            from fastembed.postprocess import Muvera as _Muvera

            self._muvera = _Muvera(
                dim=input_dim,
                k_sim=int(MUVERA_K_SIM),
                dim_proj=int(MUVERA_DIM_PROJ),
                r_reps=int(MUVERA_R_REPS),
                random_seed=int(MUVERA_RANDOM_SEED),
            )
            # Determine output dimension (fde size)
            self._embedding_size = int(self._muvera.embedding_size)
            logger.info(
                "Initialized MUVERA: input_dim=%s, k_sim=%s, dim_proj=%s, r_reps=%s, fde_dim=%s",
                input_dim,
                MUVERA_K_SIM,
                MUVERA_DIM_PROJ,
                MUVERA_R_REPS,
                self._embedding_size,
            )
        except Exception as e:
            logger.error("Failed to initialize MUVERA: %s", e)
            # Disable if initialization fails
            self.enabled = False
            self._muvera = None
            self._embedding_size = None

    @property
    def embedding_size(self) -> Optional[int]:
        return self._embedding_size

    def process_document(self, multivectors: List[List[float]]) -> Optional[List[float]]:
        """
        Compute document FDE from multi-vector embedding.
        multivectors: shape (n_tokens, dim)
        """
        if not self.enabled or self._muvera is None:
            logger.debug("MUVERA.process_document skipped (enabled=%s, has_impl=%s)", self.enabled, self._muvera is not None)
            return None
        if not multivectors:
            logger.debug("MUVERA.process_document received empty multivectors")
            return None
        arr = np.asarray(multivectors, dtype=np.float32)
        logger.debug("MUVERA.process_document input shape: %s", arr.shape)
        fde = self._muvera.process_document(arr)
        out = fde.astype(np.float32).tolist()
        logger.debug("MUVERA.process_document output length: %d", len(out))
        return out

    def process_query(self, multivectors: List[List[float]]) -> Optional[List[float]]:
        """
        Compute query FDE from multi-vector embedding.
        multivectors: shape (n_tokens, dim)
        """
        if not self.enabled or self._muvera is None:
            logger.debug("MUVERA.process_query skipped (enabled=%s, has_impl=%s)", self.enabled, self._muvera is not None)
            return None
        if not multivectors:
            logger.debug("MUVERA.process_query received empty multivectors")
            return None
        arr = np.asarray(multivectors, dtype=np.float32)
        logger.debug("MUVERA.process_query input shape: %s", arr.shape)
        fde = self._muvera.process_query(arr)
        out = fde.astype(np.float32).tolist()
        logger.debug("MUVERA.process_query output length: %d", len(out))
        return out
