import json
import os
import glob
import csv
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# Carrega variáveis de ambiente
load_dotenv()

# Configuração da IA (Groq - Llama 3)
# Temperature 0.0 garante respostas mais frias e analíticas (Ideal para Finanças)
llm = ChatGroq(temperature=0.0, model_name="llama-3.3-70b-versatile")


# --- 1. DEFINIÇÃO DO MODELO DE DADOS (OUTPUT) ---
class CreditReport(BaseModel):
    summary: str = Field(
        description="Resumo executivo da situação da empresa em 1 frase"
    )
    risk_score: int = Field(
        description="Nota de risco de 0 (Seguro) a 100 (Risco Extremo)"
    )
    final_verdict: str = Field(description="Decisão: APROVAR, NEGAR ou COM GARANTIAS")
    rationale: str = Field(description="Justificativa técnica principal para a decisão")


# --- 2. MOTOR MATEMÁTICO (Determinístico - Python Puro) ---
# GLOSSÁRIO TÉCNICO:
# - Liquidez Corrente: Capacidade de pagar dívidas de curto prazo. (< 1.0 = Risco de Quebra)
# - Margem Líquida: Eficiência do negócio. (Lucro / Receita)
# - Crescimento (YoY): Year-over-Year growth. Crescimento de receita comparado ao ano anterior.
def calculate_ratios(data):
    curr = data["financials"]["current_year"]
    prev = data["financials"].get("previous_year", {})

    # Tratamento para evitar divisão por zero
    liabilities = curr.get("current_liabilities", 0)
    revenue = curr.get("revenue", 0)

    liquidity = curr["current_assets"] / liabilities if liabilities > 0 else 0
    margin = (curr["net_income"] / revenue) * 100 if revenue > 0 else 0

    growth = 0
    if prev and prev.get("revenue", 0) > 0:
        growth = ((curr["revenue"] - prev["revenue"]) / prev["revenue"]) * 100

    return {
        "liquidity": round(liquidity, 2),
        "margin": round(margin, 2),
        "growth": round(growth, 2),
    }


# --- 3. AGENTE DE ANÁLISE (IA Generativa) ---
def analyze_company(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        company_data = json.load(f)

    name = company_data["company_info"]["name"]

    # Passo A: Cálculos Exatos
    ratios = calculate_ratios(company_data)

    # Passo B: Análise de Contexto com LLM
    parser = PydanticOutputParser(pydantic_object=CreditReport)

    # Engenharia de Prompt focada em KYP (Know Your Partner)
    prompt = ChatPromptTemplate.from_template(
        """
        Você é um Analista de Crédito Sênior da CERC. 
        Analise os dados abaixo para validar operações de Duplicata Escritural.
        
        EMPRESA: {name} | SETOR: {sector}
        
        INDICADORES (Fatos Numéricos):
        - Liquidez Corrente: {liquidity} (Abaixo de 1.0 indica risco iminente de insolvência)
        - Margem Líquida: {margin}%
        - Crescimento Receita: {growth}%
        
        DIRETRIZES DE RISCO:
        1. Se Liquidez < 1.0, o risco é ALTO, mesmo que a empresa cresça (Risco de quebra de caixa).
        2. Margem negativa (Prejuízo) exige rejeição ou garantias fortes.
        3. Priorize a segurança da infraestrutura de mercado.
        
        {format_instructions}
        """
    )

    chain = prompt | llm | parser

    result = chain.invoke(
        {
            "name": name,
            "sector": company_data["company_info"].get("sector", "N/A"),
            "liquidity": ratios["liquidity"],
            "margin": ratios["margin"],
            "growth": ratios["growth"],
            "format_instructions": parser.get_format_instructions(),
        }
    )

    # Retorna dicionário plano para facilitar a criação do CSV
    return {
        "Data_Analise": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Empresa": name,
        "Liquidez": ratios["liquidity"],
        "Margem_Percent": ratios["margin"],
        "Crescimento_Percent": ratios["growth"],
        "Score_Risco": result.risk_score,
        "Veredito": result.final_verdict,
        "Justificativa_IA": result.rationale,
    }


# --- 4. PIPELINE BATCH (Escalabilidade) ---
def run_batch_pipeline():
    input_folder = "data/input"
    # Cria pasta de output automaticamente se não existir
    os.makedirs("data/output", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = f"data/output/relatorio_consolidado_{timestamp}.csv"

    # Busca todos os JSONs na pasta
    files = glob.glob(f"{input_folder}/*.json")
    results = []

    print(f"🚀 Iniciando Pipeline de Análise de Crédito em Lote...")
    print(f"📂 Arquivos encontrados: {len(files)}\n")

    for file in files:
        try:
            print(f"🔄 Processando: {os.path.basename(file)}...")
            analysis = analyze_company(file)
            results.append(analysis)
            print(
                f"   ✅ Decisão: {analysis['Veredito']} (Score: {analysis['Score_Risco']})"
            )
        except Exception as e:
            print(f"   ❌ Erro crítico no arquivo {file}: {str(e)}")

    # Persistência em CSV (Data Engineering)
    if results:
        keys = results[0].keys()
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        print(f"\n📊 Relatório final gerado com sucesso: {output_file}")
    else:
        print("\n⚠️ Nenhum dado foi processado.")


if __name__ == "__main__":
    run_batch_pipeline()
