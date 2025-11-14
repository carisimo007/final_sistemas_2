"""
ANALIZADOR DE TENDENCIAS GENERADAS
Verifica que las tendencias sean diversas y realistas
"""
import sqlite3
import json
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

class AnalizadorTendencias:
    def __init__(self, db_path="wisc_v_database.db"):
        self.db_path = db_path

    def analizar_tendencias_cit(self):
        """Analiza las tendencias del CIT en todos los pacientes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("📊 ANALIZANDO TENDENCIAS DE EVOLUCIÓN DEL CIT")
        print("=" * 50)
        
        # Obtener todos los pacientes con sus evaluaciones
        cursor.execute('''
            SELECT p.id, p.nombre, p.notas, e.fecha_evaluacion, e.datos_evaluacion
            FROM pacientes p
            JOIN evaluaciones e ON p.id = e.paciente_id
            ORDER BY p.id, e.fecha_evaluacion
        ''')
        
        datos = cursor.fetchall()
        
        pacientes_tendencias = {}
        paciente_actual = None
        evaluaciones_actual = []
        
        for paciente_id, nombre, notas, fecha, datos_json in datos:
            if paciente_id != paciente_actual:
                if evaluaciones_actual:
                    pacientes_tendencias[paciente_actual] = {
                        'nombre': evaluaciones_actual[0]['nombre'],
                        'notas': evaluaciones_actual[0]['notas'],
                        'evaluaciones': evaluaciones_actual.copy()
                    }
                paciente_actual = paciente_id
                evaluaciones_actual = []
            
            try:
                datos_eval = json.loads(datos_json)
                for escala, info in datos_eval.get("compuestos", {}).items():
                    if "CIT" in escala:
                        cit = info.get('compuesto', 0)
                        evaluaciones_actual.append({
                            'nombre': nombre,
                            'notas': notas,
                            'fecha': datetime.fromisoformat(fecha),
                            'cit': cit
                        })
                        break
            except:
                continue
        
        # Procesar último paciente
        if evaluaciones_actual:
            pacientes_tendencias[paciente_actual] = {
                'nombre': evaluaciones_actual[0]['nombre'],
                'notas': evaluaciones_actual[0]['notas'],
                'evaluaciones': evaluaciones_actual.copy()
            }
        
        # Analizar tendencias
        categorias_tendencia = {
            'Mejora significativa': 0,    # > +5 puntos/año
            'Mejora moderada': 0,         # +2 a +5 puntos/año
            'Mejora leve': 0,             # +0.5 a +2 puntos/año
            'Estable': 0,                 # -0.5 a +0.5 puntos/año
            'Deterioro leve': 0,          # -2 a -0.5 puntos/año
            'Deterioro moderado': 0,      # -5 a -2 puntos/año
            'Deterioro significativo': 0  # < -5 puntos/año
        }
        
        cambios_anuales = []
        
        print("\n📈 EVOLUCIÓN POR PACIENTE:")
        print("-" * 60)
        
        for paciente_id, info in pacientes_tendencias.items():
            if len(info['evaluaciones']) >= 2:
                evaluaciones_ordenadas = sorted(info['evaluaciones'], key=lambda x: x['fecha'])
                cit_inicial = evaluaciones_ordenadas[0]['cit']
                cit_final = evaluaciones_ordenadas[-1]['cit']
                
                tiempo_total = (evaluaciones_ordenadas[-1]['fecha'] - evaluaciones_ordenadas[0]['fecha']).days / 365.25
                cambio_anual = (cit_final - cit_inicial) / tiempo_total if tiempo_total > 0 else 0
                
                cambios_anuales.append(cambio_anual)
                
                # Clasificar tendencia
                if cambio_anual > 5:
                    categoria = 'Mejora significativa'
                elif cambio_anual > 2:
                    categoria = 'Mejora moderada'
                elif cambio_anual > 0.5:
                    categoria = 'Mejora leve'
                elif cambio_anual > -0.5:
                    categoria = 'Estable'
                elif cambio_anual > -2:
                    categoria = 'Deterioro leve'
                elif cambio_anual > -5:
                    categoria = 'Deterioro moderado'
                else:
                    categoria = 'Deterioro significativo'
                
                categorias_tendencia[categoria] += 1
                
                print(f"👤 {info['nombre'][:20]:20} | CIT: {cit_inicial:.0f} → {cit_final:.0f} | "
                      f"Cambio anual: {cambio_anual:+.1f} | {categoria}")
        
        # Estadísticas generales
        if cambios_anuales:
            print(f"\n📊 ESTADÍSTICAS GENERALES:")
            print(f"   • Pacientes analizados: {len(cambios_anuales)}")
            print(f"   • Cambio anual promedio: {np.mean(cambios_anuales):+.2f} puntos")
            print(f"   • Desviación estándar: {np.std(cambios_anuales):.2f} puntos")
            print(f"   • Rango: {min(cambios_anuales):+.1f} a {max(cambios_anuales):+.1f} puntos/año")
            
            print(f"\n🎯 DISTRIBUCIÓN DE TENDENCIAS:")
            for categoria, count in categorias_tendencia.items():
                if count > 0:
                    porcentaje = (count / len(cambios_anuales)) * 100
                    print(f"   • {categoria}: {count} pacientes ({porcentaje:.1f}%)")
        
        conn.close()
        return cambios_anuales, categorias_tendencia

    def graficar_tendencias(self, cambios_anuales, categorias_tendencia):
        """Genera gráficas de las tendencias"""
        if not cambios_anuales:
            print("❌ No hay datos para graficar")
            return
        
        # Gráfica 1: Distribución de cambios anuales
        plt.figure(figsize=(12, 5))
        
        plt.subplot(1, 2, 1)
        plt.hist(cambios_anuales, bins=15, alpha=0.7, color='skyblue', edgecolor='black')
        plt.axvline(np.mean(cambios_anuales), color='red', linestyle='--', label=f'Promedio: {np.mean(cambios_anuales):+.2f}')
        plt.xlabel('Cambio anual en CIT (puntos)')
        plt.ylabel('Número de pacientes')
        plt.title('Distribución de Cambios Anuales en CIT')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Gráfica 2: Proporción de tendencias
        plt.subplot(1, 2, 2)
        categorias = [k for k, v in categorias_tendencia.items() if v > 0]
        valores = [v for k, v in categorias_tendencia.items() if v > 0]
        
        colores = ['#2ecc71', '#27ae60', '#3498db', '#f39c12', '#e67e22', '#e74c3c', '#c0392b']
        colores = colores[:len(categorias)]
        
        plt.pie(valores, labels=categorias, autopct='%1.1f%%', colors=colores, startangle=90)
        plt.title('Proporción de Tendencias de Evolución')
        
        plt.tight_layout()
        plt.show()

# EJECUCIÓN DEL ANALIZADOR
if __name__ == "__main__":
    analizador = AnalizadorTendencias()
    
    cambios, categorias = analizador.analizar_tendencias_cit()
    
    if cambios:
        analizador.graficar_tendencias(cambios, categorias)
        
        # Evaluar balance
        total = sum(categorias.values())
        mejora = sum(v for k, v in categorias.items() if 'Mejora' in k)
        deterioro = sum(v for k, v in categorias.items() if 'Deterioro' in k)
        estable = categorias['Estable']
        
        print(f"\n⚖️  BALANCE DE TENDENCIAS:")
        print(f"   • Mejora: {mejora}/{total} ({mejora/total*100:.1f}%)")
        print(f"   • Estable: {estable}/{total} ({estable/total*100:.1f}%)")
        print(f"   • Deterioro: {deterioro}/{total} ({deterioro/total*100:.1f}%)")
        
        # Verificar si está balanceado
        if 0.25 <= mejora/total <= 0.45 and 0.25 <= deterioro/total <= 0.45:
            print("✅ DISTRIBUCIÓN BALANCEADA - Ideal para IA")
        else:
            print("⚠️  Distribución desbalanceada - Considerar regenerar datos")