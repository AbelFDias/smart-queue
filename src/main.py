"""
SMART QUEUE - Sistema de Gestão de Filas com Visão Computacional
Detecção de pessoas usando YOLOv8 local (sem necessidade de API/internet!)

Tecnologias:
- YOLOv8 (ultralytics) para detecção de pessoas
- OpenCV para captura e processamento de vídeo
- YAML para configuração

Autor: Abel Dias e Simão Marcos
"""

import cv2
import yaml
import time
from pathlib import Path
from ultralytics.models.yolo import YOLO
from vision import detect_people, draw_detections, draw_info
from queue_metrics import QueueStats
from tracker import SimpleTracker
from emoncms_client import EmonCMSUploader, EmonCMSConfig

# ============================================
# CONFIGURAÇÃO
# ============================================

# Diretório raiz do projeto
ROOT_DIR = Path(__file__).parent.parent

# Carregar configuração do ficheiro YAML
config_path = ROOT_DIR / 'config' / 'config.yaml'
with open(config_path, 'r') as f:
    CONFIG = yaml.safe_load(f)

# Extrair configurações
VIDEO_SOURCE = CONFIG.get('video_source', 0)
PROCESS_EVERY_N = CONFIG.get('process_every_n_frames', 3)
CONFIDENCE = CONFIG.get('confidence_threshold', 0.5)
YOLO_MODEL = CONFIG.get('yolo_model', 'yolov8n.pt')

# Sub-configurações
_tracking = CONFIG.get('tracking', {})
_counting = CONFIG.get('counting', {})
_display = CONFIG.get('display', {})
_queue = CONFIG.get('queue', {})
_controls = CONFIG.get('controls', {})
_metrics = CONFIG.get('metrics', {})  # será removido quando window_sec migrar para queue
_emoncms = CONFIG.get('emoncms', {})

# Tracking e contagem
TRACK_MATCH_RADIUS_PX = _tracking.get('match_radius_px', 60)
TRACK_TTL = _tracking.get('ttl', 6)
LINE_BAND_PX = _counting.get('line_band_px', 100)
LINE_X_PERCENT = float(_counting.get('line_x_percent', 0.5))
DIRECTION = _counting.get('direction', 'left_to_right')
LINE_COLOR = tuple(_counting.get('line_color_bgr', [0, 0, 255]))
LINE_THICKNESS = int(_counting.get('line_thickness', 2))

# Display/debug
SHOW_BOXES = bool(_display.get('show_boxes', True))
SHOW_BAND = bool(_display.get('show_band', False))
DEBUG = bool(_display.get('debug', False))
SHOW_ETA = bool(_display.get('show_eta', False))
SHOW_METRICS = bool(_display.get('show_metrics', False))

# Fila/ETA
AVG_SERVICE_TIME_SEC = int(_queue.get('avg_service_time_sec', 20))
METRICS_WINDOW_SEC = int(_queue.get('window_sec', _metrics.get('window_sec', 120)))

# EmonCMS
EMON_CONFIG = EmonCMSConfig(
    enabled=bool(_emoncms.get('enabled', False)),
    base_url=_emoncms.get('base_url', 'https://emoncms.org/input/post'),
    api_key=_emoncms.get('api_key', ''),
    node=_emoncms.get('node', 'smart-queue'),
    interval_sec=float(_emoncms.get('interval_sec', 5)),
    timeout_sec=float(_emoncms.get('timeout_sec', 4)),
)
EMON_UPLOADER = EmonCMSUploader(EMON_CONFIG) if EMON_CONFIG.enabled and EMON_CONFIG.api_key else None

# Controlo (teclas configuráveis)
QUIT_KEY = _controls.get('quit', 'q').lower()
DEBUG_KEY = _controls.get('toggle_debug', 'd').lower()
BOXES_KEY = _controls.get('toggle_boxes', 'o').lower()
BAND_KEY = _controls.get('toggle_band', 'b').lower()
ETA_KEY = _controls.get('toggle_eta', 'e').lower()
DIR_KEY = _controls.get('toggle_direction', 'r').lower()
METRICS_KEY = _controls.get('toggle_metrics', 'm').lower()

# Carregar modelo YOLO
# Na primeira execução faz download automático (~6MB para nano)
print("🔄 A carregar modelo YOLO...")

# Resolver caminho do modelo (suporta caminho relativo à raiz do projeto)
_model_cfg_path = Path(YOLO_MODEL)
_resolved_model_path = _model_cfg_path if _model_cfg_path.is_absolute() else (ROOT_DIR / _model_cfg_path)

if _resolved_model_path.exists():
    MODEL = YOLO(str(_resolved_model_path))
    print(f"✅ Modelo carregado de: {_resolved_model_path}")
