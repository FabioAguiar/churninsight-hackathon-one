# 📒 Notebooks Individuais — Data Science

Este diretório é destinado ao **trabalho individual dos cientistas de dados** do projeto **ChurnInsight**.

Cada integrante pode criar seu próprio subdiretório, por exemplo:

```bash
notebooks/individual/Fábio Aguiar/
notebooks/individual/Lilian Moraes/
notebooks/individual/Lucas Frigato/
notebooks/individual/Luedji Abayomi/
```

Dentro desses diretórios, cada pessoa tem total liberdade para:

- explorar os dados;
- testar hipóteses;
- criar features;
- treinar modelos experimentais;
- gerar análises e insights.

---

## 📁 Sobre diretórios de dados

⚠️ **Importante:** diretórios de dados dentro de `notebooks/individual/` são locais e **NÃO são versionados no Git**.

Isso inclui, por exemplo:

```bash
notebooks/individual/<nome>/data/processed/
notebooks/individual/<nome>/data/external/
```

Esses dados:

- são apenas para uso local;
- podem variar entre integrantes;
- não fazem parte do pipeline oficial do projeto;
- estão corretamente ignorados pelo `.gitignore`.

---

## 🧠 Pipeline oficial do projeto

O pipeline oficial de dados e modelagem está centralizado em:

```bash
src/
```

Somente esse pipeline:

- é reutilizado pelo serviço FastAPI;
- gera o modelo exportado;
- impacta a API e a integração com o back-end.

Os notebooks individuais **não devem alterar diretamente** esse pipeline sem alinhamento prévio com o grupo.

---

## 🎯 Objetivo deste espaço

Este diretório existe para:

- incentivar exploração e aprendizado;
- evitar conflitos entre notebooks;
- manter o repositório organizado;
- permitir evolução do modelo de forma colaborativa e controlada.
