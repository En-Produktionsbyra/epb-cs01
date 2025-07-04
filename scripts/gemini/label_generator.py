# label_generator.py (Uppdaterad för att hantera ALLA mappar)

import os
import qrcode
import logging
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Tuple
import sys
from datetime import datetime
import json

from constants import FONT_PATHS, LABEL_DPI, SYSTEM_AND_HIDDEN_FOLDERS, LABEL_WIDTH_MM, LABEL_HEIGHT_MM, MARGIN_MM, QR_SIZE_MM, HEADER_HEIGHT_MM
from utils import get_text_size_global, get_preferred_font, is_system_or_hidden_folder, draw_wrapped_text

logger = logging.getLogger(__name__)

# Kontrollera om label-stöd finns
try:
    import qrcode
    from PIL import Image, ImageDraw, ImageFont
    HAS_LABEL_SUPPORT = True
except ImportError:
    HAS_LABEL_SUPPORT = False
    logger.warning("⚠️ För label-generering: pip install qrcode[pil] pillow")

def simulate_customer_list_rendering(customer_folders: List[str], font: ImageFont.FreeTypeFont, draw_obj: ImageDraw.ImageDraw, line_spacing: float = 1.2) -> int:
    total_height = 0
    approx_line_height = draw_obj.textbbox((0, 0), "A", font=font)[3] - draw_obj.textbbox((0, 0), "A", font=font)[1]
    for folder in customer_folders:
        total_height += approx_line_height * line_spacing + 2
    return int(total_height)


def ask_for_customer_level(tree_structure: Dict) -> Tuple[int, List[str]]:
    """
    Frågar användaren vilken mappnivå som representerar kunder.
    Har nu ett alternativ för att välja ALLA mappar.
    """
    first_level_dirs = sorted([name for name, data in tree_structure.get('children', {}).items() if data.get('type') == 'directory'])

    if not first_level_dirs:
        logger.info("Inga underkataloger hittades på första nivån.")
        return 0, []

    logger.info("\n--- Kundmappar ---")
    logger.info("Följande mappar finns på diskens första nivå:")
    for i, folder in enumerate(first_level_dirs):
        logger.info(f"{i+1}. {folder}")

    # Variabel för att lagra användarens slutgiltiga val
    user_choice = None

    while True:
        # Uppdaterad fråga med alternativet 'A' för Alla
        choice_input = input("\nAnge numret för en mapp (t.ex. '1'), 'A' för ALLA mappar, eller '0' om ingen mapp är kundnivå: ").strip().upper()

        if choice_input == 'A':
            user_choice = 'ALL'
            break
        
        try:
            numeric_choice = int(choice_input)
            if 0 <= numeric_choice <= len(first_level_dirs):
                user_choice = numeric_choice
                break
            else:
                logger.warning("Ogiltigt nummer. Ange ett nummer från listan, 'A' eller '0'.")
        except ValueError:
            logger.warning("Ogiltig inmatning. Ange ett nummer från listan, 'A' eller '0'.")

    # Returnera resultat baserat på användarens val
    if user_choice == 'ALL':
        logger.info("Valde ALLA mappar som kundmappar.")
        return 1, first_level_dirs  # Returnera hela listan med mappar
    elif user_choice == 0:
        return 0, []
    else:
        # Returnera den enskilda mappen som valts
        return user_choice, [first_level_dirs[user_choice - 1]]


