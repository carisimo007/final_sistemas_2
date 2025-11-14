"""
Cargador de tablas WISC-V desde archivos JSON
Soporte completo para edades 6:0 a 16:11
"""

import json
import os
from typing import Dict, Any

def cargar_tablas_completas() -> Dict[str, Any]:
    """
    Carga TODAS las tablas WISC-V para edades 6-16 desde archivos JSON
    """
    tablas = {}
    carpeta_tablas = os.path.join(os.path.dirname(__file__), 'tablas')
    
    if not os.path.exists(carpeta_tablas):
        print("⚠️  Carpeta de tablas no encontrada.")
        return obtener_tablas_por_defecto()
    
    # Función para ordenar grupos etarios
    def clave_orden(grupo):
        try:
            # Convertir "10:0-10:5" → (10, 0) para ordenar
            parte_edad = grupo.split(':')[0]
            return int(parte_edad)
        except:
            return 0
    
    # Cargar cada archivo JSON
    archivos_cargados = 0
    archivos_json = []
    
    # Primero listar todos los archivos
    for archivo in os.listdir(carpeta_tablas):
        if archivo.endswith('.json') and archivo != 'INFO.json':
            archivos_json.append(archivo)
    
    # Ordenar archivos por edad
    archivos_json.sort(key=lambda x: clave_orden(x.replace('_', ':')))
    
    for archivo in archivos_json:
        ruta_archivo = os.path.join(carpeta_tablas, archivo)
        
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                # Convertir nombre: "8_6-8_11.json" → "8:6-8:11"
                nombre_grupo = archivo.replace('.json', '').replace('_', ':')
                tablas[nombre_grupo] = json.load(f)
            
            archivos_cargados += 1
            
        except Exception as e:
            print(f"❌ Error cargando {archivo}: {e}")
    
    if archivos_cargados > 0:
        grupos_ordenados = sorted(tablas.keys(), key=clave_orden)
        print(f"📊 Tablas cargadas: {archivos_cargados} grupos etarios")
        print(f"🎯 Rango de edades: {grupos_ordenados[0]} a {grupos_ordenados[-1]}")
    else:
        print("⚠️  No se pudieron cargar tablas. Usando por defecto.")
        return obtener_tablas_por_defecto()
    
    return tablas

def obtener_tablas_por_defecto() -> Dict[str, Any]:
    """
    Tablas por defecto mínimas para emergencias
    """
    return {
        "8:6-8:11": {
            "CC": {"1": "0-3", "2": "4", "3": "5", "4": "6-7", "5": "8-9", 
                  "6": "10-11", "7": "12-14", "8": "15-16", "9": "17-19", 
                  "10": "20-21", "11": "22-24", "12": "25-27", "13": "28-30", 
                  "14": "31-32", "15": "33-35", "16": "36-37", "17": "38-39", 
                  "18": "40-41", "19": "42-58"},
            "BAL": {"1": "0-3", "2": "4-5", "3": "6-7", "4": "8-9", "5": "10", 
                   "6": "11", "7": "12", "8": "13", "9": "14", "10": "15-16", 
                   "11": "17", "12": "19", "13": "20-20", "14": "21-22", 
                   "15": "23", "16": "24-25", "17": "26", "18": "27", "19": "28-34"}
        }
    }

# Cargar tablas al importar el módulo
TABLAS_WISCV = cargar_tablas_completas()