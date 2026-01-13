
# 📐 Hyperparameter Grids — ChurnInsight (Seção 8)

Este documento define **oficialmente** os grids de hiperparâmetros utilizados no projeto **ChurnInsight**  
para a etapa de **Busca de Hiperparâmetros (GridSearchCV)** na **Seção 8**.

O objetivo é:

- garantir **consistência acadêmica** nas escolhas
- evitar grids arbitrários ou excessivamente custosos
- documentar *por que* cada hiperparâmetro foi incluído
- servir como **referência única e definitiva** do projeto

---

## 🧠 Princípios Gerais

Todos os grids seguem os seguintes critérios:

- **Cobertura conceitual**: cada hiperparâmetro controla um aspecto relevante do viés–variância
- **Custo computacional controlado**: grids pequenos e defensáveis
- **Aderência ao problema**: churn é um problema de classificação binária, frequentemente desbalanceado
- **Compatibilidade com GridSearchCV (sklearn)**

---

## 1️⃣ Regressão Logística (Logistic Regression)

### 🎯 Grid recomendado

```python
{
    "C": [0.01, 0.1, 1.0, 10.0],
    "penalty": ["l2"],
    "solver": ["liblinear", "lbfgs"],
    "class_weight": [None, "balanced"],
    "max_iter": [500]
}
```

### 📘 Justificativa acadêmica

- **C**  
  Controla a regularização (inverso da força).  
  Valores baixos → modelo mais simples (maior viés).  
  Valores altos → modelo mais flexível (maior variância).

- **penalty = l2**  
  Penalização padrão, estável e bem estudada para problemas lineares.

- **solver**  
  - `liblinear`: bom para datasets menores e binários  
  - `lbfgs`: mais moderno e eficiente para convergência

- **class_weight**  
  - `balanced` ajusta pesos automaticamente com base na distribuição das classes,
    o que é crucial em churn.

---

## 2️⃣ Random Forest

### 🎯 Grid recomendado

```python
{
    "n_estimators": [100, 300],
    "max_depth": [None, 5, 10],
    "min_samples_split": [2, 5],
    "min_samples_leaf": [1, 3],
    "class_weight": [None, "balanced"],
    "random_state": [42]
}
```

### 📘 Justificativa acadêmica

- **n_estimators**  
  Número de árvores.  
  Mais árvores → menor variância, maior custo computacional.

- **max_depth**  
  Controla complexidade da árvore.  
  Árvores muito profundas tendem a overfitting.

- **min_samples_split / min_samples_leaf**  
  Impõem restrições estruturais que reduzem overfitting.

- **class_weight**  
  Essencial para lidar com churn (classe minoritária).

---

## 3️⃣ K-Nearest Neighbors (KNN)

### 🎯 Grid recomendado

```python
{
    "n_neighbors": [3, 5, 7, 11],
    "weights": ["uniform", "distance"],
    "metric": ["euclidean", "manhattan"]
}
```

### 📘 Justificativa acadêmica

- **n_neighbors**  
  Controla o trade-off viés–variância:  
  - poucos vizinhos → sensível a ruído  
  - muitos vizinhos → suavização excessiva

- **weights**  
  - `uniform`: todos os vizinhos têm peso igual  
  - `distance`: vizinhos mais próximos influenciam mais

- **metric**  
  Avalia diferentes noções de distância no espaço de features.

---

## 4️⃣ Decision Tree

### 🎯 Grid recomendado

```python
{
    "max_depth": [None, 5, 10],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 3, 5],
    "criterion": ["gini", "entropy"],
    "class_weight": [None, "balanced"],
    "random_state": [42]
}
```

### 📘 Justificativa acadêmica

- **max_depth**  
  Principal controle de complexidade.

- **min_samples_split / min_samples_leaf**  
  Evitam divisões excessivamente específicas.

- **criterion**  
  - `gini`: mais rápido  
  - `entropy`: baseado em informação (teoria da informação)

- **class_weight**  
  Importante para evitar árvores enviesadas para a classe majoritária.

---

## 5️⃣ Gaussian Naive Bayes (GNB)

### 🎯 Grid recomendado

```python
{
    "var_smoothing": [1e-9, 1e-8, 1e-7]
}
```

### 📘 Justificativa acadêmica

- **var_smoothing**  
  Adiciona estabilidade numérica ao cálculo da variância.  
  Pequenos ajustes podem ter impacto significativo na performance.

- O GNB possui poucos hiperparâmetros por design,
  refletindo sua natureza probabilística simplificada.

---

## 📌 Status do Documento

- **Status**: Oficial
- **Escopo**: Seção 8 — Controle de Modelos
- **Alterações futuras**: somente via revisão consciente do projeto
