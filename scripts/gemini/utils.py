# utils.py

import os
import logging
from PIL import ImageFont, ImageDraw
from typing import Tuple, List
import sys 

from constants import FONT_PATHS, SYSTEM_AND_HIDDEN_FOLDERS

logger = logging.getLogger(__name__)

def setup_logging(level=logging.INFO):
    """Konfigurerar loggning för applikationen."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def _load_font(font_path: str, font_size: int):
    """Försök ladda en TrueType font, fall tillbaka till default vid fel."""
    try:
        return ImageFont.truetype(font_path, font_size)
    except (OSError, IOError):
        logger.debug(f"Kunde inte ladda font: {font_path}")
        return None
    except Exception as e:
        logger.warning(f"Oväntat fel vid laddning av font '{font_path}': {e}")
        return None

def get_preferred_font(font_size: int):
    """Försök hitta och ladda en lämplig systemfont från kända sökvägar."""
    for font_path in FONT_PATHS:
        font = _load_font(font_path, font_size)
        if font:
            return font
            
    logger.warning("Ingen specifik font hittades från kända sökvägar, använder standardfont.")
    return ImageFont.load_default()

def get_text_size_global(text: str, font: ImageFont.FreeTypeFont, draw_obj: ImageDraw.ImageDraw) -> Tuple[int, int]:
    """Helper för att få text-dimensioner kompatibelt med olika PIL versioner."""
    try:
        bbox = draw_obj.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        # Fallback för äldre PIL-versioner som använder textsize
        logger.debug("Använder deprecated draw.textsize(), uppgradera Pillow.")
        return draw_obj.textsize(text, font=font)

def is_system_or_hidden_folder(folder_name: str) -> bool:
    """Kontrollerar om ett mappnamn är en känd systemmapp eller dold."""
    if folder_name in SYSTEM_AND_HIDDEN_FOLDERS:
        return True
    if folder_name.startswith('.'):
        return True
    return False

def draw_wrapped_text(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, max_width: int, font: ImageFont.FreeTypeFont, color: str = "black", line_spacing: float = 1.2) -> int:
    """
    Rita text med automatisk radbrytning.
    Returnerar den nya Y-positionen efter att texten har ritats.
    """
    words = text.split(' ')
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        # Mät bredden på den potentiella raden
        test_bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = test_bbox[2] - test_bbox[0]
        
        if line_width <= max_width:
            current_line.append(word)
        else:
            # Om den nya raden är för lång, lägg till den nuvarande ackumulerade raden
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word] # Starta en ny rad med det aktuella ordet
            else:
                # Om ett enskilt ord är längre än max_width, lägg till det ändå (bryts inte ord)
                lines.append(word)
                current_line = []
    
    if current_line:
        lines.append(' '.join(current_line))
    
    current_y = y
    for line in lines:
        draw.text((x, current_y), line, font=font, fill=color)
        line_bbox = draw.textbbox((0, 0), line, font=font)
        line_height = line_bbox[3] - line_bbox[1]
        current_y += int(line_height * line_spacing)
    
    return current_y

def format_bytes(size_bytes: int) -> str:
    """Formaterar bytes till en läsbar sträng (t.ex. KB, MB, GB, TB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes / (1024**2):.2f} MB"
    elif size_bytes < 1024**4:
        return f"{size_bytes / (1024**3):.2f} GB"
    else:
        return f"{size_bytes / (1024**4):.2f} TB"