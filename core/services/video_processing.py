import os
import cv2
import logging
from django.core.files.storage import default_storage
from django.core.files import File
from django.apps import apps
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class VideoProcessingService:
    BEHAVIOR_MAPPING = {
        0: "exploracion",
        1: "desplazamiento",
        2: "acicalamiento",
        3: "erguido"
    }

    def __init__(self, model_path: str, segmenter_path: str):
        self.model_path = model_path
        self.segmenter_path = segmenter_path

    def process(self, video_path: str, experiment_id: int) -> Dict:
        try:
            logger.info(f"Iniciando procesamiento para experimento {experiment_id}")
            
            # 1. Preparar entorno
            workdir = self._prepare_workspace(video_path, experiment_id)
            
            # 2. Ejecutar pipeline
            pipeline_result = self._execute_behavior_pipeline(video_path, workdir)
            
            # 3. Procesar resultados y crear registros
            result = self._process_pipeline_results(
                pipeline_result, 
                video_path, 
                experiment_id
            )
            
            logger.info(f"Procesamiento completado. {result['total_clips']} clips generados")
            return result
            
        except Exception as e:
            logger.error(f"Error procesando video {video_path}: {str(e)}")
            raise

    def _prepare_workspace(self, video_path: str, experiment_id: int) -> str:
        base_dir = os.path.dirname(video_path)
        workdir = os.path.join(base_dir, "processing", str(experiment_id))
        os.makedirs(workdir, exist_ok=True)
        return workdir

    def _execute_behavior_pipeline(self, video_path: str, workdir: str) -> Dict:
        from core.services.video_behavior_pipeline import VideoProcessingPipeline
        
        pipeline = VideoProcessingPipeline(
            model_path=self.model_path,
            workdir=workdir,
            segmenter_model_path=self.segmenter_path,
            analyzer_params={
                'min_interaction_frames': 4,
                'max_gap_frames': 20,
                'max_class_change_frames': 6,
                'proximity_threshold': 40
            },
            clip_params={
                'margin_frames': 10,
                'fps': None
            },
            segmenter_params={
                'frame_index': 20,
                'confidence': 0.3,
                'max_objects': 2
            }
        )
        
        return pipeline.run(
            video_path=video_path,
            rois=None,
            export_clips=True,
            autosegment_if_missing=True,
            return_predictions_df=False
        )

    def _process_pipeline_results(self, result: Dict, video_path: str, experiment_id: int) -> Dict:
        fps = self._get_video_fps(video_path)
        clips_metadata = []
        
        for clip_path, episode in zip(result['generated_clips'], result['episodes']):
            clip_meta = self._process_single_clip(
                clip_path=clip_path,
                episode=episode,
                fps=fps,
                experiment_id=experiment_id
            )
            clips_metadata.append(clip_meta)
        
        return {
            'experiment_id': experiment_id,
            'total_clips': len(clips_metadata),
            'fps': fps,
            'clips': clips_metadata
        }

    def _get_video_fps(self, video_path: str) -> float:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        cap.release()
        return float(fps)

    def _process_single_clip(self, clip_path: str, episode: Dict, fps: float, experiment_id: int) -> Dict:
        saved_path = self._store_clip_file(clip_path, experiment_id)
        metadata = self._extract_clip_metadata(episode, fps)
        
        clip_id = self._create_clip_record(
            experiment_id=experiment_id,
            clip_path=saved_path,
            metadata=metadata,
            behavior_id=episode.get('class_id')
        )
        
        return {
            'clip_id': clip_id,
            'path': saved_path,
            **metadata
        }

    def _store_clip_file(self, clip_path: str, experiment_id: int) -> str:
        filename = os.path.basename(clip_path)
        storage_path = os.path.join(
            "experiments",
            str(experiment_id),
            "clips",
            filename
        )
        
        with open(clip_path, 'rb') as f:
            return default_storage.save(storage_path, File(f))

    def _extract_clip_metadata(self, episode: Dict, fps: float) -> Dict:
        def frames_to_seconds(frames):
            return round(float(frames) / fps, 3)
        
        start_frame = episode['start_frame']
        end_frame = episode['end_frame']
        
        return {
            'start_time': frames_to_seconds(start_frame),
            'end_time': frames_to_seconds(end_frame),
            'duration': frames_to_seconds(end_frame - start_frame),
            'object_roi': episode.get('object_roi', 'objeto_1'),
            'behavior_class': episode.get('class_id')
        }

    def _create_clip_record(self, experiment_id: int, clip_path: str, metadata: Dict, behavior_id: Optional[int]) -> int:
        Clip = apps.get_model('core', 'Clip')
        Behavior = apps.get_model('core', 'Behavior')
        ExperimentObject = apps.get_model('core', 'ExperimentObject')
        
        object_ref = self._extract_object_reference(metadata['object_roi'])
        experiment_object = self._get_or_create_experiment_object(
            experiment_id=experiment_id,
            reference=object_ref
        )
        
        behavior = self._get_behavior(behavior_id)
        
        clip = Clip.objects.create(
            experiment_id=experiment_id,
            experiment_object_id=experiment_object.id,
            behavior_id=behavior.id if behavior else None,
            video_clip=clip_path,
            start_time=metadata['start_time'],
            end_time=metadata['end_time'],
            duration=metadata['duration'],
            valid=True
        )
        
        return clip.id

    def _extract_object_reference(self, roi_name: str) -> int:
        try:
            return int(roi_name.split('_')[-1])
        except (IndexError, ValueError):
            logger.warning(f"Formato de ROI inválido: {roi_name}, usando default 1")
            return 1

    def _get_or_create_experiment_object(self, experiment_id: int, reference: int):
        ExperimentObject = apps.get_model('core', 'ExperimentObject')
        
        try:
            return ExperimentObject.objects.get(
                experiment_id=experiment_id,
                reference=reference
            )
        except ExperimentObject.DoesNotExist:
            logger.info(f"Creando objeto {reference} para experimento {experiment_id}")
            Label = ExperimentObject.Label
            return ExperimentObject.objects.create(
                experiment_id=experiment_id,
                reference=reference,
                name=f"Objeto {reference}",
                label=Label.NOVEL if reference == 1 else Label.FAMILIAR,
                time=0.0
            )

    def _get_behavior(self, class_id: Optional[int]):
        Behavior = apps.get_model('core', 'Behavior')
        
        if class_id is None:
            return Behavior.objects.first()
            
        behavior_name = self.BEHAVIOR_MAPPING.get(int(class_id))
        if behavior_name:
            return Behavior.objects.filter(name__iexact=behavior_name).first()
        
        return Behavior.objects.first()