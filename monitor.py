import requests
import re
import os
from PyPDF2 import PdfReader


BASE_URL = "https://www.tce.ce.gov.br/diario-oficial/consulta-por-data-de-edicao"
DOWNLOAD_PREFIX = "https://www.tce.ce.gov.br"

PHONE = os.getenv("WHATSAPP_PHONE")
API_KEY = os.getenv("WHATSAPP_KEY")
SEARCH_NAME = os.getenv("SEARCH_NAME")


def baixar_pdf():
    print("Buscando página principal...")

    html = requests.get(BASE_URL).text

    # pega FIRST ocorrência de link para PDF
    match = re.search(r'href="(/doeconsulta/edicoes/edicao_[0-9]+\.pdf)"', html)

    if not match:
        raise Exception("Não encontrei link para PDF")

    pdf_url = DOWNLOAD_PREFIX + match.group(1)
    nome_pdf = pdf_url.split("/")[-1]

    print("Baixando PDF:", pdf_url)

    r = requests.get(pdf_url)
    with open(nome_pdf, "wb") as f:
        f.write(r.content)

    return nome_pdf


def procurar_nome(nome_pdf):
    print("Abrindo PDF:", nome_pdf)
    reader = PdfReader(nome_pdf)
    texto = ""

    for page in reader.pages:
        texto += page.extract_text() or ""

    return SEARCH_NAME.lower() in texto.lower()


def enviar_whatsapp(msg):
    print("Enviando WhatsApp...")

    url = (
        f"https://api.callmebot.com/whatsapp.php?"
        f"phone={PHONE}&text={requests.utils.quote(msg)}&apikey={API_KEY}"
    )

    r = requests.get(url)
    print("Status WhatsApp:", r.text)


def main():
    try:
        pdf = baixar_pdf()
        achou = procurar_nome(pdf)

        if achou:
            enviar_whatsapp(f"Boa notícia! Seu nome apareceu no PDF: {pdf}")
        else:
            enviar_whatsapp("Nada ainda… seu nome não foi encontrado hoje.")

    except Exception as e:
        enviar_whatsapp(f"Erro na verificação: {str(e)}")

    finally:
        # apagar o PDF
        if os.path.exists(pdf):
            os.remove(pdf)
            print("PDF apagado:", pdf)


if __name__ == "__main__":
    main()
