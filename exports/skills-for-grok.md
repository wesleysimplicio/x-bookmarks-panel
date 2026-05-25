# Skills bookmarks — pedido pro Grok

Grok, para cada tweet abaixo abra a thread no X e me devolva **o link do PRIMEIRO comentário/reply do autor** — é normalmente onde ele cola o link da skill / repo GitHub. Se o link da skill já estiver no corpo do post original, devolva esse. Se não houver comentário com link, marque `sem link`.

Formato de resposta, uma linha por item:

```
<id> | <url_da_skill>
```

## Lista (23 tweets)

| ID | Autor | Tweet | Categoria |
|---|---|---|---|
| 5 | Nav Toor | https://x.com/navtoor/status/bookmarked | Claude Code |
| 6 | darkzodchi | https://x.com/darkzodchi/status/bookmarked | Claude Code |
| 7 | Glaucia Lemos | https://x.com/glaucia_lemos86/status/2043498698127065126 | Claude Code |
| 86 | Ihtesham Ali | https://x.com/ihtesham2005/status/bookmarked | Claude Code |
| 138 | Charlie Hills | https://x.com/charliejhills/status/2048428282174156996 | Claude Skills |
| 140 | Kōda | https://x.com/aimikoda/status/2048654096794538316 | AI Video |
| 141 | Emily | https://x.com/IamEmily2050/status/2048147198869946855 | AI Video |
| 143 | Greg | https://x.com/gregpr07/status/2044597099373858816 | Claude Skills |
| 167 | EHuanglu | https://x.com/EHuanglu/status/2048136865484824872 | AI Video |
| 191 | Gabriel Packer | https://x.com/gkpacker/status/2037137933384188037 | Workflow IA |
| 192 | Obsidian Studio (PT-JP) | https://x.com/obsidianstudio9/status/2048888680354644460 | Claude + Obsidian |
| 193 | Higgsfield | https://x.com/higgsfield/status/2049174934891692528 | AI Media MCP |
| 194 | Bolha Devs | https://x.com/BolhaDevs/status/2049154358525165635 | AI Agents |
| 195 | Jerrod Lew | https://x.com/jerrod_lew/status/2049109463014183313 | AI Video |
| 207 | Higgsfield | https://x.com/higgsfield/status/2051346056039039487 | AI Marketing CLI |
| 214 | fal | https://x.com/fal/status/2052451137970745842 | AI Marketing CLI / Skills |
| 223 | CyrilXBT | https://x.com/cyrilXBT/status/2051917898755752217 | Anthropic Skilljar / Claude Certs |
| 224 | Thariq | https://x.com/trq212/status/2052809885763747935 | Claude Code / Agentic Output Format |
| 226 | shmidt | https://x.com/shmidtqq/status/2053107967898140931 | Claude Cowork / Plugin Authoring |
| 227 | PA13L0 | https://x.com/Fluyeporlaweb/status/2053188453160874099 | AI Marketing Skills / OSS |
| 235 | Burak Bayır | https://x.com/burakbayir/status/2053205072616505372 | Hermes Agent (off-stack) |
| 236 | xIA | https://x.com/xiathis/status/2054530660681834754 | Claude Code / Vibe-Coding |
| 238 | Remotion | https://x.com/Remotion/status/2013626968386765291 | AI Video / Claude Skills (oficial) |

## Observações

- IDs 5, 6 e 86 estão com `status/bookmarked` (placeholder — URL real perdida no banco). Resolva pelo handle + contexto se possível; senão `url inválida`.
- Prioridade: extrair o **link concreto da skill** (GitHub repo, site oficial, comando `npx`, doc Anthropic). Comentário é só o atalho mais comum.
- Devolva tudo num único bloco markdown, uma linha por id.
