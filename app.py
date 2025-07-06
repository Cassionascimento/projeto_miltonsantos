from datetime import date
from decimal import Decimal
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
import pandas as pd
import requests
from werkzeug.utils import secure_filename
import json
import os
import requests
from bs4 import BeautifulSoup
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sistema.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o SQLAlchemy
db = SQLAlchemy(app)
CORS(app)

class PrecoM2(db.Model): 
    id= db.Column(db.Integer, primary_key=True)
    data= db.Column(db.Date, nullable=False)
    valor= db.Column(db.Numeric(10,2), nullable=False)
    cidade= db.Column(db.String, nullable=False)


@app.route('/')
def homepage():
    variacoes=PrecoM2.query.all()
    return render_template('index.html',variacoes=variacoes)

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
    
@app.route("/db")
def banco():
    caminho = os.path.join(app.root_path,"static/files", "csvm2SP.xls")
    df=pd.read_excel(caminho)    
    for _,linha in df.iterrows():
        ano_str, mes_str = str(linha['data']).split(".")
        ano = int(ano_str)
        mes = int(mes_str)
        data = date(ano, mes, 1)
        preco= PrecoM2(
            cidade= "São Paulo", 
            data=data,
            valor= Decimal(linha["valor"])
        )
        db.session.add(preco)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)









