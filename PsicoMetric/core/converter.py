import json
import os
from pathlib import Path
from typing import Dict, Optional

class WISCConverter:
    def __init__(self):
        self.data = self._cargar_datos()
    
    def _cargar_datos(self) -> Dict:
        """Carga los datos desde el archivo JSON"""
        try:
            # Buscar el archivo JSON en la ruta correcta
            base_dir = Path(__file__).parent.parent
            data_path = base_dir / 'data' / 'wisc_v_data.json'
            
            with open(data_path, 'r', encoding='utf-8') as file:
                datos = json.load(file)
                return datos['WISC_V_tablas_conversion']
                
        except FileNotFoundError:
            raise Exception(f"❌ Archivo JSON no encontrado en: {data_path}")
        except json.JSONDecodeError:
            raise Exception("❌ Error al decodificar el JSON")
        except Exception as e:
            raise Exception(f"❌ Error al cargar datos: {e}")
    
    def _convertir_edad_a_grupo(self, edad_formato: str) -> str:
        """
        Convierte formato 'años:meses' a ID de grupo etario
        Ejemplo: '6:5' -> '6_0_6_5'
        """
        try:
            años_str, meses_str = edad_formato.split(':')
            años = int(años_str)
            meses = int(meses_str)
            
            # Mapeo COMPLETO de edades a grupos etarios (6:0 a 16:11)
            grupos = [
                # 6 años
                ((6, 0), (6, 5), "6_0_6_5"),
                ((6, 6), (6, 11), "6_6_6_11"),
                # 7 años
                ((7, 0), (7, 5), "7_0_7_5"),
                ((7, 6), (7, 11), "7_6_7_11"),
                # 8 años
                ((8, 0), (8, 5), "8_0_8_5"),
                ((8, 6), (8, 11), "8_6_8_11"),
                # 9 años
                ((9, 0), (9, 5), "9_0_9_5"),
                ((9, 6), (9, 11), "9_6_9_11"),
                # 10 años
                ((10, 0), (10, 5), "10_0_10_5"),
                ((10, 6), (10, 11), "10_6_10_11"),
                # 11 años
                ((11, 0), (11, 5), "11_0_11_5"),
                ((11, 6), (11, 11), "11_6_11_11"),
                # 12 años
                ((12, 0), (12, 5), "12_0_12_5"),
                ((12, 6), (12, 11), "12_6_12_11"),
                # 13 años
                ((13, 0), (13, 5), "13_0_13_5"),
                ((13, 6), (13, 11), "13_6_13_11"),
                # 14 años
                ((14, 0), (14, 5), "14_0_14_5"),
                ((14, 6), (14, 11), "14_6_14_11"),
                # 15 años
                ((15, 0), (15, 5), "15_0_15_5"),
                ((15, 6), (15, 11), "15_6_15_11"),
                # 16 años
                ((16, 0), (16, 5), "16_0_16_5"),
                ((16, 6), (16, 11), "16_6_16_11")
            ]
            
            # Buscar el grupo correspondiente
            for (años_min, meses_min), (años_max, meses_max), grupo_id in grupos:
                # Verificar si la edad está en este rango
                edad_en_meses = años * 12 + meses
                min_en_meses = años_min * 12 + meses_min
                max_en_meses = años_max * 12 + meses_max
                
                if min_en_meses <= edad_en_meses <= max_en_meses:
                    print(f"✅ Edad {edad_formato} → Grupo {grupo_id}")
                    return grupo_id
            
            # Si no se encontró ningún grupo
            raise ValueError(f"Edad {edad_formato} fuera de rango válido (6:0 - 16:11)")
            
        except Exception as e:
            raise ValueError(f"Error al convertir edad '{edad_formato}': {e}")
    
    def _esta_en_rango(self, puntaje: int, rango_str: str) -> bool:
        """Verifica si un puntaje está dentro de un rango"""
        if not rango_str or rango_str == '-' or rango_str == '':
            return False
        
        # Si es un rango (ej: "8-10")
        if '-' in rango_str:
            try:
                min_val, max_val = map(int, rango_str.split('-'))
                return min_val <= puntaje <= max_val
            except ValueError:
                return False
        
        # Si es un valor único (ej: "5")
        try:
            return puntaje == int(rango_str)
        except ValueError:
            return False
    
    def convertir_puntaje(self, edad_formato: str, subprueba: str, puntaje_bruto: int) -> int:
        """
        Convierte puntaje bruto a escalar usando los datos del JSON
        """
        try:
            print(f"🔍 DIAGNÓSTICO - Entrada: Edad={edad_formato}, Subprueba={subprueba}, Bruto={puntaje_bruto}")
            
            # Convertir edad a grupo etario
            grupo_id = self._convertir_edad_a_grupo(edad_formato)
            print(f"📊 Grupo etario encontrado: {grupo_id}")
            
            # Verificar que la subprueba existe
            if subprueba not in self.data['subpruebas']:
                print(f"❌ Subprueba '{subprueba}' no encontrada en: {list(self.data['subpruebas'].keys())}")
                # Intentar con variaciones del código
                if subprueba == "INF":
                    subprueba = "IN"  # Algunas tablas usan "IN" en lugar de "INF"
                    print(f"🔄 Intentando con subprueba: {subprueba}")
                else:
                    raise ValueError(f"Subprueba no encontrada: {subprueba}")
            
            # Obtener la tabla de conversión
            tabla = self.data['grupos_etarios'][grupo_id]['tabla']
            print(f"📋 Tabla cargada con {len(tabla)} filas para grupo {grupo_id}")
            
            # Buscar en la tabla
            for i, fila in enumerate(tabla):
                rango_bruto = fila.get(subprueba)
                if self._esta_en_rango(puntaje_bruto, rango_bruto):
                    puntaje_escala = fila['puntaje_escala']
                    print(f"✅ CONVERSIÓN EXITOSA: Fila {i+1} - {subprueba}: {puntaje_bruto} → {puntaje_escala} (rango: {rango_bruto})")
                    return puntaje_escala
            
            # Si no se encontró, mostrar información de debug
            print(f"❌ Puntaje {puntaje_bruto} NO encontrado en rangos para {subprueba}")
            print(f"📊 Rangos disponibles para {subprueba} en grupo {grupo_id}:")
            for i, fila in enumerate(tabla):
                rango = fila.get(subprueba, '-')
                escala = fila['puntaje_escala']
                if rango != '-':  # Solo mostrar rangos que existen
                    print(f"   Fila {i+1}: Escala {escala} → Rango {rango}")
            
            raise ValueError(f"Puntaje bruto {puntaje_bruto} fuera de rango para {subprueba}")
            
        except Exception as e:
            print(f"💥 Error en convertir_puntaje: {e}")
            raise

    def obtener_grupos_disponibles(self):
        """Retorna lista de grupos etarios disponibles"""
        return list(self.data['grupos_etarios'].keys())
    
    def obtener_subpruebas_disponibles(self):
        """Retorna lista de subpruebas disponibles"""
        return list(self.data['subpruebas'].keys())

# Instancia global para usar en la aplicación
conversor = WISCConverter()