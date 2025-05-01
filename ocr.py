import cv2
import numpy as np
import os
from PIL import Image

# Try to import pytesseract but provide fallback if it fails
try:
    import pytesseract

    # Explicitly set the path to the Tesseract executable - adjust this path to match your installation
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    TESSERACT_AVAILABLE = True
except ImportError:
    print("Warning: pytesseract module could not be imported. OCR functionality will be limited.")
    TESSERACT_AVAILABLE = False


def extract_text_from_image(image_path):
    """
    Extract text from an image using Tesseract OCR.

    Args:
        image_path (str): Path to the image file

    Returns:
        str: Extracted text from the image
    """
    try:
        # Ensure file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Load image with OpenCV
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")

        # Check if Tesseract is available
        if not TESSERACT_AVAILABLE:
            return "(OCR unavailable - please install pytesseract and Tesseract OCR)"

        # Try direct PIL approach instead of OpenCV preprocessing
        try:
            pil_image = Image.open(image_path)
            extracted_text = pytesseract.image_to_string(pil_image, lang='eng')

            # If text was extracted successfully, return it
            if extracted_text.strip():
                return extracted_text.strip()
        except Exception as e:
            print(f"PIL-based OCR failed: {e}, trying OpenCV preprocessing")

        # If PIL approach failed, try with OpenCV preprocessing
        # Preprocess the image to improve OCR accuracy
        preprocessed_img = preprocess_image(img)

        # Use Tesseract to extract text
        extracted_text = pytesseract.image_to_string(preprocessed_img, lang='eng')

        # Clean up the extracted text
        extracted_text = extracted_text.strip()

        if not extracted_text:
            return "No text could be extracted from the image. Try a clearer image."

        return extracted_text

    except Exception as e:
        # Provide a more detailed error message
        error_message = str(e)
        if "[WinError 5] Access is denied" in error_message:
            return ("OCR failed due to permission issues. Try:\n"
                    "1. Run the application as administrator\n"
                    "2. Reinstall Tesseract to a non-system folder like C:\\Tesseract-OCR\n"
                    "3. Use text or URL input methods instead")
        else:
            return f"Error in OCR processing: {error_message}"


def preprocess_image(img):
    """
    Preprocess the image to improve OCR accuracy:
    1. Convert to grayscale
    2. Apply noise reduction
    3. Apply thresholding
    4. Attempt to detect and correct skew

    Args:
        img (numpy.ndarray): Input image

    Returns:
        numpy.ndarray: Preprocessed image
    """
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply noise reduction (Gaussian blur)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 2
    )

    # Invert the image (black text on white background)
    thresh = cv2.bitwise_not(thresh)

    # Attempt to correct skew if necessary
    try:
        corrected = correct_skew(thresh)
        return corrected
    except:
        # If skew correction fails, return the thresholded image
        return thresh


def correct_skew(image, delta=1, limit=5):
    """
    Correct skew in image.

    Args:
        image (numpy.ndarray): Input image
        delta (int): Delta angle for rotation steps
        limit (int): Max angle to rotate

    Returns:
        numpy.ndarray: Deskewed image
    """

    def determine_score(img, angle):
        # Rotate the image
        data = rotate_image(img, angle)
        # Compute histogram of horizontal projection
        histogram = np.sum(data, axis=1)
        # Calculate score as sum of squared differences
        score = np.sum((histogram[1:] - histogram[:-1]) ** 2)
        return score

    scores = []
    angles = np.arange(-limit, limit + delta, delta)

    # Find the best angle
    for angle in angles:
        score = determine_score(image, angle)
        scores.append(score)

    best_angle = angles[scores.index(max(scores))]

    # Return the rotated image using the best angle
    return rotate_image(image, best_angle)


def rotate_image(image, angle):
    """
    Rotate image around its center.

    Args:
        image (numpy.ndarray): Input image
        angle (float): Rotation angle in degrees

    Returns:
        numpy.ndarray: Rotated image
    """
    # Get image dimensions
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)

    # Get rotation matrix
    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Perform rotation
    rotated = cv2.warpAffine(
        image, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )

    return rotated


def detect_text_regions(image_path):
    """
    Detect regions of text in an image for more targeted OCR.

    Args:
        image_path (str): Path to the image file

    Returns:
        list: List of extracted text from identified regions
    """
    try:
        # Read image
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply MSER (Maximally Stable Extremal Regions) for text detection
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(gray)

        # Create a mask to visualize detected regions
        mask = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)

        texts = []

        # Group regions to form text blocks
        for region in regions:
            # Create a bounding box around the region
            x, y, w, h = cv2.boundingRect(region)

            # Filter small regions (likely noise)
            if w < 10 or h < 10:
                continue

            # Filter very large regions (unlikely to be text)
            if w > img.shape[1] * 0.8 or h > img.shape[0] * 0.8:
                continue

            # Extract region
            roi = gray[y:y + h, x:x + w]

            # Apply OCR to the region
            text = pytesseract.image_to_string(roi, config='--psm 7')
            if text.strip():
                texts.append(text.strip())

            # Draw region on mask
            cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)

        # If no text regions were successfully detected, perform OCR on the whole image
        if not texts:
            return [extract_text_from_image(image_path)]

        return texts

    except Exception as e:
        print(f"Error detecting text regions: {e}")
        # Fall back to full image OCR
        return [extract_text_from_image(image_path)]


def extract_text_from_screenshot(image_path):
    """
    Extract text from a screenshot of a news article, optimized for screen content.

    Args:
        image_path (str): Path to the screenshot image

    Returns:
        str: Extracted text
    """
    # First try region-based extraction for better results
    region_texts = detect_text_regions(image_path)

    # Combine all region texts
    combined_text = ' '.join(region_texts)

    # If no text was extracted, try full image OCR with different settings
    if not combined_text.strip():
        # Load image with PIL for different processing
        img = Image.open(image_path)

        # Try OCR with different page segmentation modes
        combined_text = pytesseract.image_to_string(img, config='--psm 3')

    return combined_text