else:
    # Fallback: usar identificador do modelo (Ultralytics faz download se necessário)
    print(f"ℹ️  Modelo local não encontrado em '{_resolved_model_path}'. A tentar carregar '{YOLO_MODEL}'.")
    MODEL = YOLO(YOLO_MODEL)
    print("✅ Modelo carregado com sucesso (Ultralytics)")

# ============================================
# LINE-CROSSING HELPERS
# ============================================

def _sign(x: float, eps: float = 1e-3) -> int:
    if x > eps:
        return 1
    if x < -eps:
        return -1
    return 0


def _point_side(p, a, b) -> float:
    # cross((b - a), (p - a))
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def _crossed_line(prev_p, curr_p, a, b) -> bool:
    s1 = _sign(_point_side(prev_p, a, b))
    s2 = _sign(_point_side(curr_p, a, b))
    return s1 != 0 and s2 != 0 and s1 != s2


# ============================================
# MAIN
# ============================================

def main():
    """Loop principal do sistema de detecção."""
    print("=" * 70)
    print("  🎯 SMART QUEUE - Sistema de Gestão de Filas")
    print("  📹 Detecção local com YOLOv8 (sem necessidade de internet!)")
    print("=" * 70)
    print()
    
    # Abrir fonte de vídeo
    print(f"📹 A abrir fonte de vídeo: {VIDEO_SOURCE}")
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    
    if not cap.isOpened():
        print(f"❌ ERRO: Não foi possível abrir a fonte de vídeo: {VIDEO_SOURCE}")
        print("\n💡 Dicas:")
        print("  - Verifica se a webcam está conectada")
        print("  - Tenta mudar video_source no config.yaml (0, 1, 2...)")
        print("  - Se usas Iriun, verifica se a app está a correr")
        return
    
    print(f"✅ Fonte de vídeo aberta com sucesso!")
    print()
    print("⚙️  Configuração:")
    print(f"  - Modelo: {YOLO_MODEL}")
    print(f"  - Processar: 1 em cada {PROCESS_EVERY_N} frames")
    print(f"  - Confiança mínima: {CONFIDENCE:.0%}")
    print()
    print("🎮 Controlos:")
    print(f"  {QUIT_KEY.upper()} - Sair")
    print(f"  {DEBUG_KEY.upper()} - Debug ON/OFF")
    print(f"  {BOXES_KEY.upper()} - Boxes ON/OFF")
    print(f"  {BAND_KEY.upper()} - Banda ON/OFF")
    print(f"  {ETA_KEY.upper()} - ETA ON/OFF")
    print(f"  {DIR_KEY.upper()} - Alternar direção")
    print(f"  {METRICS_KEY.upper()} - Métricas ON/OFF")
    if EMON_UPLOADER:
        print(f"  🌐 Upload emonCMS a cada {EMON_CONFIG.interval_sec}s (node '{EMON_CONFIG.node}')")
    elif EMON_CONFIG.enabled and not EMON_CONFIG.api_key:
        print("⚠️  emonCMS está ativado mas falta api_key. Upload desativado.")
    print()
    print("=" * 70)
    print()
    
    # Estado
    frame_counter = 0
    last_detections = []
    fps = 0
    total_frames = 0
    start_time = time.time()
    last_tick_time = start_time
    # Copiar opções de visualização/direção para variáveis mutáveis locais
    show_boxes = SHOW_BOXES
    show_band = SHOW_BAND
    debug = DEBUG
    direction = DIRECTION
    show_eta = SHOW_ETA
    show_metrics = SHOW_METRICS
    # Estado para contagem por linha
    tracker = SimpleTracker(match_radius_px=TRACK_MATCH_RADIUS_PX, ttl=TRACK_TTL)
    entry_count = 0
    queue_stats = QueueStats(window_sec=METRICS_WINDOW_SEC)
    # Linha vertical (fila esquerda → direita), inicializa com base no tamanho do frame
    line_a = None  # (x, y)
    line_b = None  # (x, y)
    
    def log_debug(msg: str):
        if debug:
            print(msg)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Erro ao ler frame")
                break

            # Inicializar linha vertical após obter dimensões do frame
            if line_a is None:
                H, W = frame.shape[:2]
                x_mid = max(0, min(W - 1, int(W * LINE_X_PERCENT)))
                line_a = (x_mid, 0)
                line_b = (x_mid, H)

            # Atualizar drenagem do modelo simulado por tempo decorrido
            now = time.time()
            dt = now - last_tick_time
            last_tick_time = now
            queue_stats.tick(dt, AVG_SERVICE_TIME_SEC)
            
            total_frames += 1
            frame_counter += 1
            
            # Calcular FPS
            elapsed = time.time() - start_time
            if elapsed > 0:
                fps = total_frames / elapsed
            
            # Fazer detecção a cada N frames (para otimizar performance)
            if frame_counter >= PROCESS_EVERY_N:
                frame_counter = 0
                
                try:
                    last_detections = detect_people(MODEL, frame, CONFIDENCE)
                    num = len(last_detections)
                    log_debug(f"📊 [Frame {total_frames}] Detectadas {num} pessoa(s) | FPS: {fps:.1f}")

                    # Calcular centroides atuais
                    curr_centroids = [
                        ((d['x1'] + d['x2']) // 2, (d['y1'] + d['y2']) // 2)
                        for d in last_detections
                    ]
                    # sem necessidade de guardar centroides para fila simulada

                    # Atualizar tracker e obter pares (track_id, prev_c, curr_c)
                    matches = tracker.update(curr_centroids)

                    # Contagem com filtro de direção (left -> right) e banda
                    x_line = line_a[0]
                    for _, prev_c, curr_c in matches:
                        # banda em torno da linha
                        if (abs(prev_c[0] - x_line) > LINE_BAND_PX and
                                abs(curr_c[0] - x_line) > LINE_BAND_PX):
                            continue
                        # cruzamento geométrico
                        if _crossed_line(prev_c, curr_c, line_a, line_b):
                            # direção válida
                            if direction == 'left_to_right' and curr_c[0] > prev_c[0]:
                                entry_count += 1
                                queue_stats.on_entry()
                            elif direction == 'right_to_left' and curr_c[0] < prev_c[0]:
                                entry_count += 1
                                queue_stats.on_entry()
                except Exception as e:
                    print(f"⚠️  Erro na detecção: {e}")
                    last_detections = []
            
            # Desenhar
            if last_detections and show_boxes:
                frame = draw_detections(frame, last_detections)

            # Calcular fila e ETA via modelo simulado
            queue_len = queue_stats.current_queue_len()
            eta_sec = queue_stats.eta_for_new(queue_len, AVG_SERVICE_TIME_SEC)
            # Construir dicionário de métricas (para emonCMS ou logs)
            metrics_dict = queue_stats.build_metrics(
                fps=fps,
                entries=entry_count,
                direction=direction,
                people_detected=len(last_detections),
                avg_service_time_sec=AVG_SERVICE_TIME_SEC,
            )

            frame = draw_info(
                frame,
                fps,
                len(last_detections),
                entry_count,
                direction,
                LINE_BAND_PX,
                queue_len,
                eta_sec,
                debug,
                show_eta,
                show_metrics,
                metrics_dict,
            )

            if EMON_UPLOADER:
                EMON_UPLOADER.maybe_send(metrics_dict)

            # Desenhar linha de contagem (após overlay para ficar visível)
            if line_a is not None and line_b is not None:
                cv2.line(frame, line_a, line_b, LINE_COLOR, LINE_THICKNESS)
                # Desenhar banda de avaliação
                if show_band:
                    x_line = line_a[0]
                    xa = max(0, x_line - LINE_BAND_PX)
                    xb = min(frame.shape[1] - 1, x_line + LINE_BAND_PX)
                    band_overlay = frame.copy()
                    cv2.rectangle(band_overlay, (xa, 0), (xb, frame.shape[0]-1), (255, 255, 0), -1)
                    cv2.addWeighted(band_overlay, 0.15, frame, 0.85, 0, frame)

            # Mostrar resultado
            cv2.imshow('Smart Queue - Sistema de Detecção', frame)
            
            # Verificar tecla pressionada
            key = cv2.waitKey(1) & 0xFF
            key_char = chr(key).lower()
            if key_char == QUIT_KEY:
                print("\n🛑 A encerrar...")
                break
            elif key_char == DEBUG_KEY:
                debug = not debug
                print(f"🐞 Debug: {'ON' if debug else 'OFF'}")
            elif key_char == BOXES_KEY:
                show_boxes = not show_boxes
                print(f"🧰 Boxes: {'ON' if show_boxes else 'OFF'}")
            elif key_char == BAND_KEY:
                show_band = not show_band
                print(f"📏 Banda: {'ON' if show_band else 'OFF'}")
            elif key_char == ETA_KEY:
                show_eta = not show_eta
                print(f"⏱️  ETA: {'ON' if show_eta else 'OFF'}")
            elif key_char == DIR_KEY:
                direction = 'right_to_left' if direction == 'left_to_right' else 'left_to_right'
                print(f"↔️  Direção: {direction}")
            elif key_char == METRICS_KEY:
                show_metrics = not show_metrics
                print(f"📈 Métricas: {'ON' if show_metrics else 'OFF'}")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo utilizador (Ctrl+C)")
    
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
    
    finally:
        # Libertar recursos
        cap.release()
        cv2.destroyAllWindows()
        
        # Estatísticas finais
        elapsed_time = time.time() - start_time
        print()
        print("=" * 70)
        print("📊 Estatísticas da sessão:")
        print(f"  - Total de frames processados: {total_frames}")
        print(f"  - FPS médio: {fps:.1f}")
        print(f"  - Tempo total: {elapsed_time:.1f}s")
        print("=" * 70)
        print("✅ Sistema encerrado com sucesso!")


if __name__ == "__main__":
    main()
