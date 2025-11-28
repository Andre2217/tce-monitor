import requests
from bs4 import BeautifulSoup
import PyPDF2
import os
import urllib.parse
import time

CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"

def send_whatsapp(msg):
    phone = os.environ["WHATSAPP_PHONE"]
    key = os.environ["WHATSAPP_KEY"]
    encoded = urllib.parse.quote(msg)
    url = f"{CALLMEBOT_URL}?phone={phone}&text={encoded}&apikey={key}"

    print("Enviando WhatsApp...")
    try:
        r = requests.get(url, timeout=20)
        print("Status WhatsApp:", r.text)
    except Exception as e:
        print("Erro WhatsApp:", e)


def download_latest_pdf():
    print("Buscando página principal...")

    url = "https://www.tce.ce.gov.br/diario-oficial/consulta-por-data-de-edicao"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    }

    # Tentativas para contornar instabilidade
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code == 200:
                break
        except Exception as e:
            print(f"Tentativa {attempt+1} falhou:", e)
            time.sleep(3)
    else:
        # Não conseguiu acessar nem na 3ª tentativa
        raise Exception("Falha ao acessar página principal após 3 tentativas.")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Pegar a primeira lupinha válida
    button = soup.find("input", {"title": "Visualizar Edição."})
    if not button:
        raise Exception("Não encontrei botão de visualizar PDF.")

    name_attr = button.get("name")
    if not name_attr:
        raise Exception("Botão não tem atributo 'name' válido.")

    form_action = "https://www.tce.ce.gov.br/diario-oficial/consulta-por-data-de-edicao"
    pdf_download_url = form_action  # POST nativo

    print("Baixando PDF...")

    data = {name_attr: name_attr}
    pdf_resp = requests.post(pdf_download_url, data=data, headers=headers, timeout=20)

    if pdf_resp.status_code != 200 or b"%PDF" not in pdf_resp.content[:10]:
        raise Exception("Servidor retornou algo que NÃO é PDF.")

    save_name = "edicao.pdf"
    with open(save_name, "wb") as f:
        f.write(pdf_resp.content)

    print("PDF salvo como:", save_name)
    return save_name


def search_name_in_pdf(pdf_path, name):
    print("Extraindo texto...")

    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            try:
                text += page.extract_text() or ""
            except:
                pass

    text_lower = text.lower()
    name_lower = name.lower()

    return name_lower in text_lower


def main():
    pdf = None  # evita erro se falhar antes do download

    try:
        search_name = os.environ["SEARCH_NAME"]

        pdf = download_latest_pdf()
        found = search_name_in_pdf(pdf, search_name)

        if found:
            send_whatsapp(f"Boa notícia! Seu nome '{search_name}' apareceu no PDF: {pdf}")
        else:
            send_whatsapp(f"Nada ainda. Seu nome NÃO apareceu no PDF de hoje.")

    except Exception as e:
        send_whatsapp(f"Erro na verificação: {e}")

    finally:
        # Só apaga se o PDF realmente existir
        if pdf and os.path.exists(pdf):
            os.remove(pdf)
            print("PDF removido.")


if __name__ == "__main__":
    main()
