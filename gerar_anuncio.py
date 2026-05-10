from PIL import Image, ImageDraw, ImageFont
import requests
import os
from io import BytesIO

PRETO    = (0, 0, 0)
AMARELO  = (255, 185, 0)
BRANCO   = (255, 255, 255)

LARGURA = 1080
ALTURA  = 1080
TOPO_H  = 210
RODAPE_H = 240
FOTOS_Y  = TOPO_H
FOTOS_H  = ALTURA - TOPO_H - RODAPE_H
RODAPE_Y = TOPO_H + FOTOS_H

def baixar_imagem(url_ou_path):
    if url_ou_path.startswith("http"):
        resp = requests.get(url_ou_path)
        return Image.open(BytesIO(resp.content)).convert("RGB")
    return Image.open(url_ou_path).convert("RGB")

def recortar_centro(img, largura, altura):
    escala = max(largura / img.width, altura / img.height)
    novo_w = int(img.width * escala)
    novo_h = int(img.height * escala)
    img = img.resize((novo_w, novo_h), Image.LANCZOS)
    x = (novo_w - largura) // 2
    y = (novo_h - altura) // 2
    return img.crop((x, y, x + largura, y + altura))

def fonte(tamanho, negrito=False):
    base = os.path.dirname(os.path.abspath(__file__))
    candidatos = (
        [os.path.join(base, "LiberationSans-Bold.ttf"),
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if negrito else
        [os.path.join(base, "LiberationSans-Regular.ttf"),
         "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for c in candidatos:
        if os.path.exists(c):
            return ImageFont.truetype(c, tamanho)
    return ImageFont.load_default()

def gerar_anuncio(foto1, foto2, foto3, titulo, preco, infos, saida="anuncio.jpg"):
    canvas = Image.new("RGB", (LARGURA, ALTURA), PRETO)
    draw   = ImageDraw.Draw(canvas)

    # ── TOPO ─────────────────────────────────────────────────────────────────
    MARG    = 22
    VENDE_W = 530
    BORDA   = 5

    # Borda amarela + interior preto = efeito de quadro
    draw.rectangle([MARG-BORDA, MARG-BORDA, VENDE_W+BORDA, TOPO_H-MARG+BORDA], fill=AMARELO)
    draw.rectangle([MARG, MARG, VENDE_W, TOPO_H-MARG], fill=PRETO)

    # VENDE-SE em amarelo
    f_vende = fonte(100, negrito=True)
    draw.text((MARG+15, MARG+10), "VENDE-SE", font=f_vende, fill=AMARELO)

    # Infos à direita em branco
    f_info = fonte(37, negrito=True)
    info_x = VENDE_W + 38
    for i, linha in enumerate(infos[:5]):
        draw.text((info_x, MARG + i * 44), linha.upper(), font=f_info, fill=BRANCO)

    # ── FOTOS ────────────────────────────────────────────────────────────────
    BD      = 4          # borda amarela entre fotos
    FOTO_GW = 676
    FOTO_PW = LARGURA - FOTO_GW - BD * 3
    FOTO_PH = (FOTOS_H - BD * 3) // 2

    # Foto grande esquerda
    img1 = recortar_centro(baixar_imagem(foto1), FOTO_GW, FOTOS_H)
    canvas.paste(img1, (0, FOTOS_Y))

    # Fundo amarelo que vira moldura das fotos pequenas
    draw.rectangle([FOTO_GW + BD, FOTOS_Y, LARGURA, FOTOS_Y + FOTOS_H], fill=AMARELO)

    px = FOTO_GW + BD * 2
    img2 = recortar_centro(baixar_imagem(foto2), FOTO_PW, FOTO_PH)
    canvas.paste(img2, (px, FOTOS_Y + BD))

    img3 = recortar_centro(baixar_imagem(foto3), FOTO_PW, FOTO_PH)
    canvas.paste(img3, (px, FOTOS_Y + BD + FOTO_PH + BD))

    # ── RODAPÉ ───────────────────────────────────────────────────────────────
    draw.rectangle([0, RODAPE_Y, LARGURA, ALTURA], fill=AMARELO)

    # Título em preto (esquerda)
    f_titulo = fonte(66, negrito=True)
    t = titulo.upper().split()
    meio = len(t) // 2
    l1 = " ".join(t[:meio])
    l2 = " ".join(t[meio:])
    MR = 25
    draw.text((MR, RODAPE_Y + 20),      l1, font=f_titulo, fill=PRETO)
    draw.text((MR, RODAPE_Y + 20 + 74), l2, font=f_titulo, fill=PRETO)

    # Preço — caixa preta, letras amarelas (direita)
    preco_fmt = preco if preco.upper().startswith("R$") else f"R${preco}"
    f_preco   = fonte(70, negrito=True)
    bb  = draw.textbbox((0,0), preco_fmt, font=f_preco)
    pw, ph = bb[2]-bb[0], bb[3]-bb[1]
    PAD = 16
    cx1 = LARGURA - pw - PAD*2 - MR
    cy1 = RODAPE_Y + (RODAPE_H - ph - PAD*2) // 2
    cx2 = LARGURA - MR
    cy2 = cy1 + ph + PAD*2
    draw.rectangle([cx1, cy1, cx2, cy2], fill=PRETO)
    draw.text((cx1+PAD, cy1+PAD), preco_fmt, font=f_preco, fill=AMARELO)

    canvas.save(saida, "JPEG", quality=95)
    print(f"✅ Anúncio gerado: {saida}")
    return saida

if __name__ == "__main__":
    gerar_anuncio(
        foto1="foto1.jpg", foto2="foto2.jpg", foto3="foto3.jpg",
        titulo="Honda Civic 2.0 Aut. 2013/2014",
        preco="R$72.900",
        infos=["Completo","196.000KM","Manual e Cópia de Chave","Bancos de Couro"],
        saida="anuncio_gerado.jpg"
    )
