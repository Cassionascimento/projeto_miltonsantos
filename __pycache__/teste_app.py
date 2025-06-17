import requests

url = 'http://127.0.0.1:5000/api/circuitos'  # ✅ Rota existente

try:
    response = requests.get(url)
    if response.status_code == 200:
        dados = response.json()
        print("Dados obtidos:")
        for item in dados.get("features", [])[:5]:  # mostra até 5
            print(item["properties"])
    else:
        print("Erro ao acessar API:", response.status_code)
except Exception as e:
    print("Erro:", str(e))

