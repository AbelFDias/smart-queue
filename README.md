# 🎯 Smart Queue - Sistema Inteligente de Gestão de Filas

Sistema de gestão de filas baseado em **visão computacional** que deteta pessoas em tempo real usando **YOLOv8**.

## 📋 Características

✅ **Detecção local com YOLOv8** - Sem necessidade de internet ou APIs externas!  
✅ **Processamento em tempo real** - 20-30 FPS com modelo nano  
✅ **Configuração flexível** - Ajusta performance vs precisão facilmente  
✅ **Interface visual** - Display com FPS e contadores em tempo real  
✅ **Simples e eficiente** - Código limpo num único ficheiro  

## 🚀 Tecnologias

- **YOLOv8** (ultralytics) - Detecção de pessoas estado-da-arte
- **OpenCV** - Captura e processamento de vídeo
- **Python 3.8+** - Linguagem principal
- **YAML** - Configuração

## 🏗️ Arquitetura

```
📱 Webcam/Iriun
    ↓ Stream de vídeo
💻 Sistema Local
    ├── 🔍 YOLOv8 (detecção de pessoas)
    ├── 📊 Contagem e tracking
    └── 🖥️ Interface visual
```

## 📁 Estrutura do Projeto

```
smart-queue/
├── src/
│   └── main.py              ← Código principal (tudo num ficheiro!)
├── config/
│   └── config.yaml          ← Configurações
├── requirements.txt         ← Dependências Python
└── README.md               ← Este ficheiro
```

## 🚀 Setup e Instalação

### 1. Pré-requisitos

- Python 3.8 ou superior
- Webcam ou smartphone com app Iriun Webcam
- ~200MB de espaço (modelo + dependências)

### 2. Clonar o repositório

```powershell
git clone https://github.com/AbelFDias/smart-queue.git
cd smart-queue
```

### 3. Criar ambiente virtual (recomendado)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Instalar dependências

```powershell
pip install -r requirements.txt
```

Na primeira execução, o YOLOv8 vai descarregar automaticamente o modelo (~6MB).

## ⚙️ Configuração

Edita `config/config.yaml`:

```yaml
# Fonte de vídeo
video_source: 0              # 0=webcam, 1=segunda webcam, ou URL do Iriun

# Performance (YOLO é rápido!)
process_every_n_frames: 3    # 1=todos os frames, 3=bom equilíbrio, 5=mais rápido

# Modelo YOLO (caminho relativo à raiz)
yolo_model: 'models/yolov8n.pt'     # n=nano (rápido), s=small, m=medium

# Detecção
confidence_threshold: 0.5    # 0.3=mais detecções, 0.7=mais preciso
```

## 🎮 Como Usar

```powershell
# 1. Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# 2. Executar
cd src
python main.py
```

### Controlos

- **Q** - Sair

## � Performance

| Modelo | Tamanho | FPS (típico) | Precisão |
|--------|---------|--------------|----------|
| YOLOv8n | ~6MB | 20-30 FPS | Boa |
| YOLOv8s | ~22MB | 15-25 FPS | Muito boa |
| YOLOv8m | ~50MB | 10-15 FPS | Excelente |

*Testado em CPU Intel i5/i7. Com GPU os valores são muito superiores.*

## 🔧 Troubleshooting

### Câmara não abre
- Verifica se a webcam está conectada
- Tenta mudar `video_source` para 1, 2, etc.
- Se usas Iriun, verifica se a app está a correr

### FPS muito baixo
- Aumenta `process_every_n_frames` no config (ex: 5 ou 10)
- Usa modelo mais leve (`yolov8n.pt`)
- Reduz resolução da câmara

### Muitos falsos positivos
- Aumenta `confidence_threshold` (ex: 0.6 ou 0.7)

### Não deteta ninguém
- Diminui `confidence_threshold` (ex: 0.3 ou 0.4)
- Verifica iluminação da sala
- Certifica-te que há pessoas no enquadramento

## 🎓 Como Funciona

1. **Captura de vídeo**: OpenCV captura frames da webcam
2. **Processamento inteligente**: Processa apenas 1 em cada N frames (otimização)
3. **Detecção YOLOv8**: Modelo identifica pessoas (classe 0 do COCO dataset)
4. **Visualização**: Desenha bounding boxes e estatísticas no frame
5. **Loop**: Repete até o utilizador sair (Q)

## 📝 Futuras Melhorias

- [ ] Line-crossing detection (contar entradas na fila)
- [ ] Tracking de pessoas individuais
- [ ] Estimativa de tempo de espera (ETA)
- [ ] Gravação de vídeo com detecções
- [ ] Dashboard web com estatísticas
- [ ] Integração com EmonCMS
- [ ] Alertas quando fila excede limite

## 🤝 Contribuir

Pull requests são bem-vindos! Para mudanças maiores, abre primeiro uma issue para discutir.

## 📄 Licença

MIT

## 👤 Autor

