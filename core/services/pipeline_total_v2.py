import os
import cv2
import json
import pandas as pd
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from shapely.geometry import Point, box as BoundingBox
from typing import Dict, List, Union, Optional
import logging
from collections import defaultdict
from math import sqrt
from tqdm import tqdm

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================
# PRIMERA PARTE: Detección de ROIs (Modelo 1)
# ==============================================

def detect_rois(video_path: str, model_path: str, output_dir: str, target_frame: int = 20) -> str:
    """Detecta ROIs en un frame específico del video."""
    model = YOLO(model_path)
    Path(output_dir).mkdir(exist_ok=True)
    
    CLASS_NAMES = {
        0: "tapa_azul",
        1: "tapa_naranja"
    }
    
    def normalize_coordinates(box, width, height):
        return [box[0]/width, box[1]/height, box[2]/width, box[3]/height]
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Error al abrir el video: {video_path}")
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    ret, frame = cap.read()
    
    if not ret:
        raise ValueError(f"Error al leer el frame {target_frame}")
    
    results = model(frame)
    rois_data = {}
    
    detections = sorted(results[0].boxes, key=lambda x: float(x.conf), reverse=True)
    selected_detections = []
    class_ids_seen = set()
    
    for detection in detections:
        class_id = int(detection.cls)
        if class_id not in class_ids_seen:
            selected_detections.append(detection)
            class_ids_seen.add(class_id)
            if len(selected_detections) == 2:
                break
    
    for i, detection in enumerate(selected_detections):
        bbox = detection.xyxy[0].tolist()
        class_id = int(detection.cls)
        
        rois_data[f"roi_{i}"] = {
            "name": CLASS_NAMES.get(class_id, f"unknown_{class_id}"),
            "class_id": class_id,
            "confidence": float(detection.conf),
            "box": {
                "x1": bbox[0],
                "y1": bbox[1],
                "x2": bbox[2],
                "y2": bbox[3]
            },
            "box_normalized": normalize_coordinates(bbox, cap.get(3), cap.get(4)),
            "frame": target_frame
        }
    
    output_json = Path(output_dir) / f"rois_frame_{target_frame}.json"
    with open(output_json, 'w') as f:
        json.dump(rois_data, f, indent=4)
    
    cv2.imwrite(str(Path(output_dir) / f"frame_{target_frame}_pred.jpg"), results[0].plot())
    cap.release()
    
    logger.info(f"ROIs detectadas: {len(rois_data)}")
    logger.info(f"Resultados guardados en: {output_json}")
    return str(output_json)

# ==============================================
# SEGUNDA PARTE: Detección de Keypoints (Modelo 2)
# ==============================================

def detect_keypoints(video_path: str, model_path: str, output_csv: str = "predicciones_completas.csv") -> str:
    """Detecta keypoints conservando siempre una detección por frame (la mejor) sin filtrado por confianza."""
    model = YOLO(model_path)
    keypoints_names = ["cabeza", "nariz", "oreja_izq", "oreja_der", "cuello", "base_cola"]
    
    results = model.predict(source=video_path, stream=True, verbose=False)
    all_data = []
    
    for frame_idx, result in enumerate(tqdm(results, desc="Procesando video")):
        boxes = result.boxes
        keypoints = result.keypoints
        
        # Frame sin detecciones
        if boxes is None or len(boxes) == 0:
            row = {
                "frame": frame_idx,
                "class_id": None,
                "confidence": None,
                "bbox_xc": None,
                "bbox_yc": None,
                "bbox_w": None,
                "bbox_h": None,
            }
            for name in keypoints_names:
                row[f"{name}_x"] = None
                row[f"{name}_y"] = None
                row[f"{name}_v"] = None
            all_data.append(row)
            continue
        
        # Para cada frame, conservar solo la detección con mayor confianza
        best_detection_idx = np.argmax([float(box.conf) for box in boxes])
        box = boxes[best_detection_idx]
        
        row = {
            "frame": frame_idx,
            "class_id": int(box.cls.item()),
            "confidence": float(box.conf.item()),
            "bbox_xc": round(box.xywh[0][0].item(), 6),
            "bbox_yc": round(box.xywh[0][1].item(), 6),
            "bbox_w": round(box.xywh[0][2].item(), 6),
            "bbox_h": round(box.xywh[0][3].item(), 6),
        }
        
        # Keypoints de la mejor detección
        if keypoints is not None:
            kpts_xy = keypoints.xy[best_detection_idx].reshape(-1).tolist()
            kpts_v = keypoints.conf[best_detection_idx].reshape(-1).tolist()
            for i, name in enumerate(keypoints_names):
                row[f"{name}_x"] = round(kpts_xy[i*2], 6) if i*2 < len(kpts_xy) else None
                row[f"{name}_y"] = round(kpts_xy[i*2+1], 6) if i*2+1 < len(kpts_xy) else None
                row[f"{name}_v"] = round(kpts_v[i], 6) if i < len(kpts_v) else None
        else:
            for name in keypoints_names:
                row[f"{name}_x"] = row[f"{name}_y"] = row[f"{name}_v"] = None
        
        all_data.append(row)
    
    # Crear DataFrame y asegurar orden por frame
    df = pd.DataFrame(all_data).sort_values("frame").reset_index(drop=True)
    
    # Eliminar posibles frames duplicados (por si acaso)
    df = df.drop_duplicates("frame", keep="first")
    
    df.to_csv(output_csv, index=False)
    logger.info(f"Resultados guardados en: {output_csv}")
    logger.info(f"Total frames procesados: {len(df)}")
    logger.info(f"Frames con detecciones: {len(df[df['class_id'].notna()])}")
    return output_csv

