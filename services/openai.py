import base64
from io import BytesIO
from typing import List, Tuple, Optional
import logging
from openai import OpenAI
from PIL import Image

from config import OPENAI_MODEL, MAX_TOKENS, OPENAI_API_KEY

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    Service for interacting with OpenAI's API for document question answering.
    Handles image encoding, prompt construction, and API communication.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, max_tokens: Optional[int] = None):
        """
        Initialize OpenAI service.
        
        Args:
            api_key: OpenAI API key. If None, uses config default or requires runtime key.
            model: Model name to use. Defaults to config OPENAI_MODEL.
            max_tokens: Maximum tokens for response. Defaults to config MAX_TOKENS.
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_MODEL
        self.max_tokens = max_tokens or MAX_TOKENS
        self.client = None
        
        # Initialize client if API key is available
        if self.api_key and self.api_key.startswith("sk"):
            self._initialize_client(self.api_key)
        
        logger.info(f"OpenAI service initialized with model: {self.model}")
    
    def _initialize_client(self, api_key: str):
        """Initialize OpenAI client with API key"""
        try:
            self.client = OpenAI(api_key=api_key.strip())
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None
    
    def encode_image_to_base64(self, image: Image.Image) -> str:
        """
        Encodes a PIL image to a base64 string.
        
        Args:
            image: PIL Image object
            
        Returns:
            Base64 encoded string of the image
        """
        try:
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to encode image to base64: {e}")
            raise
    
    def _construct_prompt(self, query: str) -> str:
        """
        Construct the system prompt for document Q&A.
        
        Args:
            query: User's question
            
        Returns:
            Formatted prompt string
        """
        prompt_template = """
You are a smart assistant designed to answer questions about a PDF document.
You are given relevant information in the form of PDF pages. Use them to construct a short response to the question, and cite your sources (page numbers, etc).
If it is not possible to answer using the provided pages, do not attempt to provide an answer and simply say the answer is not present within the documents.
Give detailed and extensive answers, only containing info in the pages you are given.
You can answer using information contained in plots and figures if necessary.
Answer in the same language as the query.

Query: {query}
PDF pages:
"""
        return prompt_template.format(query=query)
    
    def query(self, query: str, images: List[Tuple[Image.Image, str]], api_key: Optional[str] = None) -> str:
        """
        Query OpenAI with document images and question.
        
        Args:
            query: User's question
            images: List of tuples containing (PIL Image, page_info)
            api_key: Optional API key to use for this request
            
        Returns:
            AI-generated response string
        """
        # Use provided API key or instance default
        effective_api_key = api_key or self.api_key
        
        if not effective_api_key or not effective_api_key.startswith("sk"):
            return "Enter your OpenAI API key to get a custom response"
        
        # Initialize client if needed
        if not self.client or (api_key and api_key != self.api_key):
            self._initialize_client(effective_api_key)
        
        if not self.client:
            return "OpenAI API connection failure. Verify the provided key is correct (sk-***)."
        
        try:
            # Encode images to base64
            logger.info(f"Processing {len(images)} images for OpenAI query")
            base64_images = []
            for image_tuple in images:
                # Handle both (image, info) tuples and single images
                image = image_tuple[0] if isinstance(image_tuple, tuple) else image_tuple
                base64_image = self.encode_image_to_base64(image)
                base64_images.append(base64_image)
            
            # Construct the message content
            content = [
                {
                    "type": "text",
                    "text": self._construct_prompt(query)
                }
            ]
            
            # Add images to content
            for base64_image in base64_images:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                })
            
            # Make API call
            logger.info(f"Making OpenAI API call with model: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": content
                }],
                max_tokens=self.max_tokens,
            )
            
            result = response.choices[0].message.content
            logger.info("OpenAI API call completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "OpenAI API connection failure. Verify the provided key is correct (sk-***)."
    
    def set_api_key(self, api_key: str):
        """
        Update the API key and reinitialize client.
        
        Args:
            api_key: New OpenAI API key
        """
        self.api_key = api_key
        self._initialize_client(api_key)
    
    def get_model_info(self) -> dict:
        """
        Get information about the OpenAI service configuration.
        
        Returns:
            Dictionary with service information
        """
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "api_key_configured": bool(self.api_key and self.api_key.startswith("sk")),
            "client_initialized": self.client is not None
        }
