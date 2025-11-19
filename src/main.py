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
from tracker import SimpleTracker

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

# Parâmetros (fáceis de ajustar)
LINE_COLOR = (0, 0, 255)  # BGR (vermelho)
LINE_THICKNESS = 2

# Tracking e contagem
TRACK_MATCH_RADIUS_PX = 60  # raio para associar centroides entre frames
TRACK_TTL = 6               # ciclos de deteção até expirar track
LINE_BAND_PX = 100          # banda de avaliação à volta da linha
DIRECTION = 'left_to_right' # direção válida para contar

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
# FUNÇÕES
# ============================================

def draw_info(frame, fps, num_people):
    # esta função agora é importada de vision.py; manter stub se necessário
    return draw_info(frame, fps, num_people)


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
    print("  Q - Sair")
    print()
    print("=" * 70)
    print()
    
    # Estado
    frame_counter = 0
    last_detections = []
    fps = 0
    total_frames = 0
    start_time = time.time()
    # Estado para contagem por linha
    tracker = SimpleTracker(match_radius_px=TRACK_MATCH_RADIUS_PX, ttl=TRACK_TTL)
    entry_count = 0
    # Linha vertical (fila esquerda → direita), inicializa com base no tamanho do frame
    line_a = None  # (x, y)
    line_b = None  # (x, y)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Erro ao ler frame")
                break

            # Inicializar linha vertical após obter dimensões do frame
            if line_a is None:
                H, W = frame.shape[:2]
                x_mid = W // 2
                line_a = (x_mid, 0)
                line_b = (x_mid, H)
            
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
                    print(f"📊 [Frame {total_frames}] Detectadas {num} pessoa(s) | FPS: {fps:.1f}")

                    # Calcular centroides atuais
                    curr_centroids = [
                        ((d['x1'] + d['x2']) // 2, (d['y1'] + d['y2']) // 2)
                        for d in last_detections
                    ]

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
                            if DIRECTION == 'left_to_right' and curr_c[0] > prev_c[0]:
                                entry_count += 1
                except Exception as e:
                    print(f"⚠️  Erro na detecção: {e}")
                    last_detections = []
            
            # Desenhar
            if last_detections:
                frame = draw_detections(frame, last_detections)
            
            frame = draw_info(frame, fps, len(last_detections))

            # Desenhar linha de contagem (após overlay para ficar visível)
            if line_a is not None and line_b is not None:
                cv2.line(frame, line_a, line_b, LINE_COLOR, LINE_THICKNESS)

            # Mostrar total de entradas (no HUD)
            cv2.putText(frame, f"Entradas: {entry_count}", (20, 85),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Mostrar resultado
            cv2.imshow('Smart Queue - Sistema de Detecção', frame)
            
            # Verificar tecla pressionada
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                print("\n🛑 A encerrar...")
                break
    
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
