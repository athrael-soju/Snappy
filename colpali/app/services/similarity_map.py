"""Similarity map generation service for interpretability visualization."""

import base64
import io
import logging
import re
from functools import lru_cache
from typing import List, Optional, Tuple

import numpy as np
import torch
from PIL import Image

from app.models.schemas import SimilarityMapResult, TokenInfo
from app.services.model_service import model_service

logger = logging.getLogger(__name__)

# Viridis colormap values (256 colors, RGB)
# Pre-computed to avoid matplotlib dependency
VIRIDIS_COLORS = np.array([
    [68, 1, 84], [68, 2, 86], [69, 4, 87], [69, 5, 89], [70, 7, 90],
    [70, 8, 92], [70, 10, 93], [70, 11, 94], [71, 13, 96], [71, 14, 97],
    [71, 16, 99], [71, 17, 100], [71, 19, 101], [72, 20, 103], [72, 22, 104],
    [72, 23, 105], [72, 24, 106], [72, 26, 108], [72, 27, 109], [72, 28, 110],
    [72, 29, 111], [72, 31, 112], [72, 32, 113], [72, 33, 115], [72, 35, 116],
    [72, 36, 117], [72, 37, 118], [72, 38, 119], [72, 40, 120], [72, 41, 121],
    [71, 42, 122], [71, 44, 122], [71, 45, 123], [71, 46, 124], [71, 47, 125],
    [70, 48, 126], [70, 50, 126], [70, 51, 127], [69, 52, 128], [69, 53, 129],
    [69, 55, 129], [68, 56, 130], [68, 57, 131], [68, 58, 131], [67, 60, 132],
    [67, 61, 132], [66, 62, 133], [66, 63, 133], [66, 64, 134], [65, 66, 134],
    [65, 67, 135], [64, 68, 135], [64, 69, 136], [63, 71, 136], [63, 72, 137],
    [62, 73, 137], [62, 74, 137], [62, 76, 138], [61, 77, 138], [61, 78, 138],
    [60, 79, 139], [60, 80, 139], [59, 82, 139], [59, 83, 140], [58, 84, 140],
    [58, 85, 140], [57, 86, 141], [57, 88, 141], [56, 89, 141], [56, 90, 141],
    [55, 91, 142], [55, 92, 142], [54, 93, 142], [54, 95, 142], [53, 96, 142],
    [53, 97, 143], [52, 98, 143], [52, 99, 143], [51, 100, 143], [51, 101, 143],
    [50, 103, 143], [50, 104, 144], [49, 105, 144], [49, 106, 144], [49, 107, 144],
    [48, 108, 144], [48, 109, 144], [47, 110, 144], [47, 111, 144], [46, 112, 144],
    [46, 113, 145], [46, 114, 145], [45, 115, 145], [45, 116, 145], [44, 117, 145],
    [44, 118, 145], [44, 119, 145], [43, 120, 145], [43, 121, 145], [42, 122, 145],
    [42, 123, 145], [42, 124, 145], [41, 125, 145], [41, 126, 145], [41, 127, 145],
    [40, 128, 145], [40, 129, 145], [40, 130, 145], [39, 131, 145], [39, 132, 145],
    [39, 133, 145], [38, 134, 145], [38, 135, 145], [38, 135, 145], [37, 136, 145],
    [37, 137, 145], [37, 138, 145], [36, 139, 145], [36, 140, 145], [36, 141, 144],
    [36, 142, 144], [35, 143, 144], [35, 144, 144], [35, 145, 144], [35, 146, 144],
    [34, 147, 143], [34, 148, 143], [34, 149, 143], [34, 150, 143], [34, 151, 142],
    [34, 151, 142], [33, 152, 142], [33, 153, 141], [33, 154, 141], [33, 155, 141],
    [33, 156, 140], [33, 157, 140], [33, 158, 139], [33, 159, 139], [33, 160, 139],
    [34, 161, 138], [34, 162, 138], [34, 162, 137], [34, 163, 137], [35, 164, 136],
    [35, 165, 135], [35, 166, 135], [36, 167, 134], [36, 168, 134], [37, 169, 133],
    [37, 170, 132], [38, 170, 132], [38, 171, 131], [39, 172, 130], [40, 173, 130],
    [40, 174, 129], [41, 175, 128], [42, 176, 127], [43, 176, 127], [43, 177, 126],
    [44, 178, 125], [45, 179, 124], [46, 180, 123], [47, 180, 123], [48, 181, 122],
    [49, 182, 121], [50, 183, 120], [51, 183, 119], [52, 184, 118], [53, 185, 117],
    [55, 185, 116], [56, 186, 115], [57, 187, 114], [58, 188, 113], [60, 188, 112],
    [61, 189, 111], [62, 190, 110], [64, 190, 109], [65, 191, 108], [67, 192, 107],
    [68, 192, 106], [70, 193, 105], [71, 193, 103], [73, 194, 102], [74, 195, 101],
    [76, 195, 100], [78, 196, 99], [79, 196, 97], [81, 197, 96], [83, 197, 95],
    [84, 198, 94], [86, 198, 92], [88, 199, 91], [90, 199, 90], [91, 200, 88],
    [93, 200, 87], [95, 201, 86], [97, 201, 84], [99, 201, 83], [101, 202, 81],
    [103, 202, 80], [105, 203, 78], [106, 203, 77], [108, 203, 75], [110, 204, 74],
    [112, 204, 72], [114, 204, 71], [116, 205, 69], [118, 205, 67], [120, 205, 66],
    [122, 206, 64], [124, 206, 63], [126, 206, 61], [128, 206, 59], [130, 207, 58],
    [132, 207, 56], [134, 207, 54], [136, 207, 53], [138, 208, 51], [140, 208, 49],
    [142, 208, 48], [144, 208, 46], [146, 208, 44], [148, 209, 43], [150, 209, 41],
    [152, 209, 39], [154, 209, 38], [156, 209, 36], [158, 209, 34], [160, 210, 33],
    [162, 210, 31], [164, 210, 30], [166, 210, 28], [168, 210, 27], [170, 210, 25],
    [172, 210, 24], [174, 210, 22], [176, 210, 21], [178, 210, 20], [180, 210, 18],
    [182, 210, 17], [184, 210, 16], [186, 210, 15], [188, 210, 14], [190, 210, 13],
    [191, 210, 12], [193, 210, 12], [195, 210, 11], [197, 209, 11], [199, 209, 11],
    [201, 209, 11], [203, 209, 11], [205, 209, 11], [206, 209, 12], [208, 208, 12],
    [210, 208, 13], [212, 208, 14], [214, 208, 15], [215, 207, 16], [217, 207, 17],
    [219, 207, 18], [220, 206, 20], [222, 206, 21], [224, 206, 23], [225, 205, 24],
    [227, 205, 26], [228, 204, 28], [230, 204, 29], [231, 203, 31], [233, 203, 33],
    [234, 202, 35], [235, 202, 37], [237, 201, 39], [238, 200, 41], [239, 200, 43],
    [240, 199, 45], [241, 199, 47], [243, 198, 49], [244, 197, 52], [245, 197, 54],
    [246, 196, 56], [247, 195, 58], [247, 195, 61], [248, 194, 63], [249, 193, 65],
    [250, 192, 68], [250, 192, 70], [251, 191, 73], [252, 190, 75], [252, 189, 78],
    [253, 189, 80], [253, 188, 83], [254, 187, 85], [254, 186, 88], [254, 185, 91],
    [255, 185, 93], [255, 184, 96], [255, 183, 99], [255, 182, 101], [255, 181, 104],
    [255, 180, 107], [255, 179, 110], [255, 179, 112], [255, 178, 115], [255, 177, 118],
    [255, 176, 121], [254, 175, 124], [254, 174, 126], [254, 173, 129], [254, 172, 132],
    [254, 171, 135], [253, 170, 138], [253, 169, 141], [253, 168, 144], [252, 167, 147],
    [252, 166, 150], [252, 165, 153], [251, 164, 155], [251, 163, 158], [250, 162, 161],
    [250, 161, 164], [249, 160, 167], [249, 159, 170], [248, 158, 173], [248, 157, 176],
    [247, 155, 179], [246, 154, 181], [246, 153, 184], [245, 152, 187], [244, 151, 190],
    [244, 150, 193], [243, 148, 196], [242, 147, 198], [241, 146, 201], [240, 145, 204],
    [240, 144, 206], [239, 142, 209], [238, 141, 212], [237, 140, 214], [236, 139, 217],
    [235, 137, 219], [234, 136, 222], [233, 135, 224], [232, 134, 227], [231, 132, 229],
    [230, 131, 232], [229, 130, 234], [227, 129, 236], [226, 127, 239], [225, 126, 241],
    [224, 125, 243], [223, 124, 245], [221, 122, 247], [220, 121, 249], [219, 120, 251],
    [218, 119, 253], [216, 118, 254], [215, 117, 255], [214, 116, 255], [212, 115, 255],
    [211, 114, 255], [210, 113, 254], [208, 112, 254], [207, 111, 253], [206, 111, 252],
    [204, 110, 252], [203, 110, 251], [201, 109, 250], [200, 109, 249], [199, 108, 248],
    [197, 108, 247], [196, 108, 246], [194, 108, 245], [193, 107, 243], [192, 107, 242],
    [190, 107, 241], [189, 107, 240], [187, 107, 238], [186, 107, 237], [185, 107, 235],
    [183, 107, 234], [182, 108, 232], [180, 108, 231], [179, 108, 229], [178, 108, 228],
    [176, 109, 226], [175, 109, 224], [173, 110, 223], [172, 110, 221], [171, 110, 219],
    [169, 111, 217], [168, 111, 216], [167, 112, 214], [165, 113, 212], [164, 113, 210],
    [163, 114, 208], [161, 115, 206], [160, 115, 204], [159, 116, 203], [157, 117, 201],
    [156, 117, 199], [155, 118, 197], [154, 119, 195], [152, 120, 193], [151, 120, 191],
    [150, 121, 189], [149, 122, 187], [147, 123, 185], [146, 124, 183], [145, 124, 181],
    [144, 125, 179], [143, 126, 177], [141, 127, 175], [140, 128, 173], [139, 129, 171],
    [138, 130, 169], [137, 131, 167], [136, 132, 165], [135, 133, 163], [134, 133, 161],
    [133, 134, 159], [132, 135, 157], [131, 136, 155], [130, 137, 153], [129, 138, 151],
    [128, 139, 149], [127, 140, 147], [126, 141, 145], [126, 142, 143], [125, 143, 141],
    [124, 144, 139], [123, 145, 137], [123, 146, 135], [122, 147, 133], [121, 148, 131],
    [121, 150, 129], [120, 151, 127], [120, 152, 125], [119, 153, 123], [119, 154, 121],
    [118, 155, 119], [118, 156, 117], [118, 157, 115], [117, 158, 113], [117, 159, 111],
    [117, 160, 109], [117, 162, 107], [117, 163, 105], [116, 164, 103], [116, 165, 101],
    [116, 166, 99], [116, 167, 97], [117, 168, 95], [117, 169, 93], [117, 171, 91],
    [117, 172, 89], [117, 173, 87], [118, 174, 85], [118, 175, 83], [118, 176, 81],
    [119, 178, 79], [119, 179, 77], [120, 180, 75], [120, 181, 73], [121, 182, 71],
    [121, 183, 69], [122, 184, 67], [123, 185, 65], [123, 187, 63], [124, 188, 61],
    [125, 189, 59], [126, 190, 57], [127, 191, 55], [127, 192, 53], [128, 193, 51],
    [129, 195, 49], [130, 196, 47], [131, 197, 45], [132, 198, 43], [133, 199, 42],
    [135, 200, 40], [136, 201, 38], [137, 202, 36], [138, 203, 35], [140, 205, 33],
    [141, 206, 31], [142, 207, 30], [144, 208, 28], [145, 209, 27], [147, 210, 26],
    [148, 211, 24], [150, 212, 23], [151, 213, 22], [153, 214, 21], [155, 215, 20],
    [156, 216, 19], [158, 217, 18], [160, 218, 18], [161, 219, 17], [163, 220, 17],
    [165, 221, 16], [166, 222, 16], [168, 223, 16], [170, 224, 16], [172, 225, 16],
    [173, 226, 17], [175, 227, 17], [177, 228, 18], [179, 228, 18], [180, 229, 19],
    [182, 230, 20], [184, 231, 21], [186, 232, 22], [187, 232, 23], [189, 233, 25],
    [191, 234, 26], [193, 235, 28], [194, 235, 29], [196, 236, 31], [198, 237, 33],
    [199, 237, 35], [201, 238, 37], [203, 239, 39], [205, 239, 41], [206, 240, 43],
    [208, 241, 46], [210, 241, 48], [211, 242, 51], [213, 242, 53], [214, 243, 56],
    [216, 243, 59], [218, 244, 61], [219, 244, 64], [221, 245, 67], [222, 245, 70],
    [224, 246, 73], [225, 246, 76], [227, 247, 79], [228, 247, 82], [229, 247, 86],
    [231, 248, 89], [232, 248, 92], [233, 248, 96], [234, 249, 99], [236, 249, 103],
    [237, 249, 106], [238, 250, 110], [239, 250, 114], [240, 250, 117], [241, 251, 121],
    [242, 251, 125], [243, 251, 129], [243, 252, 133], [244, 252, 137], [245, 252, 141],
    [246, 252, 145], [246, 253, 149], [247, 253, 153], [247, 253, 157], [248, 253, 161],
    [248, 254, 165], [249, 254, 169], [249, 254, 174], [249, 254, 178], [250, 254, 182],
    [250, 255, 186], [250, 255, 191], [251, 255, 195], [251, 255, 199], [251, 255, 204],
    [251, 255, 208], [251, 255, 212], [252, 255, 217], [252, 255, 221], [252, 255, 225],
    [252, 255, 230], [252, 255, 234], [252, 255, 238], [252, 255, 243], [253, 255, 247],
], dtype=np.uint8)


