"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import sys

from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langsmith import Client

from utils import save_yaml, check_env_vars

load_dotenv()

PROMPT_VERSION = 'v1'
PROMPT_FILENAME_V1 = 'bug_to_user_story_v1.yml'

def extract_templates(messages) -> tuple[str, str]: 
    """Devolve (system_prompt, user_prompt), localizando as mensagens pelo tipo."""

    system_prompt = None
    user_prompt = None

    for message in messages:
        if isinstance(message, SystemMessagePromptTemplate) and system_prompt is None:
            system_prompt = message.prompt.template
        elif isinstance(message, HumanMessagePromptTemplate) and user_prompt is None:
            user_prompt = message.prompt.template

    if system_prompt is None or user_prompt is None:
        raise ValueError(
            'O prompt precisa ter uma mensagem system e uma human. '
            f'Foi encontrado: {[type(message).__name__ for message in messages]}'
        )

    return system_prompt, user_prompt


def pull_prompts_from_langsmith() -> int:
    """
    Faz pull do prompt semente do desafio e salva em YAML.

    Baixa 'leonanluppi/bug_to_user_story_v1' do LangSmith Hub, extrai o
    system_prompt e o user_prompt pelo tipo das mensagens e grava o resultado
    em prompts/bug_to_user_story_v1.yml.

    Returns:
        0 se o arquivo foi salvo, 1 caso contrário.
    """

    client = Client()
    prompt = client.pull_prompt(
        'leonanluppi/bug_to_user_story_v1',
        dangerously_pull_public_prompt=True
    )

    messages = prompt.messages

    system_prompt, user_prompt = extract_templates(messages)
    yaml_structure = {'bug_to_user_story_v1': {
        'description': "Prompt para converter relatos de bugs em User Stories",
        'system_prompt': system_prompt,
        'user_prompt': user_prompt,
        'version': PROMPT_VERSION,
        'created_at': datetime.now().strftime('%Y-%m-%d'),
        'tags': ["bug-analysis", "user-story", "product-management"]
        }}

    yaml_path = Path(__file__).resolve().parent.parent / 'prompts' / PROMPT_FILENAME_V1
    
    saved = save_yaml(yaml_structure, yaml_path)
    if saved: 
        print(f'Prompt salvo com sucesso em: {yaml_path}')
        return 0
    return 1


def main() -> int:
    """Função principal"""

    required_vars = ['LANGSMITH_API_KEY']

    if not check_env_vars(required_vars):
        return 1
    try:
        return pull_prompts_from_langsmith()
    except Exception as err:
        print(f'Erro ao fazer pull do prompt: {err}')
        return 1

if __name__ == "__main__":
    sys.exit(main())
