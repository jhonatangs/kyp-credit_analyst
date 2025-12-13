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

# Load environment variables
load_dotenv()

# AI Configuration (Groq - Llama 3.3 70B Versatile)
llm = ChatGroq(temperature=0.0, model_name="llama-3.3-70b-versatile")


# --- 1. DATA MODELS ---
class CreditReport(BaseModel):
    summary: str = Field(
        description="Executive summary of the company situation (in Portuguese)"
    )
    risk_score: int = Field(
        description="Risk score from 0 (Safe) to 100 (Extreme Risk)"
    )
    final_verdict: str = Field(
        description="Final decision: APPROVE, DENY, or WITH_CONDITIONS"
    )
    rationale: str = Field(
        description="Technical justification for the decision (in Portuguese)"
    )


# --- 2. MATH ENGINE (Deterministic) ---
def calculate_financial_ratios(data: dict) -> dict:
    curr = data["financials"]["current_year"]
    prev = data["financials"].get("previous_year", {})

    liabilities = curr.get("current_liabilities", 0)
    revenue = curr.get("revenue", 0)

    # Avoid division by zero
    liquidity = curr["current_assets"] / liabilities if liabilities > 0 else 0
    margin = (curr["net_income"] / revenue) * 100 if revenue > 0 else 0

    growth = 0.0
    if prev and prev.get("revenue", 0) > 0:
        growth = ((curr["revenue"] - prev["revenue"]) / prev["revenue"]) * 100

    return {
        "liquidity": round(liquidity, 2),
        "margin": round(margin, 2),
        "growth": round(growth, 2),
    }


# --- 3. ANALYSIS ENGINE (AI Agent) ---
def process_company_data(company_data: dict) -> dict:
    """
    Process a dictionary of data (in-memory) and return the structured analysis.
    """
    name = company_data["company_info"]["name"]
    sector = company_data["company_info"].get("sector", "N/A")

    # Step A: Math Calculations
    ratios = calculate_financial_ratios(company_data)

    # Step B: AI Context Analysis
    parser = PydanticOutputParser(pydantic_object=CreditReport)

    prompt = ChatPromptTemplate.from_template(
        """
        You are a Senior Credit Analyst at CERC. 
        Analyze the data below to validate "Duplicata Escritural" operations.
    
        COMPANY: {name} | SECTOR: {sector}
    
        FINANCIAL INDICATORS (Numeric Facts):
        - Current Liquidity: {liquidity} (Below 1.0 indicates imminent insolvency risk)
        - Net Margin: {margin}%
        - Revenue Growth: {growth}%

        RISK GUIDELINES:
        1. If Liquidity < 1.0, risk is HIGH, even if the company is growing (Cash flow break).
        2. Negative Margin (Loss) requires rejection or strong guarantees.
        3. Prioritize the safety of the market infrastructure.
       
        Output the response in the requested format. 
        The 'summary' and 'rationale' text must be written in Portuguese.
        The 'final_verdict' must be one of: APPROVE, DENY, WITH_CONDITIONS.
       
        {format_instructions}
        """
    )

    chain = prompt | llm | parser

    # Execute Chain
    result = chain.invoke(
        {
            "name": name,
            "sector": sector,
            "liquidity": ratios["liquidity"],
            "margin": ratios["margin"],
            "growth": ratios["growth"],
            "format_instructions": parser.get_format_instructions(),
        }
    )

    # Return flat dictionary
    return {
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "company_name": name,
        "liquidity_ratio": ratios["liquidity"],
        "net_margin_percent": ratios["margin"],
        "revenue_growth_percent": ratios["growth"],
        "risk_score": result.risk_score,
        "final_verdict": result.final_verdict,
        "rationale": result.rationale,
    }


# Wrapper for file-based processing (Batch Pipeline)
def analyze_company_file(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return process_company_data(data)


# --- 4. BATCH PIPELINE ORCHESTRATION ---
def run_batch_pipeline():
    input_folder = "data/input"
    os.makedirs("data/output", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = f"data/output/consolidated_report_{timestamp}.csv"

    files = glob.glob(f"{input_folder}/*.json")
    results = []

    print(f"🚀 Starting Batch Credit Analysis Pipeline...")
    print(f"📂 Files found: {len(files)}\n")

    for file in files:
        try:
            print(f"🔄 Processing: {os.path.basename(file)}...")
            analysis = analyze_company_file(file)
            results.append(analysis)
            print(
                f"   ✅ Verdict: {analysis['final_verdict']} (Score: {analysis['risk_score']})"
            )
        except Exception as e:
            print(f"   ❌ Critical error in file {file}: {str(e)}")

    if results:
        keys = results[0].keys()
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        print(f"\n📊 Final report successfully generated: {output_file}")
    else:
        print("\n⚠️ No data processed.")


if __name__ == "__main__":
    run_batch_pipeline()