# ==============================================
# TERCERA PARTE: Análisis de Interacciones
# ==============================================

class ROIAnalyzer:
    def __init__(self, data_path: str, json_path: str, video_path: str,
                min_interaction_frames: int = 4, 
                max_gap_frames: int = 3,
                max_class_change_frames: int = 3,
                proximity_threshold: int = 40):
        self.df = pd.read_csv(data_path)
        self._process_dataframe()
        self.rois = self._load_rois(json_path)
        self.min_interaction_frames = min_interaction_frames
        self.max_gap_frames = max_gap_frames
        self.max_class_change_frames = max_class_change_frames
        self.proximity_threshold = proximity_threshold
        self.video_path = video_path
        self.video_fps = self._get_video_fps()
        logger.info(f"FPS detectado para análisis: {self.video_fps}")
    
    def _get_video_fps(self) -> float:
        """Obtiene el FPS real del video con verificación robusta."""
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"No se pudo abrir el video: {self.video_path}")
        
        # Intentar obtener FPS de metadatos
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Si el FPS no es válido, calcularlo manualmente
        if fps <= 0:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
            duration = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
            fps = total_frames / duration if duration > 0 else 30.0
            logger.warning(f"FPS calculado manualmente: {fps:.2f} (no se encontró en metadatos)")
        
        cap.release()
        return float(fps)
    
    def _process_dataframe(self):
        """Procesamiento del DataFrame sin filtrado por confianza."""
        required_columns = ['frame', 'class_id', 'confidence'] + \
                        [f"{name}_x" for name in ["cabeza", "nariz", "oreja_izq", "oreja_der", "cuello", "base_cola"]]
        
        for col in required_columns:
            if col not in self.df.columns:
                raise ValueError(f"Columna requerida no encontrada: {col}")
        
        # Eliminar frames duplicados (conservar el primero que aparezca)
        original_frames = len(self.df)
        self.df = self.df.drop_duplicates('frame', keep='first') \
                        .sort_values('frame') \
                        .reset_index(drop=True)
        
        if original_frames - len(self.df) > 0:
            logger.info(f"Eliminadas {original_frames - len(self.df)} detecciones duplicadas")
        
        self._validate_frame_sequence()
    
    def _validate_frame_sequence(self):
        frames = self.df['frame'].values
        diffs = np.diff(frames)
        
        if np.any(diffs <= 0):
            logger.warning("¡Advertencia: Los frames no están estrictamente crecientes!")
        
        if len(frames) != len(set(frames)):
            dup_frames = self.df['frame'][self.df['frame'].duplicated()].unique()
            logger.warning(f"¡Advertencia: Frames duplicados encontrados y procesados: {dup_frames}")
    
    def _load_rois(self, json_path: str) -> Dict[str, dict]:
        rois = {}
        with open(json_path) as f:
            data = json.load(f)
            for roi_key, roi_data in data.items():
                box_data = roi_data["box"]
                rois[roi_data["name"]] = {
                    "bbox": BoundingBox(float(box_data["x1"]), float(box_data["y1"]), 
                                      float(box_data["x2"]), float(box_data["y2"])),
                    "class_id": roi_data["class_id"]
                }
        return rois
    
    def _is_point_in_roi(self, x: float, y: float, roi: BoundingBox) -> bool:
        if pd.isna(x) or pd.isna(y):
            return False
        return roi.contains(Point(x, y))
    
    def _is_point_near_roi(self, x: float, y: float, roi: BoundingBox) -> bool:
        if pd.isna(x) or pd.isna(y):
            return False
            
        point = Point(x, y)
        if roi.contains(point):
            return True
            
        min_x, min_y, max_x, max_y = roi.bounds
        closest_x = max(min_x, min(x, max_x))
        closest_y = max(min_y, min(y, max_y))
        distance = sqrt((x - closest_x)**2 + (y - closest_y)**2)
        
        return distance <= self.proximity_threshold
    
    def _detect_interactions(self) -> pd.DataFrame:
        df = self.df.copy()
        
        for roi_name, roi_info in self.rois.items():
            roi_bbox = roi_info["bbox"]
            roi_class = roi_info["class_id"]
            x_col, y_col = 'nariz_x', 'nariz_y'
            
            if x_col in df.columns and y_col in df.columns:
                if roi_class == 0:
                    df[f'interaction_{roi_name}'] = df.apply(
                        lambda r: self._is_point_near_roi(r[x_col], r[y_col], roi_bbox), 
                        axis=1
                    )
                else:
                    df[f'interaction_{roi_name}'] = df.apply(
                        lambda r: self._is_point_in_roi(r[x_col], r[y_col], roi_bbox), 
                        axis=1
                    )
            else:
                df[f'interaction_{roi_name}'] = False
        
        return df
    
    def _find_episodes(self, frame_series: pd.Series, interaction_series: pd.Series, 
                      class_series: pd.Series) -> List[Dict]:
        episodes = []
        current_episode = None
        consecutive_interaction = 0
        remaining_gap_tolerance = self.max_gap_frames
        current_class = None
        class_change_counter = 0
        
        for i, (frame, is_interacting, class_id) in enumerate(zip(
            frame_series, interaction_series, class_series
        )):
            if current_episode is not None:
                if class_id == current_class:
                    class_change_counter = 0
                else:
                    class_change_counter += 1
                    if class_change_counter > self.max_class_change_frames:
                        self._finalize_episode(episodes, current_episode, frame_series.iloc[i-1])
                        current_episode = None
                        consecutive_interaction = 0
                        remaining_gap_tolerance = self.max_gap_frames
                        current_class = None
                        continue
                
                if is_interacting:
                    remaining_gap_tolerance = self.max_gap_frames
                else:
                    if remaining_gap_tolerance > 0:
                        remaining_gap_tolerance -= 1
                    else:
                        self._finalize_episode(episodes, current_episode, frame_series.iloc[i-1])
                        current_episode = None
            
            if current_episode is None:
                if is_interacting:
                    consecutive_interaction += 1
                    if consecutive_interaction >= self.min_interaction_frames:
                        current_episode = {
                            'start_frame': frame_series.iloc[i - consecutive_interaction + 1],
                            'class_id': class_series.iloc[i - consecutive_interaction + 1:i+1].mode()[0],
                        }
                        current_class = current_episode['class_id']
                        consecutive_interaction = 0
                else:
                    consecutive_interaction = 0
        
        if current_episode is not None:
            self._finalize_episode(episodes, current_episode, frame_series.iloc[-1])
        
        return [ep for ep in episodes if ep['duration'] > 0]
    
    def _finalize_episode(self, episodes: List[Dict], episode: Dict, end_frame: int):
        episode['end_frame'] = end_frame
        episode['duration'] = end_frame - episode['start_frame'] + 1
        episodes.append(episode)
    
    def analyze(self) -> Dict[str, pd.DataFrame]:
        df = self._detect_interactions()
        episodes = []
        
        for roi_name in self.rois:
            roi_episodes = self._find_episodes(
                df['frame'],
                df[f'interaction_{roi_name}'],
                df['class_id']
            )
            for ep in roi_episodes:
                ep['object_roi'] = roi_name
                ep['duration_seconds'] = ep['duration'] / self.video_fps
            episodes.extend(roi_episodes)
        
        episodes_sorted = sorted(episodes, key=lambda x: x['start_frame'])
        aggregated_metrics = self._calculate_aggregated_metrics(episodes_sorted)
        
        return {
            'episodes': pd.DataFrame(episodes_sorted),
            'aggregated': aggregated_metrics
        }
    
    def _calculate_aggregated_metrics(self, episodes: List[Dict]) -> pd.DataFrame:
        metrics = defaultdict(lambda: {
            'total_episodes': 0,
            'sum_frames': 0,
            'total_time_seconds': 0.0
        })
        
        class_0_episodes = [ep for ep in episodes if ep['class_id'] == 0]
        
        for ep in class_0_episodes:
            key = (ep['class_id'], ep['object_roi'])
            metrics[key]['total_episodes'] += 1
            metrics[key]['sum_frames'] += ep['duration']
            metrics[key]['total_time_seconds'] += ep['duration'] / self.video_fps
        
        agg_df = pd.DataFrame([
            {
                'class_id': k[0],
                'object_roi': k[1],
                **v
            }
            for k, v in metrics.items()
        ])
        
        return agg_df.sort_values(['class_id', 'object_roi'])
    
    def save_results(self, results: Dict[str, pd.DataFrame], output_base_path: str):
        episodes_path = f"{output_base_path}_episodes.csv"
        results['episodes'].to_csv(episodes_path, index=False)
        logger.info(f"Episodios detallados guardados en: {episodes_path}")
        
        aggregated_path = f"{output_base_path}_aggregated.csv"
        results['aggregated'].to_csv(aggregated_path, index=False)
        logger.info(f"Métricas agregadas guardados en: {aggregated_path}")

