# V.I.S.A.O - Verificação de Impedimento por Sistema de Análise Óptica

Um sistema desktop offline para análise de lances de impedimento no futebol baseado em imagens e vídeos.

## Requisitos

- Python 3.14 (ou >= 3.10)
- Sistema Operacional: Windows, Linux ou macOS.

## Instalação

1. Clone ou baixe este repositório.
2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   ```
3. Ative o ambiente virtual:
   - No Windows: `venv\Scripts\activate`
   - No Linux/Mac: `source venv/bin/activate`
4. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Como Rodar

Com o ambiente virtual ativado, execute o comando:
```bash
python main.py
```

## Funcionalidades
- Suporte a Imagem e Vídeo.
- Posicionamento de Referências (homografia/perspectiva).
- Posicionamento de Linhas de Impedimento personalizáveis.
- Veredito da Análise.
- Modo Dark/Light automático.
- Modo Multi-Janelas (detecção de monitores).
- Ferramentas de Zoom e Arraste em imagens de alta resolução.
