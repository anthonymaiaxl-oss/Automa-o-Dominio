# Domínio Automation Engine

Motor de automação para operar o **Domínio Escrita Fiscal** (Thomson
Reuters) pela interface, para a Lucrattiva Contabilidade — começando por
uma rotina ligada a SPED. Projeto irmão do
[`docauto`](https://github.com/cristiane-art/Testes-Para-Automa-o) (que
organiza documento fiscal que **chega** ao escritório); este aqui **opera
o próprio Domínio**, risco maior, repositório separado de propósito.

## Estado atual: Fase 4 — primeira geração real confirmada (em empresa de teste)

👉 **[docs/00-analise-e-plano-fase0.md](docs/00-analise-e-plano-fase0.md)**
— riscos técnicos, achados confirmados (Domínio é entregue via GraphOn
GO-Global, não local), arquitetura recomendada, roadmap e o histórico
completo de cada descoberta técnica. **Leia isso antes de mexer em
qualquer coisa neste repositório** — economiza reaprender o que já foi
resolvido na marra (foco de janela, recorte de OCR, etc).

Já validado com o Domínio de verdade: ler estado da tela (empresa,
período, menu) por OCR, achar posição de texto pra clicar, focar a
janela antes de agir, clicar e passar o mouse (hover) de forma real,
navegar sozinho até a tela de geração da EFD ICMS/IPI (SPED Fiscal),
clicar OK, **confirmar sucesso da geração ("Final da exportação.")** e
fechar a tela sozinho — ponta a ponta, sem intervenção manual no meio
(seção 0.11 do documento acima).

**Rodado até agora só em empresa de teste**, de propósito — prova que o
mecanismo funciona, mas ainda não serve como validação de conteúdo (não
tem arquivo real entregue no passado pra comparar). O período (Data
inicial/final) é **selecionado sozinho** — sempre o mês fechado
anterior ao atual, nunca o corrente (seção 0.23) — não precisa (e não
adianta) configurar isso na tela antes de rodar. Antes de rodar contra
a empresa-alvo real, só confira que ela está selecionada (não a
empresa de teste).

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Precisa também do Tesseract instalado com o idioma português (`por`) —
mesmo binário já usado pelo projeto irmão `docauto`.

## Uso

### Jeito fácil (recomendado)

Com o Domínio Escrita Fiscal aberto e visível na tela, dá duplo clique
em **`Abrir Motor SPED.bat`** (na raiz desta pasta). Abre um menu
numerado (rodar em lote por regime, trocar empresa, gerar SPED numa
empresa só) — não precisa digitar comando nenhum (seção 0.18 do
documento). A janela fica aberta no final pra você ler o resultado.

Antes, se fizer um tempo que você não mexe nisso, dá duplo clique em
**`Atualizar.bat`** primeiro, pra puxar as correções mais recentes do
GitHub.

Precisa de `data/empresas.csv` (separado por `;`) pras opções de lote —
copie `data/empresas.exemplo.csv` e preencha com as empresas de
verdade; esse arquivo é seu, local, nunca sobe pro GitHub. Colunas:

- `codigo`, `apelido`, `regime` — sempre precisou disso.
- `tipo` — `1` (um documento só) ou `2` (os dois documentos abaixo,
  ignora a coluna `sped`). Opcional; sem ela, vira `1`.
- `sped` — qual documento gerar quando `tipo` é `1`: "ICMS" ou
  "Contribuições" (seção 0.20 do documento). Opcional; sem ela, vira
  "ICMS". **EFD Contribuições ainda não foi confirmada rodando de
  ponta a ponta pelo próprio código** (seção 0.21) — a tela foi
  explorada e o gerador escrito, mas falta o primeiro teste real via
  script (`scripts\explorar_contribuicoes.py`, abaixo, ou opção 5 do
  menu).

### Scripts individuais (linha de comando)

Cada opção do menu também roda direto por comando, se preferir:

```bash
python scripts\explorar.py               # gera o SPED Fiscal (ICMS) na empresa já selecionada
python scripts\explorar_contribuicoes.py # gera a EFD Contribuições na empresa já selecionada
python scripts\trocar_empresa.py         # troca de empresa via F8 (código fixo no arquivo)
python scripts\selecionar_empresas.py    # só carrega e filtra a lista por regime, não roda nada
python scripts\executar_lote.py          # troca de empresa + gera, para cada empresa de um regime
python scripts\executar_lote.py --real   # idem, mas com data/empresas.csv (planilha real)
```

`explorar.py` navega Relatórios → Informativos → Federais → SPED
Fiscal, clica OK, confirma o aviso "Final da exportação." e fecha a
tela — salvando cada etapa em `capturas/` (pasta local, nunca
versionada — pode conter tela real com dado fiscal). Já reconhece uma
caixa de erro do Domínio (título "Atenção", ex.: caminho de arquivo
inválido — seção 0.25 do documento): salva print, dispensa a caixa e
para aquele documento sem travar o lote. Só cobre esse formato de erro
visto até agora — outro título de erro ainda cai no caminho antigo
(espera e falha por timeout, sem mensagem específica).

- `app/tela.py` — captura de tela, recorte e leitura de texto (OCR),
  com os ajustes já validados (recorte por região, pré-processamento
  pra texto dentro de menu suspenso).
- `app/interacao.py` — foco de janela, clique, hover, tecla e digitação
  de texto, com os ajustes já validados (foco obrigatório antes de
  clicar, clique "devagar", Enter pra diálogo de um botão só).
- `app/dominio.py` — ações de alto nível (`trocar_empresa()`,
  `gerar_sped_fiscal()`), reaproveitadas pelos scripts isolados e pelo
  lote.
- `app/empresas.py` — carrega e filtra `data/empresas.csv` por regime.
- `scripts/explorar.py` — gera o SPED Fiscal numa empresa só (a que já
  estiver selecionada no Domínio).
- `scripts/trocar_empresa.py` — troca a empresa selecionada via F8.
- `scripts/selecionar_empresas.py` — só carrega e filtra a lista por
  regime, não roda nada.
- `scripts/executar_lote.py` — troca de empresa + gera o SPED Fiscal
  pra cada empresa do regime escolhido.
- `scripts/app.py` — menu único que reúne as opções acima; é o que
  `Abrir Motor SPED.bat` roda.
- `Abrir Motor SPED.bat` / `Atualizar.bat` — atalhos de duplo clique
  (raiz do repositório) pro dia a dia, sem linha de comando.

## Histórico deste repositório

Este nome (`dominio-automation-engine`) reaproveita um repositório que
antes tinha um projeto sem relação nenhuma com este (um agente de redes
sociais da Lucrattiva) — mantido em duplicidade em outra conta e removido
daqui por decisão do escritório em 18/09/2026. O conteúdo antigo continua
recuperável no histórico do Git (`git log`), caso necessário.
