import random
import os
import time

class JuegoCasaEncantada:
    def __init__(self):
        # Inicializar el tablero de 4x4
        self.filas = 4
        self.columnas = 4
        self.casa = [[' ' for _ in range(self.columnas)] for _ in range(self.filas)]
        
        # Generar posiciones aleatorias para los elementos (diferentes entre sí)
        posiciones = random.sample(range(16), 4)  # 4 posiciones únicas (jugador, dulce, puerta, fantasma)
        
        # Convertir índices lineales a coordenadas (fila, columna)
        self.pos_jugador = (posiciones[0] // self.columnas, posiciones[0] % self.columnas)
        self.pos_dulce = (posiciones[1] // self.columnas, posiciones[1] % self.columnas)
        self.pos_puerta = (posiciones[2] // self.columnas, posiciones[2] % self.columnas)
        self.pos_fantasma = (posiciones[3] // self.columnas, posiciones[3] % self.columnas)
        
        # Estado del juego
        self.dulce_encontrado = False
        self.juego_terminado = False
        self.mensaje = "¡Bienvenido! Encuentra el dulce y luego la puerta de salida. ¡Cuidado con el fantasma!"
        
        # Preguntas y respuestas
        self.preguntas = [
            {"pregunta": "¿Cuánto es 5 + 3?", "respuesta": "8"},
            {"pregunta": "¿Cuál es la capital de Francia?", "respuesta": "paris"},
            {"pregunta": "¿Cuántos días tiene una semana?", "respuesta": "7"},
            {"pregunta": "¿Cuánto es 10 - 4?", "respuesta": "6"},
            {"pregunta": "¿De qué color es el cielo en un día despejado?", "respuesta": "azul"},
            {"pregunta": "¿Cuántos dedos tiene una mano?", "respuesta": "5"},
            {"pregunta": "¿Cuál es el resultado de 3 x 4?", "respuesta": "12"},
            {"pregunta": "¿Cuál es el animal que hace 'guau'?", "respuesta": "perro"},
            {"pregunta": "¿Cuánto es 20 dividido entre 4?", "respuesta": "5"},
            {"pregunta": "¿Qué mes viene después de marzo?", "respuesta": "abril"}
        ]
    
    def limpiar_pantalla(self):
        """Limpia la pantalla de la consola"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def dibujar_casa(self):
        """Dibuja el estado actual de la casa"""
        self.limpiar_pantalla()
        print("\n🏠 CASA ENCANTADA 🏠\n")
        print("  " + " ".join([f"{i}" for i in range(self.columnas)]))
        
        for i in range(self.filas):
            fila = f"{i} "
            for j in range(self.columnas):
                if (i, j) == self.pos_jugador:
                    fila += "🧍" + " "  # Jugador
                elif (i, j) == self.pos_dulce and self.dulce_encontrado:
                    fila += "🍬" + " "  # Dulce visible si ya fue encontrado
                elif (i, j) == self.pos_puerta and self.juego_terminado and self.dulce_encontrado:
                    fila += "🚪" + " "  # Puerta visible si el juego terminó con victoria
                elif (i, j) == self.pos_fantasma and self.juego_terminado and not self.dulce_encontrado:
                    fila += "👻" + " "  # Fantasma visible si el juego terminó con derrota
                else:
                    fila += "⬜" + " "  # Casilla vacía
            print(fila)
        
        # Mensaje de estado
        print("\n" + self.mensaje)
        
        # Instrucciones
        if not self.juego_terminado:
            print("\nControles: N (Norte), S (Sur), E (Este), O (Oeste), Q (Salir)")
            if self.dulce_encontrado:
                print("¡Has encontrado el dulce! Ahora busca la puerta de salida.")
    
    def hacer_pregunta(self):
        """Hace una pregunta aleatoria y verifica la respuesta"""
        pregunta = random.choice(self.preguntas)
        print("\n" + pregunta["pregunta"])
        respuesta = input("Tu respuesta: ").strip().lower()
        return respuesta == pregunta["respuesta"].lower()
    
    def mover_jugador(self, direccion):
        """Intenta mover al jugador en la dirección indicada"""
        nueva_fila, nueva_columna = self.pos_jugador
        
        if direccion == 'n' and nueva_fila > 0:
            nueva_fila -= 1
        elif direccion == 's' and nueva_fila < self.filas - 1:
            nueva_fila += 1
        elif direccion == 'e' and nueva_columna < self.columnas - 1:
            nueva_columna += 1
        elif direccion == 'o' and nueva_columna > 0:
            nueva_columna -= 1
        else:
            self.mensaje = "¡No puedes moverte en esa dirección! Estás en el límite de la casa."
            return
        
        # Hacer una pregunta antes de permitir el movimiento
        print(f"\nPara moverte hacia {direccion.upper()}, responde:")
        if self.hacer_pregunta():
            self.pos_jugador = (nueva_fila, nueva_columna)
            self.mensaje = "¡Respuesta correcta! Te has movido."
            self.verificar_encuentros()
        else:
            self.mensaje = "Respuesta incorrecta. No puedes moverte."
    
    def verificar_encuentros(self):
        """Verifica si el jugador ha encontrado algo"""
        if self.pos_jugador == self.pos_dulce and not self.dulce_encontrado:
            self.dulce_encontrado = True
            self.mensaje = "¡Has encontrado un dulce! 🍬 Ahora busca la puerta de salida."
        
        elif self.pos_jugador == self.pos_puerta and self.dulce_encontrado:
            self.juego_terminado = True
            self.mensaje = "¡VICTORIA! 🎉 Has encontrado la puerta de salida con el dulce."
        
        elif self.pos_jugador == self.pos_fantasma:
            self.juego_terminado = True
            self.mensaje = "¡OH NO! 👻 Te has encontrado con el fantasma. GAME OVER."
    
    def jugar(self):
        """Inicia el ciclo principal del juego"""
        while not self.juego_terminado:
            self.dibujar_casa()
            
            # Solicitar movimiento
            movimiento = input("\n¿A dónde quieres moverte? ").strip().lower()
            
            if movimiento == 'q':
                print("¡Gracias por jugar!")
                break
            
            if movimiento in ['n', 's', 'e', 'o']:
                self.mover_jugador(movimiento)
            else:
                self.mensaje = "Movimiento no válido. Usa N, S, E, O o Q para salir."
            
            # Pequeña pausa para mejor experiencia
            time.sleep(0.5)
        
        # Mostrar estado final
        self.dibujar_casa()
        if self.juego_terminado:
            print("\n¿Quieres jugar de nuevo? (s/n)")
            if input().strip().lower() == 's':
                self.__init__()
                self.jugar()
            else:
                print("¡Gracias por jugar!")

# Iniciar el juego
if __name__ == "__main__":
    juego = JuegoCasaEncantada()
    juego.jugar()