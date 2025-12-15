# 🧠 How To — Data Science no Projeto ChurnInsight

Este documento explica **como o time de Data Science deve trabalhar dentro do projeto ChurnInsight**, garantindo organização, liberdade de experimentação e integração com o restante da arquitetura.

O foco aqui é **orientar**, não engessar.

---

## 🎯 Objetivo do Time de Data Science

O time de Data Science é responsável por:

- Explorar o dataset de churn
- Entender padrões de comportamento dos clientes
- Criar e testar features relevantes
- Treinar modelos de classificação
- Avaliar métricas
- Contribuir para a escolha do modelo final


---

## 📁 Estrutura de Pastas para Data Science

### Dataset compartilhado

Somente o dataset original é compartilhado entre todos:

```
data/raw/
```

⚠️ Não modifique arquivos dentro de `raw/`.

---

### Notebooks individuais

Cada cientista de dados possui seu próprio espaço:

```
notebooks/individual/<seu_nome>/
├── data/
│   ├── processed/
│   └── features/
├── 01_eda.ipynb
├── 02_features.ipynb
├── 03_modelagem.ipynb
└── README.md
```

Isso garante:
- liberdade total de experimentação
- nenhum conflito entre notebooks
- autonomia técnica

---

## 🔁 Reutilização de Código (Recomendado)

O projeto possui um **core de funções reutilizáveis** em:

```
src/
```

Exemplos:
- carregamento de dados
- preprocessamento padrão
- avaliação de métricas

Você pode:
- importar essas funções nos seus notebooks
- adaptá-las localmente se preferir

Nada é obrigatório.

---

## 📊 Fluxo de Trabalho Sugerido

1. Copie o dataset de `data/raw/`
2. Faça EDA livre no seu notebook
3. Crie e teste features
4. Treine um ou mais modelos
5. Avalie métricas
6. Documente decisões no README do seu diretório

---

## 📌 Boas Práticas

- Documente suas hipóteses
- Salve gráficos importantes
- Explique decisões (mesmo que simples)
- Prefira clareza a complexidade
- Não se preocupe em "acertar" o modelo perfeito


---

## 🤝 Integração com o Modelo Final

Ao longo do projeto, os notebooks individuais servirão como espaço de exploração, aprendizado e geração de insights sobre os dados.
Os principais aprendizados, padrões observados e ideias de features poderão ser considerados na consolidação do modelo final, que será treinado de forma centralizada para garantir:
- consistência do pipeline,
- reprodutibilidade dos resultados,
- compatibilidade com a API de inferência.
O modelo final será exportado e utilizado pela API como artefato oficial do projeto, mantendo os notebooks individuais livres para experimentação sem impacto direto na integração.