**Abel Dias**  
- GitHub: [@AbelFDias](https://github.com/AbelFDias)

---

**Nota**: Este projeto foi refatorado para usar YOLOv8 local em vez de APIs externas, garantindo melhor performance e funcionamento offline!
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Instalar dependências

```powershell
pip install -r requirements.txt
```

### 5. Configurar API Key da Roboflow

1. Vai a https://app.roboflow.com/settings/api
2. Copia a tua API key
3. Cria um ficheiro `.env` na raiz do projeto:

```powershell
cp .env.example .env
```

4. Edita `.env` e adiciona a tua key:

```env
ROBOFLOW_API_KEY=sua_key_aqui
```

### 6. Configurar parâmetros

Edita `config/config.yaml` para ajustar:
- Posição da linha virtual
- Direção de contagem
- Tempo médio de atendimento
- Fonte de vídeo (webcam ou URL)
- Thresholds de detecção

## 🎮 Utilização

### Executar o sistema

```powershell
cd src
python queue_manager.py
```

### Controlos do teclado

- **Q** - Sair do programa
- **R** - Reset dos contadores (entradas e atendimentos)
- **S** - Registar atendimento manualmente (+1 pessoa atendida)
- **ESPAÇO** - Pausar/Retomar processamento

### Interface visual

O sistema mostra em tempo real:
- 📹 FPS atual
- 📥 Número de entradas (pessoas que cruzaram a linha)
- ✅ Número de atendimentos registados
- 👥 Comprimento da fila (entradas - atendimentos)
- ⏱️ ETA estimado (em minutos e segundos)
- 🔴 Linha virtual de contagem com seta de direção
- 🟢 Bounding boxes das pessoas detectadas

## 📁 Estrutura do Projeto

```
smart-queue/
├── config/
│   └── config.yaml          # Configuração principal
├── data/                    # Imagens/vídeos de teste
│   └── .gitkeep
├── docs/                    # Documentação adicional
├── src/
│   ├── people_detector.py   # Detector Roboflow
│   ├── line_crossing.py     # Contador de line-crossing
│   └── queue_manager.py     # Sistema principal (MAIN)
├── .env.example             # Template de variáveis de ambiente
├── .gitignore
├── README.md
└── requirements.txt         # Dependências Python
```

## 🔧 Componentes Principais

### 1. People Detector (`people_detector.py`)
- Usa modelo `people-detection-o4rdr/7` da Roboflow
- Detecção via API HTTP
- Desenho de bounding boxes e labels
- Extração de centroides

### 2. Line Crossing Counter (`line_crossing.py`)
- Tracking simples baseado em distância euclidiana
- Detecção de cruzamento de linha com verificação de direção
- Evita contagem duplicada
- Visualização da linha com zona de trigger

### 3. Queue Manager (`queue_manager.py`)
- **Sistema principal** que integra tudo
- Captura de vídeo (webcam/Iriun)
- Gestão de fila e cálculo de ETA
- Interface visual com OpenCV
- Modo adaptativo (média móvel de tempos de atendimento)

## 📊 Princípio de Funcionamento

1. **Detecção**: O modelo identifica pessoas em cada frame
2. **Tracking**: Centroides são seguidos frame-a-frame
3. **Line-crossing**: Quando um centroide cruza a linha na direção configurada → +1 entrada
4. **Gestão de fila**: 
   - Comprimento = Entradas - Atendimentos
   - ETA = Comprimento × Tempo médio por pessoa
5. **Feedback**: Informação visual em tempo real no display

### Modos de operação

#### Modo Simples
- Tempo de atendimento fixo (configurável em `config.yaml`)
- Staff regista atendimentos manualmente (tecla **S**)

#### Modo Adaptativo (futuro)
- Botão físico do staff regista timestamp de atendimentos
- Sistema calcula média móvel dos últimos N atendimentos
- ETA ajusta-se automaticamente à velocidade real

## 🔮 Roadmap / Funcionalidades Futuras

- [ ] Integração com EmonCMS
  - [ ] Envio de métricas (comprimento, ETA, entradas/min)
  - [ ] Dashboard web
  - [ ] Alertas de fila longa
- [ ] ESP8266 com feedback local
  - [ ] LED RGB (verde/amarelo/vermelho baseado em ETA)
  - [ ] Display OLED com informações
  - [ ] Botão físico para registar atendimentos
- [ ] Melhorias de CV
  - [ ] Tracking mais robusto (DeepSORT/ByteTrack)
  - [ ] Detecção de oclusões
  - [ ] Múltiplas linhas de contagem
- [ ] Analytics
  - [ ] Gráficos de ocupação ao longo do dia
  - [ ] Previsão de picos
  - [ ] Exportação de dados

## 🧪 Teste Rápido

Para testar o detector básico:

```powershell
cd src
python people_detector.py
```

Para testar o line-crossing:

```powershell
cd src
python line_crossing.py
```

## 📚 Referências

- Tutorial base: [People Counting Using Computer Vision - Roboflow](https://blog.roboflow.com/people-counting-computer-vision-software/)
- Modelo usado: [People Detection - Roboflow Universe](https://universe.roboflow.com/leo-ueno/people-detection-o4rdr/model/7)

## 📝 Notas

- O sistema faz chamadas à API da Roboflow por frame - em produção, considerar:
  - Reduzir FPS de processamento
  - Usar modelo local (YOLO) se disponível GPU
  - Implementar cache/buffering
- Para Iriun Webcam: configurar `VIDEO_SOURCE` com o URL fornecido pela app

## 🤝 Contribuir

Projeto académico - LESTI 3º ano - IoT

---

**Status**: 🟢 MVP funcional | 🟡 Integrações em desenvolvimento

---

## 📄 Especificação Original do Projeto

### Resumo do projeto:
Estima o tempo de espera (ETA) posicionando uma câmara no início da fila.
Conta apenas quem entra ao atravessar uma "linha virtual" na imagem.
Mantém a contagem mesmo quando a pessoa sai do enquadramento.
Envia métricas para o EmonCMS.
ESP pode dar feedback local (LED/OLED) e receber inputs simples (botão).

### Princípio de funcionamento:
Detetor identifica pessoas e segue o movimento por alguns frames.
Evento de "entrada" quando o centroide cruza a linha na direção definida.
Atendimentos estimados:
- Modo simples: usa tempo médio por pessoa configurável (ex.: 35 s).
- Modo adaptativo: botão do staff regista "+1 atendimento" e ajusta média móvel.
- Comprimento da fila = entradas acumuladas − atendimentos estimados.
- ETA = comprimento estimado × tempo médio por pessoa.
