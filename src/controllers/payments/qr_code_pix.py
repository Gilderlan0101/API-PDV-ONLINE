# import crcmod
# import qrcode

# def gerar_payload_pix(nome, chave_pix, valor, cidade, txid="***"):
#     """
#     Gera payload PIX válido.

#     :param nome: Nome do recebedor (até 25 caracteres)
#     :param chave_pix: Chave PIX (CPF, CNPJ, email ou celular)
#     :param valor: Valor da transação (string, ex: "10.50")
#     :param cidade: Cidade do recebedor
#     :param txid: Identificador da transação (pode ser qualquer string)
#     :return: payload PIX pronto para QR code
#     """
#     # Campos básicos
#     payloadFormatIndicator = "000201"
#     merchantCategoryCode = "52040000"
#     transactionCurrency = "5303986"
#     transactionAmount = f"54{float(valor):.2f}" if valor else ""
#     countryCode = "5802BR"

#     # Merchant Account Info (chave PIX)
#     chave_len = f"{len(chave_pix):02}"
#     merchantAccountInfo = f"0014BR.GOV.BCB.PIX01{chave_len}{chave_pix}"
#     merchantAccountInfo = f"26{len(merchantAccountInfo):02}{merchantAccountInfo}"

#     # Merchant Name e City
#     nome = nome[:25]  # máximo 25 caracteres
#     cidade = cidade[:15]  # máximo 15 caracteres
#     merchantName = f"59{len(nome):02}{nome}"
#     merchantCity = f"60{len(cidade):02}{cidade}"

#     # Additional Data Field (txid)
#     txid = txid if txid else "***"
#     addDataField = f"05{len(txid):02}{txid}"
#     addDataField = f"62{len(addDataField):02}{addDataField}"

#     # Monta payload sem CRC
#     payload_sem_crc = (
#         payloadFormatIndicator +
#         merchantAccountInfo +
#         merchantCategoryCode +
#         transactionCurrency +
#         transactionAmount +
#         countryCode +
#         merchantName +
#         merchantCity +
#         addDataField +
#         "6304"
#     )

#     # CRC16
#     crc16_func = crcmod.mkCrcFun(0x11021, initCrc=0xFFFF, rev=True, xorOut=0x0000)
#     crc = crc16_func(payload_sem_crc.encode('utf-8'))
#     crc_hex = f"{crc:04X}"

#     payload_completo = f"{payload_sem_crc}{crc_hex}"
#     return payload_completo

# def gerar_qrcode_pix(nome, chave_pix, valor, cidade, txid, arquivo_saida="pix.png"):
#     payload = gerar_payload_pix(nome, chave_pix, valor, cidade, txid)
#     img = qrcode.make(payload)
#     img.save(arquivo_saida)
#     return payload

# # --- EXEMPLO DE USO ---
# nome = "Gilderlan Silva da Cruz"
# chave_pix = "12704097518"
# valor = "1.00"
# cidade = "Ibirataia"
# txid = "123456"  # pode ser qualquer identificador

# payload = gerar_qrcode_pix(nome, chave_pix, valor, cidade, txid, "teste.png")
# print("PIX Copia e Cola:", payload)
# print("QR code salvo em: teste.png")
