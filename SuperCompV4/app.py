from flask import Flask, render_template, request, jsonify, send_file
import os
import asyncio
import threading
import re
from datetime import datetime
from playwright.async_api import async_playwright
from PIL import Image

app = Flask(__name__)

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "R.U.C. consultados")
os.makedirs(SAVE_DIR, exist_ok=True)

AVAILABLE_YEARS = ["2024", "2023", "2022", "2021", "2020"]
captcha_storage = {}

@app.route("/")
def index():
    return render_template("index.html", years=AVAILABLE_YEARS)

@app.route("/consultar", methods=["POST"])
def consultar():
    data = request.get_json()
    ruc = data.get("ruc", "").strip()
    year = data.get("year", "").strip()
    
    if not ruc or len(ruc) != 13 or not ruc.isdigit():
        return jsonify({"success": False, "message": "RUC inválido"}), 400
    
    if not year or year not in AVAILABLE_YEARS:
        return jsonify({"success": False, "message": "Año inválido"}), 400
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"RUC_{ruc}_{year}_{timestamp}.txt"
    filepath = os.path.join(SAVE_DIR, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"R.U.C.: {ruc}\nAño: {year}\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        return jsonify({"success": True, "message": "Guardado."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/consultar-supercias", methods=["POST"])
def consultar_supercias():
    data = request.get_json()
    ruc = data.get("ruc", "").strip()
    
    if not ruc or len(ruc) != 13 or not ruc.isdigit():
        return jsonify({"success": False}), 400
    
    thread = threading.Thread(target=run_supercias_async, args=(ruc,))
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True})

def run_supercias_async(ruc):
    asyncio.run(automate_supercias(ruc))

async def automate_supercias(ruc):
    p = await async_playwright().start()
    browser = None
    
    try:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        
        # Navigate and select RUC
        await page.goto("https://appscvsgen.supercias.gob.ec/consultaCompanias/societario/busquedaCompanias.jsf")
        await page.wait_for_load_state("networkidle")
        await page.click('text=R.U.C.')
        await asyncio.sleep(0.5)
        
        # Type RUC
        ruc_input = await page.wait_for_selector('input[id*="parametroBusqueda_input"]')
        await ruc_input.click()
        first_12 = ruc[:12]
        for char in first_12:
            await ruc_input.type(char, delay=250)
        await asyncio.sleep(2)
        
        # Select from dropdown
        dropdown_items = await page.query_selector_all('.ui-autocomplete-item')
        for item in dropdown_items:
            text = await item.text_content()
            if ruc in text:
                await item.click()
                break
        
        await asyncio.sleep(2)
        
        # Find and screenshot CAPTCHA region
        captcha_img = await page.wait_for_selector('img[src*="captcha"]')
        box = await captcha_img.bounding_box()
        
        # Take full screenshot
        full_screenshot = os.path.join(SAVE_DIR, f"full_{ruc}_{datetime.now().strftime('%H%M%S')}.png")
        await page.screenshot(path=full_screenshot)
        
        # Crop CAPTCHA
        captcha_path = os.path.join(SAVE_DIR, f"captcha_{ruc}_{datetime.now().strftime('%H%M%S')}.png")
        img = Image.open(full_screenshot)
        x, y = int(box['x'] - 10), int(box['y'] - 10)
        w, h = int(box['width'] + 20), int(box['height'] + 20)
        cropped = img.crop((max(0,x), max(0,y), x+w, y+h))
        cropped.save(captcha_path)
        
        # Find the CAPTCHA input field
        captcha_input = await page.wait_for_selector('input[id*="captcha"]')
        
        # Store captcha info
        captcha_storage[ruc] = {
            "path": captcha_path,
            "page": page,
            "captcha_input": captcha_input,
            "submitted": False,
            "code": None,
            "status": "waiting"
        }
        
        await save_status(ruc, "CAPTCHA capturado - esperando que el usuario lo escriba")
        
        # Wait for user to submit captcha
        while captcha_storage[ruc]["status"] != "submitted":
            await asyncio.sleep(0.5)
        
        # Type captcha and submit
        captcha_code = captcha_storage[ruc]["code"]
        await captcha_input.fill(captcha_code)
        await asyncio.sleep(0.5)
        
        # Click submit
        await page.click('button[id*="consultar"]')
        await save_status(ruc, f"CAPTCHA enviado - esperando página de compañía...")
        
        # Wait for company page
        await asyncio.sleep(6)
        await page.wait_for_load_state("networkidle")
        
        # SCREENSHOT BEFORE CLICK
        before_click = os.path.join(SAVE_DIR, f"BEFORE_CLICK_{ruc}_{datetime.now().strftime('%H%M%S')}.png")
        await page.screenshot(path=before_click)
        await save_status(ruc, f"Página cargada. Screenshot ANTES del clic guardado.")
        
        # Try to click "Información anual presentada"
        clicked = False
        click_method = ""
        
        # Method 1: Try direct text selector
        try:
            element = await page.wait_for_selector('text=Información anual presentada', timeout=5000)
            if element:
                await element.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                await element.click()
                clicked = True
                click_method = "text selector"
        except:
            pass
        
        # Method 2: Try without accent
        if not clicked:
            try:
                element = await page.wait_for_selector('text=Informacion anual presentada', timeout=3000)
                if element:
                    await element.scroll_into_view_if_needed()
                    await asyncio.sleep(1)
                    await element.click()
                    clicked = True
                    click_method = "text sin acento"
            except:
                pass
        
        # Method 3: Search all elements
        if not clicked:
            try:
                all_elements = await page.query_selector_all('*')
                for el in all_elements:
                    try:
                        text = await el.text_content()
                        if text and "informacion anual" in text.lower().replace("ó", "o"):
                            await el.scroll_into_view_if_needed()
                            await asyncio.sleep(1)
                            await el.click()
                            clicked = True
                            click_method = f"elemento con texto: {text[:30]}"
                            break
                    except:
                        continue
            except:
                pass
        
        # Method 4: JavaScript click
        if not clicked:
            try:
                result = await page.evaluate('''() => {
                    const elements = document.querySelectorAll('*');
                    for (let el of elements) {
                        if (el.textContent && el.textContent.toLowerCase().includes('informacion anual')) {
                            el.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => el.click(), 500);
                            return 'Clicked via JS: ' + el.tagName + ' - ' + el.textContent.substring(0, 50);
                        }
                    }
                    return 'Not found';
                }''')
                if 'Clicked' in result:
                    clicked = True
                    click_method = result
            except:
                pass
        
        # Wait and take screenshot AFTER click
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        
        after_click = os.path.join(SAVE_DIR, f"AFTER_CLICK_{ruc}_{datetime.now().strftime('%H%M%S')}.png")
        await page.screenshot(path=after_click)
        
        if clicked:
            await save_status(ruc, f"✅ CLICK REALIZADO ({click_method}) - Revisa los screenshots BEFORE/AFTER")
        else:
            await save_status(ruc, f"⚠️ NO SE PUDO HACER CLICK - Revisa screenshot BEFORE_CLICK para ver el estado")
        
        # Keep browser open - user closes manually
        await save_status(ruc, f"✅ PROCESO TERMINADO - Chrome permanece abierto. Revisa los screenshots en 'R.U.C. consultados/'")
        
        # Wait until user closes browser
        try:
            while True:
                await page.title()
                await asyncio.sleep(3)
        except:
            pass
        
    except Exception as e:
        await save_status(ruc, f"Error: {str(e)}")
    finally:
        if ruc in captcha_storage:
            del captcha_storage[ruc]
        if browser:
            await browser.close()
        await p.stop()

