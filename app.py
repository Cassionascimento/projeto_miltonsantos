from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
import requests
from werkzeug.utils import secure_filename
import json
import os
import requests
from bs4 import BeautifulSoup



app = Flask(__name__)
CORS(app)

# ===================== CONFIGURAÇÕES DE UPLOAD =====================
UPLOAD_FOLDER = 'backend/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Cria pasta se não existir
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ===================== ROTAS DE IMAGENS ============================

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'message': 'Arquivo enviado com sucesso', 'filename': filename}), 200
    else:
        return jsonify({'error': 'Tipo de arquivo não permitido'}), 400

@app.route('/photos/<filename>')
def get_photo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/photos')
def list_photos():
    photos = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if allowed_file(filename):
            photos.append({
                'name': filename,
                'url': f'/photos/{filename}'
            })
    return jsonify({'photos': photos})

@app.route('/photos/<filename>', methods=['DELETE'])
def delete_photo(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'message': 'Foto deletada com sucesso'}), 200
    else:
        return jsonify({'error': 'Arquivo não encontrado'}), 404

# ===================== ROTAS DE DADOS ==============================

@app.route('/api/circuitos')
def get_circuitos():
    try:
        with open('backend/assets/circuitos.geojson', 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)

        filtro_circuito = request.args.get('circuito')
        if filtro_circuito:
            geojson_data['features'] = [
                f for f in geojson_data['features']
                if f['properties'].get('circuito') == filtro_circuito
            ]

        periferia = request.args.get('periferia')
        if periferia == 'true':
            geojson_data['features'] = [
                f for f in geojson_data['features']
                if f['properties'].get('periferia') is True
            ]

        return jsonify(geojson_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/renda')
def get_renda():
    renda_data = [
        {"classe": "0-1 SM", "valor": 50},
        {"classe": "1-3 SM", "valor": 30},
        {"classe": "3+ SM", "valor": 20},
    ]
    return jsonify(renda_data)

@app.route('/api/nlp', methods=['POST'])
def nlp():
    data = request.json
    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({'error': 'Prompt não fornecido'}), 400

    try:
        import openai
        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt,
            max_tokens=150,
            temperature=0.7
        )
        result = response.choices[0].text.strip()
        return jsonify({'result': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def homepage():
    return render_template('index.html')

@app.route('/api/dados_completos')
def dados_completos():
    circuitos = {}
    try:
        with open('backend/assets/circuitos.geojson', 'r', encoding='utf-8') as f:
            circuitos = json.load(f)
    except Exception as e:
        circuitos = {"error": str(e)}

    olx_data = []
    if os.path.exists('olx_baixa_renda.json'):
        with open('olx_baixa_renda.json', 'r', encoding='utf-8') as f:
            olx_data = json.load(f)

    tweets_data = []
    if os.path.exists('tweets_sp.json'):
        with open('tweets_sp.json', 'r', encoding='utf-8') as f:
            tweets_data = json.load(f)

    return jsonify({
        "circuitos": circuitos,
        "olx": olx_data,
        "tweets": tweets_data
    })


@app.route('/api/raspagem')
def raspagem_diplomatica():
    try:
        # Exemplo simples com scraping fictício de uma página qualquer
        url = 'https://www.gov.br/mre/pt-br'  # Site do Itamaraty
        resposta = requests.get(url)
        soup = BeautifulSoup(resposta.text, 'html.parser')

        # Pegando os 3 primeiros títulos de notícia (ajuste conforme a estrutura real do site)
        titulos = [item.get_text(strip=True) for item in soup.find_all('h2')[:3]]

        return jsonify({
            'fonte': url,
            'resultados': titulos
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/api/raspagem-onu')
def raspagem_onu():
    try:
        url = 'https://www.un.org/pt/sections/news-and-events/news/'
        resposta = requests.get(url)
        soup = BeautifulSoup(resposta.text, 'html.parser')

        # Na página da ONU, notícias estão em <div class="view-content"> e cada notícia é <div class="views-row">
        noticias_divs = soup.select('div.view-content div.views-row')[:5]

        noticias = []
        for noticia in noticias_divs:
            titulo = noticia.select_one('h3 a')
            resumo = noticia.select_one('div.field-content p')
            link = titulo['href'] if titulo else ''
            if titulo and resumo:
                noticias.append({
                    'titulo': titulo.get_text(strip=True),
                    'resumo': resumo.get_text(strip=True),
                    'link': f"https://www.un.org{link}"
                })

        return jsonify({'fonte': url, 'noticias': noticias})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/api/raspagem-govbr')
def raspagem_govbr():
    try:
        url = 'https://www.gov.br/mre/pt-br'
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')

        # Ajuste a seleção conforme a estrutura atual do site gov.br/mre
        noticias = soup.select('div.card')[:5]  # Exemplo: pegar os primeiros 5 cards

        resultados = []
        for noticia in noticias:
            titulo_tag = noticia.select_one('h3') or noticia.select_one('h2')
            link_tag = noticia.find('a', href=True)
            titulo = titulo_tag.get_text(strip=True) if titulo_tag else 'Sem título'
            link = link_tag['href'] if link_tag else url
            resultados.append({'titulo': titulo, 'link': link})

        return jsonify({'fonte': url, 'noticias': resultados})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/raspagem-cfr')
def raspagem_cfr():
    try:
        url = 'https://www.cfr.org/'
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')

        artigos = soup.select('div.home-featured-article__content')[:5]  # Ajuste conforme o site

        resultados = []
        for art in artigos:
            titulo_tag = art.select_one('h2 a')
            resumo_tag = art.select_one('p')
            titulo = titulo_tag.get_text(strip=True) if titulo_tag else 'Sem título'
            link = titulo_tag['href'] if titulo_tag and titulo_tag.has_attr('href') else url
            resumo = resumo_tag.get_text(strip=True) if resumo_tag else ''
            resultados.append({'titulo': titulo, 'link': link, 'resumo': resumo})

        return jsonify({'fonte': url, 'artigos': resultados})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    



if __name__ == '__main__':
    app.run(debug=True)