class SimilarityMapGenerator:
    """Generates similarity maps for query-image interpretability visualization."""

    # Tokens to filter out (stopwords, special tokens, punctuation)
    FILTER_PATTERNS = [
        r"^<.*>$",  # Special tokens like <bos>, <eos>
        r"^[^\w]+$",  # Pure punctuation
        r"^\s+$",  # Whitespace only
    ]

    STOPWORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "of", "and", "or",
        "but", "in", "on", "at", "to", "for", "with", "by", "from", "as",
        "into", "through", "during", "before", "after", "above", "below",
        "between", "under", "again", "further", "then", "once", "here",
        "there", "when", "where", "why", "how", "all", "each", "few", "more",
        "most", "other", "some", "such", "no", "nor", "not", "only", "own",
        "same", "so", "than", "too", "very", "just", "also", "now", "if",
        "it", "its", "this", "that", "these", "those", "what", "which", "who",
    }

    def __init__(self):
        """Initialize the similarity map generator."""
        self._compiled_patterns = [re.compile(p) for p in self.FILTER_PATTERNS]

    def should_filter_token(self, token: str) -> bool:
        """Check if a token should be filtered out from visualization.

        Args:
            token: The token string to check

        Returns:
            True if the token should be filtered, False otherwise
        """
        # Clean token (remove special chars from tokenizer)
        clean_token = token.strip().lower().replace("▁", "").replace("Ġ", "")

        # Filter empty tokens
        if not clean_token:
            return True

        # Filter by regex patterns
        for pattern in self._compiled_patterns:
            if pattern.match(token):
                return True

        # Filter stopwords
        if clean_token in self.STOPWORDS:
            return True

        return False

    def get_query_tokens(self, query: str) -> List[TokenInfo]:
        """Get tokenized query with filter information.

        Args:
            query: The query string

        Returns:
            List of TokenInfo objects
        """
        processor = model_service.processor

        # Tokenize the query
        tokenized = processor.tokenizer(
            query,
            return_tensors="pt",
            padding=False,
            truncation=True,
        )

        input_ids = tokenized["input_ids"][0]
        tokens = processor.tokenizer.convert_ids_to_tokens(input_ids.tolist())

        result = []
        for idx, token in enumerate(tokens):
            result.append(TokenInfo(
                index=idx,
                token=token,
                should_filter=self.should_filter_token(token),
            ))

        return result

    @staticmethod
    def _normalize_sim_map(sim_map: np.ndarray) -> np.ndarray:
        """Normalize similarity map to [0, 1] range.

        Args:
            sim_map: Raw similarity scores

        Returns:
            Normalized similarity map
        """
        min_val = sim_map.min()
        max_val = sim_map.max()

        if max_val - min_val < 1e-8:
            return np.zeros_like(sim_map)

        return (sim_map - min_val) / (max_val - min_val)

    def _apply_colormap(self, normalized_map: np.ndarray) -> np.ndarray:
        """Apply viridis colormap to normalized similarity map.

        Args:
            normalized_map: Similarity map normalized to [0, 1]

        Returns:
            RGB image array of shape (H, W, 3)
        """
        # Scale to [0, 255] and use as index into colormap
        indices = (normalized_map * 255).astype(np.uint8)
        return VIRIDIS_COLORS[indices]

    def _blend_images(
        self,
        original: Image.Image,
        heatmap_rgb: np.ndarray,
        alpha: float = 0.5,
    ) -> Image.Image:
        """Blend original image with heatmap overlay.

        Args:
            original: Original PIL image
            heatmap_rgb: Heatmap as RGB array
            alpha: Blend factor (0 = original only, 1 = heatmap only)

        Returns:
            Blended PIL image
        """
        # Resize heatmap to match original image size
        heatmap_img = Image.fromarray(heatmap_rgb, mode="RGB")
        heatmap_resized = heatmap_img.resize(original.size, Image.Resampling.BICUBIC)

        # Convert original to RGB if needed
        if original.mode != "RGB":
            original = original.convert("RGB")

        # Blend
        original_arr = np.array(original, dtype=np.float32)
        heatmap_arr = np.array(heatmap_resized, dtype=np.float32)

        blended = (1 - alpha) * original_arr + alpha * heatmap_arr
        blended = np.clip(blended, 0, 255).astype(np.uint8)

        return Image.fromarray(blended, mode="RGB")

    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL image to base64 string.

        Args:
            image: PIL image

        Returns:
            Base64-encoded PNG string
        """
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    @lru_cache(maxsize=32)
    def _get_cached_query_embedding(self, query: str) -> torch.Tensor:
        """Get cached query embedding.

        Args:
            query: Query string

        Returns:
            Query embedding tensor
        """
        device = model_service.model.device
        with torch.no_grad():
            batch_query = model_service.processor.process_queries([query]).to(device)
            query_embedding = model_service.model(**batch_query)
            return query_embedding[0].cpu()  # [seq, dim]

    def generate_similarity_maps(
        self,
        image: Image.Image,
        query: str,
        selected_tokens: Optional[List[int]] = None,
        alpha: float = 0.5,
    ) -> Tuple[List[TokenInfo], List[SimilarityMapResult]]:
        """Generate similarity maps for query tokens overlaid on image.

        Args:
            image: The page image
            query: The search query
            selected_tokens: Token indices to generate maps for (None = non-filtered tokens)
            alpha: Blend factor for overlay

        Returns:
            Tuple of (all tokens info, similarity map results for selected tokens)
        """
        device = model_service.model.device
        processor = model_service.processor

        # Get all tokens info
        all_tokens = self.get_query_tokens(query)

        # Determine which tokens to generate maps for
        if selected_tokens is None:
            # Generate for all non-filtered tokens
            target_indices = [t.index for t in all_tokens if not t.should_filter]
        else:
            target_indices = selected_tokens

        if not target_indices:
            return all_tokens, []

        # Get query embedding (cached)
        query_embedding = self._get_cached_query_embedding(query)  # [query_len, dim]

        # Process image
        with torch.no_grad():
            batch_images = processor.process_images([image]).to(device)
            image_embedding = model_service.model(**batch_images)
            image_embedding = image_embedding[0].cpu()  # [seq, dim]

        # Get patch dimensions
        get_n_patches_fn = processor.get_n_patches
        spatial_merge_size = getattr(model_service.model, "spatial_merge_size", None)

        if spatial_merge_size is not None:
            n_patches_x, n_patches_y = get_n_patches_fn(
                (image.width, image.height),
                patch_size=spatial_merge_size,
            )
        else:
            n_patches_x, n_patches_y = get_n_patches_fn((image.width, image.height))

        # Find image token indices
        if "input_ids" in batch_images:
            input_ids = batch_images["input_ids"][0].cpu()
            image_token_id = model_service.image_token_id
            image_mask = input_ids.eq(image_token_id)
            image_indices = torch.nonzero(image_mask, as_tuple=True)[0]

            if len(image_indices) > 0:
                # Get image patch embeddings
                n_patches = n_patches_x * n_patches_y

                # Handle models with global patches (Idefics3 style)
                if len(image_indices) > n_patches:
                    # Exclude global patch tokens (last 64 typically)
                    image_indices = image_indices[:n_patches]

                image_patch_embeddings = image_embedding[image_indices]  # [n_patches, dim]
            else:
                logger.warning("No image tokens found in processed image")
                return all_tokens, []
        else:
            logger.warning("No input_ids in processed image batch")
            return all_tokens, []

        # Generate similarity maps for each selected token
        results = []

        for token_idx in target_indices:
            if token_idx >= len(all_tokens):
                continue

            token_info = all_tokens[token_idx]

            # Get query token embedding
            query_token_emb = query_embedding[token_idx]  # [dim]

            # Compute similarity with each image patch
            # Cosine similarity: (q · p) / (||q|| * ||p||)
            query_norm = query_token_emb / (query_token_emb.norm() + 1e-8)
            patch_norms = image_patch_embeddings / (
                image_patch_embeddings.norm(dim=-1, keepdim=True) + 1e-8
            )

            similarities = torch.matmul(patch_norms, query_norm)  # [n_patches]

            # Reshape to 2D grid
            sim_map = similarities.numpy().reshape(n_patches_y, n_patches_x)

            # Normalize
            sim_map_normalized = self._normalize_sim_map(sim_map)

            # Apply colormap
            heatmap_rgb = self._apply_colormap(sim_map_normalized)

            # Blend with original image
            blended = self._blend_images(image, heatmap_rgb, alpha=alpha)

            # Convert to base64
            base64_str = self._image_to_base64(blended)

            results.append(SimilarityMapResult(
                token_index=token_idx,
                token=token_info.token,
                similarity_map_base64=base64_str,
            ))

        return all_tokens, results


# Global instance
similarity_map_generator = SimilarityMapGenerator()
