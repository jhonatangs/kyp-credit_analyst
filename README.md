# 🤖 KYP Challenge: Pipeline de Análise de Crédito em Escala

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![LangChain](https://img.shields.io/badge/LangChain-Orchestration-green)
![Groq](https://img.shields.io/badge/Groq-Llama3-orange)
![Architecture](https://img.shields.io/badge/Architecture-Batch%20Processing-purple)

> **Automação de alto volume para lidar com o aumento de 10x nas operações de Duplicata Escritural.**

---

## 🎯 Contexto de Negócio
A nova regulamentação das duplicatas escriturais exigirá que infraestruturas de mercado (como a CERC) processem um volume massivo de validações de crédito. O método manual ("carpintaria intelectual") não escala.

Este projeto implementa um **Pipeline de Engenharia de Dados** que automatiza o processo de **KYP (Know Your Partner)**, analisando a saúde financeira das empresas emissoras para mitigar riscos sistêmicos.

## 🏗 Arquitetura da Solução

Desenvolvi uma solução focada em **Escalabilidade (Batch)** e **Confiabilidade Financeira (Hybrid AI)**.

### 1. Processamento em Lote (Batch Processing)
Para atender ao requisito de volume, o sistema não analisa caso a caso manualmente.
* **Input:** O pipeline varre um diretório (`data/input`) ingerindo múltiplos balanços financeiros simultaneamente.
* **Resiliência:** Se um arquivo estiver corrompido, o pipeline trata o erro e continua processando os demais, garantindo disponibilidade.
* **Output:** Gera um relatório consolidado em CSV (`data/output`), facilitando a integração com sistemas legados ou dashboards de BI.

### 2. Análise Híbrida (Determinística + Generativa)
Evitamos o risco de "alucinação matemática" da IA separando as responsabilidades:
* **Python Puro (Task 3 O*NET):** Calcula indicadores exatos como **Liquidez Corrente** (Capacidade de pagamento) e **Margem Líquida** (Eficiência).
* **IA Llama 3 (Task 4 & 5 O*NET):** Atua como o Analista Sênior, interpretando se os indicadores representam risco dentro do contexto do setor.

---

## 📂 Estrutura do Projeto

```text
kyp-batch-analyst/
├── data/
│   ├── input/               # Pasta monitorada (JSONs das empresas)
│   └── output/              # Relatórios processados (CSV)
├── src/
│   ├── main.py              # Motor de análise e orquestração
├── .env                     # Credenciais seguras
└── README.md                # Documentação
```

---

## 🚀 Como Executar

1.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure a API Key:**
    Adicione sua chave da Groq no arquivo `.env`:
    ```text
    GROQ_API_KEY=gsk_...
    ```

3.  **Execute o Pipeline:**
    ```bash
    python src/main.py
    ```
    *O sistema irá processar todos os JSONs na pasta `input` e gerar um relatório consolidado na pasta `output`.*

---

## 🧪 Cenários de Teste (Calibragem da IA)

O sistema foi validado contra 3 perfis de risco distintos para garantir "Product Sense":

| Perfil | Características Financeiras | Veredito Esperado |
| :--- | :--- | :--- |
| **Saudável** | Liquidez > 1.5 e Margem Alta. | ✅ **APROVAR** |
| **Borderline** | Receita crescendo, mas Liquidez < 1.0 (Risco de Quebra). | ⚠️ **NEGAR / GARANTIAS** |
| **Zumbi** | Prejuízo Operacional e Insolvência. | ❌ **NEGAR** |

**Glossário de Risco:**
* **Liquidez Corrente < 1.0:** A empresa deve mais no curto prazo do que tem em caixa. Alto risco de default (calote).
* **Margem Decrescente:** Indica perda de eficiência operacional, muitas vezes mascarada por aumento de receita ("Crescimento a qualquer custo").