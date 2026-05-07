from PIL import Image, ImageDraw, ImageFont
import requests
import sys
import os
import textwrap
from io import BytesIO

# ─── CONFIGURAÇÕES DO TEMPLATE ───────────────────────────────────────────────
LARGURA = 1080
ALTURA = 1080

PRETO = (0, 0, 0)
AMARELO = (255, 185, 0)
BRANCO = (255, 255, 255)

def baixar_imagem(url_ou_path):
    """Carrega imagem de URL ou caminho local"""
    if url_ou_path.startswith("http"):
        resp = requests.get(url_ou_path)
        return Image.open(BytesIO(resp.content)).convert("RGB")
    else:
        return Image.open(url_ou_path).convert("RGB")

def recortar_centro(img, largura, altura):
    """Recorta a imagem no centro com o tamanho desejado"""
    img = img.resize(
        (max(largura, int(img.width * altura / img.height)),
         max(altura, int(img.height * largura / img.width))),
        Image.LANCZOS
    )
    x = (img.width - largura) // 2
    y = (img.height - altura) // 2
    return img.crop((x, y, x + largura, y + altura))

def carregar_fonte(tamanho, negrito=False):
    """Tenta carregar fonte do sistema"""
    fontes_negrito = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    ]
    fontes_normal = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
    ]
    lista = fontes_negrito if negrito else fontes_normal
    for caminho in lista:
        if os.path.exists(caminho):
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default()

def gerar_anuncio(foto1, foto2, foto3, titulo, preco, infos, saida="anuncio.jpg"):
    """
    foto1, foto2, foto3: caminhos ou URLs das fotos
    titulo: ex "Honda Civic 2.0 Aut. 2013/2014"
    preco: ex "R$72.900"
    infos: lista com até 4 strings, ex ["Completo", "196.000KM", "Manual e Cópia de Chave", "Bancos de Couro"]
    saida: nome do arquivo de saída
    """

    canvas = Image.new("RGB", (LARGURA, ALTURA), PRETO)
    draw = ImageDraw.Draw(canvas)

    # ── ZONAS DE LAYOUT ──────────────────────────────────────────────────────
    # Topo: faixa preta com VENDE-SE e infos
    topo_altura = 220

    # Meio: fotos
    fotos_y_inicio = topo_altura
    fotos_altura = 620

    # Rodapé: faixa amarela com título e preço
    rodape_y = fotos_y_inicio + fotos_altura
    rodape_altura = ALTURA - rodape_y

    # ── TOPO ─────────────────────────────────────────────────────────────────
    # Fundo preto já está
    # Caixa amarela "VENDE-SE"
    vende_largura = 530
    vende_margem = 30
    draw.rectangle([vende_margem, vende_margem, vende_largura, topo_altura - vende_margem], fill=AMARELO)

    fonte_vende = carregar_fonte(95, negrito=True)
    draw.text((vende_margem + 20, vende_margem + 10), "VENDE-SE", font=fonte_vende, fill=PRETO)

    # Infos no canto superior direito
    fonte_info = carregar_fonte(34, negrito=True)
    info_x = vende_largura + 40
    info_y = vende_margem + 10
    espacamento = 42

    for i, linha in enumerate(infos[:4]):
        draw.text((info_x, info_y + i * espacamento), linha.upper(), font=fonte_info, fill=BRANCO)

    # ── FOTOS ─────────────────────────────────────────────────────────────────
    # Foto grande à esquerda (2/3 da largura)
    foto_grande_largura = 680
    foto_grande_altura = fotos_altura

    img1 = baixar_imagem(foto1)
    img1 = recortar_centro(img1, foto_grande_largura, foto_grande_altura)
    canvas.paste(img1, (0, fotos_y_inicio))

    # Duas fotos à direita (1/3 da largura, empilhadas)
    foto_peq_largura = LARGURA - foto_grande_largura - 4
    foto_peq_altura = (fotos_altura // 2) - 2

    img2 = baixar_imagem(foto2)
    img2 = recortar_centro(img2, foto_peq_largura, foto_peq_altura)
    canvas.paste(img2, (foto_grande_largura + 4, fotos_y_inicio))

    img3 = baixar_imagem(foto3)
    img3 = recortar_centro(img3, foto_peq_largura, foto_peq_altura)
    canvas.paste(img3, (foto_grande_largura + 4, fotos_y_inicio + foto_peq_altura + 4))

    # ── RODAPÉ ───────────────────────────────────────────────────────────────
    draw.rectangle([0, rodape_y, LARGURA, ALTURA], fill=AMARELO)

    # Título do carro (esquerda)
    fonte_titulo = carregar_fonte(62, negrito=True)
    titulo_upper = titulo.upper()

    # Quebra linha se for longo
    palavras = titulo_upper.split()
    linha1 = " ".join(palavras[:len(palavras)//2])
    linha2 = " ".join(palavras[len(palavras)//2:])

    margem_rod = 30
    draw.text((margem_rod, rodape_y + 18), linha1, font=fonte_titulo, fill=PRETO)
    draw.text((margem_rod, rodape_y + 18 + 70), linha2, font=fonte_titulo, fill=PRETO)

    # Preço (direita)
    fonte_preco = carregar_fonte(72, negrito=True)
    bbox = draw.textbbox((0, 0), preco, font=fonte_preco)
    preco_largura = bbox[2] - bbox[0]
    preco_x = LARGURA - preco_largura - margem_rod
    preco_y = rodape_y + (rodape_altura - (bbox[3] - bbox[1])) // 2
    draw.text((preco_x, preco_y), preco, font=fonte_preco, fill=PRETO)

    # ── SALVAR ────────────────────────────────────────────────────────────────
    canvas.save(saida, "JPEG", quality=95)
    print(f"✅ Anúncio gerado: {saida}")
    return saida


# ─── EXEMPLO DE USO ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    gerar_anuncio(
        foto1="foto1.jpg",
        foto2="foto2.jpg",
        foto3="foto3.jpg",
        titulo="Honda Civic 2.0 Aut. 2013/2014",
        preco="R$72.900",
        infos=[
            "Completo",
            "196.000KM",
            "Manual e Cópia de Chave",
            "Bancos de Couro"
        ],
        saida="anuncio_gerado.jpg"
    )
