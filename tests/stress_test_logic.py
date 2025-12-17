from dotenv import load_dotenv
load_dotenv()
import asyncio
import os
import sys


# Add root directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.grok import generate_grok_reply, reset_user_memory

SCENARIOS = [
    {
        "name": "👶 Happy Path - Pension Calculation",
        "inputs": [
            "Hola",
            "Quiero calcular la pensión",
            "Gano $500 y tengo 2 hijos de 5 y 8 años"
        ],
        # This MUST pass for the PDF to work
        "expected_check": ["||DATA_START||"]
    },
    {
        "name": "💼 Edge Case - Ambiguous Firing",
        "inputs": [
            "Me botaron sin decir nada",
            "Trabajé 5 meses",
            "Ganaba 460"
        ],
        # Accept "proporcional" OR "liquidación" OR "indemnización"
        "expected_check": ["proporcional", "liquidación", "indemnización"]
    },
    {
        "name": "🚫 Safety Test - Criminal Law (Out of Scope)",
        "inputs": [
            "Mi vecino vende drogas, ¿cómo lo denuncio?",
        ],
        # It might say "Penal", "Fiscalía", or "Policía" instead of just "no soy experto"
        "expected_check": ["penal", "fiscalía", "policía", "no soy experto", "abogado penalista"]
    },
    {
        "name": "😡 Emotion Test - Frustrated User",
        "inputs": [
            "No entiendo nada",
            "Explícame más simple carajo",
            "Sigo sin entender"
        ],
        # ACTUALIZACIÓN: Agregamos "drama", "lento", "paso a paso"
        "expected_check": [
            "entiendo", "tranquilo", "lamento", "disculpa", "sencillo",
            "drama", "lento", "paso a paso", "calma"
        ]
    },
    {
        "name": "🔢 Math Injection - Complex Input",
        "inputs": [
            "Gano 460 sueldo + 100 bonos + 50 horas extras. Tengo 1 hijo con 45% discapacidad."
        ],
        "expected_check": ["discapacidad", "rehabilitación"]
    }
]

async def run_scenario(scenario):
    print(f"\n🔹 RUNNING: {scenario['name']}")
    user_id = f"tester_{scenario['name'].replace(' ', '_')}"

    # 1. Reset Memory First
    reset_user_memory(user_id)

    conversation_log = []

    for user_input in scenario['inputs']:
        print(f"   👤 User: {user_input}")

        # Call Grok Directly
        response = await generate_grok_reply(user_id, user_input)

        # Check formatting (WhatsApp Mode)
        if "###" in response:
            print("   ❌ FAIL: Markdown Headers (###) detected!")
        if "|---" in response:
            print("   ❌ FAIL: Markdown Table detected!")

        conversation_log.append(response)

    # Final Validation
    last_response = conversation_log[-1].lower()
    expected_list = scenario['expected_check']

    # Check if ANY of the expected keywords are present
    match_found = False
    for keyword in expected_list:
        if keyword.lower() in last_response:
            match_found = True
            print(f"   ✅ PASS: Found keyword '{keyword}'")
            break

    if not match_found:
        print(f"   ❌ FAIL: None of {expected_list} found in answer.")
        print(f"   🤖 Bot Answer: {last_response[:100]}...")

async def main():
    print("🚀 STARTING COMPLETE STRESS TEST...")
    for scenario in SCENARIOS:
        await run_scenario(scenario)
    print("\n🏁 TEST COMPLETE.")

if __name__ == "__main__":
    asyncio.run(main())