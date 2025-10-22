QADatasetCreator/
├── 📁 app/
│   ├── 📁 core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── 📁 models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── conversation.py
│   │   └── daily_events.py
│   ├── 📁 schemas/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── conversation.py
│   │   ├── daily_events.py
│   │   └── emotion.py
│   ├── 📁 services/
│   │   ├── __init__.py
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── gemini_service.py
│   │   │   └── prompts/
│   │   │       ├── __init__.py
│   │   │       ├── conversation_prompt.py
│   │   │       ├── daily_events_prompt.py
│   │   │       └── story_prompt.py
│   │   ├── conversation_service.py
│   │   ├── daily_events_service.py
│   │   └── dataset_generator.py
│   ├── 📁 utils/
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   ├── formatters.py
│   │   └── helpers.py
│   └── main.py
├── .env
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md