def generate_disk_label(disk_name: str, tree_data: Dict, output_file: str, disk_safe_name: str) -> Tuple[str, str]:
    """
    Genererar en fysisk etikett (QR-kod + text) för disken.
    Returnerar filnamnen för den skapade huvudetiketten och header-etiketten.
    """
    if not HAS_LABEL_SUPPORT:
        logger.warning("⚠️ Label-generering är inaktiverad på grund av saknade beroenden (qrcode[pil] pillow).")
        return None, None

    logger.info("🚀 Genererar fysisk etikett...")

    # QR-koddata qr_url = 
    qr_data = f"https://coldstorage.enproduktionsbyra.se/disks/{disk_safe_name}"

    # Skapa QR-kod
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=0,
    )   
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    logger.info("✅ QR-kod genererad.")

    # Etikettens dimensioner (A4 - 210x297 mm, för 300 DPI, ca 2480x3508 px, justerat för label)
    # Vår etikett är 100x70 mm @ 300 DPI = 1181 x 827 pixlar
    LABEL_WIDTH_PX = int(50 / 25.4 * LABEL_DPI)
    LABEL_HEIGHT_PX = int(80 / 25.4 * LABEL_DPI)
    
    img = Image.new('RGB', (LABEL_WIDTH_PX, LABEL_HEIGHT_PX), 'white')
    draw = ImageDraw.Draw(img)

    # Margins
    page_margin = 20
    
    # --- Centrerad rubrik högst upp (Disknamn) ---
    title_font_size = 60 # Stor initial fontstorlek
    title_font = get_preferred_font(title_font_size)
    
    # Skala disknamnsfont om den är för stor
    max_title_width = LABEL_WIDTH_PX - 2 * page_margin
    while title_font and get_text_size_global(disk_name, title_font, draw)[0] > max_title_width and title_font_size > 20:
        title_font_size -= 2
        title_font = get_preferred_font(title_font_size)

    if title_font is None:
        title_font = get_preferred_font(30) # Fallback
        logger.warning("⚠️ Använder fallback font för disknamn, kanske inte optimalt.")
        
    title_bbox = draw.textbbox((0, 0), disk_name, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]

    title_x = (LABEL_WIDTH_PX - title_width) // 2
    title_y = page_margin
    
    if title_font:
        draw.text((title_x, title_y), disk_name, fill='black', font=title_font)
        logger.info("✅ Huvudetikett disknamn placerat i mitten högst upp.")
    else:
        logger.error("❌ Kunde inte ladda någon font för disknamn.")

    current_y_after_title = title_y + title_height + page_margin # Start Y för kolumnerna

    # --- Två kolumner direkt under rubriken ---
    column_area_height = LABEL_HEIGHT_PX - current_y_after_title - page_margin
    
    # Vänster kolumn (2/3 bredd)
    left_column_width = int(LABEL_WIDTH_PX * (2/3)) - page_margin * 2 # Justera för padding
    left_column_x = page_margin
    
    # Höger kolumn (1/3 bredd)
    right_column_width = LABEL_WIDTH_PX - left_column_width - page_margin * 2
    right_column_x = left_column_x + left_column_width + page_margin * 2

    # --- Placera QR-kod (Höger kolumn) ---
    qr_target_size = min(int(LABEL_WIDTH_PX / 3), column_area_height) 
    qr_size_with_margin = qr_target_size - page_margin
    qr_x_in_column = right_column_x - page_margin + (right_column_width - qr_size_with_margin) // 2
    qr_y_in_column = current_y_after_title
    
    qr_img_resized = qr_img.resize((qr_size_with_margin, qr_size_with_margin), Image.Resampling.LANCZOS)
    img.paste(qr_img_resized, (qr_x_in_column, qr_y_in_column))
    logger.info("✅ QR-kod placerad i höger kolumn och linjerad med första kundposten.")

    # --- Kundlista (Vänster kolumn) ---
    customer_list_max_height = column_area_height
    customer_list_font_size = 200 # Initial font size

    customer_level, customer_folders = ask_for_customer_level(tree_data['tree'])
    
    customer_list_font = get_preferred_font(customer_list_font_size)
    
    if customer_folders:
        longest_display_text = ""
        for folder in customer_folders:
            display_text = folder
            if len(display_text) > len(longest_display_text):
                longest_display_text = display_text

        while customer_list_font and customer_list_font_size > 8:
            current_total_height = simulate_customer_list_rendering(customer_folders, customer_list_font, draw)
            current_max_folder_width = get_text_size_global(longest_display_text, customer_list_font, draw)[0]
            
            if current_total_height > customer_list_max_height or current_max_folder_width > left_column_width:
                logger.warning(f"⚠️ Fontstorlek {customer_list_font_size} för kundlista för stor. Minskar...")
                customer_list_font_size -= 1
                customer_list_font = get_preferred_font(customer_list_font_size)
            else:
                break
        
        if customer_list_font is None:
            customer_list_font = get_preferred_font(8)
            logger.warning("⚠️ Använder fallback font (8px) för kundlista efter skalning.")

        if customer_list_font:
            current_y_customer_list = current_y_after_title
            approx_line_height = draw.textbbox((0, 0), "A", font=customer_list_font)[3] - draw.textbbox((0, 0), "A", font=customer_list_font)[1]
            line_spacing_factor = 1.5

            for folder in customer_folders:
                display_text = folder
                draw.text((left_column_x, current_y_customer_list), display_text, fill='black', font=customer_list_font)
                current_y_customer_list += approx_line_height * line_spacing_factor + 2
            logger.info(f"✅ Kundlista placerad utan radbrytning och bullet points ({len(customer_folders)} poster).")
        else:
            logger.error("❌ Kunde inte ladda någon font för kundlista.")
    else:
        logger.info("Ingen kundlista att placera på etiketten.")

    # === Generera Header-etikett ===
    HEADER_WIDTH_PX = int(80 / 25.4 * LABEL_DPI)
    HEADER_HEIGHT_PX = int(50 / 25.4 * LABEL_DPI)
    
    header = Image.new('RGB', (HEADER_WIDTH_PX, HEADER_HEIGHT_PX), 'white')
    drawHeader = ImageDraw.Draw(header)
    
    header_margin = 10
    
    qr_header_px = int(HEADER_HEIGHT_PX / 3) 
    qr_header_px = max(20, qr_header_px) 
    qr_header_x = HEADER_WIDTH_PX - qr_header_px - header_margin 
    qr_header_y = header_margin
    
    qr_header_resized = qr_img.resize((qr_header_px, qr_header_px), Image.Resampling.LANCZOS)
    header.paste(qr_header_resized, (qr_header_x, qr_header_y))
    logger.info(f"✅ QR-kod placerad på header-etiketten med storlek: {qr_header_px}x{qr_header_px} pixlar.")

    disk_name_header = disk_name
    text_available_width = qr_header_x - (header_margin * 2)
    text_available_height = HEADER_HEIGHT_PX - (header_margin * 2)

    header_font_size = 8
    header_optimal_font = get_preferred_font(header_font_size)
    
    while True:
        next_font_size = header_font_size + 1
        test_font = get_preferred_font(next_font_size)
        
        if test_font is None or next_font_size > 200:
            break
        
        test_text_w, test_text_h = get_text_size_global(disk_name_header, test_font, drawHeader)
        
        if test_text_w > text_available_width or test_text_h > text_available_height:
            break
        
        header_font_size = next_font_size
        header_optimal_font = test_font
    
    if header_optimal_font is None:
        header_optimal_font = get_preferred_font(8)
        if header_optimal_font is None:
            logger.error("❌ Kunde inte ladda någon font för header-text, ens fallback.")
            return None, None
        logger.warning("⚠️ Använder fallback font (8px) för header-text efter skalning.")

    text_w, text_h = get_text_size_global(disk_name_header, header_optimal_font, drawHeader)
    
    header_text_x = header_margin
    header_text_y = (qr_header_px / 2) - (text_h / 2)
    
    drawHeader.text((header_text_x, header_text_y), disk_name_header, fill='black', font=header_optimal_font)
    logger.info(f"✅ Header-etikett disknamn '{disk_name_header}' placerat (font: {header_font_size}px, bredd: {text_w}px, höjd: {text_h}px).")

    header_rotated = header.rotate(-90, expand=True)
    logger.info("✅ Header roterad 90° för utskrift.")

    try:
        label_file_main = output_file.replace('.json', '_label_main.jpg')
        img.save(label_file_main, 'JPEG', dpi=(LABEL_DPI, LABEL_DPI), quality=95)

        label_file_header = output_file.replace('.json', '_label_header.jpg')
        header_rotated.save(label_file_header, 'JPEG', dpi=(LABEL_DPI, LABEL_DPI), quality=95)

        if os.path.exists(label_file_main) and os.path.exists(label_file_header):
            logger.info(f"✅ Etiketter sparade som '{label_file_main}' och '{label_file_header}'.")
            return label_file_main, label_file_header
        else:
            logger.error("❌ Etikettfilerna verkar inte ha sparats korrekt.")
            return None, None
    except Exception as e:
        logger.error(f"❌ Kunde inte spara etikettfilerna: {e}", exc_info=True)
        return None, None