from flask import Flask, jsonify, render_template, send_from_directory
from flask_cors import CORS
import geopandas as gpd
import pandas as pd
import json
import os
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuração de logging avançada
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()
    ]
)

# Diretórios
DATA_DIR = 'data'
GEOJSON_DIR = os.path.join(DATA_DIR, 'geojson')
CSV_DIR = os.path.join(DATA_DIR, 'csv')

# --- Carregamento de dados com cache e tratamento de erros ---
def load_data_with_fallback(file_path, loader, fallback_data=None):
    try:
        data = loader(file_path)
        logging.info(f"Dados carregados com sucesso: {file_path}")
        return data
    except Exception as e:
        logging.error(f"Erro ao carregar {file_path}: {str(e)}")
        return fallback_data

def load_geojson(path):
    return gpd.read_file(path)

def load_csv(path):
    return pd.read_csv(path)

# Carregamento dos dados principais
circuitos = load_data_with_fallback(
    os.path.join(GEOJSON_DIR, 'circuitos_faria_lima.geojson'),
    load_geojson
)

dados_wifi = load_data_with_fallback(
    os.path.join(CSV_DIR, 'wifi_livre_sp.csv'),
    load_csv,
    pd.DataFrame({
        'ano': [2019, 2020, 2021, 2022, 2023],
        'acessos': [15000, 18000, 22000, 25000, 28000],
        'velocidade_media': [5.2, 5.8, 6.3, 6.7, 7.1]
    })
)

dados_telecentro = load_data_with_fallback(
    os.path.join(CSV_DIR, 'telecentros_sp.csv'),
    load_csv,
    pd.DataFrame({
        'bairro': ['Pinheiros', 'Itaim Bibi', 'Vila Olímpia', 'Jardim Paulista'],
        'acessos_2025': [1250, 980, 760, 1100],
        'usuarios_unicos': [850, 620, 510, 780]
    })
)

# --- Dados simulados para análise espacial ---
def generate_spatial_analysis():
    years = list(range(2015, 2025))
    return pd.DataFrame({
        'ano': years,
        'circuito_superior': [10 + i * 1.5 for i in range(len(years))],
        'circuito_inferior': [5 + i * 0.8 for i in range(len(years))],
        'disparidade': [5 + i * 0.7 for i in range(len(years))]
    })

def generate_income_distribution():
    categories = [
        'Banqueiros/CFOs', 'CEOs/CTOs', 'Analistas/Gerentes', 
        'Desenvolvedores', 'Entregadores/Office-boys'
    ]
    return pd.DataFrame({
        'categoria': categories,
        'renda_media': [45000, 32000, 8500, 6500, 2200],
        'participacao': [2, 8, 25, 35, 30]
    })

# --- Rotas da API ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route('/api/circuitos')
def get_circuitos():
    if circuitos is None:
        return jsonify({'error': 'Dados geoespaciais não disponíveis'}), 503
    
    # Processamento adicional dos dados
    circuitos['centroid'] = circuitos.geometry.centroid
    circuitos['area_ha'] = circuitos.geometry.area / 10000
    
    return jsonify(json.loads(circuitos.to_json()))

@app.route('/api/dados-wifi')
def get_wifi_data():
    # Adiciona cálculo de variação percentual
    dados = dados_wifi.copy()
    dados['variacao_percentual'] = dados['acessos'].pct_change() * 100
    return jsonify(dados.to_dict(orient='records'))

@app.route('/api/dados-telecentro')
def get_telecentro_data():
    dados = dados_telecentro.copy()
    dados['acessos_por_usuario'] = dados['acessos_2025'] / dados['usuarios_unicos']
    return jsonify(dados.to_dict(orient='records'))

@app.route('/api/analise-espacial')
def get_spatial_analysis():
    analysis = generate_spatial_analysis()
    return jsonify(analysis.to_dict(orient='records'))

@app.route('/api/dados-renda')
def get_income_data():
    income_data = generate_income_distribution()
    return jsonify(income_data.to_dict(orient='records'))

@app.route('/api/indicadores')
def get_indicators():
    return jsonify({
        'pib_regional': 215000000000,  # 215 bilhões
        'empregos_formais': 185000,
        'startups': 1250,
        'salario_medio_superior': 18500,
        'salario_medio_inferior': 2200,
        'indice_gini': 0.68,
        'ultima_atualizacao': datetime.now().isoformat()
    })

@app.route('/api/milton-santos')
def get_milton_info():
    return jsonify({
        'nome': 'Milton Santos',
        'nascimento': '1926-05-03',
        'falecimento': '2001-06-24',
        'biografia': 'Geógrafo brasileiro pioneiro na análise crítica da globalização e dos circuitos espaciais.',
        'contribuicoes': [
            'Teoria dos Circuitos Espaciais',
            'Conceito de Globalização Perversa',
            'Espaço como instância social',
            'Rugosidades do espaço'
        ],
        'foto_url': '/api/milton-santos/foto'
    })

@app.route('/api/milton-santos/foto')
def get_milton_photo():
    photo_path = os.path.join(DATA_DIR, 'images', 'milton_santos.jpg')
    if os.path.exists(photo_path):
        return send_from_directory(os.path.dirname(photo_path), os.path.basename(photo_path))
    return jsonify({'error': 'Foto não disponível'}), 404

# --- Documentação da API ---
@app.route('/api')
def api_docs():
    endpoints = {
        'circuitos': '/api/circuitos - Dados geoespaciais dos circuitos econômicos',
        'wifi': '/api/dados-wifi - Dados de acesso ao WiFi público',
        'telecentros': '/api/dados-telecentro - Acessos a telecentros',
        'analise-espacial': '/api/analise-espacial - Evolução temporal dos circuitos',
        'renda': '/api/dados-renda - Distribuição de renda por categoria',
        'indicadores': '/api/indicadores - Principais indicadores da região',
        'milton-santos': '/api/milton-santos - Biografia e contribuições'
    }
    return jsonify(endpoints)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)







