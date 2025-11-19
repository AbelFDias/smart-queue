# 🎯 Smart Queue (estado atual)

Sistema simples de detecção de pessoas em tempo real usando **YOLOv8 local**, pensado como base para um sistema de gestão de filas.

Foco atual: implementação rápida, estável e offline (sem APIs externas).

## ✅ O que está feito

- Detecção local com **YOLOv8** (ultralytics)
- Visualização em tempo real com bounding boxes e **FPS**
- Configuração simples via `config.yaml`
- Suporte a diferentes fontes de vídeo (webcam/Iriun)
- Caminho do modelo resolvido de forma robusta (`models/yolov8n.pt`)

## 📁 Estrutura do projeto

```
smart-queue/
├── src/
│   └── main.py              # Script principal (YOLO + OpenCV)
├── config/
│   └── config.yaml          # Configurações (fonte vídeo, modelo, FPS, confiança)
├── models/
│   └── yolov8n.pt           # (opcional) Peso local do modelo
├── data/
│   └── .gitkeep
├── requirements.txt
└── README.md
```

Nota: ficheiros `*.pt` estão ignorados no git; se não existir `models/yolov8n.pt`, o Ultralytics faz download automático.

## ⚙️ Configuração

Edita `config/config.yaml`:

```yaml
# Fonte de vídeo
video_source: 0                # 0=webcam, 1=segunda webcam, ou URL Iriun

# Performance (YOLO é rápido)
process_every_n_frames: 3      # 1=todos os frames; 3=bom equilíbrio; 5=mais rápido

# Modelo YOLO (caminho relativo à raiz do projeto)
yolo_model: 'models/yolov8n.pt'  # n=nano (rápido), s=small, m=medium

# Detecção
confidence_threshold: 0.5      # 0.3=mais detecções; 0.7=mais preciso
```

## 🚀 Instalação

```powershell
git clone https://github.com/AbelFDias/smart-queue.git
cd smart-queue
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## ▶️ Execução

```powershell
.\venv\Scripts\Activate.ps1
cd src
python main.py
```

Controlo: tecla `Q` para sair.

## 📊 Performance (CPU)

- `yolov8n.pt` (nano): 20–30 FPS típicos
- `yolov8s.pt` (small): 15–25 FPS
- `yolov8m.pt` (medium): 10–15 FPS

Valores dependem do hardware. Com GPU os FPS aumentam bastante.

## 🧰 Troubleshooting

- Câmara não abre: altera `video_source` (0/1/2) e confirma Iriun ativo
- FPS baixo: aumenta `process_every_n_frames` (5/10) ou usa `yolov8n.pt`
- Muitos falsos positivos: aumenta `confidence_threshold` (0.6/0.7)
- Não deteta ninguém: baixa `confidence_threshold` (0.3/0.4) e verifica iluminação
- Modelo em falta: o código tenta caminho local; se não existir, usa download do Ultralytics

## 🗺️ Próximos passos (roadmap curto)

- Contagem por line-crossing (entradas na fila)
- Tracking simples por ID
- Estimativa de ETA baseada no comprimento da fila

## 📄 Licença

MIT

## 👤 Autores

- Abel Dias — [@AbelFDias](https://github.com/AbelFDias)

