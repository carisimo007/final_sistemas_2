"""
Interfaz gráfica principal de la aplicación WISC-V con SQLite, panel colapsable y sistema de IA
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from math import erf, sqrt
import json
import os
import sys
import sqlite3
import uuid

# Agregar el directorio core al path para importar el conversor
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

try:
    from core.converter import conversor
    print("✅ Conversor de puntajes escala cargado correctamente")
except ImportError as e:
    print(f"❌ Error cargando conversor de escala: {e}")
    conversor = None

# Intentar importar matplotlib para gráficas
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib
    matplotlib.use('TkAgg')
    MATPLOTLIB_AVAILABLE = True
    print("✅ Matplotlib cargado correctamente")
except ImportError as e:
    print(f"❌ Matplotlib no disponible: {e}")
    MATPLOTLIB_AVAILABLE = False

# Importaciones para IA
try:
    import numpy as np
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_absolute_error, r2_score
    import joblib
    import warnings
    warnings.filterwarnings('ignore')
    SKLEARN_AVAILABLE = True
    print("✅ Scikit-learn cargado correctamente")
except ImportError as e:
    print(f"❌ Scikit-learn no disponible: {e}")
    SKLEARN_AVAILABLE = False


class DatabaseManager:
    """Gestor de base de datos SQLite para la aplicación WISC-V"""
    
    def __init__(self, db_path="wisc_v_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos con las tablas necesarias"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Activar claves foráneas
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Tabla de pacientes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pacientes (
                    id TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    dni TEXT,
                    fecha_nacimiento DATE NOT NULL,
                    notas TEXT,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de evaluaciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS evaluaciones (
                    id TEXT PRIMARY KEY,
                    paciente_id TEXT NOT NULL,
                    fecha_evaluacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    datos_evaluacion TEXT NOT NULL,
                    FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
                )
            ''')
            
            # Índices para mejor rendimiento
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_pacientes_nombre ON pacientes(nombre)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_pacientes_dni ON pacientes(dni)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_evaluaciones_paciente_id ON evaluaciones(paciente_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_evaluaciones_fecha ON evaluaciones(fecha_evaluacion)')
            
            conn.commit()
            conn.close()
            print("✅ Base de datos SQLite inicializada correctamente")
            
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")
    
    def ejecutar_consulta(self, query, params=(), fetch=False):
        """Ejecuta una consulta en la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            # ACTIVAR CLAVES FORÁNEAS EN CADA CONEXIÓN
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if fetch:
                resultado = cursor.fetchall()
            else:
                resultado = True  # Indicar éxito para operaciones sin fetch
                
            conn.commit()
            conn.close()
            
            # CORRECCIÓN: Retornar consistentemente
            return resultado if fetch else True
            
        except Exception as e:
            print(f"❌ Error en consulta: {e}")
            # CORRECCIÓN: Retornar lista vacía para fetch=True, False para fetch=False
            return [] if fetch else False
    
    def agregar_paciente(self, nombre, dni, fecha_nacimiento, notas=""):
        """Agrega un nuevo paciente a la base de datos"""
        paciente_id = str(uuid.uuid4())[:8]
        
        query = '''
            INSERT INTO pacientes (id, nombre, dni, fecha_nacimiento, notas)
            VALUES (?, ?, ?, ?, ?)
        '''
        
        # CORRECCIÓN: Cambiar la forma de verificar el éxito
        try:
            exito = self.ejecutar_consulta(query, 
                                         (paciente_id, nombre, dni, fecha_nacimiento.isoformat(), notas))
            
            # CORRECCIÓN: Verificar explícitamente si es True
            if exito:
                print(f"✅ Paciente agregado: {nombre} (ID: {paciente_id})")
                return paciente_id
            else:
                print(f"❌ Error al agregar paciente: {nombre}")
                return None
                
        except Exception as e:
            print(f"❌ Excepción al agregar paciente: {e}")
            return None
    
    def buscar_pacientes(self, texto_busqueda=""):
        """Busca pacientes por nombre o DNI"""
        query = '''
            SELECT id, nombre, dni, fecha_nacimiento, notas, fecha_registro
            FROM pacientes
            WHERE nombre LIKE ? OR dni LIKE ?
            ORDER BY nombre
        '''
        
        texto_busqueda = f"%{texto_busqueda}%"
        resultados = self.ejecutar_consulta(query, (texto_busqueda, texto_busqueda), fetch=True)
        
        # CORRECCIÓN: Verificar que resultados sea una lista antes de iterar
        pacientes = []
        if resultados and isinstance(resultados, list):  # Verificar que es una lista
            for row in resultados:
                pacientes.append({
                    'id': row[0],
                    'nombre': row[1],
                    'dni': row[2],
                    'fecha_nacimiento': row[3],
                    'notas': row[4],
                    'fecha_registro': row[5]
                })
        else:
            print(f"⚠️ No se pudieron obtener pacientes. Resultados: {resultados}")
        
        return pacientes
    
    def obtener_paciente(self, paciente_id):
        """Obtiene un paciente por su ID"""
        query = '''
            SELECT id, nombre, dni, fecha_nacimiento, notas, fecha_registro
            FROM pacientes
            WHERE id = ?
        '''
        
        resultado = self.ejecutar_consulta(query, (paciente_id,), fetch=True)
        
        # CORRECCIÓN: Verificar que sea lista y tenga elementos
        if resultado and isinstance(resultado, list) and len(resultado) > 0:
            row = resultado[0]
            return {
                'id': row[0],
                'nombre': row[1],
                'dni': row[2],
                'fecha_nacimiento': row[3],
                'notas': row[4],
                'fecha_registro': row[5]
            }
        return None
    
    def actualizar_paciente(self, paciente_id, nombre, dni, fecha_nacimiento, notas=""):
        """Actualiza los datos de un paciente"""
        query = '''
            UPDATE pacientes
            SET nombre = ?, dni = ?, fecha_nacimiento = ?, notas = ?
            WHERE id = ?
        '''
        
        exito = self.ejecutar_consulta(query, 
                                     (nombre, dni, fecha_nacimiento.isoformat(), notas, paciente_id))
        
        # CORRECCIÓN: Verificar explícitamente True
        if exito:
            print(f"✅ Paciente actualizado: {nombre} (ID: {paciente_id})")
            return True
        return False
    
    def eliminar_paciente(self, paciente_id):
        """Elimina un paciente y todas sus evaluaciones"""
        try:
            # Primero eliminar las evaluaciones manualmente para evitar problemas con CASCADE
            query_evaluaciones = 'DELETE FROM evaluaciones WHERE paciente_id = ?'
            exito_eval = self.ejecutar_consulta(query_evaluaciones, (paciente_id,))
            
            # Luego eliminar el paciente
            query_paciente = 'DELETE FROM pacientes WHERE id = ?'
            exito_pac = self.ejecutar_consulta(query_paciente, (paciente_id,))
            
            # CORRECCIÓN: Verificar ambos éxitos
            if exito_eval and exito_pac:
                print(f"✅ Paciente eliminado: {paciente_id}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Error eliminando paciente {paciente_id}: {e}")
            return False
    
    def agregar_evaluacion(self, paciente_id, datos_evaluacion):
        """Agrega una nueva evaluación para un paciente"""
        evaluacion_id = str(uuid.uuid4())[:8]
        
        query = '''
            INSERT INTO evaluaciones (id, paciente_id, datos_evaluacion)
            VALUES (?, ?, ?)
        '''
        
        try:
            # Convertir datos a JSON con manejo de tipos no serializables
            def json_serializer(obj):
                """Serializador personalizado para tipos no estándar"""
                if isinstance(obj, (date, datetime)):
                    return obj.isoformat()
                raise TypeError(f"Tipo {type(obj)} no serializable")
            
            datos_json = json.dumps(datos_evaluacion, ensure_ascii=False, default=json_serializer)
            
            exito = self.ejecutar_consulta(query, (evaluacion_id, paciente_id, datos_json))
            
            if exito:
                print(f"✅ Evaluación agregada: {evaluacion_id} para paciente {paciente_id}")
                return evaluacion_id
            else:
                print(f"❌ Error al agregar evaluación")
                return None
                
        except Exception as e:
            print(f"❌ Error serializando datos de evaluación: {e}")
            # Intentar con una serialización más simple
            try:
                # Crear una copia serializable de los datos
                datos_serializables = {}
                for key, value in datos_evaluacion.items():
                    if isinstance(value, dict):
                        datos_serializables[key] = {}
                        for k, v in value.items():
                            if isinstance(v, (date, datetime)):
                                datos_serializables[key][k] = v.isoformat()
                            else:
                                datos_serializables[key][k] = v
                    elif isinstance(value, (date, datetime)):
                        datos_serializables[key] = value.isoformat()
                    else:
                        datos_serializables[key] = value
                
                datos_json = json.dumps(datos_serializables, ensure_ascii=False)
                exito = self.ejecutar_consulta(query, (evaluacion_id, paciente_id, datos_json))
                
                if exito:
                    print(f"✅ Evaluación agregada (segundo intento): {evaluacion_id}")
                    return evaluacion_id
                return None
                
            except Exception as e2:
                print(f"❌ Error crítico serializando evaluación: {e2}")
                return None
    
    def obtener_evaluaciones_paciente(self, paciente_id):
        """Obtiene todas las evaluaciones de un paciente"""
        query = '''
            SELECT id, fecha_evaluacion, datos_evaluacion
            FROM evaluaciones
            WHERE paciente_id = ?
            ORDER BY fecha_evaluacion DESC
        '''
        
        resultados = self.ejecutar_consulta(query, (paciente_id,), fetch=True)
        
        evaluaciones = []
        # CORRECCIÓN: Verificar que resultados sea una lista
        if resultados and isinstance(resultados, list):
            for row in resultados:
                try:
                    datos = json.loads(row[2])
                except:
                    datos = {}
                    
                evaluaciones.append({
                    'id': row[0],
                    'fecha_evaluacion': row[1],
                    'datos': datos
                })
        
        return evaluaciones
    
    def obtener_evaluacion(self, evaluacion_id):
        """Obtiene una evaluación específica por ID"""
        query = '''
            SELECT id, paciente_id, fecha_evaluacion, datos_evaluacion
            FROM evaluaciones
            WHERE id = ?
        '''
        
        resultado = self.ejecutar_consulta(query, (evaluacion_id,), fetch=True)
        
        # CORRECCIÓN: Verificar que sea lista y tenga elementos
        if resultado and isinstance(resultado, list) and len(resultado) > 0:
            row = resultado[0]
            try:
                datos = json.loads(row[3])
            except:
                datos = {}
                
            return {
                'id': row[0],
                'paciente_id': row[1],
                'fecha_evaluacion': row[2],
                'datos': datos
            }
        return None
    
    def obtener_estadisticas(self):
        """Obtiene estadísticas generales de la base de datos"""
        query_pacientes = "SELECT COUNT(*) FROM pacientes"
        query_evaluaciones = "SELECT COUNT(*) FROM evaluaciones"
        query_ultima_eval = "SELECT MAX(fecha_evaluacion) FROM evaluaciones"
        
        total_pacientes = self.ejecutar_consulta(query_pacientes, fetch=True)
        total_evaluaciones = self.ejecutar_consulta(query_evaluaciones, fetch=True)
        ultima_evaluacion = self.ejecutar_consulta(query_ultima_eval, fetch=True)
        
        # CORRECCIÓN: Verificar que sean listas antes de acceder
        total_pac = total_pacientes[0][0] if total_pacientes and isinstance(total_pacientes, list) and len(total_pacientes) > 0 else 0
        total_eval = total_evaluaciones[0][0] if total_evaluaciones and isinstance(total_evaluaciones, list) and len(total_evaluaciones) > 0 else 0
        ultima_eval = ultima_evaluacion[0][0] if ultima_evaluacion and isinstance(ultima_evaluacion, list) and len(ultima_evaluacion) > 0 else None
        
        return {
            'total_pacientes': total_pac,
            'total_evaluaciones': total_eval,
            'ultima_evaluacion': ultima_eval
        }


