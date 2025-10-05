import requests

def gerar_qr_code_pix():
    URL = "https://gerarqrcodepix.com.br/api/v1"
    
    PARAMETROS = {
        "nome": "Gilderlan Silva da Cruz",
        "cidade": "Ibirataia",
        "chave": "12704097518",  # substitua pela sua chave Pix válida
        "valor": 100.00,
        "saida": "qr"  # ou "br" para código brcode
    }
    
    try:
        print("Gerando QR Code PIX...")
        response = requests.get(URL, params=PARAMETROS)
        
        if response.status_code == 200:
            print("QR Code gerado com sucesso!")
            
            # A API retorna a imagem diretamente no conteúdo
            with open("pix_qrcode.png", "wb") as f:
                f.write(response.content)
            print("Imagem salva como pix_qrcode.png")
            
        else:
            print(f"Erro ao gerar QR Code: {response.status_code}")
            print("Resposta:", response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")

# Executar a função
if __name__ == "__main__":
    gerar_qr_code_pix()