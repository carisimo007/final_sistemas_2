"""
Interfaz gráfica principal de la aplicación WISC-V
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from core.converter import conversor

class WiscVApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WISC-V - Sistema de Evaluación Psicológica")
        self.root.geometry("1000x800")
        self.root.configure(bg='#f0f0f0')
        
        self.crear_interfaz()
    
    def crear_interfaz(self):
        """Crea todos los elementos de la interfaz"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        titulo = tk.Label(main_frame, 
                         text="WISC-V - Sistema de Evaluación Psicológica", 
                         font=("Arial", 18, "bold"),
                         foreground="#2c3e50",
                         bg='#f0f0f0')
        titulo.grid(row=0, column=0, columnspan=6, pady=(0, 30))
        
        # ========== DATOS DEL PACIENTE ==========
        paciente_frame = ttk.LabelFrame(main_frame, text="📋 Datos del Paciente", padding="15")
        paciente_frame.grid(row=1, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Título interno con estilo
        titulo_paciente = tk.Label(paciente_frame, 
                                  text="Datos del Paciente",
                                  font=("Arial", 12, "bold"),
                                  foreground="#2c3e50",
                                  bg='#f0f0f0')
        titulo_paciente.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 15))
        
        # Nombre
        tk.Label(paciente_frame, text="Nombre completo:", 
                font=("Arial", 10),
                bg='#f0f0f0').grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.nombre_entry = ttk.Entry(paciente_frame, width=30, font=("Arial", 10))
        self.nombre_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 30))
        
        # Fecha de nacimiento
        tk.Label(paciente_frame, text="Fecha de Nacimiento (DD/MM/AAAA):", 
                font=("Arial", 10),
                bg='#f0f0f0').grid(row=1, column=2, sticky=tk.W, padx=(0, 10))
        
        # Frame para fecha
        fecha_frame = ttk.Frame(paciente_frame)
        fecha_frame.grid(row=1, column=3, sticky=tk.W)
        
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
                  command=self.calcular_edad_actual).grid(row=2, column=3, sticky=tk.W, pady=(10, 0))
        
        # Mostrar edad calculada
        tk.Label(paciente_frame, text="Edad calculada:", 
                font=("Arial", 10, "bold"),
                bg='#f0f0f0').grid(row=2, column=0, sticky=tk.W)
        self.edad_label = tk.Label(paciente_frame, text="", 
                                  foreground="#2980b9", 
                                  font=("Arial", 11, "bold"),
                                  bg='#f0f0f0')
        self.edad_label.grid(row=2, column=1, sticky=tk.W)
        
        # ========== PUNTAJES BRUTOS ==========
        puntajes_frame = ttk.LabelFrame(main_frame, text="📊 Ingreso de Puntajes Brutos", padding="15")
        puntajes_frame.grid(row=2, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=(0, 20))
        
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
        
        # ========== BOTONES ==========
        botones_frame = ttk.Frame(main_frame)
        botones_frame.grid(row=3, column=0, columnspan=6, pady=30)
        
        ttk.Button(botones_frame, text="🎯 Calcular Puntajes Escala", 
                  command=self.calcular_puntajes,
                  width=25).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(botones_frame, text="🔄 Limpiar Todo", 
                  command=self.limpiar_formulario,
                  width=15).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(botones_frame, text="💾 Guardar Evaluación", 
                  command=self.guardar_evaluacion,
                  width=18).pack(side=tk.LEFT)
        
        # Configurar expansión
        paciente_frame.columnconfigure(1, weight=1)
        puntajes_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
    
    def crear_tabla_puntajes(self, parent):
        """Crea la tabla para ingresar puntajes brutos"""
        # Lista completa de subpruebas organizadas
        subpruebas_columnas = [
            # Columna 1
            ["CC", "AN", "MR", "RD", "CLA"],
            # Columna 2  
            ["VOC", "BAL", "RV", "RI", "BS"],
            # Columna 3
            ["INF", "SLN", "CAN", "COM", "ARI"]
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
            "INF": "Información",
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
    
    def calcular_edad_actual(self):
        """Calcula la edad exacta en años, meses y días"""
        try:
            dia = self.dia_var.get().strip()
            mes = self.mes_var.get().strip()
            ano = self.ano_var.get().strip()
            
            # Validar que no estén vacíos
            if not dia or not mes or not ano:
                messagebox.showerror("Error", "Por favor completa todos los campos de fecha")
                return
                
            dia = int(dia)
            mes = int(mes) 
            ano = int(ano)
            
            # Validar fecha
            if not (1 <= dia <= 31) or not (1 <= mes <= 12) or not (1900 <= ano <= 2100):
                messagebox.showerror("Error", "Fecha inválida. Usa formato: DD/MM/AAAA")
                return
            
            fecha_nacimiento = date(ano, mes, dia)
            hoy = date.today()
            
            # Validar que la fecha no sea futura
            if fecha_nacimiento > hoy:
                messagebox.showerror("Error", "La fecha de nacimiento no puede ser futura")
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
                'edad_formato': f"{diferencia.years}:{diferencia.months}"
            }
            
            print(f"✅ Edad calculada: {edad_texto}")
            print(f"📅 Formato para conversión: {self.edad_calculada['edad_formato']}")
            
        except ValueError as e:
            messagebox.showerror("Error", "Fecha inválida. Usa formato numérico: DD/MM/AAAA")
        except Exception as e:
            messagebox.showerror("Error", f"Error al calcular edad: {e}")
    
    def calcular_puntajes(self):
        """Calcula y muestra los puntajes escala"""
        try:
            # Verificar que se calculó la edad
            if not hasattr(self, 'edad_calculada'):
                messagebox.showerror("Error", "Primero calcula la edad del paciente")
                return
            
            # Verificar que haya nombre
            nombre = self.nombre_entry.get().strip()
            if not nombre:
                messagebox.showerror("Error", "Por favor ingresa el nombre del paciente")
                return
            
            # Usar el formato de edad para búsqueda en tablas
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
                        
                        # CONVERSIÓN PRINCIPAL
                        puntaje_escala = conversor.convertir_puntaje(
                            edad_formato, subprueba, puntaje_bruto
                        )
                        print(f"✅ {subprueba}: {puntaje_bruto} → {puntaje_escala}")
                        
                        # Mostrar resultado en la interfaz
                        widgets["label"].config(text=f"{puntaje_escala}", foreground="#27ae60")
                        resultados[subprueba] = {
                            'bruto': puntaje_bruto,
                            'escala': puntaje_escala
                        }
                        subpruebas_calculadas += 1
                        
                    except ValueError as e:
                        error_msg = f"Puntaje inválido en {subprueba}: {puntaje_bruto_str}"
                        print(f"❌ {error_msg}")
                        widgets["label"].config(text="Inválido", foreground="#e74c3c")
                        errores.append(error_msg)
                    except Exception as e:
                        error_msg = f"Error en {subprueba}: {str(e)}"
                        print(f"❌ {error_msg}")
                        widgets["label"].config(text="Error", foreground="#e74c3c")
                        errores.append(error_msg)
            
            # Mostrar resumen
            if subpruebas_calculadas > 0:
                mensaje = f"✅ Puntajes calculados: {subpruebas_calculadas} subpruebas"
                if errores:
                    mensaje += f"\n⚠️ Errores: {len(errores)} subpruebas"
                messagebox.showinfo("Resultado", mensaje)
                print(f"🎯 Resultados finales: {resultados}")
            else:
                messagebox.showwarning("Advertencia", "No se ingresaron puntajes brutos válidos")
                
        except Exception as e:
            error_msg = f"Error general: {str(e)}"
            print(f"💥 {error_msg}")
            messagebox.showerror("Error", error_msg)
    
    def limpiar_formulario(self):
        """Limpia todos los campos del formulario"""
        self.nombre_entry.delete(0, tk.END)
        self.dia_var.set("")
        self.mes_var.set("")
        self.ano_var.set("")
        self.edad_label.config(text="")
        
        if hasattr(self, 'edad_calculada'):
            del self.edad_calculada
        
        for widgets in self.entries_puntajes.values():
            widgets["entry"].delete(0, tk.END)
            widgets["label"].config(text="")
        
        print("🔄 Formulario limpiado")
        messagebox.showinfo("Listo", "Formulario limpiado correctamente")
    
    def guardar_evaluacion(self):
        """Guarda la evaluación actual"""
        try:
            # Verificar datos mínimos
            if not hasattr(self, 'edad_calculada'):
                messagebox.showerror("Error", "Primero calcula la edad del paciente")
                return
                
            nombre = self.nombre_entry.get().strip()
            if not nombre:
                messagebox.showerror("Error", "Ingresa el nombre del paciente")
                return
            
            # Recolectar resultados
            resultados = {}
            for subprueba, widgets in self.entries_puntajes.items():
                texto_resultado = widgets["label"].cget("text")
                if texto_resultado and texto_resultado not in ["", "Inválido", "Error"]:
                    try:
                        resultados[subprueba] = int(texto_resultado)
                    except:
                        pass
            
            if not resultados:
                messagebox.showwarning("Advertencia", "No hay puntajes calculados para guardar")
                return
            
            # Por ahora solo mostramos preview
            preview = f"Paciente: {nombre}\n"
            preview += f"Edad: {self.edad_calculada['años']}a {self.edad_calculada['meses']}m {self.edad_calculada['días']}d\n"
            preview += f"Subpruebas: {len(resultados)}\n"
            preview += f"Resultados: {resultados}"
            
            messagebox.showinfo("💾 Guardar Evaluación", 
                              f"Función de guardado en desarrollo\n\nPreview:\n{preview}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")