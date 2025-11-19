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

def detect_people(frame):
    """
    Detecta pessoas num frame usando YOLOv8 local.
    
    Args:
        frame: Frame numpy array (BGR) do OpenCV
    
    Returns:
        Lista de dicionários com detecções:
        [{
            'x1': int, 'y1': int,  # Canto superior esquerdo
            'x2': int, 'y2': int,  # Canto inferior direito
            'confidence': float    # Confiança da detecção (0-1)
        }, ...]
    """
    # Inferência YOLO
    # classes=[0] = apenas pessoas (classe 0 do COCO dataset)
    # verbose=False = sem prints no terminal
    results = MODEL(frame, conf=CONFIDENCE, classes=[0], verbose=False)
    
    # Extrair bounding boxes
    detections = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # Coordenadas do bounding box
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0])
            
            detections.append({
                'x1': int(x1),
                'y1': int(y1),
                'x2': int(x2),
                'y2': int(y2),
                'confidence': conf
            })
    
    return detections


def draw_detections(frame, detections):
    """
    Desenha bounding boxes sobre as detecções de pessoas.
    
    Args:
        frame: Frame onde desenhar
        detections: Lista de detecções da função detect_people()
    
    Returns:
        Frame com as detecções desenhadas
    """
    for det in detections:
        x1, y1 = det['x1'], det['y1']
        x2, y2 = det['x2'], det['y2']
        conf = det['confidence']
        
        # Desenhar retângulo verde em volta da pessoa
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Label com confiança
        label = f"Pessoa: {conf:.0%}"
        
        # Fundo para o texto (melhor legibilidade)
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        label_w, label_h = label_size
        cv2.rectangle(frame, (x1, y1 - label_h - 10), (x1 + label_w, y1), (0, 255, 0), -1)
        
        # Texto
        cv2.putText(frame, label, (x1, y1 - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    
    return frame


def draw_info(frame, fps, num_people):
    """
    Desenha painel de informações no canto superior esquerdo.
    
    Args:
        frame: Frame onde desenhar
        fps: FPS atual
        num_people: Número de pessoas detectadas
    
    Returns:
        Frame com overlay de informações
    """
    # Criar fundo semi-transparente
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (280, 85), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    
    # Informações
    cv2.putText(frame, f"FPS: {fps:.1f}", (20, 35),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"Pessoas detectadas: {num_people}", (20, 60),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    return frame


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
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Erro ao ler frame")
                break
            
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
                    last_detections = detect_people(frame)
                    num = len(last_detections)
                    print(f"📊 [Frame {total_frames}] Detectadas {num} pessoa(s) | FPS: {fps:.1f}")
                except Exception as e:
                    print(f"⚠️  Erro na detecção: {e}")
                    last_detections = []
            
            # Desenhar
            if last_detections:
                frame = draw_detections(frame, last_detections)
            
            frame = draw_info(frame, fps, len(last_detections))
            
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