class ConversorCompuestos:
    """Clase para manejar la conversión de puntajes compuestos usando JSON"""
    
    def __init__(self):
        self.tablas_compuestos = self.cargar_tablas_compuestos()
    
    def cargar_tablas_compuestos(self):
        """Carga las tablas de conversión para puntajes compuestos desde JSON"""
        try:
            # Buscar el archivo en varias ubicaciones posibles
            posibles_rutas = [
                os.path.join('data', 'wisc_v_compuestos.json'),
                os.path.join(os.path.dirname(__file__), 'data', 'wisc_v_compuestos.json'),
                'wisc_v_compuestos.json'
            ]
            
            ruta_encontrada = None
            for ruta in posibles_rutas:
                if os.path.exists(ruta):
                    ruta_encontrada = ruta
                    break
            
            if not ruta_encontrada:
                raise FileNotFoundError("No se encontró el archivo wisc_v_compuestos.json")
            
            with open(ruta_encontrada, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            
            print(f"✅ Tablas de compuestos cargadas: {list(datos['tablas_conversion'].keys())}")
            return datos
        except Exception as e:
            print(f"❌ Error cargando tablas de compuestos: {e}")
            # Crear estructura vacía para evitar errores
            return {"tablas_conversion": {}}
    
    def convertir_compuesto(self, escala_abrev, suma_escalar):
        """Convierte la suma de puntajes escalares a puntaje compuesto usando las tablas JSON"""
        try:
            if not self.tablas_compuestos or not self.tablas_compuestos['tablas_conversion']:
                raise ValueError("No se cargaron las tablas de compuestos")
            
            if escala_abrev not in self.tablas_compuestos['tablas_conversion']:
                raise ValueError(f"Escala {escala_abrev} no encontrada en las tablas")
            
            tabla_escala = self.tablas_compuestos['tablas_conversion'][escala_abrev]
            datos = tabla_escala['datos']
            
            # Buscar la fila correspondiente a la suma escalar
            for fila in datos:
                if fila['suma'] == suma_escalar:
                    return {
                        'compuesto': fila['valor'],
                        'percentil': fila['percentil'],
                        'conf_90': fila['conf_90'],
                        'conf_95': fila['conf_95'],
                        'nombre_escala': tabla_escala['nombre']
                    }
            
            # Si no se encuentra exacto, usar interpolación o extrapolación
            sumas = [fila['suma'] for fila in datos]
            if suma_escalar < min(sumas):
                # Extrapolación para valores bajos
                fila_min = datos[0]
                fila_sig = datos[1]
                pendiente = (fila_sig['valor'] - fila_min['valor']) / (fila_sig['suma'] - fila_min['suma'])
                valor_extrapolado = fila_min['valor'] + pendiente * (suma_escalar - fila_min['suma'])
                valor_extrapolado = max(40, min(160, round(valor_extrapolado)))
                
                return {
                    'compuesto': int(valor_extrapolado),
                    'percentil': fila_min['percentil'],
                    'conf_90': fila_min['conf_90'],
                    'conf_95': fila_min['conf_95'],
                    'nombre_escala': tabla_escala['nombre']
                }
            elif suma_escalar > max(sumas):
                # Extrapolación para valores altos - MÁS CONSERVADORA
                fila_max = datos[-1]
                fila_ant = datos[-2]
                
                # Calcular pendiente pero limitar el crecimiento
                pendiente = (fila_max['valor'] - fila_ant['valor']) / (fila_max['suma'] - fila_ant['suma'])
                
                # Reducir la pendiente para extrapolaciones más conservadoras
                pendiente_conservadora = pendiente * 0.7  # Reducir 30%
                
                valor_extrapolado = fila_max['valor'] + pendiente_conservadora * (suma_escalar - fila_max['suma'])
                valor_extrapolado = max(fila_max['valor'], min(160, round(valor_extrapolado)))
                
                # Para percentiles, si ya está en >99.9, mantenerlo
                percentil = ">99.9" if "99.9" in str(fila_max['percentil']) else fila_max['percentil']
                
                return {
                    'compuesto': int(valor_extrapolado),
                    'percentil': percentil,
                    'conf_90': fila_max['conf_90'],
                    'conf_95': fila_max['conf_95'],
                    'nombre_escala': tabla_escala['nombre']
                }
            else:
                # Interpolación lineal para valores intermedios
                for i in range(len(datos)-1):
                    if datos[i]['suma'] <= suma_escalar <= datos[i+1]['suma']:
                        fila_inf = datos[i]
                        fila_sup = datos[i+1]
                        ratio = (suma_escalar - fila_inf['suma']) / (fila_sup['suma'] - fila_inf['suma'])
                        
                        valor = fila_inf['valor'] + ratio * (fila_sup['valor'] - fila_inf['valor'])
                        return {
                            'compuesto': int(round(valor)),
                            'percentil': fila_inf['percentil'],
                            'conf_90': fila_inf['conf_90'],
                            'conf_95': fila_inf['conf_95'],
                            'nombre_escala': tabla_escala['nombre']
                        }
            
            # Fallback
            return {
                'compuesto': datos[-1]['valor'],
                'percentil': datos[-1]['percentil'],
                'conf_90': datos[-1]['conf_90'],
                'conf_95': datos[-1]['conf_95'],
                'nombre_escala': tabla_escala['nombre']
            }
            
        except Exception as e:
            print(f"❌ Error en conversión de compuesto para {escala_abrev}, suma {suma_escalar}: {e}")
            raise


class ConversorCIT:
    """Clase para manejar la conversión del CIT usando la tabla específica"""
    
    def __init__(self):
        self.tabla_cit = self.cargar_tabla_cit()
    
    def cargar_tabla_cit(self):
        """Carga la tabla de conversión para el CIT"""
        try:
            # Buscar el archivo en varias ubicaciones posibles
            posibles_rutas = [
                os.path.join('data', 'wisc_v_cit.json'),
                os.path.join(os.path.dirname(__file__), 'data', 'wisc_v_cit.json'),
                'wisc_v_cit.json'
            ]
            
            ruta_encontrada = None
            for ruta in posibles_rutas:
                if os.path.exists(ruta):
                    ruta_encontrada = ruta
                    break
            
            if not ruta_encontrada:
                raise FileNotFoundError("No se encontró el archivo wisc_v_cit.json")
            
            with open(ruta_encontrada, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            print(f"✅ Tabla CIT cargada: {datos['tabla']}")
            return datos
        except Exception as e:
            print(f"❌ Error cargando tabla CIT: {e}")
            return {"datos": []}
    
    def convertir_cit(self, suma_escalar):
        """Convierte la suma de 7 puntajes escalares a CIT usando la tabla específica"""
        try:
            if not self.tabla_cit or not self.tabla_cit['datos']:
                raise ValueError("No se cargó la tabla CIT")
            
            datos = self.tabla_cit['datos']
            
            # Buscar la fila correspondiente a la suma escalar
            for fila in datos:
                if fila['suma'] == suma_escalar:
                    return {
                        'compuesto': fila['cit'],
                        'percentil': fila['percentil'],
                        'conf_90': fila['conf_90'],
                        'conf_95': fila['conf_95']
                    }
            
            # Si no se encuentra exacto, usar interpolación
            sumas = [fila['suma'] for fila in datos]
            if suma_escalar < min(sumas):
                fila = datos[0]
            elif suma_escalar > max(sumas):
                fila = datos[-1]
            else:
                # Encontrar el rango
                for i in range(len(datos)-1):
                    if datos[i]['suma'] <= suma_escalar <= datos[i+1]['suma']:
                        # Interpolar
                        fila_inf = datos[i]
                        fila_sup = datos[i+1]
                        ratio = (suma_escalar - fila_inf['suma']) / (fila_sup['suma'] - fila_inf['suma'])
                        
                        valor = fila_inf['cit'] + ratio * (fila_sup['cit'] - fila_inf['cit'])
                        return {
                            'compuesto': int(round(valor)),
                            'percentil': fila_inf['percentil'],
                            'conf_90': fila_inf['conf_90'],
                            'conf_95': fila_inf['conf_95']
                        }
            
            return {
                'compuesto': fila['cit'],
                'percentil': fila['percentil'],
                'conf_90': fila['conf_90'],
                'conf_95': fila['conf_95']
            }
            
        except Exception as e:
            print(f"❌ Error en conversión de CIT: {e}")
            raise


class PredictorEvolucionWISC:
    """Sistema de IA para predecir la evolución del CIT y índices WISC-V"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.modelo_cit = None
        self.modelo_indices = None
        self.scaler = StandardScaler()
        self.entrenado = False
        self.accuracy = 0.0
        
    def extraer_datos_entrenamiento(self):
        """Extrae y prepara los datos de entrenamiento desde la base de datos"""
        if not SKLEARN_AVAILABLE:
            return []
            
        print("📊 Extrayendo datos para entrenamiento de IA...")
        
        # Obtener todos los pacientes
        pacientes = self.db.buscar_pacientes("")
        datos_entrenamiento = []
        
        for paciente in pacientes:
            evaluaciones = self.db.obtener_evaluaciones_paciente(paciente['id'])
            
            if len(evaluaciones) >= 2:  # Solo pacientes con múltiples evaluaciones
                # Ordenar evaluaciones por fecha
                evaluaciones.sort(key=lambda x: x['fecha_evaluacion'])
                
                # Crear pares consecutivos de evaluaciones
                for i in range(len(evaluaciones) - 1):
                    eval_actual = evaluaciones[i]
                    eval_siguiente = evaluaciones[i + 1]
                    
                    dato = self._procesar_par_evaluaciones(paciente, eval_actual, eval_siguiente)
                    if dato:
                        datos_entrenamiento.append(dato)
        
        print(f"✅ Datos extraídos: {len(datos_entrenamiento)} pares de evaluaciones")
        return datos_entrenamiento
    
    def _procesar_par_evaluaciones(self, paciente, eval_actual, eval_siguiente):
        """Procesa un par de evaluaciones para entrenamiento"""
        try:
            # Datos de la evaluación actual (features)
            datos_actual = eval_actual['datos']
            datos_siguiente = eval_siguiente['datos']
            
            # Calcular tiempo entre evaluaciones (en meses)
            fecha_actual = datetime.fromisoformat(eval_actual['fecha_evaluacion'])
            fecha_siguiente = datetime.fromisoformat(eval_siguiente['fecha_evaluacion'])
            meses_diferencia = (fecha_siguiente.year - fecha_actual.year) * 12 + (fecha_siguiente.month - fecha_actual.month)
            
            if meses_diferencia <= 0 or meses_diferencia > 36:  # Límite de 3 años
                return None
            
            # Obtener puntajes compuestos
            compuestos_actual = datos_actual.get('compuestos', {})
            compuestos_siguiente = datos_siguiente.get('compuestos', {})
            
            # Features básicas
            feature = {
                'meses_diferencia': meses_diferencia,
                'edad_meses_actual': self._calcular_edad_meses(paciente, fecha_actual),
            }
            
            # Añadir puntajes actuales como features
            indices = ['ICV', 'IVE', 'IRF', 'IMT', 'IVP', 'CIT']
            for indice in indices:
                clave = f"{indice}_actual"
                feature[clave] = self._obtener_puntaje_compuesto(compuestos_actual, indice)
            
            # Targets (lo que queremos predecir)
            target = {}
            for indice in indices:
                clave = f"{indice}_siguiente"
                target[clave] = self._obtener_puntaje_compuesto(compuestos_siguiente, indice)
            
            return {'features': feature, 'targets': target}
            
        except Exception as e:
            print(f"⚠️ Error procesando par de evaluaciones: {e}")
            return None
    
    def _calcular_edad_meses(self, paciente, fecha_evaluacion):
        """Calcula la edad en meses en el momento de la evaluación"""
        try:
            fecha_nac = datetime.fromisoformat(paciente['fecha_nacimiento']).date()
            fecha_eval = fecha_evaluacion.date()
            return (fecha_eval.year - fecha_nac.year) * 12 + (fecha_eval.month - fecha_nac.month)
        except:
            return 0
    
    def _obtener_puntaje_compuesto(self, compuestos, indice):
        """Obtiene el puntaje compuesto de un índice específico"""
        try:
            # Buscar en las diferentes posibles claves
            for clave, datos in compuestos.items():
                if indice in clave:
                    return datos.get('compuesto', 0)
            return 0
        except:
            return 0
    
    def entrenar_modelos(self):
        """Entrena los modelos de predicción"""
        if not SKLEARN_AVAILABLE:
            print("❌ Scikit-learn no está disponible")
            return False

        print("🧠 Entrenando modelos de IA...")
        
        datos = self.extraer_datos_entrenamiento()
        
        if len(datos) < 10:
            print("❌ Insuficientes datos para entrenar el modelo (mínimo 10 pares)")
            self.entrenado = False
            return False
        
        # Preparar datos
        features = [d['features'] for d in datos]
        targets = [d['targets'] for d in datos]
        
        # Convertir a DataFrame
        df_features = pd.DataFrame(features)
        df_targets = pd.DataFrame(targets)
        
        # Separar features y targets
        X = df_features.values
        y_cit = df_targets['CIT_siguiente'].values
        y_indices = df_targets[['ICV_siguiente', 'IVE_siguiente', 'IRF_siguiente', 'IMT_siguiente', 'IVP_siguiente']].values
        
        # Escalar features
        X_scaled = self.scaler.fit_transform(X)
        
        # Dividir en train/test
        X_train, X_test, y_cit_train, y_cit_test = train_test_split(X_scaled, y_cit, test_size=0.2, random_state=42)
        _, _, y_indices_train, y_indices_test = train_test_split(X_scaled, y_indices, test_size=0.2, random_state=42)
        
        # Entrenar modelo para CIT
        self.modelo_cit = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self.modelo_cit.fit(X_train, y_cit_train)
        
        # Entrenar modelo para índices
        self.modelo_indices = RandomForestRegressor(n_estimators=100, random_state=42)
        self.modelo_indices.fit(X_train, y_indices_train)
        
        # Evaluar modelos
        cit_pred = self.modelo_cit.predict(X_test)
        indices_pred = self.modelo_indices.predict(X_test)
        
        mae_cit = mean_absolute_error(y_cit_test, cit_pred)
        r2_cit = r2_score(y_cit_test, cit_pred)
        
        self.accuracy = r2_cit
        self.entrenado = True
        
        print(f"✅ Modelos entrenados exitosamente")
        print(f"📊 Precisión CIT: R² = {r2_cit:.3f}, MAE = {mae_cit:.2f} puntos")
        
        return True
    
    def predecir_evolucion(self, paciente_id, meses_futuro=12):
        """Predice la evolución futura de un paciente"""
        if not self.entrenado:
            if not self.entrenar_modelos():
                return None
        
        try:
            # Obtener evaluación más reciente del paciente
            evaluaciones = self.db.obtener_evaluaciones_paciente(paciente_id)
            if not evaluaciones:
                return None
            
            eval_reciente = max(evaluaciones, key=lambda x: x['fecha_evaluacion'])
            paciente = self.db.obtener_paciente(paciente_id)
            
            # Preparar features para predicción
            features = self._preparar_features_prediccion(paciente, eval_reciente, meses_futuro)
            if features is None:
                return None
            
            # Escalar features
            features_scaled = self.scaler.transform([features])
            
            # Realizar predicciones
            cit_pred = self.modelo_cit.predict(features_scaled)[0]
            indices_pred = self.modelo_indices.predict(features_scaled)[0]
            
            # Formatear resultados
            prediccion = {
                'cit_actual': self._obtener_puntaje_actual(eval_reciente, 'CIT'),
                'cit_predicho': max(40, min(160, round(cit_pred))),
                'indices_actuales': self._obtener_indices_actuales(eval_reciente),
                'indices_predichos': {
                    'ICV': max(40, min(160, round(indices_pred[0]))),
                    'IVE': max(40, min(160, round(indices_pred[1]))),
                    'IRF': max(40, min(160, round(indices_pred[2]))),
                    'IMT': max(40, min(160, round(indices_pred[3]))),
                    'IVP': max(40, min(160, round(indices_pred[4])))
                },
                'meses_futuro': meses_futuro,
                'tendencia': 'mejora' if cit_pred > self._obtener_puntaje_actual(eval_reciente, 'CIT') else 'estable' if cit_pred == self._obtener_puntaje_actual(eval_reciente, 'CIT') else 'deterioro',
                'confianza': min(95, max(60, int(self.accuracy * 100))),
                'recomendaciones': self._generar_recomendaciones(indices_pred)
            }
            
            return prediccion
            
        except Exception as e:
            print(f"❌ Error en predicción: {e}")
            return None
    
    def _preparar_features_prediccion(self, paciente, evaluacion, meses_futuro):
        """Prepara las features para la predicción"""
        try:
            datos = evaluacion['datos']
            compuestos = datos.get('compuestos', {})
            fecha_eval = datetime.fromisoformat(evaluacion['fecha_evaluacion'])
            
            features = {
                'meses_diferencia': meses_futuro,
                'edad_meses_actual': self._calcular_edad_meses(paciente, fecha_eval),
                'ICV_actual': self._obtener_puntaje_compuesto(compuestos, 'ICV'),
                'IVE_actual': self._obtener_puntaje_compuesto(compuestos, 'IVE'),
                'IRF_actual': self._obtener_puntaje_compuesto(compuestos, 'IRF'),
                'IMT_actual': self._obtener_puntaje_compuesto(compuestos, 'IMT'),
                'IVP_actual': self._obtener_puntaje_compuesto(compuestos, 'IVP'),
                'CIT_actual': self._obtener_puntaje_compuesto(compuestos, 'CIT')
            }
            
            return list(features.values())
        except:
            return None
    
    def _obtener_puntaje_actual(self, evaluacion, indice):
        """Obtiene el puntaje actual de un índice"""
        compuestos = evaluacion['datos'].get('compuestos', {})
        return self._obtener_puntaje_compuesto(compuestos, indice)
    
    def _obtener_indices_actuales(self, evaluacion):
        """Obtiene todos los índices actuales"""
        compuestos = evaluacion['datos'].get('compuestos', {})
        return {
            'ICV': self._obtener_puntaje_compuesto(compuestos, 'ICV'),
            'IVE': self._obtener_puntaje_compuesto(compuestos, 'IVE'),
            'IRF': self._obtener_puntaje_compuesto(compuestos, 'IRF'),
            'IMT': self._obtener_puntaje_compuesto(compuestos, 'IMT'),
            'IVP': self._obtener_puntaje_compuesto(compuestos, 'IVP')
        }
    
    def _generar_recomendaciones(self, indices_predichos):
        """Genera recomendaciones basadas en los índices predichos"""
        recomendaciones = []
        
        # Análisis de patrones
        puntajes = {
            'ICV': indices_predichos[0],
            'IVE': indices_predichos[1],
            'IRF': indices_predichos[2],
            'IMT': indices_predichos[3],
            'IVP': indices_predichos[4]
        }
        
        # Identificar áreas fuertes y débiles
        area_max = max(puntajes, key=puntajes.get)
        area_min = min(puntajes, key=puntajes.get)
        
        # Recomendaciones basadas en patrones
        if puntajes[area_min] < 90:
            recomendaciones.append(f"💡 Enfocar intervención en {self._nombre_completo_indice(area_min)} (área más débil)")
        
        if puntajes[area_max] > 110:
            recomendaciones.append(f"⭐ Potenciar {self._nombre_completo_indice(area_max)} (área más fuerte)")
        
        # Recomendaciones específicas por índice
        if puntajes['IMT'] < 90:
            recomendaciones.append("🧠 Implementar ejercicios de memoria de trabajo")
        
        if puntajes['IVP'] < 90:
            recomendaciones.append("⚡ Realizar actividades de velocidad de procesamiento")
        
        if puntajes['IRF'] < 90:
            recomendaciones.append("🔍 Desarrollar estrategias de razonamiento fluido")
        
        if len(recomendaciones) == 0:
            recomendaciones.append("📈 Perfil equilibrado. Continuar con intervención general")
        
        return recomendaciones
    
    def _nombre_completo_indice(self, abreviatura):
        """Devuelve el nombre completo del índice"""
        nombres = {
            'ICV': 'Comprensión Verbal',
            'IVE': 'Razonamiento Visoespacial',
            'IRF': 'Razonamiento Fluido',
            'IMT': 'Memoria de Trabajo',
            'IVP': 'Velocidad de Procesamiento'
        }
        return nombres.get(abreviatura, abreviatura)
    
    def obtener_estadisticas_modelo(self):
        """Obtiene estadísticas del modelo entrenado"""
        if not self.entrenado:
            return {"estado": "No entrenado"}
        
        return {
            "estado": "Entrenado",
            "precision_cit": f"{self.accuracy:.1%}",
            "confianza_predicciones": f"{min(95, max(60, int(self.accuracy * 100)))}%",
            "recomendacion_uso": "Alta" if self.accuracy > 0.7 else "Media" if self.accuracy > 0.5 else "Baja"
        }


class WiscVApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PsicoMetric - Sistema de Evaluación psicometicas con IA")
        self.root.geometry("1200x800")  # Tamaño inicial más manejable
        self.root.configure(bg='#f0f0f0')
        
        # Inicializar base de datos SQLite
        self.db = DatabaseManager()
        
        # Variables de estado
        self.nivel_confianza = tk.StringVar(value="95%")
        self.paciente_actual = None
        self.evaluacion_actual = None
        self.panel_pacientes_visible = False  # Estado del panel lateral
        
        # Inicializar conversores
        self.conversor_compuestos = ConversorCompuestos()
        self.conversor_cit = ConversorCIT()
        
        # Inicializar sistema de IA
        self.predictor_ia = PredictorEvolucionWISC(self.db)
        
        # Diccionario para almacenar resultados actuales
        self.resultados_actuales = {}
        
        self.crear_interfaz_con_panel_colapsable()

    def crear_interfaz_con_panel_colapsable(self):
        """Crea la interfaz con panel lateral colapsable"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame para el contenido principal (se expandirá)
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear la interfaz principal
        self.crear_interfaz_principal(self.content_frame)
        
        # Crear botón flotante para mostrar/ocultar panel de pacientes
        self.crear_boton_panel_flotante()

    def crear_boton_panel_flotante(self):
        """Crea un botón flotante para mostrar/ocultar el panel de pacientes"""
        self.btn_toggle_panel = tk.Button(
            self.root, 
            text="👥", 
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            relief="raised",
            bd=2,
            width=3,
            height=1,
            command=self.toggle_panel_pacientes
        )
        
        # Posicionar en la esquina superior derecha
        self.btn_toggle_panel.place(relx=0.98, rely=0.02, anchor="ne")
        
        # Tooltip
        self.crear_tooltip(self.btn_toggle_panel, "Mostrar/Ocultar Panel de Pacientes")

    def toggle_panel_pacientes(self):
        """Muestra u oculta el panel de pacientes"""
        if self.panel_pacientes_visible:
            self.ocultar_panel_pacientes()
        else:
            self.mostrar_panel_pacientes()

    def mostrar_panel_pacientes(self):
        """Muestra el panel de pacientes centrado en la pantalla"""
        if hasattr(self, 'panel_window') and self.panel_window.winfo_exists():
            # Si ya existe, traer al frente
            self.panel_window.lift()
            return
        
        # Crear ventana flotante para el panel de pacientes
        self.panel_window = tk.Toplevel(self.root)
        self.panel_window.title("👥 Gestión de Pacientes")
        self.panel_window.geometry("400x700")
        self.panel_window.configure(bg='#f0f0f0')
        self.panel_window.transient(self.root)
        self.panel_window.resizable(True, True)
        
        # Centrar la ventana en la pantalla
        self.centrar_ventana(self.panel_window, 400, 700)
        
        # Hacer que se cierre cuando se cierre la ventana principal
        self.panel_window.protocol("WM_DELETE_WINDOW", self.ocultar_panel_pacientes)
        
        # Crear contenido del panel
        self.crear_panel_pacientes(self.panel_window)
        
        self.panel_pacientes_visible = True
        self.btn_toggle_panel.config(text="👥", bg="#2ecc71")

    def centrar_ventana(self, ventana, ancho, alto):
        """Centra una ventana en la pantalla"""
        # Obtener dimensiones de la pantalla
        ancho_pantalla = ventana.winfo_screenwidth()
        alto_pantalla = ventana.winfo_screenheight()
        
        # Calcular posición
        x = (ancho_pantalla - ancho) // 2
        y = (alto_pantalla - alto) // 2
        
        # Establecer posición
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    def ocultar_panel_pacientes(self):
        """Oculta el panel de pacientes"""
        if hasattr(self, 'panel_window'):
            self.panel_window.destroy()
        self.panel_pacientes_visible = False
        self.btn_toggle_panel.config(text="👥", bg="#3498db")

    def crear_interfaz_principal(self, parent):
        """Crea la interfaz principal del formulario"""
        # Crear canvas con scroll para el formulario principal
        canvas = tk.Canvas(parent, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, padding="20")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Configurar scroll con rueda del mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Ahora crear la interfaz dentro del scrollable_frame
        self.crear_interfaz()

    def crear_interfaz(self):
        """Crea todos los elementos de la interfaz dentro del frame scrollable"""
        # Título
        titulo = tk.Label(self.scrollable_frame, 
                         text="Sistema de Evaluación psicometrica basadas en WISC V con IA", 
                         font=("Arial", 18, "bold"),
                         foreground="#2c3e50",
                         bg='#f0f0f0')
        titulo.grid(row=0, column=0, columnspan=6, pady=(0, 30))
        
        # Información del paciente actual
        self.info_paciente_frame = ttk.LabelFrame(self.scrollable_frame, text="👤 Paciente Actual", padding="10")
        self.info_paciente_frame.grid(row=1, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.info_paciente_label = tk.Label(self.info_paciente_frame, 
                                          text="Ningún paciente seleccionado", 
                                          font=("Arial", 10),
                                          foreground="#7f8c8d",
                                          bg='#f0f0f0')
        self.info_paciente_label.pack(anchor=tk.W)
        
        # ========== DATOS DEL PACIENTE ==========
        paciente_frame = ttk.LabelFrame(self.scrollable_frame, text="📋 Datos del Paciente", padding="15")
        paciente_frame.grid(row=2, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Título interno con estilo
        titulo_paciente = tk.Label(paciente_frame, 
                                  text="Datos del Paciente",
                                  font=("Arial", 12, "bold"),
                                  foreground="#2c3e50",
                                  bg='#f0f0f0')
        titulo_paciente.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 15))
        
        # Fila 1: Nombre y DNI
        tk.Label(paciente_frame, text="Nombre completo:", 
                font=("Arial", 10),
                bg='#f0f0f0').grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.nombre_entry = ttk.Entry(paciente_frame, width=30, font=("Arial", 10))
        self.nombre_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 30))
        
        tk.Label(paciente_frame, text="DNI:", 
                font=("Arial", 10),
                bg='#f0f0f0').grid(row=1, column=2, sticky=tk.W, padx=(0, 10))
        self.dni_entry = ttk.Entry(paciente_frame, width=15, font=("Arial", 10))
        self.dni_entry.grid(row=1, column=3, sticky=tk.W)
        
        # Fila 2: Fecha de nacimiento
        tk.Label(paciente_frame, text="Fecha de Nacimiento (DD/MM/AAAA):", 
                font=("Arial", 10),
                bg='#f0f0f0').grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        
        # Frame para fecha
        fecha_frame = ttk.Frame(paciente_frame)
        fecha_frame.grid(row=2, column=1, sticky=tk.W)
        
        self.dia_var = tk.StringVar()
        self.mes_var = tk.StringVar() 
        self.ano_var = tk.StringVar()
        
        ttk.Entry(fecha_frame, textvariable=self.dia_var, width=3, 
                 font=("Arial", 10), justify='center').pack(side=tk.LEFT)
        tk.Label(fecha_frame, text="/", font=("Arial", 10), bg='#f0f0f0').pack(side=tk.LEFT, padx=2)
        ttk.Entry(fecha_frame, textvariable=self.mes_var, width=3, 
                 font=("Arial", 10), justify='center').pack(side=tk.LEFT)
        tk.Label(fecha_frame, text="/", font=("Arial", 10), bg='#f0f0f0').pack(side=tk.LEFT, padx=2)
        ttk.Entry(fecha_frame, textvariable=self.ano_var, width=5, 
                 font=("Arial", 10), justify='center').pack(side=tk.LEFT)
        
        # Botón calcular edad
        ttk.Button(paciente_frame, text="📅 Calcular Edad", 
                  command=self.calcular_edad_actual).grid(row=2, column=2, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Fila 3: Edad calculada
        tk.Label(paciente_frame, text="Edad calculada:", 
                font=("Arial", 10, "bold"),
                bg='#f0f0f0').grid(row=3, column=0, sticky=tk.W)
        self.edad_label = tk.Label(paciente_frame, text="", 
                                  foreground="#2980b9", 
                                  font=("Arial", 11, "bold"),
                                  bg='#f0f0f0')
        self.edad_label.grid(row=3, column=1, sticky=tk.W)
        
        # ========== PUNTAJES BRUTOS ==========
        puntajes_frame = ttk.LabelFrame(self.scrollable_frame, text="📊 Ingreso de Puntajes Brutos", padding="15")
        puntajes_frame.grid(row=3, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Título interno
        titulo_puntajes = tk.Label(puntajes_frame, 
                                  text="Ingreso de Puntajes Brutos",
                                  font=("Arial", 12, "bold"),
                                  foreground="#2c3e50",
                                  bg='#f0f0f0')
        titulo_puntajes.grid(row=0, column=0, columnspan=6, sticky=tk.W, pady=(0, 15))
        
        # Instrucciones
        tk.Label(puntajes_frame, 
                text="Ingrese los puntajes brutos obtenidos en cada subprueba:",
                font=("Arial", 10),
                bg='#f0f0f0').grid(row=1, column=0, columnspan=6, sticky=tk.W, pady=(0, 15))
        
        # Crear tabla de puntajes
        self.crear_tabla_puntajes(puntajes_frame)
        
        # ========== RESULTADOS COMPUESTOS ==========
        self.crear_seccion_resultados_compuestos()
        
        # ========== BOTONES PRINCIPALES ==========
        botones_frame = ttk.Frame(self.scrollable_frame)
        botones_frame.grid(row=5, column=0, columnspan=6, pady=20)
        
        ttk.Button(botones_frame, text="🎯 Calcular Puntajes Escala", 
                  command=self.calcular_puntajes,
                  width=25).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(botones_frame, text="📈 Calcular Puntajes Compuestos", 
                  command=self.calcular_puntajes_compuestos,
                  width=25).pack(side=tk.LEFT, padx=(0, 15))
        
        if MATPLOTLIB_AVAILABLE:
            ttk.Button(botones_frame, text="📊 Mostrar Gráfica de Perfil", 
                      command=self.mostrar_grafica_perfil,
                      width=22).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(botones_frame, text="🔄 Limpiar Todo", 
                  command=self.limpiar_formulario,
                  width=15).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(botones_frame, text="💾 Guardar Evaluación", 
                  command=self.guardar_evaluacion,
                  width=18).pack(side=tk.LEFT)
        
        # ========== BOTONES DE IA ==========
        self.agregar_botones_ia()
        
        # ========== INFORMACIÓN DEL SISTEMA ==========
        info_frame = ttk.LabelFrame(self.scrollable_frame, text="ℹ️ Información del Sistema", padding="10")
        info_frame.grid(row=7, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=(10, 0))
        
        info_text = ("✅ Sistema WISC-V con datos completos desde 6:0 hasta 16:11 años\n"
                    "✅ Conversión automática usando tablas estandarizadas\n"
                    "✅ Base de datos SQLite local para almacenamiento seguro\n"
                    "✅ Cálculo automático de puntajes compuestos, percentiles e intervalos de confianza\n"
                    "✅ Gestión completa de pacientes y evaluaciones")
        
        if MATPLOTLIB_AVAILABLE:
            info_text += "\n✅ Gráfica de perfil disponible"
        else:
            info_text += "\n⚠️ Gráfica de perfil no disponible (instalar matplotlib)"

        if SKLEARN_AVAILABLE:
            info_text += "\n✅ IA de predicción de evolución disponible"
        else:
            info_text += "\n⚠️ IA no disponible (instalar scikit-learn, pandas, numpy, joblib)"
        
        tk.Label(info_frame, text=info_text, 
                font=("Arial", 9),
                justify=tk.LEFT,
                bg='#f0f0f0',
                foreground="#34495e").grid(row=0, column=0, sticky=tk.W)
        
        # Configurar expansión de columnas
        paciente_frame.columnconfigure(1, weight=1)
        puntajes_frame.columnconfigure(1, weight=1)
        self.scrollable_frame.columnconfigure(0, weight=1)

    def agregar_botones_ia(self):
        """Agrega botones para las funcionalidades de IA"""
        # En el frame de botones principales, agregar:
        botones_ia_frame = ttk.Frame(self.scrollable_frame)
        botones_ia_frame.grid(row=6, column=0, columnspan=6, pady=10)
        
        ttk.Button(botones_ia_frame, text="🤖 Predecir Evolución", 
                  command=self.mostrar_prediccion_evolucion,
                  width=20).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(botones_ia_frame, text="📈 Análisis con IA", 
                  command=self.analisis_avanzado_ia,
                  width=18).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(botones_ia_frame, text="🧠 Entrenar IA", 
                  command=self.entrenar_sistema_ia,
                  width=15).pack(side=tk.LEFT)

    def crear_panel_pacientes(self, parent):
        """Crea el panel lateral de gestión de pacientes"""
        # Barra de búsqueda
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(search_frame, text="🔍 Buscar:", 
                font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        
        self.busqueda_var = tk.StringVar()
        busqueda_entry = ttk.Entry(search_frame, textvariable=self.busqueda_var, width=20)
        busqueda_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        busqueda_entry.bind('<KeyRelease>', self.buscar_pacientes)
        
        # Botón nuevo paciente
        ttk.Button(search_frame, text="➕", 
                  command=self.mostrar_dialogo_nuevo_paciente,
                  width=3).pack(side=tk.RIGHT)
        
        # Lista de pacientes
        lista_frame = ttk.Frame(parent)
        lista_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeview para mostrar pacientes
        columns = ("nombre", "dni", "edad")
        self.tree_pacientes = ttk.Treeview(lista_frame, columns=columns, show="headings", height=15)
        
        # Configurar columnas
        self.tree_pacientes.heading("nombre", text="Nombre")
        self.tree_pacientes.heading("dni", text="DNI")
        self.tree_pacientes.heading("edad", text="Edad")
        
        self.tree_pacientes.column("nombre", width=150)
        self.tree_pacientes.column("dni", width=80)
        self.tree_pacientes.column("edad", width=60)
        
        # Scrollbar para la treeview
        scrollbar = ttk.Scrollbar(lista_frame, orient="vertical", command=self.tree_pacientes.yview)
        self.tree_pacientes.configure(yscrollcommand=scrollbar.set)
        
        self.tree_pacientes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind evento de selección
        self.tree_pacientes.bind('<<TreeviewSelect>>', self.seleccionar_paciente)
        
        # Frame de botones de paciente
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="📋 Nueva Evaluación", 
                  command=self.nueva_evaluacion,
                  width=15).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(btn_frame, text="📊 Ver Evaluaciones", 
                  command=self.mostrar_evaluaciones_paciente,
                  width=15).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(btn_frame, text="✏️ Editar", 
                  command=self.editar_paciente,
                  width=8).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(btn_frame, text="🗑️ Eliminar", 
                  command=self.eliminar_paciente,
                  width=8).pack(side=tk.RIGHT)
        
        # Panel de información del paciente seleccionado
        info_frame = ttk.LabelFrame(parent, text="Información del Paciente", padding="10")
        info_frame.pack(fill=tk.X)
        
        self.info_paciente_text = tk.Text(info_frame, height=6, font=("Arial", 9), wrap=tk.WORD)
        self.info_paciente_text.pack(fill=tk.BOTH, expand=True)
        self.info_paciente_text.config(state=tk.DISABLED)
        
        # Estadísticas de la base de datos
        stats_frame = ttk.LabelFrame(parent, text="📊 Estadísticas", padding="10")
        stats_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.stats_label = tk.Label(stats_frame, text="", font=("Arial", 8), justify=tk.LEFT)
        self.stats_label.pack(fill=tk.X)
        
        # Cargar pacientes iniciales y estadísticas
        self.actualizar_lista_pacientes()
        self.actualizar_estadisticas()

    def crear_seccion_resultados_compuestos(self):
        """Crea la sección para mostrar resultados compuestos"""
        resultados_frame = ttk.LabelFrame(self.scrollable_frame, text="📈 Resultados Compuestos", padding="15")
        resultados_frame.grid(row=4, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Título interno
        titulo_resultados = tk.Label(resultados_frame, 
                                   text="Puntajes Compuestos, Percentiles e Intervalos de Confianza",
                                   font=("Arial", 12, "bold"),
                                   foreground="#2c3e50",
                                   bg='#f0f0f0')
        titulo_resultados.grid(row=0, column=0, columnspan=6, sticky=tk.W, pady=(0, 15))
        
        # Selector de nivel de confianza
        confianza_frame = ttk.Frame(resultados_frame)
        confianza_frame.grid(row=1, column=0, columnspan=6, sticky=tk.W, pady=(0, 15))
        
        tk.Label(confianza_frame, text="Nivel de Confianza:", 
                font=("Arial", 10, "bold"),
                bg='#f0f0f0').pack(side=tk.LEFT, padx=(0, 10))
        
        confianza_combo = ttk.Combobox(confianza_frame, 
                                      textvariable=self.nivel_confianza,
                                      values=["90%", "95%"],
                                      state="readonly",
                                      width=10,
                                      font=("Arial", 10))
        confianza_combo.pack(side=tk.LEFT)
        confianza_combo.bind('<<ComboboxSelected>>', self.actualizar_intervalos_confianza)
        
        # Crear tabla de resultados compuestos
        self.crear_tabla_resultados_compuestos(resultados_frame)

    def crear_tabla_resultados_compuestos(self, parent):
        """Crea la tabla para mostrar resultados compuestos"""
        # Encabezados de la tabla
        encabezados = ["Escala", "Suma Puntajes Escala", "Puntaje Compuesto", "Rango Percentil", "Intervalo de Confianza"]
        
        for i, encabezado in enumerate(encabezados):
            tk.Label(parent, text=encabezado, font=("Arial", 10, "bold"),
                    bg='#f0f0f0').grid(row=2, column=i, padx=5, pady=5, sticky=tk.W)
        
        # Definir las escalas y sus subtests correspondientes CORREGIDOS con abreviaturas
        self.escalas_compuestas = {
            "Comprensión Verbal (ICV)": ["AN", "VOC"],  # Analogías y Vocabulario
            "Visoespacial (IVE)": ["CC", "RV"],  # Cubos y Rompecabezas Visuales
            "Razonamiento Fluido (IRF)": ["MR", "BAL"],  # Matrices y Balanzas
            "Memoria de Trabajo (IMT)": ["RI", "RD"],  # Retención de Imágenes y Retención de Dígitos
            "Velocidad de Procesamiento (IVP)": ["CLA", "BS"],  # Claves y Búsqueda de Símbolos
            "Escala Total (CIT)": ["CC", "AN", "MR", "RD", "CLA", "VOC", "BAL"]  # 7 subpruebas para CIT
        }
        
        self.labels_resultados_compuestos = {}
        
        for i, (escala, subtests) in enumerate(self.escalas_compuestas.items()):
            fila = i + 3
            
            # Nombre de la escala CON ABREVIATURA
            tk.Label(parent, text=escala, font=("Arial", 9, "bold"),
                    bg='#f0f0f0').grid(row=fila, column=0, padx=5, pady=3, sticky=tk.W)
            
            # Suma de puntajes escala
            suma_label = tk.Label(parent, text="", font=("Arial", 9),
                                bg='#f0f0f0', width=15)
            suma_label.grid(row=fila, column=1, padx=5, pady=3, sticky=tk.W)
            
            # Puntaje compuesto
            compuesto_label = tk.Label(parent, text="", font=("Arial", 9, "bold"),
                                     bg='#f0f0f0', width=15)
            compuesto_label.grid(row=fila, column=2, padx=5, pady=3, sticky=tk.W)
            
            # Rango percentil
            percentil_label = tk.Label(parent, text="", font=("Arial", 9),
                                     bg='#f0f0f0', width=15)
            percentil_label.grid(row=fila, column=3, padx=5, pady=3, sticky=tk.W)
            
            # Intervalo de confianza
            confianza_label = tk.Label(parent, text="", font=("Arial", 9),
                                     bg='#f0f0f0', width=20)
            confianza_label.grid(row=fila, column=4, padx=5, pady=3, sticky=tk.W)
            
            self.labels_resultados_compuestos[escala] = {
                'suma': suma_label,
                'compuesto': compuesto_label,
                'percentil': percentil_label,
                'confianza': confianza_label,
                'subtests': subtests,
                'abreviatura': self.obtener_abreviatura_escala(escala)
            }

    def obtener_abreviatura_escala(self, escala_completa):
        """Extrae la abreviatura del nombre completo de la escala"""
        if "(ICV)" in escala_completa:
            return "ICV"
        elif "(IVE)" in escala_completa:
            return "IVE"
        elif "(IRF)" in escala_completa:
            return "IRF"
        elif "(IMT)" in escala_completa:
            return "IMT"
        elif "(IVP)" in escala_completa:
            return "IVP"
        elif "(CIT)" in escala_completa:
            return "CIT"
        else:
            return ""

    def crear_tabla_puntajes(self, parent):
        """Crea la tabla para ingresar puntajes brutos"""
        # Lista completa de subpruebas organizadas
        subpruebas_columnas = [
            # Columna 1
            ["CC", "AN", "MR", "RD", "CLA"],
            # Columna 2  
            ["VOC", "BAL", "RV", "RI", "BS"],
            # Columna 3
            ["IN", "SLN", "CAN", "COM", "ARI"]
        ]
        
        self.entries_puntajes = {}
        
        # Títulos de columnas
        for col_idx in range(3):
            col_offset = col_idx * 3
            
            # Títulos para cada columna
            tk.Label(parent, text="Subprueba", font=("Arial", 10, "bold"),
                    bg='#f0f0f0').grid(row=2, column=col_offset, padx=(0, 10), pady=(0, 10), sticky=tk.W)
            tk.Label(parent, text="Puntaje Bruto", font=("Arial", 10, "bold"),
                    bg='#f0f0f0').grid(row=2, column=col_offset + 1, padx=(0, 10), pady=(0, 10), sticky=tk.W)
            tk.Label(parent, text="Puntaje Escala", font=("Arial", 10, "bold"),
                    bg='#f0f0f0').grid(row=2, column=col_offset + 2, padx=(0, 10), pady=(0, 10), sticky=tk.W)
        
        # Crear filas para cada columna de subpruebas
        for col_idx, subpruebas_col in enumerate(subpruebas_columnas):
            col_offset = col_idx * 3  # 3 columnas por grupo (subprueba, bruto, escala)
            
            for row_idx, subprueba in enumerate(subpruebas_col):
                fila = row_idx + 3  # +3 por los títulos
                
                # Nombre subprueba
                nombre_completo = self.obtener_nombre_completo_subprueba(subprueba)
                label_subprueba = tk.Label(parent, text=subprueba, width=8,
                                          font=("Arial", 9, "bold"),
                                          foreground="#2c3e50",
                                          cursor="hand2",
                                          bg='#f0f0f0')
                label_subprueba.grid(row=fila, column=col_offset, 
                                   padx=(0, 5), pady=3, sticky=tk.W)
                
                # Tooltip
                self.crear_tooltip(label_subprueba, nombre_completo)
                
                # Entry para puntaje bruto
                entry = ttk.Entry(parent, width=8, font=("Arial", 9),
                                 justify='center')
                entry.grid(row=fila, column=col_offset + 1, 
                          padx=(0, 10), pady=3, sticky=tk.W)
                
                # Label para resultado
                resultado_label = tk.Label(parent, text="", 
                                          font=("Arial", 9, "bold"),
                                          foreground="#27ae60",
                                          width=8,
                                          bg='#f0f0f0')
                resultado_label.grid(row=fila, column=col_offset + 2, 
                                   pady=3, sticky=tk.W)
                
                self.entries_puntajes[subprueba] = {
                    "entry": entry, 
                    "label": resultado_label
                }

    def obtener_nombre_completo_subprueba(self, abreviatura):
        """Retorna el nombre completo de la subprueba"""
        nombres = {
            "CC": "Construcción con Cubos",
            "AN": "Analogías", 
            "MR": "Matrices de Razonamiento",
            "RD": "Retención de Dígitos",
            "CLA": "Claves",
            "VOC": "Vocabulario",
            "BAL": "Balanzas",
            "RV": "Rompecabezas Visuales", 
            "RI": "Retención de Imágenes",
            "BS": "Búsqueda de Símbolos",
            "IN": "Información",
            "SLN": "Secuenciación Letras-Números",
            "CAN": "Cancelación",
            "COM": "Comprensión",
            "ARI": "Aritmética"
        }
        return nombres.get(abreviatura, abreviatura)

    def crear_tooltip(self, widget, text):
        """Crea un tooltip para un widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="yellow", 
                           relief='solid', borderwidth=1,
                           font=("Arial", 8))
            label.pack()
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    # ========== MÉTODOS DE GESTIÓN DE PACIENTES ==========

    def actualizar_lista_pacientes(self, texto_busqueda=""):
        """Actualiza la lista de pacientes en el treeview"""
        # Limpiar treeview
        for item in self.tree_pacientes.get_children():
            self.tree_pacientes.delete(item)
        
        # Obtener pacientes
        pacientes = self.db.buscar_pacientes(texto_busqueda)
        
        # Agregar pacientes al treeview
        for paciente in pacientes:
            # Calcular edad
            fecha_nac = datetime.fromisoformat(paciente["fecha_nacimiento"]).date()
            hoy = date.today()
            edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
            
            self.tree_pacientes.insert("", "end", values=(
                paciente["nombre"],
                paciente.get("dni", ""),
                f"{edad} años"
            ), tags=(paciente["id"],))
        
        # Actualizar información del paciente seleccionado
        self.actualizar_info_paciente()

    def buscar_pacientes(self, event=None):
        """Busca pacientes según el texto ingresado"""
        texto = self.busqueda_var.get()
        self.actualizar_lista_pacientes(texto)

    def seleccionar_paciente(self, event):
        """Maneja la selección de un paciente de la lista"""
        seleccion = self.tree_pacientes.selection()
        if seleccion:
            item = seleccion[0]
            paciente_id = self.tree_pacientes.item(item, "tags")[0]
            self.paciente_actual = self.db.obtener_paciente(paciente_id)
            self.actualizar_info_paciente()
            self.actualizar_info_paciente_principal()
            
            # Cargar datos del paciente en el formulario
            self.cargar_datos_paciente_formulario()

    def actualizar_estadisticas(self):
        """Actualiza las estadísticas en el panel lateral de forma segura"""
        try:
            if hasattr(self, 'stats_label') and self.stats_label.winfo_exists():
                stats = self.db.obtener_estadisticas()
                texto = f"Pacientes: {stats['total_pacientes']} | "
                texto += f"Evaluaciones: {stats['total_evaluaciones']}"
            
                if stats['ultima_evaluacion']:
                    fecha = datetime.fromisoformat(stats['ultima_evaluacion']).strftime("%d/%m/%Y")
                    texto += f"\nÚltima evaluación: {fecha}"
            
                self.stats_label.config(text=texto)
        except Exception as e:
            print(f"⚠️ Error actualizando estadísticas: {e}")

    def actualizar_info_paciente(self):
        """Actualiza el panel de información del paciente de forma segura"""
        try:
            if (hasattr(self, 'info_paciente_text') and 
                self.info_paciente_text.winfo_exists()):
            
                self.info_paciente_text.config(state=tk.NORMAL)
                self.info_paciente_text.delete(1.0, tk.END)
            
                if self.paciente_actual:
                    info = f"Nombre: {self.paciente_actual['nombre']}\n"
                    info += f"DNI: {self.paciente_actual.get('dni', 'No registrado')}\n"
                
                    fecha_nac = datetime.fromisoformat(self.paciente_actual["fecha_nacimiento"]).date()
                    hoy = date.today()
                    edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
                    info += f"Fecha Nacimiento: {fecha_nac.strftime('%d/%m/%Y')}\n"
                    info += f"Edad: {edad} años\n"
                
                # Obtener número de evaluaciones
                    evaluaciones = self.db.obtener_evaluaciones_paciente(self.paciente_actual["id"])
                    info += f"Evaluaciones: {len(evaluaciones)}\n"
                
                    if self.paciente_actual.get('notas'):
                        info += f"\nNotas: {self.paciente_actual['notas']}"
                else:
                    info = "Selecciona un paciente para ver su información"
            
                self.info_paciente_text.insert(1.0, info)
                self.info_paciente_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"⚠️ Error actualizando info paciente: {e}")

    def actualizar_info_paciente_principal(self):
        """Actualiza la información del paciente en la interfaz principal de forma segura"""
        try:
            if (hasattr(self, 'info_paciente_label') and 
                self.info_paciente_label.winfo_exists()):
            
                if self.paciente_actual:
                    texto = f"👤 {self.paciente_actual['nombre']}"
                    if self.paciente_actual.get('dni'):
                        texto += f" | DNI: {self.paciente_actual['dni']}"
                
                    fecha_nac = datetime.fromisoformat(self.paciente_actual["fecha_nacimiento"]).date()
                    hoy = date.today()
                    edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
                    texto += f" | Edad: {edad} años"
                
                    evaluaciones = self.db.obtener_evaluaciones_paciente(self.paciente_actual["id"])
                    texto += f" | Evaluaciones: {len(evaluaciones)}"
                
                    self.info_paciente_label.config(text=texto, foreground="#2c3e50")
                else:
                    self.info_paciente_label.config(text="Ningún paciente seleccionado", foreground="#7f8c8d")
        except Exception as e:
            print(f"⚠️ Error actualizando info paciente principal: {e}")

    def cargar_datos_paciente_formulario(self):
        """Carga los datos del paciente actual en el formulario"""
        if self.paciente_actual:
            # Cargar datos básicos
            self.nombre_entry.delete(0, tk.END)
            self.nombre_entry.insert(0, self.paciente_actual['nombre'])
            
            self.dni_entry.delete(0, tk.END)
            self.dni_entry.insert(0, self.paciente_actual.get('dni', ''))
            
            # Cargar fecha de nacimiento
            fecha_nac = datetime.fromisoformat(self.paciente_actual["fecha_nacimiento"]).date()
            self.dia_var.set(str(fecha_nac.day))
            self.mes_var.set(str(fecha_nac.month))
            self.ano_var.set(str(fecha_nac.year))
            
            # Calcular y mostrar edad
            self.calcular_edad_actual()

    def mostrar_dialogo_nuevo_paciente(self):
        """Muestra diálogo para agregar nuevo paciente"""
        dialogo = tk.Toplevel(self.root)
        dialogo.title("➕ Nuevo Paciente")
        dialogo.geometry("400x300")
        dialogo.configure(bg='#f0f0f0')
        dialogo.transient(self.root)
        dialogo.grab_set()
        
        # Centrar la ventana
        self.centrar_ventana(dialogo, 400, 300)
        
        # Campos del formulario
        ttk.Label(dialogo, text="Nombre completo:").pack(pady=(20, 5))
        nombre_var = tk.StringVar()
        ttk.Entry(dialogo, textvariable=nombre_var, width=40).pack(pady=5)
        
        ttk.Label(dialogo, text="DNI:").pack(pady=(10, 5))
        dni_var = tk.StringVar()
        ttk.Entry(dialogo, textvariable=dni_var, width=20).pack(pady=5)
        
        ttk.Label(dialogo, text="Fecha de Nacimiento (DD/MM/AAAA):").pack(pady=(10, 5))
        fecha_frame = ttk.Frame(dialogo)
        fecha_frame.pack(pady=5)
        
        dia_var = tk.StringVar()
        mes_var = tk.StringVar()
        ano_var = tk.StringVar()
        
        ttk.Entry(fecha_frame, textvariable=dia_var, width=3).pack(side=tk.LEFT)
        ttk.Label(fecha_frame, text="/").pack(side=tk.LEFT)
        ttk.Entry(fecha_frame, textvariable=mes_var, width=3).pack(side=tk.LEFT)
        ttk.Label(fecha_frame, text="/").pack(side=tk.LEFT)
        ttk.Entry(fecha_frame, textvariable=ano_var, width=5).pack(side=tk.LEFT)
        
        ttk.Label(dialogo, text="Notas:").pack(pady=(10, 5))
        notas_text = tk.Text(dialogo, height=4, width=40)
        notas_text.pack(pady=5, fill=tk.BOTH, expand=True)
        
        def guardar_paciente():
            """Guarda el nuevo paciente"""
            try:
                nombre = nombre_var.get().strip()
                if not nombre:
                    tk.messagebox.showerror("Error", "El nombre es obligatorio")
                    return
                
                # Validar fecha
                dia = int(dia_var.get())
                mes = int(mes_var.get())
                ano = int(ano_var.get())
                fecha_nac = date(ano, mes, dia)
                
                if fecha_nac > date.today():
                    tk.messagebox.showerror("Error", "La fecha de nacimiento no puede ser futura")
                    return
                
                # Agregar paciente
                paciente_id = self.db.agregar_paciente(
                    nombre=nombre,
                    dni=dni_var.get().strip(),
                    fecha_nacimiento=fecha_nac,
                    notas=notas_text.get(1.0, tk.END).strip()
                )
                
                if paciente_id:
                    tk.messagebox.showinfo("Éxito", "Paciente agregado correctamente")
                    self.actualizar_lista_pacientes()
                    self.actualizar_estadisticas()
                    dialogo.destroy()
                else:
                    tk.messagebox.showerror("Error", "No se pudo guardar el paciente")
                    
            except ValueError:
                tk.messagebox.showerror("Error", "Fecha inválida")
            except Exception as e:
                tk.messagebox.showerror("Error", f"Error al guardar: {str(e)}")
        
        # Botones
        btn_frame = ttk.Frame(dialogo)
        btn_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(btn_frame, text="Guardar", 
                  command=guardar_paciente).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(btn_frame, text="Cancelar", 
                  command=dialogo.destroy).pack(side=tk.RIGHT)

    def nueva_evaluacion(self):
        """Prepara el formulario para una nueva evaluación"""
        if not self.paciente_actual:
            tk.messagebox.showwarning("Advertencia", "Primero selecciona un paciente")
            return
        
        # Limpiar formulario de evaluación (manteniendo datos del paciente)
        for widgets in self.entries_puntajes.values():
            widgets["entry"].delete(0, tk.END)
            widgets["label"].config(text="")
        
        # Limpiar resultados compuestos
        for escala_data in self.labels_resultados_compuestos.values():
            escala_data['suma'].config(text="")
            escala_data['compuesto'].config(text="")
            escala_data['percentil'].config(text="")
            escala_data['confianza'].config(text="")
        
        self.resultados_actuales = {}
        self.evaluacion_actual = None
        
        tk.messagebox.showinfo("Nueva Evaluación", 
                          f"Formulario listo para nueva evaluación de {self.paciente_actual['nombre']}")

    def mostrar_evaluaciones_paciente(self):
        """Muestra el historial de evaluaciones del paciente"""
        if not self.paciente_actual:
            tk.messagebox.showwarning("Advertencia", "Primero selecciona un paciente")
            return
        
        evaluaciones = self.db.obtener_evaluaciones_paciente(self.paciente_actual["id"])
        
        dialogo = tk.Toplevel(self.root)
        dialogo.title(f"📊 Evaluaciones - {self.paciente_actual['nombre']}")
        dialogo.geometry("800x500")
        dialogo.configure(bg='#f0f0f0')
        
        # Centrar la ventana
        self.centrar_ventana(dialogo, 800, 500)
        
        # Treeview para evaluaciones
        frame_tree = ttk.Frame(dialogo)
        frame_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("fecha", "compuestos")
        tree = ttk.Treeview(frame_tree, columns=columns, show="headings", height=15)
        
        tree.heading("fecha", text="Fecha Evaluación")
        tree.heading("compuestos", text="Puntajes Compuestos")
        
        tree.column("fecha", width=150)
        tree.column("compuestos", width=400)
        
        scrollbar = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Llenar con evaluaciones
        for eval in evaluaciones:
            fecha = datetime.fromisoformat(eval["fecha_evaluacion"]).strftime("%d/%m/%Y %H:%M")
            compuestos = self.formatear_compuestos_para_lista(eval["datos"].get("compuestos", {}))
            tree.insert("", "end", values=(fecha, compuestos), tags=(eval["id"],))
        
        # Botones
        btn_frame = ttk.Frame(dialogo)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="📋 Cargar Evaluación", 
                  command=lambda: self.cargar_evaluacion_seleccionada(tree),
                  width=15).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(btn_frame, text="📊 Ver Gráfica", 
                  command=lambda: self.mostrar_grafica_evaluacion(tree),
                  width=12).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(btn_frame, text="📄 Generar Informe", 
                  command=lambda: self.generar_informe_pdf(eval_data=eval["datos"]),
                  width=15).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(btn_frame, text="Cerrar", 
                  command=dialogo.destroy,
                  width=10).pack(side=tk.RIGHT)

    def formatear_compuestos_para_lista(self, compuestos):
        """Formatea los puntajes compuestos para mostrar en la lista"""
        if not compuestos:
            return "Sin datos"
        
        texto = ""
        for escala, datos in compuestos.items():
            if datos.get('compuesto'):
                texto += f"{escala[:10]}: {datos['compuesto']} | "
        return texto[:-3] if texto else "Sin compuestos"

    def cargar_evaluacion_seleccionada(self, tree):
        """Carga la evaluación seleccionada en el formulario"""
        seleccion = tree.selection()
        if not seleccion:
            tk.messagebox.showwarning("Advertencia", "Selecciona una evaluación")
            return
        
        item = seleccion[0]
        eval_id = tree.item(item, "tags")[0]
        evaluacion = self.db.obtener_evaluacion(eval_id)
        
        if evaluacion:
            self.cargar_datos_evaluacion(evaluacion["datos"])
            self.evaluacion_actual = evaluacion
            tk.messagebox.showinfo("Éxito", "Evaluación cargada correctamente")

    def cargar_datos_evaluacion(self, datos_evaluacion):
        """Carga los datos de una evaluación en el formulario"""
        # Cargar puntajes brutos
        for subprueba, datos in datos_evaluacion.get("subpruebas", {}).items():
            if subprueba in self.entries_puntajes:
                self.entries_puntajes[subprueba]["entry"].delete(0, tk.END)
                self.entries_puntajes[subprueba]["entry"].insert(0, str(datos["bruto"]))
                self.entries_puntajes[subprueba]["label"].config(text=str(datos["escalar"]))
        
        # Calcular y mostrar resultados compuestos
        self.mostrar_resultados_guardados(datos_evaluacion.get("compuestos", {}))

    def mostrar_resultados_guardados(self, compuestos):
        """Muestra los resultados compuestos guardados"""
        for escala, datos_comp in compuestos.items():
            if escala in self.labels_resultados_compuestos:
                datos = self.labels_resultados_compuestos[escala]
                datos['suma'].config(text=str(datos_comp.get('suma_escalar', '')))
                datos['compuesto'].config(text=str(datos_comp.get('compuesto', '')), 
                                       foreground=self.obtener_color_puntaje(datos_comp.get('compuesto', 0)))
                datos['percentil'].config(text=datos_comp.get('percentil', ''))
                datos['confianza'].config(text=datos_comp.get('intervalo_confianza', ''))
                
                # Guardar en resultados actuales para gráficas
                if datos_comp.get('compuesto'):
                    self.resultados_actuales[datos['abreviatura']] = datos_comp['compuesto']

    def mostrar_grafica_evaluacion(self, tree):
        """Muestra la gráfica de la evaluación seleccionada"""
        seleccion = tree.selection()
        if not seleccion:
            tk.messagebox.showwarning("Advertencia", "Selecciona una evaluación")
            return
        
        item = seleccion[0]
        eval_id = tree.item(item, "tags")[0]
        evaluacion = self.db.obtener_evaluacion(eval_id)
        
        if evaluacion and evaluacion["datos"].get("compuestos"):
            # Cargar temporalmente los resultados para la gráfica
            resultados_temp = {}
            for escala, datos_comp in evaluacion["datos"]["compuestos"].items():
                if datos_comp.get('compuesto'):
                    abreviatura = self.obtener_abreviatura_escala(escala)
                    if abreviatura:
                        resultados_temp[abreviatura] = datos_comp['compuesto']
            
            # Guardar temporalmente y mostrar gráfica
            resultados_originales = self.resultados_actuales
            self.resultados_actuales = resultados_temp
            self.mostrar_grafica_perfil()
            self.resultados_actuales = resultados_originales
        else:
            tk.messagebox.showwarning("Advertencia", "La evaluación seleccionada no tiene datos de compuestos")

    def editar_paciente(self):
        """Edita el paciente actual"""
        if not self.paciente_actual:
            tk.messagebox.showwarning("Advertencia", "Primero selecciona un paciente")
            return
        
        dialogo = tk.Toplevel(self.root)
        dialogo.title("✏️ Editar Paciente")
        dialogo.geometry("400x300")
        dialogo.configure(bg='#f0f0f0')
        dialogo.transient(self.root)
        dialogo.grab_set()
        
        # Centrar la ventana
        self.centrar_ventana(dialogo, 400, 300)
        
        # Campos del formulario con datos actuales
        ttk.Label(dialogo, text="Nombre completo:").pack(pady=(20, 5))
        nombre_var = tk.StringVar(value=self.paciente_actual['nombre'])
        ttk.Entry(dialogo, textvariable=nombre_var, width=40).pack(pady=5)
        
        ttk.Label(dialogo, text="DNI:").pack(pady=(10, 5))
        dni_var = tk.StringVar(value=self.paciente_actual.get('dni', ''))
        ttk.Entry(dialogo, textvariable=dni_var, width=20).pack(pady=5)
        
        ttk.Label(dialogo, text="Fecha de Nacimiento (DD/MM/AAAA):").pack(pady=(10, 5))
        fecha_frame = ttk.Frame(dialogo)
        fecha_frame.pack(pady=5)
        
        fecha_nac = datetime.fromisoformat(self.paciente_actual["fecha_nacimiento"]).date()
        dia_var = tk.StringVar(value=str(fecha_nac.day))
        mes_var = tk.StringVar(value=str(fecha_nac.month))
        ano_var = tk.StringVar(value=str(fecha_nac.year))
        
        ttk.Entry(fecha_frame, textvariable=dia_var, width=3).pack(side=tk.LEFT)
        ttk.Label(fecha_frame, text="/").pack(side=tk.LEFT)
        ttk.Entry(fecha_frame, textvariable=mes_var, width=3).pack(side=tk.LEFT)
        ttk.Label(fecha_frame, text="/").pack(side=tk.LEFT)
        ttk.Entry(fecha_frame, textvariable=ano_var, width=5).pack(side=tk.LEFT)
        
        ttk.Label(dialogo, text="Notas:").pack(pady=(10, 5))
        notas_text = tk.Text(dialogo, height=4, width=40)
        notas_text.pack(pady=5, fill=tk.BOTH, expand=True)
        notas_text.insert(1.0, self.paciente_actual.get('notas', ''))
        
        def actualizar_paciente():
            """Actualiza los datos del paciente"""
            try:
                nombre = nombre_var.get().strip()
                if not nombre:
                    tk.messagebox.showerror("Error", "El nombre es obligatorio")
                    return
                
                # Validar fecha
                dia = int(dia_var.get())
                mes = int(mes_var.get())
                ano = int(ano_var.get())
                fecha_nac = date(ano, mes, dia)
                
                if fecha_nac > date.today():
                    tk.messagebox.showerror("Error", "La fecha de nacimiento no puede ser futura")
                    return
                
                # Actualizar paciente
                exito = self.db.actualizar_paciente(
                    self.paciente_actual["id"],
                    nombre=nombre,
                    dni=dni_var.get().strip(),
                    fecha_nacimiento=fecha_nac,
                    notas=notas_text.get(1.0, tk.END).strip()
                )
                
                if exito:
                    tk.messagebox.showinfo("Éxito", "Paciente actualizado correctamente")
                    self.actualizar_lista_pacientes()
                    self.paciente_actual = self.db.obtener_paciente(self.paciente_actual["id"])
                    self.actualizar_info_paciente()
                    self.actualizar_info_paciente_principal()
                    self.cargar_datos_paciente_formulario()
                    dialogo.destroy()
                else:
                    tk.messagebox.showerror("Error", "No se pudo actualizar el paciente")
                    
            except ValueError:
                tk.messagebox.showerror("Error", "Fecha inválida")
            except Exception as e:
                tk.messagebox.showerror("Error", f"Error al actualizar: {str(e)}")
        
        # Botones
        btn_frame = ttk.Frame(dialogo)
        btn_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(btn_frame, text="Guardar", 
                  command=actualizar_paciente).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(btn_frame, text="Cancelar", 
                  command=dialogo.destroy).pack(side=tk.RIGHT)

    def eliminar_paciente(self):
        """Elimina el paciente actual con mejor manejo de errores"""
        if not self.paciente_actual:
            tk.messagebox.showwarning("Advertencia", "Primero selecciona un paciente")
            return
        
        # Obtener número de evaluaciones para confirmación
        evaluaciones = self.db.obtener_evaluaciones_paciente(self.paciente_actual["id"])
        
        confirmacion = tk.messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de eliminar al paciente {self.paciente_actual['nombre']}?\n"
            f"Se eliminarán {len(evaluaciones)} evaluaciones asociadas.\n\n"
            f"Esta acción no se puede deshacer."
        )
        
        if confirmacion:
            try:
                if self.db.eliminar_paciente(self.paciente_actual["id"]):
                    tk.messagebox.showinfo("Éxito", "Paciente eliminado correctamente")
                    self.paciente_actual = None
                    self.actualizar_lista_pacientes()
                    self.actualizar_estadisticas()
                    self.actualizar_info_paciente_principal()
                    self.limpiar_formulario()
                else:
                    tk.messagebox.showerror("Error", 
                                       "No se pudo eliminar el paciente.\n"
                                       "Puede que tenga evaluaciones asociadas que no se pueden eliminar.")
            except Exception as e:
                tk.messagebox.showerror("Error", f"Error al eliminar paciente: {str(e)}")

    # ========== MÉTODOS DE CÁLCULO Y EVALUACIÓN ==========

    def calcular_edad_actual(self):
        """Calcula la edad exacta en años, meses y días"""
        try:
            dia = self.dia_var.get().strip()
            mes = self.mes_var.get().strip()
            ano = self.ano_var.get().strip()
            
            # Validar que no estén vacíos
            if not dia or not mes or not ano:
                tk.messagebox.showerror("Error", "Por favor completa todos los campos de fecha")
                return
                
            dia = int(dia)
            mes = int(mes) 
            ano = int(ano)
            
            # Validar fecha
            if not (1 <= dia <= 31) or not (1 <= mes <= 12) or not (1900 <= ano <= 2100):
                tk.messagebox.showerror("Error", "Fecha inválida. Usa formato: DD/MM/AAAA")
                return
            
            fecha_nacimiento = date(ano, mes, dia)
            hoy = date.today()
            
            # Validar que la fecha no sea futura
            if fecha_nacimiento > hoy:
                tk.messagebox.showerror("Error", "La fecha de nacimiento no puede ser futura")
                return
            
            # Calcular diferencia exacta
            diferencia = relativedelta(hoy, fecha_nacimiento)
            
            edad_texto = f"{diferencia.years} años, {diferencia.months} meses, {diferencia.days} días"
            self.edad_label.config(text=edad_texto)
            
            # Guardar la edad calculada para usar en las conversiones
            self.edad_calculada = {
                'años': diferencia.years,
                'meses': diferencia.months, 
                'días': diferencia.days,
                'fecha_nacimiento': fecha_nacimiento,
                'edad_formato': f"{diferencia.years}:{diferencia.months}",
                'edad_meses': diferencia.years * 12 + diferencia.months
            }
            
            # Validar que la edad esté en rango (6-16 años)
            edad_meses_total = self.edad_calculada['edad_meses']
            if edad_meses_total < 72:  # 6 años = 72 meses
                tk.messagebox.showwarning("Advertencia", 
                                    f"Edad {diferencia.years} años es menor al rango mínimo (6 años)\n"
                                    "Los resultados pueden no ser precisos")
            elif edad_meses_total > 203:  # 16 años 11 meses = 203 meses
                tk.messagebox.showwarning("Advertencia",
                                    f"Edad {diferencia.years} años excede el rango máximo (16 años 11 meses)\n"
                                    "Los resultados pueden no ser precisos")
            
            print(f"✅ Edad calculada: {edad_texto}")
            print(f"📅 Formato para conversión: {self.edad_calculada['edad_formato']}")
            print(f"🔢 Edad en meses: {self.edad_calculada['edad_meses']}")
            
        except ValueError as e:
            tk.messagebox.showerror("Error", "Fecha inválida. Usa formato numérico: DD/MM/AAAA")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Error al calcular edad: {e}")

    def calcular_puntajes(self):
        """Calcula y muestra los puntajes escala usando el JSON"""
        try:
            # Verificar que se calculó la edad
            if not hasattr(self, 'edad_calculada'):
                tk.messagebox.showerror("Error", "Primero calcula la edad del paciente")
                return
            
            # Verificar que haya nombre
            nombre = self.nombre_entry.get().strip()
            if not nombre:
                tk.messagebox.showerror("Error", "Por favor ingresa el nombre del paciente")
                return
            
            # Verificar que el conversor esté disponible
            if conversor is None:
                tk.messagebox.showerror("Error", "No se pudo cargar el conversor de puntajes escala")
                return
            
            # Usar el formato de edad para búsqueda en tablas JSON
            edad_formato = self.edad_calculada['edad_formato']
            print(f"🔍 Iniciando cálculo para: {nombre}, Edad: {edad_formato}")
            
            resultados = {}
            subpruebas_calculadas = 0
            errores = []
            
            for subprueba, widgets in self.entries_puntajes.items():
                puntaje_bruto_str = widgets["entry"].get().strip()
                if puntaje_bruto_str:
                    try:
                        puntaje_bruto = int(puntaje_bruto_str)
                        print(f"🔄 Procesando {subprueba}: {puntaje_bruto}")
                        
                        # CONVERSIÓN PRINCIPAL CON JSON
                        puntaje_escala = conversor.convertir_puntaje(
                            edad_formato, subprueba, puntaje_bruto
                        )
                        
                        # Mostrar resultado en la interfaz
                        widgets["label"].config(text=f"{puntaje_escala}", foreground="#27ae60")
                        resultados[subprueba] = {
                            'bruto': puntaje_bruto,
                            'escala': puntaje_escala,
                            'nombre': self.obtener_nombre_completo_subprueba(subprueba)
                        }
                        subpruebas_calculadas += 1
                        
                        print(f"✅ {subprueba}: {puntaje_bruto} → {puntaje_escala}")
                        
                    except ValueError as e:
                        error_msg = f"Puntaje inválido en {subprueba}: {str(e)}"
                        print(f"❌ {error_msg}")
                        widgets["label"].config(text="Inválido", foreground="#e74c3c")
                        errores.append(error_msg)
                    except Exception as e:
                        error_msg = f"Error en {subprueba}: {str(e)}"
                        print(f"❌ {error_msg}")
                        widgets["label"].config(text="Error", foreground="#e74c3c")
                        errores.append(error_msg)
                else:
                    # Limpiar label si no hay puntaje
                    widgets["label"].config(text="")
            
            # Mostrar resumen
            if subpruebas_calculadas > 0:
                mensaje = f"✅ Puntajes calculados: {subpruebas_calculadas} subpruebas"
                if errores:
                    mensaje += f"\n⚠️ Errores: {len(errores)} subpruebas"
                    for error in errores:
                        mensaje += f"\n   • {error}"
                
                tk.messagebox.showinfo("Resultado", mensaje)
                print(f"🎯 Resultados finales: {resultados}")
                
                # Mostrar resumen en consola
                print("\n" + "="*50)
                print("📊 RESUMEN DE RESULTADOS")
                print("="*50)
                for subprueba, datos in resultados.items():
                    print(f"   {subprueba}: {datos['bruto']} → {datos['escala']}")
                print("="*50)
                
            else:
                tk.messagebox.showwarning("Advertencia", "No se ingresaron puntajes brutos válidos")
                
        except Exception as e:
            error_msg = f"Error general en el cálculo: {str(e)}"
            print(f"💥 {error_msg}")
            tk.messagebox.showerror("Error", error_msg)

    def calcular_puntajes_compuestos(self):
        """Calcula los puntajes compuestos usando las tablas JSON"""
        try:
            # Verificar que hay puntajes escalares calculados
            puntajes_escalares = {}
            for subprueba, widgets in self.entries_puntajes.items():
                texto = widgets["label"].cget("text")
                if texto and texto.strip() and texto not in ["Inválido", "Error"]:
                    try:
                        puntajes_escalares[subprueba] = int(texto)
                    except ValueError:
                        continue
            
            if not puntajes_escalares:
                tk.messagebox.showwarning("Advertencia", 
                                    "Primero calcula los puntajes escala antes de calcular los compuestos")
                return
            
            print(f"🔢 Puntajes escalares disponibles: {puntajes_escalares}")
            
            # Mapeo de escalas a sus abreviaturas en el JSON
            mapeo_escalas_json = {
                "Comprensión Verbal (ICV)": "ICV",
                "Visoespacial (IVE)": "IVE", 
                "Razonamiento Fluido (IRF)": "IRF",
                "Memoria de Trabajo (IMT)": "IMT",
                "Velocidad de Procesamiento (IVP)": "IVP"
            }
            
            # Limpiar resultados anteriores
            self.resultados_actuales = {}
            
            # Calcular para cada escala
            for escala, datos in self.labels_resultados_compuestos.items():
                if escala == "Escala Total (CIT)":
                    # Para la escala total, usamos el conversor CIT específico
                    self.calcular_escala_total_cit(datos, puntajes_escalares)
                    continue
                    
                subtests_escala = datos['subtests']
                puntajes_disponibles = []
                
                # Recolectar puntajes disponibles para esta escala
                for subtest in subtests_escala:
                    if subtest in puntajes_escalares:
                        puntajes_disponibles.append(puntajes_escalares[subtest])
                
                if puntajes_disponibles:
                    suma_puntajes = sum(puntajes_disponibles)
                    
                    # Usar el conversor de compuestos con JSON
                    abreviatura = mapeo_escalas_json.get(escala)
                    if abreviatura:
                        try:
                            resultado = self.conversor_compuestos.convertir_compuesto(abreviatura, suma_puntajes)
                            
                            if resultado:
                                # Determinar el intervalo de confianza según el nivel seleccionado
                                nivel = self.nivel_confianza.get()
                                intervalo_confianza = resultado['conf_90'] if nivel == "90%" else resultado['conf_95']
                                
                                # Actualizar interfaz
                                datos['suma'].config(text=str(suma_puntajes))
                                datos['compuesto'].config(text=str(resultado['compuesto']), 
                                                       foreground=self.obtener_color_puntaje(resultado['compuesto']))
                                datos['percentil'].config(text=f"{resultado['percentil']}%")
                                datos['confianza'].config(text=intervalo_confianza)
                                
                                # Guardar resultado para la gráfica
                                self.resultados_actuales[datos['abreviatura']] = resultado['compuesto']
                                
                                print(f"📊 {escala}: Suma={suma_puntajes}, Compuesto={resultado['compuesto']}, Percentil={resultado['percentil']}%")
                            else:
                                self.limpiar_fila_compuesto(datos)
                        except Exception as e:
                            print(f"❌ Error calculando {escala}: {e}")
                            self.limpiar_fila_compuesto(datos)
                    else:
                        self.limpiar_fila_compuesto(datos)
                else:
                    self.limpiar_fila_compuesto(datos)
            
            tk.messagebox.showinfo("Éxito", "Puntajes compuestos calculados correctamente")
            
        except Exception as e:
            tk.messagebox.showerror("Error", f"Error al calcular puntajes compuestos: {str(e)}")
            print(f"💥 Error en cálculo compuesto: {e}")

    def calcular_escala_total_cit(self, datos, puntajes_escalares):
        """Calcula la escala total (CIT) usando las 7 subpruebas principales y tabla específica"""
        # Las 7 subpruebas principales para el CIT
        subpruebas_principales = ["CC", "AN", "MR", "RD", "CLA", "VOC", "BAL"]
        
        puntajes_disponibles = []
        for subtest in subpruebas_principales:
            if subtest in puntajes_escalares:
                puntajes_disponibles.append(puntajes_escalares[subtest])
        
        if len(puntajes_disponibles) == 7:  # Necesitamos exactamente 7 subpruebas
            suma_puntajes = sum(puntajes_disponibles)
            
            # Usar el conversor CIT específico
            try:
                resultado = self.conversor_cit.convertir_cit(suma_puntajes)
                
                if resultado:
                    # Determinar el intervalo de confianza según el nivel seleccionado
                    nivel = self.nivel_confianza.get()
                    intervalo_confianza = resultado['conf_90'] if nivel == "90%" else resultado['conf_95']
                    
                    # Actualizar interfaz
                    datos['suma'].config(text=str(suma_puntajes))
                    datos['compuesto'].config(text=str(resultado['compuesto']), 
                                           foreground=self.obtener_color_puntaje(resultado['compuesto']))
                    datos['percentil'].config(text=f"{resultado['percentil']}%")
                    datos['confianza'].config(text=intervalo_confianza)
                    
                    # Guardar resultado para la gráfica
                    self.resultados_actuales[datos['abreviatura']] = resultado['compuesto']
                    
                    print(f"📊 Escala Total (CIT): Suma={suma_puntajes}, Compuesto={resultado['compuesto']}, Percentil={resultado['percentil']}%")
                else:
                    self.limpiar_fila_compuesto(datos)
            except Exception as e:
                print(f"❌ Error calculando CIT: {e}")
                self.limpiar_fila_compuesto(datos)
        else:
            self.limpiar_fila_compuesto(datos)
            print("⚠️ Se necesitan exactamente 7 subpruebas para calcular la Escala Total (CIT)")

    def limpiar_fila_compuesto(self, datos):
        """Limpia una fila de resultados compuestos"""
        datos['suma'].config(text="")
        datos['compuesto'].config(text="")
        datos['percentil'].config(text="")
        datos['confianza'].config(text="")

    def actualizar_intervalos_confianza(self, event=None):
        """Actualiza los intervalos de confianza cuando cambia el nivel seleccionado"""
        try:
            # Mapeo de escalas a abreviaturas JSON
            mapeo_escalas_json = {
                "Comprensión Verbal (ICV)": "ICV",
                "Visoespacial (IVE)": "IVE", 
                "Razonamiento Fluido (IRF)": "IRF",
                "Memoria de Trabajo (IMT)": "IMT",
                "Velocidad de Procesamiento (IVP)": "IVP"
            }
            
            nivel = self.nivel_confianza.get()
            
            for escala, datos in self.labels_resultados_compuestos.items():
                texto_suma = datos['suma'].cget("text")
                if texto_suma and texto_suma.strip():
                    suma_puntajes = int(texto_suma)
                    
                    if escala == "Escala Total (CIT)":
                        # Para escala total usar conversor CIT
                        try:
                            resultado = self.conversor_cit.convertir_cit(suma_puntajes)
                            if resultado:
                                intervalo_confianza = resultado['conf_90'] if nivel == "90%" else resultado['conf_95']
                                datos['confianza'].config(text=intervalo_confianza)
                        except Exception as e:
                            print(f"⚠️ Error actualizando intervalo CIT: {e}")
                    else:
                        # Para otras escalas usar JSON
                        abreviatura = mapeo_escalas_json.get(escala)
                        if abreviatura:
                            try:
                                resultado = self.conversor_compuestos.convertir_compuesto(abreviatura, suma_puntajes)
                                if resultado:
                                    intervalo_confianza = resultado['conf_90'] if nivel == "90%" else resultado['conf_95']
                                    datos['confianza'].config(text=intervalo_confianza)
                            except Exception as e:
                                print(f"⚠️ Error actualizando intervalo para {escala}: {e}")
            
            tk.messagebox.showinfo("Actualizado", f"Intervalos de confianza actualizados al {nivel}")
        except Exception as e:
            print(f"⚠️ Error actualizando intervalos: {e}")

    def mostrar_grafica_perfil(self):
        """Muestra una gráfica de perfil con los resultados de los índices"""
        if not MATPLOTLIB_AVAILABLE:
            tk.messagebox.showerror("Error", "Matplotlib no está disponible. Instala con: pip install matplotlib")
            return
        
        if not self.resultados_actuales:
            tk.messagebox.showwarning("Advertencia", "Primero calcula los puntajes compuestos para generar la gráfica")
            return
        
        # Crear ventana para la gráfica
        grafica_window = tk.Toplevel(self.root)
        grafica_window.title("📊 Gráfica de Perfil WISC-V")
        grafica_window.geometry("800x600")
        grafica_window.configure(bg='#f0f0f0')
        
        # Centrar la ventana
        self.centrar_ventana(grafica_window, 800, 600)
        
        # Obtener nombre del paciente
        nombre_paciente = self.nombre_entry.get().strip()
        if not nombre_paciente:
            nombre_paciente = "Paciente"
        
        # Crear figura
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        # Definir los índices en orden
        indices = ['ICV', 'IVE', 'IRF', 'IMT', 'IVP', 'CIT']
        nombres_completos = {
            'ICV': 'Comprensión Verbal',
            'IVE': 'Visoespacial', 
            'IRF': 'Razonamiento Fluido',
            'IMT': 'Memoria de Trabajo',
            'IVP': 'Velocidad de Procesamiento',
            'CIT': 'Escala Total'
        }
        
        # Obtener valores para cada índice
        valores = []
        etiquetas_completas = []
        
        for indice in indices:
            if indice in self.resultados_actuales:
                valores.append(self.resultados_actuales[indice])
                etiquetas_completas.append(f"{indice}\n{nombres_completos[indice]}")
            else:
                valores.append(0)  # Valor por defecto si no está calculado
                etiquetas_completas.append(f"{indice}\n{nombres_completos[indice]}")
        
        # Crear gráfica de LÍNEAS en lugar de barras
        x_pos = range(len(indices))
        
        # Línea principal con marcadores
        line = ax.plot(x_pos, valores, marker='o', linestyle='-', linewidth=3, 
                       markersize=8, color='#3498db', label='Perfil del Paciente')[0]
        
        # Añadir valores en los puntos
        for i, valor in enumerate(valores):
            if valor > 0:  # Solo mostrar valor si es mayor que 0
                ax.annotate(f'{valor}', 
                           (i, valor), 
                           textcoords="offset points", 
                           xytext=(0,10), 
                           ha='center', 
                           fontweight='bold',
                           fontsize=10,
                           color='#2c3e50')
        
        # Añadir línea azul para promedio (100)
        ax.axhline(y=100, color='blue', linestyle='-', linewidth=2, alpha=0.7, label='Promedio (100)')
        
        # Añadir línea roja para el CIT del evaluado si está disponible
        if 'CIT' in self.resultados_actuales:
            cit_valor = self.resultados_actuales['CIT']
            ax.axhline(y=cit_valor, color='red', linestyle='--', linewidth=2, alpha=0.7, label=f'CIT Evaluado ({cit_valor})')
        
        # Personalizar gráfica
        ax.set_ylabel('Puntaje Compuesto', fontsize=12, fontweight='bold')
        ax.set_xlabel('Índices WISC-V', fontsize=12, fontweight='bold')
        ax.set_title(f'Perfil de Resultados WISC-V - {nombre_paciente}', fontsize=14, fontweight='bold')
        
        # Configurar eje X con etiquetas completas
        ax.set_xticks(x_pos)
        ax.set_xticklabels(etiquetas_completas, fontsize=9)
        
        # Configurar límites del eje Y
        ax.set_ylim(40, 160)
        
        # Añadir líneas de referencia para categorías (mantenemos las áreas de fondo)
        ax.axhspan(130, 160, alpha=0.1, color='green', label='Muy Superior')
        ax.axhspan(120, 129, alpha=0.1, color='lightgreen', label='Superior')
        ax.axhspan(110, 119, alpha=0.1, color='lightblue', label='Alto')
        ax.axhspan(90, 109, alpha=0.1, color='yellow', label='Promedio')
        ax.axhspan(80, 89, alpha=0.1, color='orange', label='Bajo')
        ax.axhspan(70, 79, alpha=0.1, color='red', label='Muy Bajo')
        ax.axhspan(40, 69, alpha=0.1, color='darkred', label='Extremadamente Bajo')
        
        # Añadir grid para mejor lectura
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Añadir leyenda
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Ajustar layout para que quepa la leyenda
        fig.tight_layout()
        
        # Embedder la gráfica en Tkinter
        canvas = FigureCanvasTkAgg(fig, master=grafica_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Botón para guardar gráfica
        btn_frame = ttk.Frame(grafica_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(btn_frame, text="💾 Guardar Gráfica", 
                  command=lambda: self.guardar_grafica(fig, nombre_paciente),
                  width=15).pack(side=tk.LEFT)
        
        ttk.Button(btn_frame, text="Cerrar", 
                  command=grafica_window.destroy,
                  width=10).pack(side=tk.RIGHT)

    def guardar_grafica(self, fig, nombre_paciente):
        """Guarda la gráfica como archivo PNG"""
        try:
            from tkinter import filedialog
            import os
            
            # Sugerir nombre de archivo
            nombre_archivo = f"WISC-V_Perfil_{nombre_paciente.replace(' ', '_')}_{date.today().strftime('%Y%m%d')}.png"
            
            archivo = filedialog.asksaveasfilename(
                title="Guardar gráfica como...",
                defaultextension=".png",
                filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("Todos los archivos", "*.*")],
                initialfile=nombre_archivo
            )
            
            if archivo:
                fig.savefig(archivo, dpi=300, bbox_inches='tight')
                tk.messagebox.showinfo("Éxito", f"Gráfica guardada en:\n{archivo}")
        except Exception as e:
            tk.messagebox.showerror("Error", f"No se pudo guardar la gráfica: {str(e)}")

    def obtener_color_puntaje(self, puntaje):
        """Devuelve el color según el puntaje compuesto"""
        if puntaje >= 130:
            return "#27ae60"  # Verde - Muy Superior
        elif puntaje >= 120:
            return "#2ecc71"  # Verde claro - Superior
        elif puntaje >= 110:
            return "#3498db"  # Azul - Medio Alto
        elif puntaje >= 90:
            return "#f39c12"  # Naranja - Medio
        elif puntaje >= 80:
            return "#e67e22"  # Naranja oscuro - Medio Bajo
        elif puntaje >= 70:
            return "#e74c3c"  # Rojo - Bajo
        else:
            return "#c0392b"  # Rojo oscuro - Muy Bajo

    def limpiar_formulario(self):
        """Limpia todos los campos del formulario"""
        self.nombre_entry.delete(0, tk.END)
        self.dni_entry.delete(0, tk.END)
        self.dia_var.set("")
        self.mes_var.set("")
        self.ano_var.set("")
        self.edad_label.config(text="")
        
        if hasattr(self, 'edad_calculada'):
            del self.edad_calculada
        
        for widgets in self.entries_puntajes.values():
            widgets["entry"].delete(0, tk.END)
            widgets["label"].config(text="")
        
        # Limpiar también la sección de resultados compuestos
        for escala_data in self.labels_resultados_compuestos.values():
            escala_data['suma'].config(text="")
            escala_data['compuesto'].config(text="")
            escala_data['percentil'].config(text="")
            escala_data['confianza'].config(text="")
        
        # Limpiar resultados actuales
        self.resultados_actuales = {}
        
        # Actualizar información del paciente
        self.actualizar_info_paciente_principal()
        
        print("🔄 Formulario limpiado")
        tk.messagebox.showinfo("Listo", "Formulario limpiado correctamente")

    def guardar_evaluacion(self):
        """Guarda la evaluación actual en la base de datos SQLite"""
        try:
            if not self.paciente_actual:
            # Usar messagebox de forma segura
                self.root.after(0, lambda: tk.messagebox.showerror("Error", "Primero selecciona un paciente"))
                return
                
            if not hasattr(self, 'edad_calculada'):
                self.root.after(0, lambda: tk.messagebox.showerror("Error", "Primero calcula la edad del paciente"))
                return
        
        # Recolectar datos de la evaluación
            datos_evaluacion = self.recolectar_datos_evaluacion()
        
            if not datos_evaluacion["subpruebas"] and not datos_evaluacion["compuestos"]:
                self.root.after(0, lambda: tk.messagebox.showwarning("Advertencia", "No hay datos calculados para guardar"))
                return
        
            print(f"💾 Intentando guardar evaluación para paciente: {self.paciente_actual['nombre']}")
            print(f"📊 Subpruebas: {len(datos_evaluacion['subpruebas'])}")
            print(f"🎯 Compuestos: {len(datos_evaluacion['compuestos'])}")
        
        # Guardar en base de datos SQLite
            eval_id = self.db.agregar_evaluacion(self.paciente_actual["id"], datos_evaluacion)
        
            if eval_id:
                print(f"✅ Evaluación guardada exitosamente: {eval_id}")
            
            # Actualizar datos internos primero
                self.evaluacion_actual = self.db.obtener_evaluacion(eval_id)
            
            # Programar las actualizaciones de UI para ejecutar de forma segura
                self.root.after(0, self.actualizar_estadisticas)
                self.root.after(0, self.actualizar_info_paciente)
                self.root.after(0, self.actualizar_info_paciente_principal)
            
            # Mostrar mensaje de éxito de forma segura
                def mostrar_exito():
                    try:
                        tk.messagebox.showinfo("Éxito", 
                                            f"Evaluación guardada correctamente\n"
                                            f"ID: {eval_id}\n"
                                            f"Paciente: {self.paciente_actual['nombre']}")
                    
                    # Preguntar sobre el informe PDF
                        if tk.messagebox.askyesno("Generar Informe", "¿Desea generar un informe PDF de esta evaluación?"):
                            self.generar_informe_pdf(datos_evaluacion)
                    except Exception as e:
                        print(f"⚠️ Error mostrando diálogos: {e}")
            
                self.root.after(100, mostrar_exito)
                
            else:
                self.root.after(0, lambda: tk.messagebox.showerror("Error", 
                                    "No se pudo guardar la evaluación en la base de datos.\n"
                                    "Verifica que los datos sean válidos."))
                
        except Exception as e:
            error_msg = f"Error al guardar evaluación: {str(e)}"
            print(f"💥 {error_msg}")
            self.root.after(0, lambda: tk.messagebox.showerror("Error", error_msg))

    def recolectar_datos_evaluacion(self):
        """Recolecta todos los datos de la evaluación actual de forma serializable"""
        # Obtener datos de edad calculada de forma serializable
        edad_calculada_serializable = {}
        if hasattr(self, 'edad_calculada'):
            for key, value in self.edad_calculada.items():
                if isinstance(value, date):
                    # Convertir date a string ISO
                    edad_calculada_serializable[key] = value.isoformat()
                else:
                    edad_calculada_serializable[key] = value
        
        datos = {
            "fecha": datetime.now().isoformat(),
            "edad_paciente": edad_calculada_serializable,
            "subpruebas": {},
            "compuestos": {},
            "nivel_confianza": self.nivel_confianza.get()
        }
        
        # Recolectar subpruebas
        for subprueba, widgets in self.entries_puntajes.items():
            texto_resultado = widgets["label"].cget("text")
            if texto_resultado and texto_resultado not in ["", "Inválido", "Error"]:
                try:
                    datos["subpruebas"][subprueba] = {
                        'escalar': int(texto_resultado),
                        'bruto': widgets["entry"].get().strip(),
                        'nombre': self.obtener_nombre_completo_subprueba(subprueba)
                    }
                except:
                    pass
        
        # Recolectar compuestos
        for escala, datos_ui in self.labels_resultados_compuestos.items():
            texto_compuesto = datos_ui['compuesto'].cget("text")
            if texto_compuesto and texto_compuesto.strip():
                try:
                    datos["compuestos"][escala] = {
                        'suma_escalar': datos_ui['suma'].cget("text"),
                        'compuesto': int(texto_compuesto),
                        'percentil': datos_ui['percentil'].cget("text"),
                        'intervalo_confianza': datos_ui['confianza'].cget("text")
                    }
                except:
                    pass
        
        return datos

    def generar_informe_pdf(self, eval_data=None):
        """Genera un informe PDF con los resultados de la evaluación incluyendo el gráfico"""
        try:
            if not self.paciente_actual:
                self.root.after(0, lambda: tk.messagebox.showerror("Error", "Primero selecciona un paciente"))
                return

        # Si no se proporcionan datos, usar los actuales
            if eval_data is None:
                eval_data = self.recolectar_datos_evaluacion()

            if not eval_data["subpruebas"] and not eval_data["compuestos"]:
                self.root.after(0, lambda: tk.messagebox.showwarning("Advertencia", "No hay datos de evaluación para generar el informe"))
                return

        # Importar FPDF con imports modernos
            try:
                from fpdf import FPDF
                from fpdf.enums import XPos, YPos
            except ImportError:
            # Fallback para versiones antiguas
                try:
                    from fpdf import FPDF
                # Definir enums manualmente para versiones antiguas
                    class XPos:
                        LEFT = 'LEFT'
                        RIGHT = 'RIGHT'
                        START = 'START'
                        END = 'END'
                        LMARGIN = 'LMARGIN'
                        RMARGIN = 'RMARGIN'
                        WCONT = 'WCONT'
                        CENTER = 'CENTER'
                
                    class YPos:
                        TOP = 'TOP'
                        LAST = 'LAST'
                        TMARGIN = 'TMARGIN'
                        BMARGIN = 'BMARGIN'
                        NEXT = 'NEXT'
                except ImportError:
                    self.root.after(0, lambda: tk.messagebox.showerror("Error", "Para generar PDFs, instala fpdf2: pip install fpdf2"))
                    return

        # Función de limpieza mejorada
            def limpiar_texto(texto):
                """Limpia el texto para evitar problemas de codificación"""
                if texto is None:
                    return ""
                texto = str(texto)
            # Reemplazar caracteres problemáticos específicos
                reemplazos = {
                    '•': '-',      # Bullet point
                    '·': '-',      # Punto medio  
                    '…': '...',    # Puntos suspensivos
                    '–': '-',      # Raya
                    '—': '-',      # Otra raya
                    '“': '"',      # Comillas
                    '”': '"',
                    '‘': "'",
                    '’': "'",
                    'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
                    'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
                    'ñ': 'n', 'Ñ': 'N',
                    'ü': 'u', 'Ü': 'U',
                }
                for char, replacement in reemplazos.items():
                    texto = texto.replace(char, replacement)
                return texto

        # Crear PDF
            pdf = FPDF()
            pdf.add_page()

        # Configurar fuentes - usar fuentes core para evitar warnings
            pdf.set_font("helvetica", 'B', 16)
        
        # Título
            titulo = limpiar_texto("Informe de Evaluación WISC-V")
            pdf.cell(0, 10, titulo, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            pdf.ln(10)

        # Información del paciente
            pdf.set_font("helvetica", 'B', 12)
            pdf.cell(0, 10, limpiar_texto("Datos del Paciente"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("helvetica", '', 12)
        
            nombre_limpio = limpiar_texto(self.paciente_actual['nombre'])
            pdf.cell(0, 10, f"Nombre: {nombre_limpio}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
            if self.paciente_actual.get('dni'):
                dni_limpio = limpiar_texto(self.paciente_actual['dni'])
                pdf.cell(0, 10, f"DNI: {dni_limpio}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Fecha de nacimiento y edad
            fecha_nac = datetime.fromisoformat(self.paciente_actual["fecha_nacimiento"]).date()
            pdf.cell(0, 10, f"Fecha de Nacimiento: {fecha_nac.strftime('%d/%m/%Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
            if hasattr(self, 'edad_calculada'):
                edad_texto = f"Edad: {self.edad_calculada['años']} años, {self.edad_calculada['meses']} meses"
                pdf.cell(0, 10, limpiar_texto(edad_texto), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
            pdf.cell(0, 10, f"Fecha de Evaluación: {datetime.now().strftime('%d/%m/%Y %H:%M')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(10)

        # Tabla de subpruebas
            if eval_data["subpruebas"]:
                pdf.set_font("helvetica", 'B', 12)
                pdf.cell(0, 10, limpiar_texto("Resultados de Subpruebas"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Encabezados de tabla
                pdf.set_font("helvetica", 'B', 10)
                pdf.cell(60, 10, "Subprueba", border=1, align='C')
                pdf.cell(40, 10, "Puntaje Bruto", border=1, align='C')
                pdf.cell(40, 10, "Puntaje Escalar", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            
            # Datos de subpruebas
                pdf.set_font("helvetica", '', 10)
                for subprueba, datos in eval_data["subpruebas"].items():
                    nombre_subprueba_limpio = limpiar_texto(datos['nombre'])
                    texto_fila = f"{subprueba} - {nombre_subprueba_limpio}"
                # Asegurarse de que el texto no sea demasiado largo
                    if len(texto_fila) > 25:
                        texto_fila = texto_fila[:25] + "..."
                    pdf.cell(60, 10, texto_fila, border=1)
                    pdf.cell(40, 10, str(datos.get('bruto', '')), border=1, align='C')
                    pdf.cell(40, 10, str(datos.get('escalar', '')), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            
                pdf.ln(10)

        # Tabla de compuestos
            if eval_data["compuestos"]:
                pdf.set_font("helvetica", 'B', 12)
                pdf.cell(0, 10, limpiar_texto("Puntajes Compuestos"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Encabezados de tabla
                pdf.set_font("helvetica", 'B', 10)
                pdf.cell(60, 10, "Escala", border=1, align='C')
                pdf.cell(30, 10, "Compuesto", border=1, align='C')
                pdf.cell(30, 10, "Percentil", border=1, align='C')
                pdf.cell(70, 10, "Intervalo Confianza", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            
            # Datos de compuestos
                pdf.set_font("helvetica", '', 10)
                for escala, datos in eval_data["compuestos"].items():
                    escala_limpia = limpiar_texto(escala)
                # Acortar texto largo
                    if len(escala_limpia) > 25:
                        escala_limpia = escala_limpia[:25] + "..."
                    pdf.cell(60, 10, escala_limpia, border=1)
                    pdf.cell(30, 10, str(datos.get('compuesto', '')), border=1, align='C')
                    pdf.cell(30, 10, str(datos.get('percentil', '')), border=1, align='C')
                    pdf.cell(70, 10, str(datos.get('intervalo_confianza', '')), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            
                pdf.ln(10)

        # NUEVA SECCIÓN: Gráfico de perfil
            if self.resultados_actuales and MATPLOTLIB_AVAILABLE:
                try:
                # Crear gráfico temporal
                    import tempfile
                    import os
                
                # Crear archivo temporal para la imagen
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                        temp_image_path = tmp_file.name
                
                # Generar el gráfico
                    self.generar_grafico_para_pdf(temp_image_path)
                
                # Agregar el gráfico al PDF
                    pdf.set_font("helvetica", 'B', 12)
                    pdf.cell(0, 10, limpiar_texto("Gráfico de Perfil de Resultados"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    pdf.ln(5)
                
                # Insertar la imagen en el PDF (ajustar tamaño según necesidad)
                    pdf.image(temp_image_path, x=10, w=190)
                    pdf.ln(10)
                
                # Limpiar archivo temporal
                    os.unlink(temp_image_path)
                
                except Exception as e:
                    print(f"Error al generar gráfico para PDF: {e}")
                    pdf.cell(0, 10, "No se pudo incluir el gráfico de perfil", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Interpretación de resultados
            pdf.set_font("helvetica", 'B', 12)
            pdf.cell(0, 10, limpiar_texto("Interpretación de Resultados"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("helvetica", '', 10)
        
            interpretacion = """Los puntajes compuestos en el WISC-V tienen una media de 100 y una desviacion estandar de 15.

    Rango de interpretacion:
    - 130 y superior: Muy Superior
    - 120-129: Superior  
    - 110-119: Alto
    - 90-109: Promedio
    - 80-89: Bajo
    - 70-79: Muy Bajo
    - 69 e inferior: Extremadamente Bajo

    Los intervalos de confianza representan el rango dentro del cual se encuentra el verdadero puntaje del evaluado con un 95% de certeza.
    """
            interpretacion_limpia = limpiar_texto(interpretacion)
            pdf.multi_cell(0, 8, interpretacion_limpia)
            pdf.ln(10)

        # Observaciones
            pdf.set_font("helvetica", 'B', 12)
            pdf.cell(0, 10, limpiar_texto("Observaciones"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("helvetica", 'I', 10)
            observaciones = "Este informe ha sido generado automaticamente por el sistema WISC-V. Para una interpretacion completa consulte con un profesional calificado."
            observaciones_limpias = limpiar_texto(observaciones)
            pdf.multi_cell(0, 8, observaciones_limpias)

        # Guardar PDF
            from tkinter import filedialog
            import os
        
        # Nombre de archivo más simple
            nombre_archivo_simple = f"Informe_WISC_V_{nombre_limpio.replace(' ', '_').replace('.', '')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        
            archivo = filedialog.asksaveasfilename(
                title="Guardar informe como...",
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf"), ("Todos los archivos", "*.*")],
                initialfile=nombre_archivo_simple
            )   
        
            if archivo:
                try:
                    pdf.output(archivo)
                    self.root.after(0, lambda: tk.messagebox.showinfo("Éxito", f"Informe PDF generado:\n{archivo}"))
                
                # Preguntar si quiere abrir el PDF
                    if self.root.after(0, lambda: tk.messagebox.askyesno("Abrir PDF", "¿Desea abrir el informe generado?")):
                        try:
                            if os.name == 'nt':  # Windows
                                os.startfile(archivo)
                            elif os.name == 'posix':  # macOS y Linux
                                os.system(f'open "{archivo}"' if sys.platform == 'darwin' else f'xdg-open "{archivo}"')
                        except:
                            self.root.after(0, lambda: tk.messagebox.showinfo("Información", f"El archivo se guardó en: {archivo}"))
                except Exception as e:
                    print(f"Error al guardar PDF: {e}")
                    self.root.after(0, lambda: tk.messagebox.showerror("Error", f"No se pudo guardar el PDF: {str(e)}"))

        except Exception as e:
            print(f"Error general en PDF: {e}")
            self.root.after(0, lambda: tk.messagebox.showerror("Error", f"No se pudo generar el informe PDF: {str(e)}"))

    def generar_grafico_para_pdf(self, ruta_guardado):
        """Genera el gráfico de perfil para incluir en el PDF"""
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("Matplotlib no está disponible")
    
        if not self.resultados_actuales:
            raise ValueError("No hay resultados para graficar")
    
    # Obtener nombre del paciente
        nombre_paciente = self.nombre_entry.get().strip()
        if not nombre_paciente:
            nombre_paciente = "Paciente"
    
    # Crear figura con tamaño optimizado para PDF
        fig = Figure(figsize=(8, 5), dpi=150)
        ax = fig.add_subplot(111)
    
    # Definir los índices en orden
        indices = ['ICV', 'IVE', 'IRF', 'IMT', 'IVP', 'CIT']
        nombres_completos = {
            'ICV': 'Comprension Verbal',
            'IVE': 'Visoespacial', 
            'IRF': 'Razonamiento Fluido',
            'IMT': 'Memoria de Trabajo',
            'IVP': 'Velocidad de Procesamiento',
            'CIT': 'Escala Total'
        }
    
    # Obtener valores para cada índice
        valores = []
        etiquetas_completas = []
    
        for indice in indices:
            if indice in self.resultados_actuales:
                valores.append(self.resultados_actuales[indice])
            # Limpiar nombres para el gráfico también
                nombre_limpio = nombres_completos[indice].replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
                etiquetas_completas.append(f"{indice}\n{nombre_limpio}")
            else:
                valores.append(0)
                nombre_limpio = nombres_completos[indice].replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
                etiquetas_completas.append(f"{indice}\n{nombre_limpio}")
    
    # Crear gráfica de líneas
        x_pos = range(len(indices))
    
    # Línea principal con marcadores
        line = ax.plot(x_pos, valores, marker='o', linestyle='-', linewidth=2, 
                       markersize=6, color='#3498db', label='Perfil del Paciente')[0]
    
    # Añadir valores en los puntos
        for i, valor in enumerate(valores):
            if valor > 0:
                ax.annotate(f'{valor}', 
                           (i, valor), 
                           textcoords="offset points", 
                           xytext=(0,8), 
                           ha='center', 
                           fontweight='bold',
                           fontsize=9,
                           color='#2c3e50')
    
    # Añadir línea para promedio (100)
        ax.axhline(y=100, color='blue', linestyle='-', linewidth=1.5, alpha=0.7, label='Promedio (100)')
    
    # Añadir línea para el CIT del evaluado si está disponible
        if 'CIT' in self.resultados_actuales:
            cit_valor = self.resultados_actuales['CIT']
            ax.axhline(y=cit_valor, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label=f'CIT Evaluado ({cit_valor})')
    
    # Personalizar gráfica para PDF
        ax.set_ylabel('Puntaje Compuesto', fontsize=10, fontweight='bold')
        ax.set_xlabel('Indices WISC-V', fontsize=10, fontweight='bold')
    
    # Limpiar título también
        titulo_limpio = nombre_paciente.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        ax.set_title(f'Perfil de Resultados WISC-V - {titulo_limpio}', fontsize=12, fontweight='bold')
    
    # Configurar eje X con etiquetas completas
        ax.set_xticks(x_pos)
        ax.set_xticklabels(etiquetas_completas, fontsize=8)
    
    # Configurar límites del eje Y
        ax.set_ylim(40, 160)
    
    # Añadir áreas de referencia (más sutiles para PDF)
        ax.axhspan(130, 160, alpha=0.08, color='green', label='Muy Superior')
        ax.axhspan(120, 129, alpha=0.08, color='lightgreen', label='Superior')
        ax.axhspan(110, 119, alpha=0.08, color='lightblue', label='Alto')
        ax.axhspan(90, 109, alpha=0.08, color='yellow', label='Promedio')
        ax.axhspan(80, 89, alpha=0.08, color='orange', label='Bajo')
        ax.axhspan(70, 79, alpha=0.08, color='red', label='Muy Bajo')
        ax.axhspan(40, 69, alpha=0.08, color='darkred', label='Extremadamente Bajo')
    
    # Añadir grid para mejor lectura
        ax.grid(True, alpha=0.2, linestyle='--')
    
    # Añadir leyenda compacta
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    
    # Ajustar layout para PDF
        fig.tight_layout()
    
    # Guardar la figura
        fig.savefig(ruta_guardado, dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    # Liberar memoria
        import matplotlib.pyplot as plt
        plt.close(fig)

    # ========== MÉTODOS DE IA ==========

    def mostrar_prediccion_evolucion(self):
        """Muestra la ventana de predicción de evolución"""
        if not SKLEARN_AVAILABLE:
            tk.messagebox.showerror("Error", "Scikit-learn no está disponible. Instala: pip install scikit-learn pandas numpy joblib")
            return
            
        if not self.paciente_actual:
            tk.messagebox.showwarning("Advertencia", "Primero selecciona un paciente")
            return
        
        # Verificar que tenga evaluaciones previas
        evaluaciones = self.db.obtener_evaluaciones_paciente(self.paciente_actual["id"])
        if len(evaluaciones) == 0:
            tk.messagebox.showwarning("Advertencia", "El paciente no tiene evaluaciones previas")
            return
        
        dialogo = tk.Toplevel(self.root)
        dialogo.title("🤖 Predicción de Evolución - IA")
        dialogo.geometry("600x500")
        dialogo.configure(bg='#f0f0f0')
        
        # Centrar ventana
        self.centrar_ventana(dialogo, 600, 500)
        
        tk.Label(dialogo, text="Predicción de Evolución con IA", 
                font=("Arial", 14, "bold"),
                bg='#f0f0f0').pack(pady=10)
        
        # Selector de meses futuros
        meses_frame = ttk.Frame(dialogo)
        meses_frame.pack(pady=10)
        
        tk.Label(meses_frame, text="Predecir para dentro de:", 
                font=("Arial", 10),
                bg='#f0f0f0').pack(side=tk.LEFT, padx=(0, 10))
        
        meses_var = tk.StringVar(value="12")
        meses_combo = ttk.Combobox(meses_frame, 
                                  textvariable=meses_var,
                                  values=["6", "12", "18", "24"],
                                  state="readonly",
                                  width=8)
        meses_combo.pack(side=tk.LEFT)
        
        # Botón predecir
        def realizar_prediccion():
            try:
                meses = int(meses_var.get())
                resultado = self.predictor_ia.predecir_evolucion(self.paciente_actual["id"], meses)
                
                if resultado:
                    self.mostrar_resultado_prediccion(resultado, contenido_frame)
                else:
                    tk.messagebox.showerror("Error", "No se pudo realizar la predicción")
            except Exception as e:
                tk.messagebox.showerror("Error", f"Error en predicción: {str(e)}")
        
        ttk.Button(dialogo, text="🎯 Realizar Predicción", 
                  command=realizar_prediccion).pack(pady=10)
        
        # Frame para resultados
        contenido_frame = ttk.Frame(dialogo)
        contenido_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Mostrar estadísticas del modelo
        stats = self.predictor_ia.obtener_estadisticas_modelo()
        stats_text = f"Estado del modelo: {stats['estado']}"
        if stats['estado'] == 'Entrenado':
            stats_text += f"\nPrecisión: {stats['precision_cit']} | Confianza: {stats['confianza_predicciones']}"
        
        tk.Label(contenido_frame, text=stats_text,
                font=("Arial", 9),
                justify=tk.LEFT,
                bg='#f0f0f0').pack(anchor=tk.W)
    
    def mostrar_resultado_prediccion(self, prediccion, parent):
        """Muestra los resultados de la predicción"""
        # Limpiar frame
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Información general
        info_frame = ttk.LabelFrame(parent, text="📊 Resumen de Predicción", padding="10")
        info_frame.pack(fill=tk.X, pady=5)
        
        tendencia_color = "#27ae60" if prediccion['tendencia'] == 'mejora' else "#e74c3c" if prediccion['tendencia'] == 'deterioro' else "#f39c12"
        
        info_text = f"• CIT Actual: {prediccion['cit_actual']} puntos\n"
        info_text += f"• CIT Predicho ({prediccion['meses_futuro']} meses): {prediccion['cit_predicho']} puntos\n"
        info_text += f"• Tendencia: {prediccion['tendencia'].upper()}\n"
        info_text += f"• Confianza del modelo: {prediccion['confianza']}%"
        
        tk.Label(info_frame, text=info_text,
                font=("Arial", 10),
                justify=tk.LEFT,
                bg='#f0f0f0').pack(anchor=tk.W)
        
        # Índices predichos
        indices_frame = ttk.LabelFrame(parent, text="🎯 Índices Predichos", padding="10")
        indices_frame.pack(fill=tk.X, pady=5)
        
        for indice, valor in prediccion['indices_predichos'].items():
            frame_indice = ttk.Frame(indices_frame)
            frame_indice.pack(fill=tk.X, pady=2)
            
            tk.Label(frame_indice, text=f"{indice}:", 
                    font=("Arial", 9, "bold"),
                    width=8,
                    bg='#f0f0f0').pack(side=tk.LEFT)
            
            actual = prediccion['indices_actuales'].get(indice, 0)
            color = "#27ae60" if valor > actual else "#e74c3c" if valor < actual else "#f39c12"
            flecha = "↑" if valor > actual else "↓" if valor < actual else "→"
            
            texto = f"{actual} {flecha} {valor}"
            tk.Label(frame_indice, text=texto,
                    font=("Arial", 9),
                    foreground=color,
                    bg='#f0f0f0').pack(side=tk.LEFT)
        
        # Recomendaciones
        rec_frame = ttk.LabelFrame(parent, text="💡 Recomendaciones de IA", padding="10")
        rec_frame.pack(fill=tk.X, pady=5)
        
        for i, rec in enumerate(prediccion['recomendaciones']):
            tk.Label(rec_frame, text=f"• {rec}",
                    font=("Arial", 9),
                    justify=tk.LEFT,
                    bg='#f0f0f0').pack(anchor=tk.W)
    
    def analisis_avanzado_ia(self):
        """Análisis avanzado con IA"""
        if not SKLEARN_AVAILABLE:
            tk.messagebox.showerror("Error", "Scikit-learn no está disponible. Instala: pip install scikit-learn pandas numpy joblib")
            return
            
        if not self.paciente_actual:
            tk.messagebox.showwarning("Advertencia", "Primero selecciona un paciente")
            return
        
        # Implementar análisis de patrones, comparativa con población, etc.
        tk.messagebox.showinfo("Análisis IA", "Funcionalidad en desarrollo...")
    
    def entrenar_sistema_ia(self):
        """Entrena el sistema de IA"""
        if not SKLEARN_AVAILABLE:
            tk.messagebox.showerror("Error", "Scikit-learn no está disponible. Instala: pip install scikit-learn pandas numpy joblib")
            return
            
        try:
            tk.messagebox.showinfo("Entrenamiento IA", "El sistema se entrenará con los datos existentes. Esto puede tomar unos momentos...")
            
            if self.predictor_ia.entrenar_modelos():
                stats = self.predictor_ia.obtener_estadisticas_modelo()
                tk.messagebox.showinfo("Entrenamiento Completado", 
                                    f"✅ Modelo entrenado exitosamente\n"
                                    f"📊 Precisión: {stats['precision_cit']}\n"
                                    f"🎯 Nivel de confianza: {stats['confianza_predicciones']}")
            else:
                tk.messagebox.showwarning("Entrenamiento Fallido", 
                                       "No se pudo entrenar el modelo. Se necesitan más datos de evaluaciones.")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Error en entrenamiento: {str(e)}")


def main():
    """Función principal para ejecutar la aplicación"""
    try:
        root = tk.Tk()
        app = WiscVApp(root)
        
        # Verificar que los componentes se cargaron correctamente
        print("✅ Sistema WISC-V iniciado correctamente")
        print("🗄️ Base de datos SQLite: INICIALIZADA")
        if conversor:
            print("📊 Conversor de escala: CARGADO")
        else:
            print("📊 Conversor de escala: NO CARGADO")
        print("🎯 Conversor de compuestos: CARGADO")
        print("🧠 Conversor de CIT: CARGADO")
        if MATPLOTLIB_AVAILABLE:
            print("📈 Gráficas: DISPONIBLE")
        else:
            print("📈 Gráficas: NO DISPONIBLE")
        if SKLEARN_AVAILABLE:
            print("🤖 IA de predicción: DISPONIBLE")
        else:
            print("🤖 IA de predicción: NO DISPONIBLE")
        
        root.mainloop()
        
    except Exception as e:
        print(f"💥 Error al iniciar la aplicación: {e}")
        tk.messagebox.showerror("Error de Inicio", 
                           f"No se pudo iniciar la aplicación:\n{str(e)}\n\n"
                           f"Verifica que los archivos JSON estén presentes en la carpeta data.")


if __name__ == "__main__":
    main()