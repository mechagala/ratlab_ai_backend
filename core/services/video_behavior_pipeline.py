import os
import logging
from typing import Dict, List, Optional
from pathlib import Path
import pandas as pd
from .pipeline_total_v2 import (
    detect_rois,
    detect_keypoints,
    ROIAnalyzer,
    VideoClipExtractor
)

logger = logging.getLogger(__name__)

class VideoProcessingPipeline:
    def __init__(
        self,
        model_path: str,
        workdir: str,
        segmenter_model_path: str,
        analyzer_params: Dict,
        clip_params: Dict,
        segmenter_params: Dict
    ):
        self.model_path = model_path
        self.workdir = workdir
        self.segmenter_model_path = segmenter_model_path
        self.analyzer_params = analyzer_params
        self.clip_params = clip_params
        self.segmenter_params = segmenter_params

    def run(
        self,
        video_path: str,
        rois: Optional[List[Dict]] = None,
        export_clips: bool = True,
        autosegment_if_missing: bool = True,
        return_predictions_df: bool = False
    ) -> Dict:
        """
        Ejecuta el pipeline completo de procesamiento de video.
        
        Args:
            video_path: Ruta al video a procesar
            rois: ROIs predefinidas (opcional)
            export_clips: Si se deben exportar clips de video
            autosegment_if_missing: Si se deben detectar ROIs automáticamente si no se proporcionan
            return_predictions_df: Si se debe devolver el DataFrame completo de predicciones
            
        Returns:
            Dict con los resultados del procesamiento
        """
        os.makedirs(self.workdir, exist_ok=True)
        
        # 1. Detección de ROIs (si es necesario)
        roi_json_path = None
        if rois is None and autosegment_if_missing:
            logger.info("Detectando ROIs automáticamente...")
            roi_json_path = detect_rois(
                video_path=video_path,
                model_path=self.segmenter_model_path,
                output_dir=self.workdir,
                target_frame=self.segmenter_params.get('frame_index', 20)
            )
        elif rois is not None:
            # Guardar ROIs proporcionadas como JSON
            roi_json_path = self._save_provided_rois(rois)
        
        # 2. Detección de keypoints
        logger.info("Detectando keypoints...")
        keypoints_csv = os.path.join(self.workdir, "predictions.csv")
        detect_keypoints(
            video_path=video_path,
            model_path=self.model_path,
            output_csv=keypoints_csv
        )
        
        # 3. Análisis de interacciones
        logger.info("Analizando interacciones...")
        analyzer = ROIAnalyzer(
            data_path=keypoints_csv,
            json_path=roi_json_path,
            video_path=video_path,
            **self.analyzer_params
        )
        analysis_results = analyzer.analyze()
        
        # 4. Extracción de clips (si se solicita)
        generated_clips = []
        if export_clips:
            logger.info("Extrayendo clips de interacción...")
            clips_dir = os.path.join(self.workdir, "clips")
            extractor = VideoClipExtractor(
                video_path=video_path,
                episodes_data=analysis_results['episodes'],
                output_dir=clips_dir,
                **self.clip_params
            )
            
            try:
                generated_clips = extractor.extract_all_clips(show_progress=True)
            finally:
                extractor.close()
        
        # Preparar resultados
        result = {
            'episodes': analysis_results['episodes'].to_dict('records'),
            'aggregated_metrics': analysis_results['aggregated'].to_dict('records'),
            'generated_clips': generated_clips,
            'roi_detection_path': roi_json_path,
            'keypoints_detection_path': keypoints_csv
        }
        
        if return_predictions_df:
            result['predictions_df'] = pd.read_csv(keypoints_csv)
        
        return result

    def _save_provided_rois(self, rois: List[Dict]) -> str:
        """Guarda las ROIs proporcionadas como un archivo JSON."""
        roi_data = {}
        for i, roi in enumerate(rois):
            roi_data[f"roi_{i}"] = {
                "name": roi.get("name", f"roi_{i}"),
                "class_id": roi.get("class_id", 0),
                "confidence": 1.0,
                "box": {
                    "x1": roi["x1"],
                    "y1": roi["y1"],
                    "x2": roi["x2"],
                    "y2": roi["y2"]
                },
                "box_normalized": [
                    roi["x1"] / roi["frame_width"],
                    roi["y1"] / roi["frame_height"],
                    roi["x2"] / roi["frame_width"],
                    roi["y2"] / roi["frame_height"]
                ],
                "frame": roi.get("frame", 0)
            }
        
        output_path = os.path.join(self.workdir, "provided_rois.json")
        with open(output_path, 'w') as f:
            json.dump(roi_data, f, indent=4)
        
        return output_path