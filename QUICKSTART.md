# 🚀 Quick Start - Smart Queue

## Executar o Projeto

```powershell
# 1. Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# 2. Ir para src e executar
cd src
python main.py

# 3. Sair: pressiona Q
```

## Configuração Rápida

Edita `config/config.yaml`:

```yaml
video_source: 1                    # 0=webcam principal, 1=segunda webcam
process_every_n_frames: 3          # 1-5 = bom para YOLO
yolo_model: 'models/yolov8n.pt'    # n=rápido, s=médio, m=preciso
confidence_threshold: 0.5          # 0.3-0.7
```

## Troubleshooting

### Câmara não abre
- Muda `video_source` para 0, 1 ou 2
- Verifica se a webcam está ligada

### FPS baixo
- Aumenta `process_every_n_frames` para 5 ou 10
- Mantém `yolov8n.pt` (mais rápido)

### Muitos falsos positivos
- Aumenta `confidence_threshold` para 0.6 ou 0.7

### Não deteta pessoas
- Baixa `confidence_threshold` para 0.3 ou 0.4
- Verifica a iluminação

## Estrutura do Projeto

```
smart-queue/
├── src/
│   └── main.py              ← Código principal (255 linhas!)
├── config/
│   └── config.yaml          ← Configurações
├── requirements.txt         ← Dependências
└── README.md               ← Documentação completa
```

## Tecnologias

- **YOLOv8** (ultralytics) - Detecção local, sem API
- **OpenCV** - Processamento de vídeo
- **Python 3.13** - Linguagem

## Performance

| Modelo | FPS típico | Precisão |
|--------|------------|----------|
| yolov8n | 20-30 | Boa |
| yolov8s | 15-25 | Muito boa |
| yolov8m | 10-15 | Excelente |

---

**🎯 Objetivo**: Sistema de gestão de filas com visão computacional  
**📹 Input**: Webcam ou Iriun  
**🔍 Output**: Detecção de pessoas em tempo real  
