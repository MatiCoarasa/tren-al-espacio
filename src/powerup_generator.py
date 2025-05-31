import os
import random
import json
from openai import OpenAI
from constants import USE_OPENAI_API, OA_API_KEY

class PowerupGenerator:
    """Genera powerups dinámicos basados en el prompt/dimensión del usuario"""
    
    DEFAULT_POWERUPS = [
        {
            "id": "triple_shot",
            "name": "Triple Disparo",
            "description": "Dispara 3 proyectiles a la vez",
            "duration": 10,
            "color": (255, 100, 100),
            "effect": "bullet_count",
            "value": 3
        },
        {
            "id": "speed_boost",
            "name": "Velocidad",
            "description": "Aumenta la velocidad del tren",
            "duration": 15,
            "color": (100, 255, 100),
            "effect": "player_speed",
            "value": 2.0
        },
        {
            "id": "shield",
            "name": "Escudo",
            "description": "Protege contra impactos",
            "duration": 8,
            "color": (100, 100, 255),
            "effect": "shield",
            "value": True
        },
        {
            "id": "rapid_fire",
            "name": "Disparo Rápido",
            "description": "Reduce el tiempo entre disparos",
            "duration": 12,
            "color": (255, 255, 100),
            "effect": "fire_rate",
            "value": 0.5
        },
        {
            "id": "points_multiplier",
            "name": "Multiplicador",
            "description": "x2 puntos por enemigo",
            "duration": 10,
            "color": (255, 100, 255),
            "effect": "score_multiplier",
            "value": 2
        }
    ]
    
    def __init__(self):
        # Inicializar cliente de OpenAI si está habilitado
        self.api_key = None
        self.client = None
        
        if USE_OPENAI_API:
            # Intentar obtener API key (primero de variables de entorno, luego hardcodeada)
            self.api_key = OA_API_KEY
            self.client = OpenAI(api_key=self.api_key)
        
        self.dimension = ""
        self.custom_powerups = []
        self.available_powerups = self.DEFAULT_POWERUPS.copy()
        
    def set_dimension(self, dimension_text):
        """Establece la dimensión y genera powerups temáticos"""
        self.dimension = dimension_text
        
        # Si no hay API o no está habilitada, usar powerups por defecto
        if not USE_OPENAI_API or not self.client:
            print("Usando powerups por defecto (OpenAI API no configurada)")
            return
            
        # Generar powerups personalizados basados en la dimensión
        try:
            self._generate_themed_powerups()
        except Exception as e:
            print(f"Error generando powerups: {e}")
    
    def _generate_themed_powerups(self):
        """Genera powerups personalizados usando OpenAI API basados en la dimensión"""
        if not self.client:
            return
            
        prompt = f"""
        Genera 3 powerups temáticos para un juego de disparos espacial ambientado en "{self.dimension}".
        
        Cada powerup debe incluir:
        1. Un ID único (snake_case)
        2. Un nombre corto (máximo 12 caracteres)
        3. Una descripción breve (máximo 30 caracteres)
        4. Duración en segundos (entre 5 y 15)
        5. Un color RGB representativo (valores entre 0-255)
        6. Un efecto (uno de: "bullet_count", "player_speed", "shield", "fire_rate", "score_multiplier", "bullet_size", "invincibility")
        7. Un valor numérico para el efecto
        
        Devuelve SOLO un array JSON con los 3 powerups sin ninguna explicación adicional.
        Ejemplo:
        [
          {{
            "id": "frost_beam",
            "name": "Rayo de Hielo",
            "description": "Congela a los enemigos",
            "duration": 8,
            "color": [150, 220, 255],
            "effect": "bullet_size",
            "value": 2.5
          }},
          ...
        ]
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un generador de powerups para videojuegos. Responde únicamente con JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            
            # Extraer solo el JSON (por si acaso incluye texto adicional)
            import re
            json_match = re.search(r'(\[\s*{.*}\s*\])', result, re.DOTALL)
            if json_match:
                result = json_match.group(1)
            
            # Parsear los powerups generados
            generated_powerups = json.loads(result)
            
            # Formatear y validar los powerups generados
            self.custom_powerups = []
            for p in generated_powerups:
                # Convertir color si viene como lista a tupla
                if isinstance(p.get("color"), list):
                    p["color"] = tuple(p["color"])
                
                # Validar efectos
                valid_effects = ["bullet_count", "player_speed", "shield", "fire_rate", 
                                "score_multiplier", "bullet_size", "invincibility"]
                if p.get("effect") not in valid_effects:
                    p["effect"] = random.choice(valid_effects)
                
                # Asegurar que los valores son correctos
                if p["effect"] == "shield" or p["effect"] == "invincibility":
                    p["value"] = True
                elif not isinstance(p.get("value"), (int, float)) or p.get("value") <= 0:
                    p["value"] = random.uniform(1.5, 3.0) if p["effect"] in ["player_speed", "bullet_size"] else random.randint(2, 4)
                
                # Limitar duración
                p["duration"] = max(5, min(15, p.get("duration", 10)))
                
                self.custom_powerups.append(p)
            
            print(f"Generados {len(self.custom_powerups)} powerups temáticos para {self.dimension}")
            
            # Combinar con algunos powerups por defecto
            self.available_powerups = self.custom_powerups + random.sample(self.DEFAULT_POWERUPS, 2)
            
        except Exception as e:
            print(f"Error generando powerups temáticos: {e}")
            self.available_powerups = self.DEFAULT_POWERUPS.copy()
    
    def get_random_powerup(self):
        """Devuelve un powerup aleatorio de los disponibles"""
        return random.choice(self.available_powerups)
