# label_generator.py

import os
import qrcode
import logging
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Tuple
import sys 
from datetime import datetime

from constants import FONT_PATHS, LABEL_DPI, SYSTEM_AND_HIDDEN_FOLDERS
from utils import get_text_size_global, get_preferred_font, is_system_or_hidden_folder, draw_wrapped_text # Keep draw_wrapped_text for title or future use if needed, but not for list items

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
    """
    Simulera renderingen av kundlistan för att beräkna total höjd den kommer att ta,
    utan automatisk radbrytning per mapp. Varje mapp antas vara en egen rad.
    """
    total_height = 0
    
    # Borttaget: Beräkning av höjd för "Kunder:"-rubriken
    
    # Ungefärlig radhöjd (med 'A') för konsekvent avståndsberäkning
    approx_line_height = draw_obj.textbbox((0, 0), "A", font=font)[3] - draw_obj.textbbox((0, 0), "A", font=font)[1]

    for folder in customer_folders:
        total_height += approx_line_height * line_spacing + 2 # Lägg till höjd för varje rad och en liten marginal
            
    return total_height


def ask_for_customer_level(tree_structure: Dict) -> List[str]:
    """
    Frågar användaren om kundnivå och returnerar en lista med kundmappar.
    Om koden körs utan en interaktiv terminal, väljs toppkatalogen automatiskt.
    """
    customer_folders = []
    
    # Identifiera toppnivåmappar som inte är systemmappar
    top_level_dirs = sorted([
        name for name, content in tree_structure.items() 
        if isinstance(content, dict) and not is_system_or_hidden_folder(name)
    ])
    
    if not top_level_dirs:
        logger.info("Inga synliga toppkataloger hittades för kundlista.")
        return []

    if not sys.stdin.isatty(): 
        logger.info("Körs utan interaktiv terminal. Väljer toppkatalogen som kundnivå.")
        # Om det bara finns en synlig toppnivåmapp, välj den
        if len(top_level_dirs) == 1:
            customer_folders = [top_level_dirs[0]]
            logger.info(f"Automatisk val av kundnivå: '{top_level_dirs[0]}'")
        else:
            # Om flera toppnivåmappar finns och vi inte är interaktiva, inkludera dem alla
            customer_folders = top_level_dirs
            logger.info(f"Automatisk val av kundnivå: Alla toppnivåkataloger: {', '.join(top_level_dirs)}")
        return customer_folders


    print("\n--- Välj kundnivå ---")
    print("Vänligen ange vilken mapp som representerar 'kundnivån'.")
    print("Detta kommer att användas för att generera en lista över kundmappar på etiketten.")
    print("Ange numret för önskad mapp, eller '0' för att hoppa över kundlista.")
    print("Om '0' anges, kommer rotkatalogen för disken att användas för etiketten.")
    print("Om du vill ha en lista över mappar på den *första* nivån, välj '0'.") # Förtydligande

    
    while True:
        print("\nTillgängliga toppkataloger:")
        for i, folder in enumerate(top_level_dirs):
            print(f"{i+1}. {folder}")
        
        print("0. (Ingen specifik kundnivå - använd toppkatalogerna direkt på etiketten)")

        choice = input("Ditt val (nummer): ").strip()

        if choice == '0':
            # Om användaren väljer 0, används toppkatalogerna som kundlista
            customer_folders = top_level_dirs
            logger.info("Användaren valde att lista toppkataloger som kundnivå.")
            break
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(top_level_dirs):
                selected_folder = top_level_dirs[idx]
                customer_folders = [selected_folder]
                logger.info(f"Användaren valde kundnivå: '{selected_folder}'")
                
                # Nu, om den valda mappen har undermappar, fråga om att inkludera dessa
                if selected_folder in tree_structure and isinstance(tree_structure[selected_folder], dict):
                    sub_dirs = sorted([
                        name for name, content in tree_structure[selected_folder].items()
                        if isinstance(content, dict) and not is_system_or_hidden_folder(name)
                    ])
                    if sub_dirs:
                        include_sub_dirs = input(f"Vill du inkludera undermapparna i '{selected_folder}' som kunder? (ja/nej): ").strip().lower()
                        if include_sub_dirs == 'ja':
                            customer_folders = [os.path.join(selected_folder, sd) for sd in sub_dirs]
                            logger.info(f"Inkluderar undermappar som kunder som kunder från '{selected_folder}'.")
                        else:
                            customer_folders = [selected_folder] # Bara den valda mappen
                            logger.info(f"Inkluderar endast den valda mappen '{selected_folder}' som kund.")
                break
            else:
                print("Ogiltigt val. Vänligen ange ett giltigt nummer.")
        else:
            print("Ogiltigt val. Vänligen ange ett nummer.")
            
    return customer_folders

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
    LABEL_WIDTH_PX = int(50 / 25.4 * LABEL_DPI)  # 100 mm till pixlar
    LABEL_HEIGHT_PX = int(80 / 25.4 * LABEL_DPI) # 70 mm till pixlar
    
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
    # QR-koden ska vara 1/3 av sidans bredd och lika hög som den är bred
    # Begränsas av höger kolumns bredd och tillgänglig kolumnhöjd
    qr_target_size = min(int(LABEL_WIDTH_PX / 3), column_area_height) 
    
    # Justera för marginaler inuti kolumnen
    qr_size_with_margin = qr_target_size - page_margin
    
    # QR-koden linjerar nu med toppen av kundlistan
    qr_x_in_column = right_column_x - page_margin + (right_column_width - qr_size_with_margin) // 2
    qr_y_in_column = current_y_after_title # Linjera med toppen av kundlistan
    
    qr_img_resized = qr_img.resize((qr_size_with_margin, qr_size_with_margin), Image.Resampling.LANCZOS)
    img.paste(qr_img_resized, (qr_x_in_column, qr_y_in_column))
    logger.info("✅ QR-kod placerad i höger kolumn och linjerad med första kundposten.")

    # --- Kundlista (Vänster kolumn) ---
    customer_list_max_height = column_area_height
    customer_list_font_size = 200 # Initial font size

    customer_folders = ask_for_customer_level(tree_data['tree'])
    
    customer_list_font = get_preferred_font(customer_list_font_size)
    
    if customer_folders:
        # Hitta den längsta mappen för breddkontroll (utan bullet point)
        longest_display_text = ""
        for folder in customer_folders:
            # display_text = f"• {folder}" # Borttagen bullet point
            display_text = folder
            if len(display_text) > len(longest_display_text):
                longest_display_text = display_text

        # Skala font för kundlista om det behövs
        while customer_list_font and customer_list_font_size > 8: # Behåll en nedre gräns för fontstorlek
            current_total_height = simulate_customer_list_rendering(customer_folders, customer_list_font, draw)
            current_max_folder_width = get_text_size_global(longest_display_text, customer_list_font, draw)[0]
            
            if current_total_height > customer_list_max_height or current_max_folder_width > left_column_width:
                logger.warning(f"⚠️ Fontstorlek {customer_list_font_size} för kundlista för stor. Minskar...")
                customer_list_font_size -= 1
                customer_list_font = get_preferred_font(customer_list_font_size)
            else:
                break # Fontstorleken är bra
        
        # Fallback om loopen avslutas utan en lämplig font
        if customer_list_font is None:
            customer_list_font = get_preferred_font(8)
            logger.warning("⚠️ Använder fallback font (8px) för kundlista efter skalning.")

        # Rita kundlistan utan radbrytning per mapp och utan rubrik
        if customer_list_font:
            current_y_customer_list = current_y_after_title # Start Y för kundlistan

            # Borttaget: Rita rubriken "Kunder:"
            
            # Ungefärlig radhöjd för konsekvent avstånd, som beräknats i simuleringen
            approx_line_height = draw.textbbox((0, 0), "A", font=customer_list_font)[3] - draw.textbbox((0, 0), "A", font=customer_list_font)[1]
            line_spacing_factor = 1.5 # Matchar värdet som används i simuleringen

            for folder in customer_folders:
                # Borttagen bullet point
                # display_text = f"• {folder}"
                display_text = folder
                draw.text((left_column_x, current_y_customer_list), display_text, fill='black', font=customer_list_font) # Justerad x-position
                current_y_customer_list += approx_line_height * line_spacing_factor + 2 # Liten marginal mellan kundposter
            logger.info(f"✅ Kundlista placerad utan radbrytning och bullet points ({len(customer_folders)} poster).")
        else:
            logger.error("❌ Kunde inte ladda någon font för kundlista.")
    else:
        logger.info("Ingen kundlista att placera på etiketten.")

    # === Generera Header-etikett ===
    # En smalare etikett, t.ex. 80x50 mm för header (FÖRE rotation)
    HEADER_WIDTH_PX = int(80 / 25.4 * LABEL_DPI)
    HEADER_HEIGHT_PX = int(50 / 25.4 * LABEL_DPI)
    
    header = Image.new('RGB', (HEADER_WIDTH_PX, HEADER_HEIGHT_PX), 'white')
    drawHeader = ImageDraw.Draw(header)
    
    header_margin = 10 # Marginal för elementen inuti headern
    
    # --- Placera QR-kod på header-etiketten ---
    # Storlek på QR-koden på headern, t.ex. 50/3 mm eller 1/3 av HEADER_HEIGHT_PX
    # Din instruktion: "qr koden ska vara 50 / 3" - antar du menar av de 50mm (HEADER_HEIGHT_PX)
    # Så, QR-kodens sida blir HEADER_HEIGHT_PX / 3
    qr_header_px = int(HEADER_HEIGHT_PX / 3) 
    # Säkerställ att den inte blir för liten
    qr_header_px = max(20, qr_header_px) 

    # QR-kodens position på den ORÖRDA header-etiketten (högerställd, centrerad vertikalt)
    qr_header_x = HEADER_WIDTH_PX - qr_header_px - header_margin 
    qr_header_y = header_margin
    
    qr_header_resized = qr_img.resize((qr_header_px, qr_header_px), Image.Resampling.LANCZOS)
    header.paste(qr_header_resized, (qr_header_x, qr_header_y))
    logger.info(f"✅ QR-kod placerad på header-etiketten med storlek: {qr_header_px}x{qr_header_px} pixlar.")

    # --- Skala och placera texten på headern ---
    disk_name_header = disk_name # Använd safe_name för header

    # Tillgängligt utrymme för texten på den ORÖRDA header-etiketten
    # Texten placeras till vänster om QR-koden.
    text_available_width = qr_header_x - (header_margin * 2) # Utrymme från vänster marginal till QR-kodens start
    text_available_height = HEADER_HEIGHT_PX - (header_margin * 2) # Höjd för texten

    # Skalningslogik: Börja med en liten font och öka tills den fyller utrymmet eller blir för stor
    # Detta är att "maximera" textstorleken.
    header_font_size = 8 # Börja med en liten fontstorlek
    header_optimal_font = get_preferred_font(header_font_size)
    
    # Loop för att växa fontstorleken
    while True:
        # Försök med nästa större fontstorlek
        next_font_size = header_font_size + 1
        test_font = get_preferred_font(next_font_size)
        
        # Om vi inte kan ladda en större font, eller om fontstorleken blir orimligt stor, avbryt
        if test_font is None or next_font_size > 200: # Max 200px för att undvika oändlig loop med vissa fonter
            break
        
        # Få dimensionerna för texten med den TESTade fontstorleken
        test_text_w, test_text_h = get_text_size_global(disk_name_header, test_font, drawHeader)
        
        # Kontrollera om texten med den NÄSTA fontstorleken blir för bred ELLER för hög
        if test_text_w > text_available_width or test_text_h > text_available_height:
            break # Om den blir för stor, använd den FÖREGÅENDE (aktuella) fontstorleken
        
        # Om den ryms, uppdatera till den större fontstorleken och fortsätt
        header_font_size = next_font_size
        header_optimal_font = test_font
    
    # Om header_optimal_font fortfarande är None (ingen font kunde laddas alls)
    # Detta är en fallback om get_preferred_font aldrig lyckas, eller om initiala fontstorleken inte ens ryms
    if header_optimal_font is None:
        header_optimal_font = get_preferred_font(8) # Använd en minsta fallback font
        if header_optimal_font is None: # Sista utvägen
            logger.error("❌ Kunde inte ladda någon font för header-text, ens fallback.")
            return None, None
        logger.warning("⚠️ Använder fallback font (8px) för header-text efter skalning.")

    # Beräkna textens faktiska dimensioner med den optimala fonten som hittades
    text_w, text_h = get_text_size_global(disk_name_header, header_optimal_font, drawHeader)
    
    # Centrera texten vertikalt inom dess tillgängliga höjd
    header_text_x = header_margin
    header_text_y = (qr_header_px / 2) - (text_h / 2)
    
    drawHeader.text((header_text_x, header_text_y), disk_name_header, fill='black', font=header_optimal_font)
    logger.info(f"✅ Header-etikett disknamn '{disk_name_header}' placerat (font: {header_font_size}px, bredd: {text_w}px, höjd: {text_h}px).")

    # Rotera header 90 grader för utskrift
    header_rotated = header.rotate(-90, expand=True)
    logger.info("✅ Header roterad 90° för utskrift.")

    # === SPARA BÅDA LABELS ===
    try:
        label_file_main = output_file.replace('.json', '_label_main.jpg') 
        img.save(label_file_main, 'JPEG', dpi=(LABEL_DPI, LABEL_DPI), quality=95) 
        
        label_file_header = output_file.replace('.json', '_label_header.jpg')
        header_rotated.save(label_file_header, 'JPEG', dpi=(LABEL_DPI, LABEL_DPI), quality=95)
        
        if os.path.exists(label_file_main):
            logger.info(f"✅ Main label sparad: {label_file_main}")
        
        if os.path.exists(label_file_header):
            logger.info(f"✅ Header label sparad: {label_file_header}")
        
        return label_file_main, label_file_header
            
    except Exception as e:
        logger.error(f"❌ Fel vid sparande av etiketter: {e}", exc_info=True)
        return None, None