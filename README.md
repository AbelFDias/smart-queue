# 🎯 Smart Queue

Sistema de detecção de pessoas e contagem por linha em tempo real usando **YOLOv8 local**, pensado como base para um sistema de gestão de filas (queueing).

Foco atual: implementação rápida, estável e offline (sem APIs externas), com HUD e configurações simples.

## ✅ O que está feito

- Detecção local com **YOLOv8** (ultralytics)
- Tracking leve por centróides (associação 1:1, TTL)
- Contagem por cruzamento de linha vertical com filtro de direção (L→R ou R→L)
- HUD com FPS, pessoas, entradas, direção, banda, fila e ETA
- Parâmetros no `config.yaml` (modelo, FPS, confiança, tracking, linha, display, ETA, emonCMS)
- Suporte a diferentes fontes de vídeo (webcam/Iriun)
- Caminho do modelo resolvido de forma robusta (`models/yolov8n.pt`)

## 📁 Estrutura do projeto

```
smart-queue/
├── src/
│   ├── main.py              # Orquestra captura, deteção, tracking e HUD
│   ├── vision.py            # YOLO + desenhos (boxes, HUD)
│   └── tracker.py           # SimpleTracker (centróides, TTL)
├── config/
│   └── config.yaml          # Fonte vídeo, modelo, detecção, tracking, linha, display, ETA
├── models/
│   └── yolov8n.pt           # (opcional) Peso local do modelo
├── data/
│   └── .gitkeep
├── requirements.txt
└── README.md
```

Nota: ficheiros `*.pt` estão ignorados no git; se não existir `models/yolov8n.pt`, o Ultralytics faz download automático.

## ⚙️ Configuração

Edita `config/config.yaml` (principais opções):

```yaml
# Fonte de vídeo
video_source: 0

# Performance (processar 1 em cada N frames)
process_every_n_frames: 3

# Modelo YOLO (caminho relativo à raiz do projeto)
yolo_model: 'models/yolov8n.pt'

# Detecção
confidence_threshold: 0.5

# Tracking (associação simples por centróides)
tracking:
	match_radius_px: 60
	ttl: 6

# Contagem por linha vertical
counting:
	direction: 'left_to_right'   # ou 'right_to_left'
	line_band_px: 100            # largura da banda de avaliação
	line_x_percent: 0.5          # posição da linha (0.0 esquerda, 1.0 direita)
	line_color_bgr: [0, 0, 255]
	line_thickness: 2

# Visualização e debug
display:
	show_boxes: true
	show_band: false
	debug: false
	show_eta: true
	show_metrics: false

# Fila (estimativa de tempo de espera)
queue:
	avg_service_time_sec: 20
	window_sec: 120

# Upload opcional para emonCMS (HTTP GET /input/post)
emoncms:
	enabled: false
	base_url: 'https://emoncms.org/input/post'
	api_key: 'SUA-KEY'
	node: 'smart-queue'
	interval_sec: 5
	timeout_sec: 4
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

Controlo (durante execução):

- `Q`: sair
- `D`: alterna debug (logs)
- `O`: alterna boxes (YOLO)
- `B`: alterna banda de contagem
- `R`: alterna direção (L→R ↔ R→L)
- `E`: mostra/oculta linha compacta com fila + ETA
- `M`: mostra/oculta overlay JSON das métricas (o mesmo payload enviado para emonCMS)

## 🌐 Upload opcional para emonCMS

1. Obtém uma API Key no teu servidor emonCMS (pode ser self-hosted ou https://emoncms.org).
2. Ajusta o bloco `emoncms` no `config.yaml` (ativa `enabled: true`, define `api_key`, `node`, etc.).
3. Ao iniciar o programa verás uma linha `🌐 Upload emonCMS...` a confirmar a configuração.
4. O sistema envia pedidos `GET /input/post` com `json={...}` contendo exatamente as métricas mostradas no overlay (`fps`, `direction`, `queue_len`, `entries`, `people_detected`, `eta_sec`).
5. Erros de rede são registados no terminal mas não bloqueiam o loop principal.

> Exemplo equivalente ao link oficial do projeto: `https://emoncms.org/input/post?node=emontx&fulljson={"power1":100,...}&apikey=XXXX`. O código usa o parâmetro `fulljson` para garantir compatibilidade.

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

## 🗺️ Próximos passos (curto prazo)

- Ajustes finos no tracking (distâncias adaptativas)
- Persistência dos contadores/logs
- Zona de ROI para a fila e contagem segmentada

## 📄 Licença

MIT

## 👤 Autores

- Abel Dias — [@AbelFDias](https://github.com/AbelFDias)

