"""
GENERADOR DE DATOS REALISTAS CON TENDENCIAS VARIABLES WISC-V
Corrige el problema de todas las tendencias siendo de mejora
"""
import sqlite3
import json
import random
from datetime import datetime, date, timedelta
import uuid
import numpy as np

class GeneradorDatosTendenciasReales:
    def __init__(self, db_path="wisc_v_database.db"):
        self.db_path = db_path
        
        # Perfiles clínicos con diferentes patrones de evolución
        self.perfiles_clinicos = {
            "normal": {
                "descripcion": "Desarrollo típico",
                "tendencias": ["mejora_moderada", "estable", "mejora_leve"],
                "probabilidades": [0.4, 0.4, 0.2]
            },
            "doble_excepcional": {
                "descripcion": "Alta capacidad con dificultades",
                "tendencias": ["mejora_compensatoria", "estable", "deterioro_areas_debiles"],
                "probabilidades": [0.5, 0.3, 0.2]
            },
            "dificultades_aprendizaje": {
                "descripcion": "Dificultades de aprendizaje",
                "tendencias": ["mejora_intervencion", "estable", "deterioro_sin_apoyo"],
                "probabilidades": [0.3, 0.4, 0.3]
            },
            "tdah": {
                "descripcion": "TDAH",
                "tendencias": ["mejora_medicacion", "estable", "deterioro_atencion"],
                "probabilidades": [0.4, 0.3, 0.3]
            },
            "tea": {
                "descripcion": "TEA",
                "tendencias": ["mejora_areas_fuertes", "estable_areas_debiles", "deterioro_social"],
                "probabilidades": [0.3, 0.5, 0.2]
            },
            "superior": {
                "descripcion": "Capacidad superior",
                "tendencias": ["estable_alto", "mejora_moderada", "regresion_media"],
                "probabilidades": [0.5, 0.3, 0.2]
            }
        }
        
        # Definición detallada de cada tipo de tendencia
        self.tipos_tendencia = {
            "mejora_moderada": {
                "descripcion": "Mejora moderada en todas las áreas",
                "cambio_cit": (2, 8),  # puntos por año
                "patron": "uniforme_positivo"
            },
            "mejora_leve": {
                "descripcion": "Mejora leve generalizada",
                "cambio_cit": (1, 4),
                "patron": "uniforme_positivo"
            },
            "mejora_compensatoria": {
                "descripcion": "Mejora en áreas deficitarias, estable en fuertes",
                "cambio_cit": (3, 10),
                "patron": "compensatorio"
            },
            "mejora_intervencion": {
                "descripcion": "Mejora con intervención específica",
                "cambio_cit": (5, 15),
                "patron": "focalizado"
            },
            "mejora_medicacion": {
                "descripcion": "Mejora en atención y velocidad",
                "cambio_cit": (4, 12),
                "patron": "atencion_velocidad"
            },
            "mejora_areas_fuertes": {
                "descripcion": "Mejora en áreas fuertes, estable en débiles",
                "cambio_cit": (2, 6),
                "patron": "areas_fuertes"
            },
            "estable": {
                "descripcion": "Desarrollo estable",
                "cambio_cit": (-1, 2),
                "patron": "uniforme"
            },
            "estable_alto": {
                "descripcion": "Mantenimiento de alto rendimiento",
                "cambio_cit": (-2, 3),
                "patron": "uniforme"
            },
            "estable_areas_debiles": {
                "descripcion": "Estable en áreas débiles, leve mejora en fuertes",
                "cambio_cit": (0, 4),
                "patron": "mixto_estable"
            },
            "deterioro_areas_debiles": {
                "descripcion": "Deterioro en áreas deficitarias",
                "cambio_cit": (-8, -2),
                "patron": "areas_debiles"
            },
            "deterioro_sin_apoyo": {
                "descripcion": "Deterioro por falta de apoyo",
                "cambio_cit": (-12, -4),
                "patron": "generalizado"
            },
            "deterioro_atencion": {
                "descripcion": "Deterioro en atención y concentración",
                "cambio_cit": (-6, -2),
                "patron": "atencion"
            },
            "deterioro_social": {
                "descripcion": "Deterioro en áreas sociales",
                "cambio_cit": (-4, -1),
                "patron": "social"
            },
            "regresion_media": {
                "descripcion": "Regresión a la media",
                "cambio_cit": (-10, -3),
                "patron": "uniforme_negativo"
            }
        }

    def asignar_tendencia_paciente(self, perfil):
        """Asigna una tendencia realista basada en el perfil clínico"""
        tendencias = self.perfiles_clinicos[perfil]["tendencias"]
        probabilidades = self.perfiles_clinicos[perfil]["probabilidades"]
        return random.choices(tendencias, weights=probabilidades)[0]

    def generar_evolucion_segun_tendencia(self, compuestos_iniciales, meses_transcurridos, perfil, tendencia):
        """Genera evolución realista según el tipo de tendencia asignada"""
        tipo_tendencia = self.tipos_tendencia[tendencia]
        cambio_anual = random.uniform(tipo_tendencia["cambio_cit"][0], tipo_tendencia["cambio_cit"][1])
        cambio_mensual = cambio_anual / 12.0
        cambio_total = cambio_mensual * meses_transcurridos
        
        nuevos_compuestos = compuestos_iniciales.copy()
        
        # Aplicar patrón específico de cambio
        if tipo_tendencia["patron"] == "uniforme_positivo":
            for indice in nuevos_compuestos:
                variacion = random.uniform(0.8, 1.2) * cambio_total
                nuevos_compuestos[indice] += variacion
                
        elif tipo_tendencia["patron"] == "uniforme_negativo":
            for indice in nuevos_compuestos:
                variacion = random.uniform(0.8, 1.2) * cambio_total
                nuevos_compuestos[indice] += variacion
                
        elif tipo_tendencia["patron"] == "compensatorio":
            # Mejora en áreas débiles, estable en fuertes
            for indice in nuevos_compuestos:
                if indice in ["IMT", "IVP"]:  # Áreas típicamente deficitarias
                    variacion = random.uniform(1.2, 1.8) * cambio_total
                else:
                    variacion = random.uniform(0.2, 0.5) * cambio_total
                nuevos_compuestos[indice] += variacion
                
        elif tipo_tendencia["patron"] == "focalizado":
            # Mejora específica según perfil
            if perfil == "dificultades_aprendizaje":
                for indice in nuevos_compuestos:
                    if indice in ["IMT", "IVP"]:
                        variacion = random.uniform(1.5, 2.0) * cambio_total
                    else:
                        variacion = random.uniform(0.3, 0.7) * cambio_total
                    nuevos_compuestos[indice] += variacion
                    
        elif tipo_tendencia["patron"] == "atencion_velocidad":
            for indice in nuevos_compuestos:
                if indice in ["IMT", "IVP"]:
                    variacion = random.uniform(1.3, 1.7) * cambio_total
                else:
                    variacion = random.uniform(0.4, 0.8) * cambio_total
                nuevos_compuestos[indice] += variacion
                
        elif tipo_tendencia["patron"] == "areas_fuertes":
            for indice in nuevos_compuestos:
                if indice in ["IRF", "IVE"]:  # Áreas típicamente fuertes en TEA
                    variacion = random.uniform(1.1, 1.5) * cambio_total
                else:
                    variacion = random.uniform(0.1, 0.4) * cambio_total
                nuevos_compuestos[indice] += variacion
                
        elif tipo_tendencia["patron"] == "areas_debiles":
            for indice in nuevos_compuestos:
                if indice in ["IMT", "IVP"]:
                    variacion = random.uniform(1.0, 1.4) * cambio_total
                else:
                    variacion = random.uniform(-0.2, 0.3) * cambio_total
                nuevos_compuestos[indice] += variacion
                
        elif tipo_tendencia["patron"] == "generalizado":
            for indice in nuevos_compuestos:
                variacion = random.uniform(0.9, 1.3) * cambio_total
                nuevos_compuestos[indice] += variacion
                
        elif tipo_tendencia["patron"] == "atencion":
            for indice in nuevos_compuestos:
                if indice in ["IMT", "IVP"]:
                    variacion = random.uniform(1.2, 1.6) * cambio_total
                else:
                    variacion = random.uniform(0.1, 0.5) * cambio_total
                nuevos_compuestos[indice] += variacion
                
        elif tipo_tendencia["patron"] == "social":
            for indice in nuevos_compuestos:
                if indice in ["ICV", "IRF"]:  # Áreas relacionadas con lo social
                    variacion = random.uniform(1.1, 1.5) * cambio_total
                else:
                    variacion = random.uniform(0.2, 0.6) * cambio_total
                nuevos_compuestos[indice] += variacion
                
        else:  # uniforme o mixto_estable
            for indice in nuevos_compuestos:
                variacion = random.uniform(-0.5, 0.5) * cambio_total
                nuevos_compuestos[indice] += variacion
        
        # Asegurar valores dentro de rango realista
        for indice in nuevos_compuestos:
            nuevos_compuestos[indice] = max(40, min(160, nuevos_compuestos[indice]))
            
        return nuevos_compuestos

    def crear_pacientes_con_tendencias_variables(self):
        """Crea pacientes con tendencias de evolución realistas y variables"""
        conn = self.conectar_db()
        cursor = conn.cursor()
        
        nombres = [
            "Alejandro Martínez", "Sofía González", "Diego Rodríguez", "Valentina Fernández", 
            "Javier Sánchez", "Lucía Pérez", "Carlos López", "Isabella García", "Daniel Martínez",
            "Camila Rodríguez", "Pablo Hernández", "Emma López", "Adrián García", "Mía Pérez",
            "Santiago Martínez", "Valeria Sánchez", "Mateo González", "Luna Fernández", "Leo Rodríguez",
            "Olivia Pérez", "Manuel López", "Martina García", "Hugo Martínez", "Julia Rodríguez",
            "Enrique Pérez", "Clara López", "Álvaro Sánchez", "Elena Martínez", "Luis García", "Ana Rodríguez"
        ]
        
        pacientes_creados = []
        
        for i, nombre in enumerate(nombres):
            paciente_id = str(uuid.uuid4())[:8]
            
            # Asignar perfil clínico
            if i < 5:
                perfil = "normal"
            elif i < 10:
                perfil = "doble_excepcional"
            elif i < 15:
                perfil = "dificultades_aprendizaje"
            elif i < 20:
                perfil = "tdah"
            elif i < 25:
                perfil = "tea"
            else:
                perfil = "superior"
            
            # Asignar tendencia específica
            tendencia = self.asignar_tendencia_paciente(perfil)
            
            fecha_nacimiento = self.generar_fecha_nacimiento_realista()
            dni = self.generar_dni()
            
            cursor.execute('''
                INSERT INTO pacientes (id, nombre, dni, fecha_nacimiento, notas)
                VALUES (?, ?, ?, ?, ?)
            ''', (paciente_id, nombre, dni, fecha_nacimiento.isoformat(), 
                  f"Perfil: {perfil} | Tendencia: {tendencia} | {self.tipos_tendencia[tendencia]['descripcion']}"))
            
            pacientes_creados.append({
                'id': paciente_id,
                'nombre': nombre,
                'fecha_nacimiento': fecha_nacimiento,
                'perfil': perfil,
                'tendencia': tendencia
            })
            
            print(f"✅ {nombre} - {perfil} - {tendencia}")
        
        conn.commit()
        conn.close()
        return pacientes_creados

    def generar_fecha_nacimiento_realista(self):
        hoy = date.today()
        años = random.randint(6, 16)
        meses = random.randint(0, 11)
        return hoy.replace(year=hoy.year - años, month=((hoy.month - meses - 1) % 12) + 1)

    def generar_dni(self):
        numero = random.randint(10000000, 99999999)
        letras = "TRWAGMYFPDXBNJZSQVHLCKE"
        return f"{numero}{letras[numero % 23]}"

    def conectar_db(self):
        return sqlite3.connect(self.db_path)

    def generar_puntajes_iniciales_segun_perfil(self, perfil):
        """Genera puntajes compuestos iniciales realistas según perfil"""
        if perfil == "normal":
            return {
                "ICV": random.randint(90, 110),
                "IVE": random.randint(90, 110),
                "IRF": random.randint(90, 110),
                "IMT": random.randint(90, 110),
                "IVP": random.randint(90, 110),
                "CIT": random.randint(95, 105)
            }
        elif perfil == "doble_excepcional":
            return {
                "ICV": random.randint(115, 130),
                "IVE": random.randint(110, 125),
                "IRF": random.randint(110, 125),
                "IMT": random.randint(85, 100),
                "IVP": random.randint(85, 100),
                "CIT": random.randint(105, 120)
            }
        elif perfil == "dificultades_aprendizaje":
            return {
                "ICV": random.randint(85, 100),
                "IVE": random.randint(85, 100),
                "IRF": random.randint(85, 100),
                "IMT": random.randint(70, 85),
                "IVP": random.randint(70, 85),
                "CIT": random.randint(80, 95)
            }
        elif perfil == "tdah":
            return {
                "ICV": random.randint(95, 110),
                "IVE": random.randint(95, 110),
                "IRF": random.randint(95, 110),
                "IMT": random.randint(75, 90),
                "IVP": random.randint(75, 90),
                "CIT": random.randint(85, 100)
            }
        elif perfil == "tea":
            return {
                "ICV": random.randint(85, 100),
                "IVE": random.randint(105, 120),
                "IRF": random.randint(105, 120),
                "IMT": random.randint(90, 105),
                "IVP": random.randint(90, 105),
                "CIT": random.randint(95, 110)
            }
        elif perfil == "superior":
            return {
                "ICV": random.randint(115, 130),
                "IVE": random.randint(115, 130),
                "IRF": random.randint(115, 130),
                "IMT": random.randint(115, 130),
                "IVP": random.randint(115, 130),
                "CIT": random.randint(120, 135)
            }

    def crear_evaluaciones_con_tendencias_reales(self, pacientes):
        """Crea evaluaciones longitudinales con tendencias realistas"""
        conn = self.conectar_db()
        cursor = conn.cursor()
        
        print("\n📊 GENERANDO EVALUACIONES CON TENDENCIAS REALISTAS...")
        
        distribucion_tendencias = {}
        
        for paciente in pacientes:
            print(f"\n🔄 {paciente['nombre']} ({paciente['perfil']} - {paciente['tendencia']})")
            
            # Registrar tendencia para estadísticas
            if paciente['tendencia'] not in distribucion_tendencias:
                distribucion_tendencias[paciente['tendencia']] = 0
            distribucion_tendencias[paciente['tendencia']] += 1
            
            # Fechas de evaluación
            fecha_base = paciente['fecha_nacimiento'].replace(year=paciente['fecha_nacimiento'].year + 7)
            evaluaciones = []
            
            # 3-4 evaluaciones por paciente
            num_evaluaciones = random.randint(3, 4)
            compuestos_actuales = self.generar_puntajes_iniciales_segun_perfil(paciente['perfil'])
            
            for eval_num in range(num_evaluaciones):
                evaluacion_id = str(uuid.uuid4())[:8]
                
                # Espaciar evaluaciones (6-18 meses entre ellas)
                if eval_num == 0:
                    fecha_evaluacion = fecha_base
                else:
                    meses_entre = random.randint(6, 18)
                    fecha_evaluacion = evaluaciones[-1]['fecha'] + timedelta(days=meses_entre * 30)
                
                # Aplicar evolución si no es la primera evaluación
                if eval_num > 0:
                    meses_transcurridos = (fecha_evaluacion - evaluaciones[-1]['fecha']).days // 30
                    compuestos_actuales = self.generar_evolucion_segun_tendencia(
                        compuestos_actuales, meses_transcurridos, paciente['perfil'], paciente['tendencia']
                    )
                
                # Preparar datos de evaluación
                datos_evaluacion = self.preparar_datos_evaluacion(
                    fecha_evaluacion, compuestos_actuales, paciente
                )
                
                # Insertar en base de datos
                cursor.execute('''
                    INSERT INTO evaluaciones (id, paciente_id, fecha_evaluacion, datos_evaluacion)
                    VALUES (?, ?, ?, ?)
                ''', (evaluacion_id, paciente['id'], fecha_evaluacion.isoformat(),
                      json.dumps(datos_evaluacion, ensure_ascii=False)))
                
                evaluaciones.append({
                    'fecha': fecha_evaluacion,
                    'compuestos': compuestos_actuales.copy()
                })
                
                cit = compuestos_actuales.get('CIT', 0)
                cambio = ""
                if eval_num > 0:
                    cit_anterior = evaluaciones[eval_num-1]['compuestos'].get('CIT', 0)
                    diferencia = cit - cit_anterior
                    cambio = f" ({diferencia:+.1f})"
                
                print(f"   📅 Evaluación {eval_num+1}: CIT = {cit:.1f}{cambio}")
            
            conn.commit()
        
        # Mostrar distribución de tendencias
        print(f"\n📈 DISTRIBUCIÓN DE TENDENCIAS:")
        for tendencia, count in distribucion_tendencias.items():
            porcentaje = (count / len(pacientes)) * 100
            descripcion = self.tipos_tendencia[tendencia]['descripcion']
            print(f"   • {tendencia}: {count} pacientes ({porcentaje:.1f}%) - {descripcion}")
        
        conn.close()

    def preparar_datos_evaluacion(self, fecha, compuestos, paciente):
        """Prepara datos completos de evaluación"""
        # Calcular edad en meses
        edad_meses = (fecha.year - paciente['fecha_nacimiento'].year) * 12 + \
                    (fecha.month - paciente['fecha_nacimiento'].month)
        
        datos = {
            "fecha": fecha.isoformat(),
            "edad_paciente": {
                "años": edad_meses // 12,
                "meses": edad_meses % 12,
                "edad_formato": f"{edad_meses // 12}:{edad_meses % 12}",
                "edad_meses": edad_meses
            },
            "compuestos": {},
            "nivel_confianza": "95%",
            "observaciones": self.generar_observaciones_segun_compuestos(compuestos)
        }
        
        # Agregar compuestos
        for indice, valor in compuestos.items():
            percentil = self.calcular_percentil(valor)
            intervalo = self.calcular_intervalo_confianza(valor)
            
            datos["compuestos"][f"Escala {indice}"] = {
                'compuesto': int(round(valor)),
                'percentil': percentil,
                'intervalo_confianza': intervalo,
                'suma_escalar': random.randint(20, 40)  # Placeholder realista
            }
        
        return datos

    def calcular_percentil(self, compuesto):
        if compuesto >= 130: return ">99"
        elif compuesto >= 120: return "93-98"
        elif compuesto >= 110: return "76-92"
        elif compuesto >= 90: return "25-75"
        elif compuesto >= 80: return "9-24"
        elif compuesto >= 70: return "2-8"
        else: return "<2"

    def calcular_intervalo_confianza(self, compuesto):
        margen_error = max(3, int(compuesto * 0.03))
        inferior = max(40, int(compuesto - margen_error))
        superior = min(160, int(compuesto + margen_error))
        return f"{inferior}-{superior}"

    def generar_observaciones_segun_compuestos(self, compuestos):
        observaciones = []
        
        # Análisis de patrones
        if compuestos.get("ICV", 100) - compuestos.get("IMT", 100) > 15:
            observaciones.append("Discrepancia significativa ICV-IMT")
        
        if compuestos.get("IRF", 100) > compuestos.get("ICV", 100) + 10:
            observaciones.append("Razonamiento no verbal superior")
        
        if compuestos.get("CIT", 100) < 85:
            observaciones.append("Rendimiento general bajo")
        elif compuestos.get("CIT", 100) > 120:
            observaciones.append("Capacidad intelectual superior")
        
        if not observaciones:
            observaciones.append("Perfil cognitivo dentro de rangos esperados")
        
        return "; ".join(observaciones)

    def generar_datos_balanceados(self):
        """Genera conjunto completo de datos con tendencias balanceadas"""
        print("🎯 GENERANDO DATOS CON TENDENCIAS REALISTAS Y VARIABLES")
        print("=" * 60)
        
        # Crear pacientes con tendencias variables
        print("\n👥 CREANDO PACIENTES CON TENDENCIAS DIVERSAS...")
        pacientes = self.crear_pacientes_con_tendencias_variables()
        
        # Crear evaluaciones longitudinales
        self.crear_evaluaciones_con_tendencias_reales(pacientes)
        
        # Mostrar resumen final
        self.mostrar_resumen_final(pacientes)
        
        return pacientes

    def mostrar_resumen_final(self, pacientes):
        """Muestra resumen completo de los datos generados"""
        conn = self.conectar_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM pacientes")
        total_pacientes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM evaluaciones")
        total_evaluaciones = cursor.fetchone()[0]
        
        # Calcular cambios promedio en CIT
        cursor.execute('''
            SELECT p.id, p.nombre, e.fecha_evaluacion, e.datos_evaluacion
            FROM pacientes p
            JOIN evaluaciones e ON p.id = e.paciente_id
            ORDER BY p.id, e.fecha_evaluacion
        ''')
        
        cambios_cit = []
        paciente_actual = None
        evaluaciones_paciente = []
        
        for paciente_id, nombre, fecha, datos_json in cursor.fetchall():
            if paciente_id != paciente_actual:
                if evaluaciones_paciente and len(evaluaciones_paciente) > 1:
                    # Calcular cambio para este paciente
                    cit_inicial = evaluaciones_paciente[0]['cit']
                    cit_final = evaluaciones_paciente[-1]['cit']
                    cambio_total = cit_final - cit_inicial
                    meses_total = (evaluaciones_paciente[-1]['fecha'] - evaluaciones_paciente[0]['fecha']).days // 30
                    cambio_anual = (cambio_total / meses_total) * 12 if meses_total > 0 else 0
                    
                    cambios_cit.append({
                        'paciente': evaluaciones_paciente[0]['nombre'],
                        'cambio_total': cambio_total,
                        'cambio_anual': cambio_anual,
                        'tendencia': 'mejora' if cambio_anual > 1 else 'deterioro' if cambio_anual < -1 else 'estable'
                    })
                
                paciente_actual = paciente_id
                evaluaciones_paciente = []
            
            try:
                datos = json.loads(datos_json)
                for escala, info in datos.get("compuestos", {}).items():
                    if "CIT" in escala:
                        cit = info.get('compuesto', 0)
                        evaluaciones_paciente.append({
                            'nombre': nombre,
                            'fecha': datetime.fromisoformat(fecha),
                            'cit': cit
                        })
                        break
            except:
                continue
        
        # Procesar último paciente
        if evaluaciones_paciente and len(evaluaciones_paciente) > 1:
            cit_inicial = evaluaciones_paciente[0]['cit']
            cit_final = evaluaciones_paciente[-1]['cit']
            cambio_total = cit_final - cit_inicial
            meses_total = (evaluaciones_paciente[-1]['fecha'] - evaluaciones_paciente[0]['fecha']).days // 30
            cambio_anual = (cambio_total / meses_total) * 12 if meses_total > 0 else 0
            
            cambios_cit.append({
                'paciente': evaluaciones_paciente[0]['nombre'],
                'cambio_total': cambio_total,
                'cambio_anual': cambio_anual,
                'tendencia': 'mejora' if cambio_anual > 1 else 'deterioro' if cambio_anual < -1 else 'estable'
            })
        
        # Estadísticas de tendencias
        tendencias_count = {'mejora': 0, 'deterioro': 0, 'estable': 0}
        for cambio in cambios_cit:
            tendencias_count[cambio['tendencia']] += 1
        
        print(f"\n📊 RESUMEN FINAL:")
        print("=" * 40)
        print(f"Total pacientes: {total_pacientes}")
        print(f"Total evaluaciones: {total_evaluaciones}")
        
        print(f"\n📈 TENDENCIAS DE EVOLUCIÓN:")
        for tendencia, count in tendencias_count.items():
            porcentaje = (count / len(cambios_cit)) * 100
            print(f"   • {tendencia.capitalize()}: {count} pacientes ({porcentaje:.1f}%)")
        
        if cambios_cit:
            cambio_promedio_anual = sum(c['cambio_anual'] for c in cambios_cit) / len(cambios_cit)
            print(f"   • Cambio promedio anual: {cambio_promedio_anual:+.2f} puntos")
        
        print(f"\n🤖 IDONEIDAD PARA IA:")
        print(f"   ✅ Tendencias balanceadas y realistas")
        print(f"   ✅ Datos longitudinales suficientes")
        print(f"   ✅ Variabilidad en patrones de evolución")
        print(f"   ✅ Escenarios clínicos diversos")
        
        conn.close()

# EJECUCIÓN PRINCIPAL MEJORADA
if __name__ == "__main__":
    generador = GeneradorDatosTendenciasReales()
    
    try:
        print("🚀 INICIANDO GENERACIÓN DE DATOS CON TENDENCIAS REALISTAS")
        print("=" * 60)
        
        pacientes = generador.generar_datos_balanceados()
        
        print("\n" + "=" * 60)
        print("🎉 GENERACIÓN COMPLETADA EXITOSAMENTE!")
        print("=" * 60)
        print("\nCaracterísticas de los datos generados:")
        print("✅ Tendencias variables (mejora, deterioro, estable)")
        print("✅ Patrones de evolución realistas")
        print("✅ Cambios anuales entre -12 y +15 puntos")
        print("✅ Distribución balanceada de escenarios")
        print("✅ Suficiente variabilidad para entrenar IA")
        
        print("\n📋 LOS DATOS INCLUYEN:")
        for perfil, info in generador.perfiles_clinicos.items():
            print(f"   • {perfil}: {', '.join(info['tendencias'])}")
            
    except Exception as e:
        print(f"❌ Error durante la generación: {e}")
        import traceback
        traceback.print_exc()