import asyncio
from app.agents.validador_farmaceutico import validar_lista_medicamentos

def test_validador():
    print("--- Teste do Validador Farmacêutico ---")
    
    # Caso 1: Seguro
    meds_seguros = [
        {
            "nome": "Paracetamol",
            "dosagem": "750mg",
            "frequencia": "de 8 em 8 horas",
            "frequencia_por_dia": 3,
            "duracao_dias": 5
        }
    ]
    aprovados, alertas = validar_lista_medicamentos(meds_seguros)
    print("\nTeste 1 - Paracetamol 750mg 3x/dia (Seguro):")
    print(f"Aprovados: {[m['nome'] for m in aprovados]}")
    print(f"Alertas: {alertas}")
    assert len(aprovados) == 1
    assert len(alertas) == 0

    # Caso 2: Inseguro (Overdose Unitária)
    meds_overdose_unitaria = [
        {
            "nome": "Amoxicilina",
            "dosagem": "1500mg", # MAX é 1000mg
            "frequencia": "de 12 em 12 horas",
            "frequencia_por_dia": 2,
            "duracao_dias": 7
        }
    ]
    aprovados, alertas = validar_lista_medicamentos(meds_overdose_unitaria)
    print("\nTeste 2 - Amoxicilina 1500mg (Dose unitária alta):")
    print(f"Aprovados: {[m['nome'] for m in aprovados]}")
    print(f"Alertas: {alertas}")
    assert len(aprovados) == 0
    assert len(alertas) > 0

    # Caso 3: Inseguro (Overdose Diária)
    meds_overdose_diaria = [
        {
            "nome": "Dipirona",
            "dosagem": "1g",
            "frequencia": "de 4 em 4 horas", # 6x dia = 6000mg (Max é 4000)
            "frequencia_por_dia": 6,
            "duracao_dias": 3
        }
    ]
    aprovados, alertas = validar_lista_medicamentos(meds_overdose_diaria)
    print("\nTeste 3 - Dipirona 1g 6x/dia (Dose diária excessiva):")
    print(f"Aprovados: {[m['nome'] for m in aprovados]}")
    print(f"Alertas: {alertas}")
    assert len(aprovados) == 0
    assert len(alertas) > 0

    print("\n[SUCESSO] Todos os testes isolados passaram perfeitamente!")

if __name__ == "__main__":
    test_validador()