# ==============================================
# CUARTA PARTE: Extracción de Clips
# ==============================================

class VideoClipExtractor:
    def __init__(self, video_path: str, episodes_data: List[Dict], 
                 output_dir: str, margin_frames: int = 5,
                 fps: Optional[float] = None):
        """Inicializa el extractor de clips.
        
        Args:
            video_path: Ruta al video original
            episodes_data: Lista de episodios detectados
            output_dir: Carpeta de salida para los clips
            margin_frames: Frames de margen a añadir
            fps: FPS del video (None para auto-detectar)
        """
        self.video_path = video_path
        self.output_dir = output_dir
        self.margin_frames = margin_frames
        self.fps = fps 
        
        if isinstance(episodes_data, pd.DataFrame):
            self.episodes = episodes_data.to_dict('records')
        else:
            self.episodes = episodes_data
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise ValueError(f"No se pudo abrir el video: {self.video_path}")
        
        self.video_fps = self.fps if self.fps is not None else self._get_video_fps()
        logger.info(f"FPS detectado para extracción: {self.video_fps}")
        
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    def _get_video_fps(self) -> float:
        """Obtiene el FPS real del video."""
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Si el FPS no es válido, calcularlo manualmente
        if fps <= 0:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
            duration = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
            fps = total_frames / duration if duration > 0 else 30.0
            logger.warning(f"FPS calculado manualmente: {fps:.2f}")
        
        cap.release()
        return float(fps)
    
    def _get_clip_filename(self, episode: Dict, episode_id: int) -> str:
        class_id = episode.get('class_id', 'unknown')
        object_roi = episode.get('object_roi', 'unknown')
        return f"clip_{episode_id}_class_{class_id}_roi_{object_roi}.mp4"
    
    def _get_adjusted_frames(self, start_frame: int, end_frame: int) -> tuple[int, int]:
        new_start = max(0, start_frame - self.margin_frames)
        new_end = min(self.total_frames - 1, end_frame + self.margin_frames)
        return new_start, new_end
    
    def extract_clip(self, episode: Dict, episode_id: int) -> str:
        start_frame = episode['start_frame']
        end_frame = episode['end_frame']
        adjusted_start, adjusted_end = self._get_adjusted_frames(start_frame, end_frame)
        
        clip_filename = self._get_clip_filename(episode, episode_id)
        output_path = os.path.join(self.output_dir, clip_filename)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(
            output_path, 
            fourcc, 
            self.video_fps, 
            (self.frame_width, self.frame_height)
        )

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, adjusted_start)
        
        frames_written = 0
        for frame_num in range(adjusted_start, adjusted_end + 1):
            ret, frame = self.cap.read()
            if not ret:
                logger.warning(f"Frame {frame_num} no pudo leerse")
                break
            out.write(frame)
            frames_written += 1
        
        out.release()
        logger.debug(f"Clip {episode_id}: Esperados {adjusted_end-adjusted_start+1} frames, escritos {frames_written}")
        return output_path
    
    def extract_all_clips(self, show_progress: bool = True) -> List[str]:
        generated_clips = []
        
        iterator = enumerate(self.episodes)
        if show_progress:
            iterator = tqdm(iterator, total=len(self.episodes), desc="Extrayendo clips")
        
        for idx, episode in iterator:
            try:
                clip_path = self.extract_clip(episode, idx)
                generated_clips.append(clip_path)
            except Exception as e:
                logger.error(f"Error procesando episodio {idx}: {str(e)}")
        
        return generated_clips
    
    def close(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

# ==============================================
# FUNCIÓN PRINCIPAL
# ==============================================

def main():
    # Configuración (sin video_fps)
    config = {
        'video_path': 'TS12-2024-02-02.mp4',
        'roi_model_path': 'bestseg.pt',
        'keypoints_model_path': 'best.pt',
        'output_dir': 'resultadosTS12',
        'min_interaction_frames': 20,
        'max_gap_frames': 8,
        'max_class_change_frames': 3,
        'proximity_threshold': 5,
        'clip_margin_frames': 3
    }
    
    os.makedirs(config['output_dir'], exist_ok=True)
    
    # 1. Detección de ROIs
    logger.info("=== Ejecutando detección de ROIs ===")
    roi_json = detect_rois(
        video_path=config['video_path'],
        model_path=config['roi_model_path'],
        output_dir=config['output_dir'],
        target_frame=20
    )
    
    # 2. Detección de keypoints
    logger.info("\n=== Ejecutando detección de keypoints ===")
    keypoints_csv = os.path.join(config['output_dir'], 'predicciones_completas.csv')
    detect_keypoints(
        video_path=config['video_path'],
        model_path=config['keypoints_model_path'],
        output_csv=keypoints_csv
    )
    
    # 3. Análisis de interacciones
    logger.info("\n=== Analizando interacciones ===")
    analyzer = ROIAnalyzer(
        data_path=keypoints_csv,
        json_path=roi_json,
        video_path=config['video_path'],
        min_interaction_frames=config['min_interaction_frames'],
        max_gap_frames=config['max_gap_frames'],
        max_class_change_frames=config['max_class_change_frames'],
        proximity_threshold=config['proximity_threshold']
    )
    
    results = analyzer.analyze()
    results_path = os.path.join(config['output_dir'], 'resultados_interaccion')
    analyzer.save_results(results, results_path)
    
    # Mostrar resumen
    print("\n✅ Análisis completado")
    print(f"Total episodios detectados (todos): {len(results['episodes'])}")
    print(f"Total episodios class_id=0: {len(results['episodes'][results['episodes']['class_id'] == 0])}")
    print("\nResumen de métricas agregadas (solo class_id=0):")
    print(results['aggregated'].to_string(index=False))
    
    # 4. Extracción de clips
    logger.info("\n=== Extrayendo clips de interacción ===")
    clips_dir = os.path.join(config['output_dir'], 'clips_interaccion')
    extractor = VideoClipExtractor(
        video_path=config['video_path'],
        episodes_data=results['episodes'],
        output_dir=clips_dir,
        margin_frames=config['clip_margin_frames']
    )

    try:
        generated_clips = extractor.extract_all_clips(show_progress=True)
        
        # Cálculo del tiempo total CORREGIDO
        if not results['episodes'].empty:
            class_0_episodes = results['episodes'][results['episodes']['class_id'] == 0]
            total_clip_time = sum(
                (row['end_frame'] - row['start_frame'] + 1 + 2*config['clip_margin_frames']) / extractor.video_fps
                for _, row in class_0_episodes.iterrows()
            )
        else:
            total_clip_time = 0
        
        print(f"\nExtracción completada. Se generaron {len(generated_clips)} clips.")
        print(f"Los clips se guardaron en: {os.path.abspath(clips_dir)}")
        print(f"\nComparación de tiempos (solo class_id=0):")
        print(f"- Tiempo total calculado: {results['aggregated']['total_time_seconds'].sum():.2f} segundos")
        print(f"- Tiempo total en clips (con márgenes): {total_clip_time:.2f} segundos")
        
    finally:
        extractor.close()  

if __name__ == "__main__":
    main()