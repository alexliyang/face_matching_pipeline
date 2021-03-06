# pylint: disable = R0903
"""
Face detection, encoding, and matching.
"""
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image

from facematch.face_detection import FaceDetector
from facematch.face_encoding import FaceEncoder


class FaceMatcher:
    """
    Face detection and recognition
    """

    def __init__(self, reference):
        self.reference = reference
        self.detector = FaceDetector()
        self.encoder = FaceEncoder()

    def recoginze(self, image: Image.Image,
                  threshold: float = 0.0) -> List[Dict]:
        """
        Find faces in an image and compare them to reference photos.
        Returning faces are sorted from left to right.

        Parameters
        ----------
        image : Image.Image
            Input image
        threshold : float, default 0
            Detection threshold, above which best match is THE match.
            As a rule of thumb, 0.5 - 0.6 provides reasonable TP/FP ratio.

        Returns
        -------
        result : list of dicts
            List of dicts for every face found in an image.
        """
        detected = self.detector.find_faces(image)
        if not detected:
            return []
        face_images = [face.image for face in detected]
        embeddings = self.encoder.calculate_embeddings(
            face_images, report_progress=False)

        best_matches, distances = find_closest(embeddings,
                                               self.reference.embeddings)
        names = [self.reference.names[i] for i in best_matches]
        boxes = [face.box for face in detected]

        result = [{
            'id': i,
            'coordinates': box,
            'best_match': name if distance > threshold else 'unknown',
            'distance': distance.item() if distance > threshold else -1
        } for i, (box, name,
                  distance) in enumerate(zip(boxes, names, distances))]
        result = sorted(result, key=lambda x: x['coordinates'][0])
        return result


def find_closest(embeddings: np.ndarray,
                 references: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute pair-wise distance between
    current and reference embeddings.

    Parameters
    ----------
    embeddings : np.ndarray
        Unknown embeddings, shape = (n_candidates, n_dims)
    references : np.ndarray
        Reference embeddings, shape = (n_references, n_dims)

    Returns
    -------
    Length-2 tuple:
        best_matches : np.ndarray
            Indexes of closest references to embeddings of unknown faces,
            shape = (n_candidates,)
        distances : np.ndarray
            Cosine distances between references and unknown embeddings,
            shape = (n_candidates,)
    """
    cosines = np.dot(embeddings, references.T)
    best_matches = cosines.argmax(axis=1)
    distances = cosines.max(axis=1)
    return best_matches, distances
