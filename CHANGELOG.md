# Changelog

Todas as mudanças notáveis deste projeto são documentadas aqui.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto adere a [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]

## [0.1.0] — 2026-04-24

### Added
- Versão inicial open-source do painel.
- Backend Flask 3 com rotas `/api/healthz`, `/api/stats`, `/api/oportunidades`, `/api/oportunidades/<id>/executar`, `/api/oportunidades/import`, `/api/projetos`.
- Schema SQLite com três tabelas: `oportunidades`, `execucoes`, `projetos`. Migração idempotente.
- UI single-page em HTML+CSS+JS vanilla: cards com prioridade/status/categoria, busca textual com debounce, filtros combinados, flags de progresso independentes (instalado / aplicado / projeto iniciado).
- Heurística Claude×Cowork via keywords + categoria, com override manual pela UI ou API.
- Botão **+ Novo projeto** cria pasta `<repo>/<slug>/`, escreve `README.md` + `CLAUDE.md`, roda `git init` e, se `gh` estiver autenticado, `gh repo create --private --push`.
- Importer idempotente: lê array `BOOKMARKS` de `relatorio-bookmarks-x.html`, preserva campos editados no painel.
- Scripts macOS: `setup.sh` idempotente, `install-launchd.sh` com templates plist, `healthcheck.sh` watchdog a cada 5min, `start.sh`/`stop.sh`.
- Configuração por `.env` (porta, host, label prefix, app Cowork, caminho alternativo do HTML).
- Exemplo em `examples/sample-relatorio.html` com dados sintéticos.
- Documentação: `README.md`, `CLAUDE.md`, `DESIGN.md`, `CONTRIBUTING.md`.
- `.gitignore` bloqueando dados do usuário (DB, HTML de triagem, logs, `.env`, `.venv`, capturas, análises de perfil, pastas geradas).

[Unreleased]: https://github.com/wesleysimplicio/x-bookmarks-panel/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/wesleysimplicio/x-bookmarks-panel/releases/tag/v0.1.0