async def save_status(ruc, status):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"RUC_{ruc}_SUPERCIAS_{timestamp}.txt"
    filepath = os.path.join(SAVE_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"R.U.C.: {ruc}\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nEstado: {status}\n")

@app.route("/captcha-status/<ruc>", methods=["GET"])
def captcha_status(ruc):
    if ruc in captcha_storage:
        return jsonify({
            "ready": True,
            "status": captcha_storage[ruc]["status"]
        })
    return jsonify({"ready": False})

@app.route("/captcha-image/<ruc>", methods=["GET"])
def captcha_image(ruc):
    if ruc in captcha_storage and os.path.exists(captcha_storage[ruc]["path"]):
        return send_file(captcha_storage[ruc]["path"], mimetype='image/png')
    return jsonify({"error": "CAPTCHA not found"}), 404

@app.route("/submit-captcha", methods=["POST"])
def submit_captcha():
    data = request.get_json()
    ruc = data.get("ruc", "").strip()
    captcha_code = data.get("captcha", "").strip()
    
    if not ruc or ruc not in captcha_storage:
        return jsonify({"success": False, "message": "Sesión no encontrada"}), 404
    
    if not captcha_code:
        return jsonify({"success": False, "message": "Código vacío"}), 400
    
    captcha_storage[ruc]["code"] = captcha_code
    captcha_storage[ruc]["status"] = "submitted"
    
    return jsonify({"success": True, "message": "CAPTCHA recibido, procesando..."})

@app.route("/historial", methods=["GET"])
def historial():
    try:
        files = [f for f in os.listdir(SAVE_DIR) if f.endswith('.txt')]
        files.sort(reverse=True)
        return jsonify({"success": True, "files": files})
    except Exception as e:
        return jsonify({"success": False}), 500

if __name__ == "__main__":
    print("🚀 SuperComp V4 en http://localhost:8889")
    app.run(host="0.0.0.0", port=8889, debug=False)
