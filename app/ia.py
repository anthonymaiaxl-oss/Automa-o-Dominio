"""Consulta à IA (Claude Haiku) para classificar uma caixa de erro nova.

Regras fixas (seção 5.5 e 0.32 do documento):

- Só recebe **texto já anonimizado** (`erros.anonimizar()`), nunca
  imagem, nunca nome/código/CNPJ de empresa.
- Só **escolhe** uma das ações fixas de `erros.ACOES` — a resposta é
  forçada num formato JSON com a lista fechada de ações; qualquer coisa
  fora disso é descartada.
- Tudo que é enviado fica registrado em `data/ia_envios.log` (local),
  pra conferir depois exatamente o que saiu da máquina.

Chave da API: variável de ambiente `ANTHROPIC_API_KEY` ou uma linha só
no arquivo `data/chave_api.txt` (pasta `data/` nunca sobe pro GitHub).
Sem chave, `classificar_erro()` devolve None e o motor segue sem IA.
"""

import datetime
import json
import os
from pathlib import Path

from . import erros

MODELO = "claude-haiku-4-5"
PASTA_DADOS = Path(__file__).resolve().parent.parent / "data"
ARQUIVO_CHAVE = PASTA_DADOS / "chave_api.txt"
ARQUIVO_LOG = PASTA_DADOS / "ia_envios.log"

_SISTEMA = (
    "Você ajuda um robô que opera o sistema contábil Domínio Escrita Fiscal "
    "(Thomson Reuters) pela tela, gerando arquivos SPED Fiscal (EFD ICMS/IPI) e "
    "EFD Contribuições, empresa por empresa, em lote. No meio da geração apareceu "
    "uma caixa de mensagem do Domínio. Você recebe só o texto dela (lido por OCR, "
    "pode ter erro de leitura; dados da empresa foram trocados por marcadores como "
    "<EMPRESA>, <NOME>, <CAMINHO> e #). Escolha a ação do robô entre as opções "
    "abaixo. Nenhuma ação altera lançamentos nem transmite nada.\n\n"
    + "\n".join(f"- {nome}: {descricao}" for nome, descricao in erros.ACOES.items())
    + "\n\nUse confiança \"alta\" só quando o texto deixa claro o que aconteceu. "
    "Se o texto estiver ilegível ou ambíguo, use confiança \"baixa\". "
    "Responda o motivo em português, em uma frase curta."
)

_FORMATO = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "acao": {"type": "string", "enum": list(erros.ACOES)},
            "confianca": {"type": "string", "enum": ["alta", "baixa"]},
            "motivo": {"type": "string"},
        },
        "required": ["acao", "confianca", "motivo"],
        "additionalProperties": False,
    },
}


def _chave_api():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"].strip()
    try:
        return ARQUIVO_CHAVE.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def _registrar(texto, resultado):
    try:
        PASTA_DADOS.mkdir(parents=True, exist_ok=True)
        with ARQUIVO_LOG.open("a", encoding="utf-8") as f:
            agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            f.write(f"[{agora}] ENVIADO: {texto!r}\n[{agora}] RESPOSTA: {resultado}\n")
    except OSError:
        pass


def disponivel():
    """True se tem chave configurada e a biblioteca instalada."""
    if not _chave_api():
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def classificar_erro(texto_anonimizado, documento=""):
    """Pergunta à IA qual ação tomar. Devolve (acao, confianca, motivo)
    ou None se a IA não estiver disponível ou a resposta não servir."""
    chave = _chave_api()
    if not chave:
        print("IA não configurada (sem chave em data/chave_api.txt nem ANTHROPIC_API_KEY).")
        return None
    try:
        import anthropic
    except ImportError:
        print("Biblioteca 'anthropic' não instalada (rode Atualizar.bat / pip install -r requirements.txt).")
        return None

    pergunta = f"Documento sendo gerado: {documento or 'não informado'}\n\nTexto da caixa:\n{texto_anonimizado}"
    print("Consultando a IA (só o texto anonimizado acima é enviado)...")
    try:
        cliente = anthropic.Anthropic(api_key=chave, timeout=30.0, max_retries=2)
        resposta = cliente.messages.create(
            model=MODELO,
            max_tokens=512,
            system=_SISTEMA,
            messages=[{"role": "user", "content": pergunta}],
            output_config={"format": _FORMATO},
        )
    except anthropic.AuthenticationError:
        print("A chave da IA foi recusada — confira data/chave_api.txt.")
        _registrar(texto_anonimizado, "erro: chave recusada")
        return None
    except anthropic.APIConnectionError:
        print("Sem conexão com a IA (internet?).")
        _registrar(texto_anonimizado, "erro: sem conexão")
        return None
    except anthropic.APIError as e:
        print(f"A IA respondeu com erro: {e}")
        _registrar(texto_anonimizado, f"erro: {e}")
        return None

    if resposta.stop_reason != "end_turn":
        _registrar(texto_anonimizado, f"resposta incompleta ({resposta.stop_reason})")
        return None
    texto = next((b.text for b in resposta.content if b.type == "text"), "")
    _registrar(texto_anonimizado, texto)
    try:
        dados = json.loads(texto)
    except ValueError:
        return None
    if dados.get("acao") not in erros.ACOES:
        return None
    return dados["acao"], dados.get("confianca", "baixa"), dados.get("motivo", "")
