import os
import time
import json
from pathlib import Path
import pygame
from openai import OpenAI
from constants import WIDTH, HEIGHT, ASSETS, OA_API_KEY

# Use pygbag.net for browser-compatible requests
try:
    import pygbag.net as net
except ImportError:
    net = None

class BackgroundGenerator:
    def __init__(self):
        self.api_key = OA_API_KEY
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        self.backgrounds_dir = ASSETS / "backgrounds"
        self._ensure_dir_exists()
        
    def _ensure_dir_exists(self):
        """Ensure the backgrounds directory exists"""
        if not self.backgrounds_dir.exists():
            self.backgrounds_dir.mkdir(parents=True, exist_ok=True)
            
    def generate_background(self, prompt_text):
        """Generate background image using DALL-E 3 API"""
        if not self.client:
            print("No OpenAI API key found in environment variables. Using default background.")
            return None
            
        # Create a more detailed prompt for better results
        # Solicitar una imagen más ancha (2560x1024) para tener más contenido visual y menos problemas de costuras
        dimension_prompt = f"Create a super wide panoramic game background showing {prompt_text}. " \
                         f"Make it a beautiful wide-format illustration (at least 2:1 aspect ratio, wider than tall). " \
                         f"The scene must be a continuous horizontal landscape with rich detail throughout. " \
                         f"Drawn in a gorgeous pixel art or digital art style with vibrant colors. " \
                         f"Perfect for a side-scrolling space game with a train. Make it impressive and epic in scale. The image must be 1792x1024"
                         
        try:
            # Generate unique filename based on the prompt
            filename = f"bg_{int(time.time())}.png"
            file_path = self.backgrounds_dir / filename
            
            # Check if we've already generated something similar to avoid duplicate calls
            if self._check_existing_background(prompt_text):
                return self._check_existing_background(prompt_text)
            
            print(f"Generating background with DALL-E 3 using prompt: {dimension_prompt}")
            
            # Call OpenAI API
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=dimension_prompt,
                size="1792x1024",  # DALL-E 3 supports 1792x1024 wide format
                quality="standard",
                n=1,
            )
            
            # Get the image URL
            image_url = response.data[0].url
            
            # Download the image
            if net:
                # Use pygbag.net for browser
                image_response = net.get(image_url)
                if hasattr(image_response, 'content'):
                    content = image_response.content
                else:
                    content = image_response.read()
                status_code = getattr(image_response, 'status_code', 200)
            else:
                import requests
                image_response = requests.get(image_url)
                content = image_response.content
                status_code = image_response.status_code
            if status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                # Save prompt to metadata file for future reference
                metadata_path = file_path.with_suffix('.json')
                with open(metadata_path, 'w') as f:
                    json.dump({"prompt": prompt_text, "full_prompt": dimension_prompt}, f)
                    
                print(f"Background generated and saved to {file_path}")
                return file_path
            else:
                print(f"Failed to download image: {status_code}")
                return None
                
        except Exception as e:
            print(f"Error generating background: {e}")
            return None
    
    def _check_existing_background(self, prompt_text):
        """Check if we already have a similar background"""
        if not self.backgrounds_dir.exists():
            return None
            
        for metadata_file in self.backgrounds_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    # If prompt is similar, return the corresponding image
                    if prompt_text.lower() in metadata.get("prompt", "").lower():
                        image_path = metadata_file.with_suffix('.png')
                        if image_path.exists():
                            return image_path
            except:
                continue
                
        return None
        
    def load_default_background(self):
        """Load a default background if DALL-E generation fails"""
        default_bg_path = ASSETS / "backgrounds" / "default_bg.png"
        
        # Create a simple default background if it doesn't exist
        if not default_bg_path.exists():
            self._create_default_background(default_bg_path)
            
        return default_bg_path
        
    def _create_default_background(self, path):
        """Create a simple starfield background"""
        self._ensure_dir_exists()
        
        # Create a pygame surface and save it
        bg = pygame.Surface((WIDTH, HEIGHT))
        bg.fill((10, 10, 30))  # Dark blue/purple space color
        
        # Add some stars
        for _ in range(200):
            x = pygame.Rect(0, 0, WIDTH, HEIGHT).width * pygame.math.Vector2.random().x
            y = pygame.Rect(0, 0, WIDTH, HEIGHT).height * pygame.math.Vector2.random().y
            radius = pygame.math.Vector2.random().x * 2
            brightness = 128 + int(pygame.math.Vector2.random().x * 127)
            color = (brightness, brightness, brightness)
            pygame.draw.circle(bg, color, (x, y), radius)
            
        # Save the surface as an image
        pygame.image.save(bg, str(path))
        print(f"Created default background at {path}")
