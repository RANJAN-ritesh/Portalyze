"""
Face Detection using MediaPipe (preferred) or OpenCV Haar Cascades (fallback)
MediaPipe: 95%+ accuracy (Python 3.12 and below)
OpenCV: 70-80% accuracy (works with any Python version)
"""

import logging
from typing import Dict, Any, Optional
from functools import lru_cache
import asyncio
import aiohttp
import io
from app.config import settings

# Try to import image processing libraries (optional)
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️  OpenCV not available - face detection disabled")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️  NumPy not available")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  PIL not available")

# Try to import MediaPipe, fall back to OpenCV if unavailable
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("MediaPipe not available (Python 3.13+). Falling back to OpenCV Haar Cascades.")

logger = logging.getLogger(__name__)


class ImageValidator:
    """
    Image validation using MediaPipe (preferred) or OpenCV Haar Cascades (fallback)
    Provides face detection with confidence scores
    """

    def __init__(self):
        self.detection_method = None
        self.face_detector = None

        if settings.enable_face_detection:
            if MEDIAPIPE_AVAILABLE and CV2_AVAILABLE and NUMPY_AVAILABLE:
                # Initialize MediaPipe Face Detection (preferred)
                self.mp_face_detection = mp.solutions.face_detection
                self.face_detector = self.mp_face_detection.FaceDetection(
                    model_selection=1,  # 1 = full range (0-5m), 0 = short range (2m)
                    min_detection_confidence=0.7
                )
                self.detection_method = "mediapipe"
                logger.info("MediaPipe Face Detection initialized (95%+ accuracy)")
            elif CV2_AVAILABLE and NUMPY_AVAILABLE:
                # Fall back to OpenCV Haar Cascades
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                self.face_detector = cv2.CascadeClassifier(cascade_path)
                self.detection_method = "opencv"
                logger.info("OpenCV Haar Cascade initialized (70-80% accuracy, fallback mode)")
            else:
                logger.warning("Face detection enabled but required libraries not available")
                self.detection_method = None
        else:
            logger.info("Face detection disabled in config")

    async def validate_image_url(self, img_url: str) -> Dict[str, Any]:
        """
        Main validation method - checks if image exists and contains a professional face

        Returns:
            {
                "exists": bool,
                "has_face": bool,
                "confidence": float (0-1),
                "face_count": int,
                "is_professional": bool,
                "details": str
            }
        """
        if not img_url:
            return self._error_result("No image URL provided")

        # Download image
        img_data = await self._download_image(img_url)
        if not img_data:
            return self._error_result("Failed to download image")

        # Check if face detection is enabled
        if not settings.enable_face_detection or not self.face_detector:
            return {
                "exists": True,
                "has_face": None,  # Unknown
                "confidence": None,
                "face_count": None,
                "is_professional": True,  # Assume professional if can't check
                "details": "Image exists (face detection disabled)"
            }

        # Detect faces
        return await self._detect_faces(img_data)

    async def _download_image(self, img_url: str) -> Optional[bytes]:
        """Download image with timeout"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    img_url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.read()
                    logger.warning(f"Image download failed with status {response.status}: {img_url}")
                    return None

        except asyncio.TimeoutError:
            logger.warning(f"Image download timeout: {img_url}")
            return None
        except Exception as e:
            logger.warning(f"Image download error: {str(e)}")
            return None

    async def _detect_faces(self, img_data: bytes) -> Dict[str, Any]:
        """
        Detect faces using MediaPipe (preferred) or OpenCV Haar Cascades (fallback)
        """
        try:
            # Convert bytes to numpy array
            img_array = np.asarray(bytearray(img_data), dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if img is None:
                return self._error_result("Invalid image format")

            if self.detection_method == "mediapipe":
                return await self._detect_faces_mediapipe(img)
            elif self.detection_method == "opencv":
                return await self._detect_faces_opencv(img)
            else:
                return self._error_result("No face detection method available")

        except Exception as e:
            logger.error(f"Face detection error: {str(e)}")
            return self._error_result(f"Face detection failed: {str(e)}")

    async def _detect_faces_mediapipe(self, img: Any) -> Dict[str, Any]:
        """Detect faces using MediaPipe (95%+ accuracy)"""
        # Convert BGR to RGB (MediaPipe expects RGB)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Detect faces
        results = self.face_detector.process(img_rgb)

        if not results.detections:
            return {
                "exists": True,
                "has_face": False,
                "confidence": 0.0,
                "face_count": 0,
                "is_professional": False,
                "details": "No face detected in image"
            }

        # Get primary face (first detection)
        primary_face = results.detections[0]
        confidence = primary_face.score[0]
        face_count = len(results.detections)

        # Determine if professional (high confidence, single face)
        is_professional = bool(confidence > 0.85 and face_count == 1)

        details = self._generate_face_details(confidence, face_count, is_professional)

        return {
            "exists": True,
            "has_face": True,
            "confidence": float(confidence),
            "face_count": int(face_count),
            "is_professional": is_professional,
            "details": details
        }

    async def _detect_faces_opencv(self, img: Any) -> Dict[str, Any]:
        """Detect faces using OpenCV Haar Cascades (70-80% accuracy, fallback)"""
        # Convert to grayscale for Haar Cascade
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = self.face_detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        if len(faces) == 0:
            return {
                "exists": True,
                "has_face": False,
                "confidence": 0.0,
                "face_count": 0,
                "is_professional": False,
                "details": "No face detected in image (OpenCV Haar Cascade)"
            }

        face_count = len(faces)
        # OpenCV doesn't provide confidence, so we estimate based on face size
        # Larger face = more likely to be a proper profile photo
        largest_face = max(faces, key=lambda f: f[2] * f[3])  # w * h
        img_area = int(img.shape[0] * img.shape[1])
        face_area = int(largest_face[2] * largest_face[3])
        face_ratio = float(face_area / img_area)

        # Estimate confidence (0.5-0.95) based on face size
        # Professional photos typically have face taking 10-40% of image
        if 0.1 <= face_ratio <= 0.4:
            confidence = 0.85 + (0.1 * min(face_ratio / 0.4, 1.0))
        else:
            confidence = 0.5 + (0.35 * min(face_ratio, 1.0))

        # Determine if professional (single face, good size)
        is_professional = bool(face_count == 1 and 0.1 <= face_ratio <= 0.5)

        details = self._generate_face_details(confidence, face_count, is_professional)
        details += " (OpenCV detection)"

        return {
            "exists": True,
            "has_face": True,
            "confidence": float(confidence),
            "face_count": int(face_count),
            "is_professional": is_professional,
            "details": details
        }

    def _generate_face_details(
        self,
        confidence: float,
        face_count: int,
        is_professional: bool
    ) -> str:
        """Generate human-readable details about face detection"""
        if is_professional:
            return f"Professional photo detected (confidence: {confidence:.0%})"

        if face_count > 1:
            return f"Multiple faces detected ({face_count}). Consider using a single-person photo."

        if confidence < 0.85:
            return f"Face detected but quality could be improved (confidence: {confidence:.0%})"

        return f"Face detected (confidence: {confidence:.0%})"

    def _error_result(self, message: str) -> Dict[str, Any]:
        """Return error result structure"""
        return {
            "exists": False,
            "has_face": False,
            "confidence": 0.0,
            "face_count": 0,
            "is_professional": False,
            "details": message
        }

    @lru_cache(maxsize=100)
    def _cached_image_check(self, img_url: str) -> str:
        """
        Simple cached check for image existence
        Returns: "exists", "not_found", or "error"
        """
        try:
            import requests
            response = requests.head(img_url, timeout=5)
            return "exists" if response.status_code == 200 else "not_found"
        except Exception:
            return "error"

    def get_status(self) -> Dict[str, Any]:
        """Get validator status"""
        if self.detection_method == "mediapipe":
            return {
                "enabled": settings.enable_face_detection,
                "model": "MediaPipe Face Detection v1",
                "accuracy": "95%+",
                "confidence_threshold": 0.7
            }
        elif self.detection_method == "opencv":
            return {
                "enabled": settings.enable_face_detection,
                "model": "OpenCV Haar Cascade (fallback)",
                "accuracy": "70-80%",
                "confidence_threshold": "estimated"
            }
        else:
            return {
                "enabled": False,
                "model": "None",
                "accuracy": "N/A",
                "confidence_threshold": "N/A"
            }


# Utility functions for backward compatibility
async def validate_profile_image(img_url: str) -> bool:
    """
    Simple boolean check for profile image validity
    For backward compatibility with existing code
    """
    validator = ImageValidator()
    result = await validator.validate_image_url(img_url)
    return result.get("is_professional", False)


async def check_image_exists(img_url: str) -> bool:
    """
    Quick check if image URL is accessible
    """
    validator = ImageValidator()
    result = await validator.validate_image_url(img_url)
    return result.get("exists", False)
