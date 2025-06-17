import geopandas as gpd

def analyze_spatial_inequality():
    # Aqui é só um exemplo simples que lê um arquivo geojson e retorna um GeoDataFrame
    # Depois você pode trocar essa lógica pelo que quiser

    try:
        gdf = gpd.read_file('backend/assets/circuitos.geojson')
        # Só para garantir que retorne um GeoDataFrame válido
        return gdf
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
        # Retorna um GeoDataFrame vazio em caso de erro
        return gpd.GeoDataFrame()
