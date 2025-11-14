#!/usr/bin/env python3
"""
Script de depuración del conversor WISC-V
"""

import sys
import os

# Agregar el directorio actual al path para importar nuestros módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.converter import ConversorWISCV

def debug_conversor():
    """Depura paso a paso el conversor"""
    print("🔍 DEPURANDO CONVERSOR WISC-V")
    print("=" * 60)
    
    # Crear instancia del conversor
    conversor = ConversorWISCV()
    
    # Test caso específico que debería funcionar
    edad = "8:6"
    subprueba = "CC"
    puntaje_bruto = 25
    
    print(f"📝 Test case: {edad} | {subprueba} | {puntaje_bruto}")
    print()
    
    # Paso 1: Obtener grupo etario
    try:
        grupo_etario = conversor.obtener_grupo_etario(edad)
        print(f"✅ Grupo etario: {grupo_etario}")
    except Exception as e:
        print(f"❌ Error grupo etario: {e}")
        return
    
    # Paso 2: Verificar si el grupo existe
    if grupo_etario in conversor.tablas:
        print(f"✅ Grupo encontrado en tablas")
        print(f"   Subpruebas disponibles en este grupo: {list(conversor.tablas[grupo_etario].keys())}")
    else:
        print(f"❌ Grupo NO encontrado. Grupos disponibles: {list(conversor.tablas.keys())}")
        return
    
    # Paso 3: Verificar subprueba
    if subprueba in conversor.tablas[grupo_etario]:
        print(f"✅ Subprueba '{subprueba}' encontrada")
        tabla_subprueba = conversor.tablas[grupo_etario][subprueba]
        print(f"   Tabla completa: {tabla_subprueba}")
    else:
        print(f"❌ Subprueba NO encontrada. Subpruebas disponibles: {list(conversor.tablas[grupo_etario].keys())}")
        return
    
    # Paso 4: Probar conversión directa
    print()
    print("🎯 PROBANDO CONVERSIÓN DIRECTA:")
    try:
        resultado = conversor.convertir_puntaje(edad, subprueba, puntaje_bruto)
        print(f"✅ RESULTADO: {puntaje_bruto} → {resultado}")
    except Exception as e:
        print(f"❌ Error en conversión: {e}")
        import traceback
        traceback.print_exc()
    
    # Paso 5: Probar múltiples casos
    print()
    print("🧪 TEST MULTIPLES CASOS:")
    test_cases = [
        ("8:6", "CC", 25),
        ("8:6", "BAL", 29),
        ("8:6", "AN", 12),
        ("8:6", "MR", 12),
    ]
    
    for test_edad, test_subprueba, test_bruto in test_cases:
        try:
            resultado = conversor.convertir_puntaje(test_edad, test_subprueba, test_bruto)
            print(f"✅ {test_edad} | {test_subprueba}: {test_bruto} → {resultado}")
        except Exception as e:
            print(f"❌ {test_edad} | {test_subprueba}: {test_bruto} → ERROR: {e}")

if __name__ == "__main__":
    debug_conversor()