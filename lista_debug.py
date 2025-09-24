from datetime import datetime


def parcial():
    item = 1400  # valor total da dívida
    valor_pago = 0
    cliente = {"nome": "Gilderlan", "cpf": "12345678", "pagamentos": []}  # lista de pagamentos realizados

    print(f"💰 Dívida total: R$ {item}")

    while valor_pago < item:
        busca_cliente = input("Busque cliente (nome ou cpf): ")

        if busca_cliente in (cliente["nome"], cliente["cpf"]):
            entrada = float(input("Valor pago: R$ "))

            if entrada == 0:
                print("🚫 Pagamento cancelado.")
                break

            valor_pago += entrada
            falta = item - valor_pago if valor_pago < item else 0

            pagamento = {"valor": entrada, "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "restante": falta}
            cliente["pagamentos"].append(pagamento)

            print(f"✅ Pagamento registrado: R$ {entrada}")
            print(f"📅 Data: {pagamento['data']}")
            print(f"🔎 Restante da dívida: R$ {falta}\n")

        else:
            print("❌ Cliente não encontrado.")

    if valor_pago >= item:
        print("🎉 Dívida quitada!")
        print("Resumo dos pagamentos:")
        for i, p in enumerate(cliente["pagamentos"], start=1):
            print(f"{i}. R$ {p['valor']} em {p['data']} | Restante após: R$ {p['restante']}")


parcial()
