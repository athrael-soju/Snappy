import torch
import logging
from typing import Optional

from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor
from config import MODEL_NAME, MODEL_DEVICE

logger = logging.getLogger(__name__)


class ColPaliService:
    """
    Service for managing ColPali model and processor initialization.
    Handles model loading, device management, and provides a clean interface
    for other services to access the model and processor.
    """
    
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize ColPali service with model and processor.
        
        Args:
            model_name: Name/path of the model to load. Defaults to config MODEL_NAME.
            device: Device to load model on. Defaults to config MODEL_DEVICE.
        """
        self.model_name = model_name or MODEL_NAME
        self.device = device or MODEL_DEVICE
        self.model = None
        self.processor = None
        
        logger.info(f"Initializing ColPali service with model: {self.model_name}, device: {self.device}")
        self._initialize_model()
        self._initialize_processor()
    
    def _initialize_model(self):
        """Initialize the ColPali model"""
        try:
            logger.info(f"Loading ColPali model: {self.model_name}")
            self.model = ColQwen2_5.from_pretrained(
                self.model_name,
                torch_dtype=torch.bfloat16,
                device_map=self.device,
                attn_implementation=None
            ).eval()
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Failed to initialize ColPali model: {e}")
    
    def _initialize_processor(self):
        """Initialize the ColPali processor"""
        try:
            logger.info(f"Loading ColPali processor: {self.model_name}")
            self.processor = ColQwen2_5_Processor.from_pretrained(self.model_name)
            logger.info("Processor loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load processor: {e}")
            raise RuntimeError(f"Failed to initialize ColPali processor: {e}")
    
    def get_model(self):
        """
        Get the initialized model.
        
        Returns:
            The ColPali model instance
        """
        if self.model is None:
            raise RuntimeError("Model not initialized")
        return self.model
    
    def get_processor(self):
        """
        Get the initialized processor.
        
        Returns:
            The ColPali processor instance
        """
        if self.processor is None:
            raise RuntimeError("Processor not initialized")
        return self.processor
    
    def get_model_and_processor(self):
        """
        Get both model and processor.
        
        Returns:
            Tuple of (model, processor)
        """
        return self.get_model(), self.get_processor()
    
    def get_device(self):
        """
        Get the device the model is loaded on.
        
        Returns:
            Device string
        """
        return self.device
    
    def get_model_info(self):
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "model_loaded": self.model is not None,
            "processor_loaded": self.processor is not None,
            "model_dtype": str(self.model.dtype) if self.model else None,
            "model_device": str(next(self.model.parameters()).device) if self.model else None
        }
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up ColPali service resources")
        if self.model is not None:
            del self.model
            self.model = None
        if self.processor is not None:
            del self.processor
            self.processor = None
        
        # Clear CUDA cache if using GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
