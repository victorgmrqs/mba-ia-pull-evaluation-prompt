"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""
import os
import sys

from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate

from utils import check_env_vars,load_yaml


load_dotenv()


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        prompt_template = ChatPromptTemplate.from_messages([
            ('system', prompt_data.get('system_prompt')),
            ('user', prompt_data.get('user_prompt')),
        ])

        version = prompt_data.get('version')
        model = os.getenv('LLM_MODEL')
        description = prompt_data.get('description')
        techniques = prompt_data.get('techniques_applied') or []

        client = Client()
        url = client.push_prompt(
            prompt_name,
            object=prompt_template, 
            is_public=True,
            tags=[ 
                version,
                f"model: {model}",
                *techniques
            ], 
            description=description,
        )
        print(url)

        return True
    except Exception as err :
        if 'Nothing to commit' in str(err):
            print('Prompt já está atualizado no Hub (nada novo para commitar).')
            return True
        print(err)
        return False



def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    required_fields = ['description', 'system_prompt', 'version']

    for field in required_fields:
        if field not in prompt_data:
            errors.append(f'Campo obrigatório {field} não foi encontrado')
    
    system_prompt = prompt_data.get('system_prompt') or ''
    user_prompt = prompt_data.get('user_prompt') or ''
    techniques = prompt_data.get('techniques_applied')

    if not system_prompt.strip():
        errors.append('"system_prompt" está vazio')
    elif 'TODO' in system_prompt:
        errors.append('"system_prompt" ainda contém TODOs')

    if '{bug_report}' not in user_prompt:
        errors.append('"user_prompt" precisa conter a variável {bug_report}')

    if not isinstance(techniques, list) or len(techniques) < 2:
        errors.append('"techniques_applied" deve ser uma lista com ao menos 2 técnicas')
    
    return (len(errors) == 0, errors)

def get_hub_username() -> str | None: 
    """Handle do Hub vindo do .env, sem espaços nas pontas; None se for inválido."""
    username = (os.getenv('USERNAME_LANGSMITH_HUB') or '').strip()
    if not username or '/' in username:
        return None
    return username   

def main() -> int:
    """Função principal"""

    envs_to_check = [
        'USERNAME_LANGSMITH_HUB',
        'LANGSMITH_API_KEY',
        'LLM_MODEL'
    ]
        
    vars = check_env_vars(envs_to_check)

    if not vars: return 1

    username = get_hub_username()
    if username is None:
        print("USERNAME_LANGSMITH_HUB inválido: informe só o handle, sem '/' e sem espaços.")
        return 1

    prompt_id = 'bug_to_user_story_v2'
    prompt_filename = 'bug_to_user_story_v2.yml'

    local_prompt_dir = Path(__file__).resolve().parent.parent / 'prompts'
    local_prompt_path = local_prompt_dir / prompt_filename

    prompt_handle_langsmith = f'{username}/{prompt_id}'
    
    prompt_yaml = load_yaml(local_prompt_path)
    if not prompt_yaml: return 1

    prompt = prompt_yaml.get(prompt_id)

    if not prompt: 
        print(f'Chave "{prompt_id}" não encontrada em "{prompt_filename}"')
        return 1

    is_valid_prompt, errors = validate_prompt(prompt)

    if not is_valid_prompt:
        print('Prompt inválido:')
        for error in errors:
            print(f'  - {error}')
        return 1
    
    success = push_prompt_to_langsmith(prompt_handle_langsmith, prompt)
    return 0 if success else 1

    
if __name__ == "__main__":
    sys.exit(main())
