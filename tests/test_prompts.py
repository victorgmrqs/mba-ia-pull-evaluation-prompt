"""
Testes automatizados para validação de prompts.
"""
import pytest
import re
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data():
    """Dicionário do prompt v2, carregado uma única vez por módulo."""
    data = load_prompts(str(PROMPT_FILE))
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada em {PROMPT_FILE.name}"
    return data[PROMPT_KEY]


@pytest.fixture(scope="module")
def system_prompt(prompt_data):
    """Texto do system_prompt (vazio se o campo não existir)."""
    return prompt_data.get("system_prompt") or ""


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data, "Campo 'system_prompt' não encontrado no YAML"
        assert isinstance(prompt_data["system_prompt"], str), "'system_prompt' deve ser texto"
        assert prompt_data["system_prompt"].strip(), "'system_prompt' está vazio"

    def test_prompt_has_role_definition(self, system_prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        persona = re.search(r"Você é (um|uma|o|a)\s+\w+", system_prompt, re.IGNORECASE)

        assert persona, "O prompt não define uma persona (esperado algo como 'Você é um ...')"

    def test_prompt_mentions_format(self, system_prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        user_story_template = re.search(
            r"Como\b[^.]*\bquero\b[^.]*\bpara\b", system_prompt, re.IGNORECASE
        )

        assert user_story_template, (
            "O prompt não exige o formato padrão de User Story ('Como ..., quero ..., para ...')"
        )

    def test_prompt_has_few_shot_examples(self, system_prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        entradas = re.findall(r"^\s*Relato:", system_prompt, re.MULTILINE)
        saidas = re.findall(r"^\s*Resposta:", system_prompt, re.MULTILINE)

        assert len(entradas) >= 2, f"Esperado ao menos 2 exemplos de entrada ('Relato:'), encontrado {len(entradas)}"
        assert len(entradas) == len(saidas), (
            f"Cada exemplo precisa de entrada e saída: {len(entradas)} 'Relato:' e {len(saidas)} 'Resposta:'"
        )

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        texto = f"{prompt_data.get('system_prompt') or ''}\n{prompt_data.get('user_prompt') or ''}"
        todo = re.search(r"\[\s*todo[^\]]*\]", texto, re.IGNORECASE)

        assert not todo, f"Encontrado marcador pendente no prompt: {todo.group(0)}"

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        tecnicas = prompt_data.get("techniques_applied")

        assert isinstance(tecnicas, list), "'techniques_applied' deve ser uma lista"

        distintas = {t.strip().lower() for t in tecnicas if isinstance(t, str) and t.strip()}
        assert len(distintas) >= 2, f"Esperado ao menos 2 técnicas distintas, encontrado {len(distintas)}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
