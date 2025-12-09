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
- Integração opcional com botão físico (Arduino + keypad) para registar atendimentos
- Caminho do modelo resolvido de forma robusta (`models/yolov8n.pt`)

## 📁 Estrutura do projeto

```
smart-queue/
├── src/
│   ├── main.py              # Orquestra captura, deteção, tracking e HUD
│   ├── vision.py            # YOLO + desenhos (boxes, HUD)
│   ├── tracker.py           # SimpleTracker (centróides, TTL)
│   ├── queue_metrics.py     # Modelo simples da fila / ETA
│   ├── emoncms_client.py    # Upload periódico das métricas
│   └── button_listener.py   # Listener série para o botão físico
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

# Botão físico (Arduino)
button:
	enabled: false
	port: 'COM6'
	baudrate: 115200
	trigger_key: '1'
	debounce_sec: 0.3
	service_window: 5
	use_button_mode: false

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
- `T`: alterna modo de atendimento (automático com tempo médio ↔ botão físico)

## 🌐 Upload opcional para emonCMS

1. Obtém uma API Key no teu servidor emonCMS (pode ser self-hosted ou https://emoncms.org).
2. Ajusta o bloco `emoncms` no `config.yaml` (ativa `enabled: true`, define `api_key`, `node`, etc.).
3. Ao iniciar o programa verás uma linha `🌐 Upload emonCMS...` a confirmar a configuração.
4. O sistema envia pedidos `GET /input/post` com `json={...}` contendo as métricas do overlay (`fps`, `direction`, `queue_len`, `entries`, `people_detected`, `eta_sec`) e também `arrival_rate_min`, `service_rate_min`, `service_time_sec` para usares em dashboards.
5. Erros de rede são registados no terminal mas não bloqueiam o loop principal.

> Exemplo equivalente ao link oficial do projeto: `https://emoncms.org/input/post?node=emontx&fulljson={"power1":100,...}&apikey=XXXX`. O código usa o parâmetro `fulljson` para garantir compatibilidade.

## 🔘 Botão físico (Arduino)

1. Carrega o sketch do Arduino IDE (teclado matricial) e confirma que o monitor série imprime `Tecla: 1` quando carregas no botão desejado.
2. Liga o microcontrolador ao PC e verifica em que porta COM ele aparece.
3. Atualiza o bloco `button` no `config.yaml` (porta, baudrate, tecla) e define `enabled: true`.
4. Se quiseres que a fila seja esvaziada **apenas** com o botão, define `use_button_mode: true` ou, durante a execução, pressiona `T` para alternar o modo.

Sempre que a tecla configurada é recibida via série, o sistema regista um atendimento (subtrai 1 da fila e envia o novo valor para o HUD/emonCMS). No modo automático, a fila continua a drenar pelo tempo médio configurado e o botão serve apenas para acelerar atendimentos.

Quando `use_button_mode` está ativo o ETA deixa de usar o valor fixo e passa a calcular o tempo médio real usando os últimos `service_window` atendimentos (por omissão, 5). Assim a estimativa adapta-se ao ritmo manual observado sem precisar alterar a configuração.

### 🎛️ Dashboard rápido no emonCMS

1. **Feeds**: depois de correres o `main.py` com upload ativo, o emonCMS cria feeds automáticos com o prefixo do `node` (ex.: `smart-queue:queue_len`, `smart-queue:eta_sec`, `smart-queue:arrival_rate_min`, `smart-queue:service_rate_min`).
2. **Dashboard**: navega em *Dashboards → Add New*, escolhe um layout e adiciona widgets do tipo *LED*, *Dial* ou *Feed value*. Liga cada widget ao feed correspondente.
3. **Fila atual**: usa o feed `queue_len` para mostrar o número de pessoas em tempo real.
4. **ETA**: usa `eta_sec` e define a unidade para segundos/minutos conforme preferires (podes dividir por 60 usando a opção *Scale* do widget).
5. **Taxas**: `arrival_rate_min` dá chegadas por minuto, `service_rate_min` dá atendimentos/minuto. Dials funcionam bem aqui.
6. **Refresh**: define o *Refresh interval* do dashboard para 5s (ou o valor configurado em `interval_sec`) para acompanhar quase em tempo real.
7. **Histórico**: se quiseres gráficos, usa *Visualizations → Graph* e seleciona os mesmos feeds; podes embedar o gráfico no dashboard via *Embed graph*.

Com isso tens um painel completo sem código adicional – tudo alimentado pelo payload já enviado.

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

