# 🌸 Rosa Flow Messages

Automatización de conversaciones en Telegram con GPT-5.5 usando la API MTProto (autenticación como usuario real).

## ✨ Características

- **MTProto como usuario real:** Conexión a Telegram como usuario, no como bot.
- **Personalidad humana:** System prompt en Markdown con bio, emociones, actitudes y límites.
- **Delay realista:** Tiempo de espera configurable antes de responder, simulando lectura/escritura humana.
- **Detección de despedidas:** Identifica cuando el usuario quiere terminar la conversación y no insiste.
- **Reactivación automática:** Si vuelven a escribir después de una despedida, la conversación se reactiva.
- **Frontend React + Tailwind:** Panel web para gestionar chats y activar/desactivar el flujo automático.
- **Sin base de datos:** Todo el estado se mantiene en memoria (volátil).

## 🏗️ Arquitectura

```
backend/
├── app/
│   ├── modules/
│   │   ├── telegram/       # MTProto client con Telethon
│   │   ├── openai_client/  # Generador de respuestas GPT-5.5
│   │   ├── trigger/        # Motor de decisión + delay + detector de despedidas
│   │   ├── context/        # Historial + system prompt loader/validator
│   │   ├── chat_registry/  # Registro en memoria de chats
│   │   └── logger/         # Logging estructurado + excepciones
│   └── templates/
│       └── system_prompt.md # Plantilla editable de personalidad
└── tests/                   # Tests unitarios (pytest)

frontend/
├── src/
│   ├── components/          # React components (Tailwind)
│   ├── hooks/               # Custom hooks
│   └── services/            # API client
└── tests/                   # Tests unitarios (vitest)
```

## 🚀 Inicio rápido

### Requisitos

- Python 3.9+
- Node.js 20+
- Credenciales de Telegram API ([my.telegram.org](https://my.telegram.org/apps))
- API key de OpenAI

### Configuración

1. Clona el repo:
```bash
git clone https://github.com/{user}/rosa-flow-messages.git
cd rosa-flow-messages
```

2. Configura variables de entorno:
```bash
cp backend/.env.example backend/.env
# Edita backend/.env con tus credenciales
```

3. Instala dependencias:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ../frontend
npm install
cd ..
```

4. Autentica tu sesión de Telegram (requerido para usar MTProto como usuario real):
```bash
cd backend
source .venv/bin/activate
python scripts/auth_telegram.py
# Ingresa el código SMS cuando se solicite
cd ../
```

5. Inicia todo con un solo comando:
```bash
./start.sh
```

O con Docker:
```bash
./start.sh --docker
```

6. Asegúrate de editar `backend/app/templates/system_prompt.md` para personalizar la personalidad de tu IA.

## 📝 Plantilla de personalidad

Edita `backend/app/templates/system_prompt.md` para definir:

- **Bio:** Nombre, edad, ocupación, hobbies
- **Personalidad:** Tono, humor, imperfecciones
- **Emociones:** Cómo reacciona en diferentes situaciones
- **Estilo de escritura:** Frases cortas, expresiones propias, errores humanos
- **Límites:** Temas prohibidos, información personal, citas reales
- **Instrucciones técnicas:** Nunca revelar que es IA, recordar detalles del interlocutor

## 🧪 Testing

### Backend
```bash
cd backend
source .venv/bin/activate
pytest --cov=app --cov-report=term
```

### Frontend
```bash
cd frontend
npm test
```

## ⚠️ Aviso legal

El uso de MTProto como usuario está sujeto a los Términos de Servicio de Telegram. Úsalo con responsabilidad para evitar restricciones en tu cuenta.

## 📄 Licencia

MIT
