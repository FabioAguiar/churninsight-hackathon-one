# Principais tipos de commits (Conventional Commits)

Este guia descreve os prefixos que utilizamos para padronizar nossas mensagens de commit, facilitando a leitura do histórico e a geração de changelogs.

| Tipo | O que significa e quando usar | Exemplo |
| :--- | :--- | :--- |
| **feat** | Usado para adicionar uma nova funcionalidade/feature ao projeto. Deve ser usado para qualquer mudança que resulte em algo novo para o usuário ou para a funcionalidade do sistema. | `feat: adiciona o botão de avançar` |
| **fix** | Usado para corrigir um bug. Deve ser usado para qualquer mudança que resolva um comportamento incorreto. | `fix: corrigir erro de carregamento da página inicial` |
| **docs** | Mudanças que afetam apenas a documentação (ex: arquivos README, documentação gerada, comentários de código que não afetam a lógica). | `docs: atualizar seção de design no README` |
| **style** | Mudanças que não afetam o significado do código (espaços em branco, formatação, ponto e vírgula ausente, etc.). Ex: formatação via Prettier. | `style: formatar código com Prettier` |
| **refactor** | Uma mudança de código que não corrige um bug nem adiciona uma funcionalidade (ex: renomear uma variável, reestruturar um módulo). | `refactor: extrair cálculo de imposto para função auxiliar` |
| **test** | Adicionar testes ausentes ou corrigir testes existentes. | `test: adicionar testes de unidade para a função de login` |
| **chore** | Outras mudanças que não afetam o código de produção ou a documentação (ex: atualizações de dependências de build, ajustes em arquivos de configuração). | `chore: atualizar versão do Node.js no Dockerfile` |
| **build** | Mudanças que afetam o sistema de build ou dependências externas (ex: npm, yarn, pip, maven). | `build: adicionar dependência da biblioteca Lodash` |
| **ci** | Mudanças nos arquivos e scripts de configuração de Integração Contínua (CI) (ex: Jenkins, GitLab CI, GitHub Actions). | `ci: configurar cache para acelerar o pipeline` |
| **perf** | Uma mudança de código que melhora o desempenho (performance) do sistema. | `perf: otimizar consulta ao banco de dados para a dashboard` |