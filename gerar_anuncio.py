from PIL import Image, ImageDraw, ImageFont
import requests
import os
from io import BytesIO

PRETO   = (0, 0, 0)
AMARELO = (255, 185, 0)
BRANCO  = (255, 255, 255)

LARGURA = 1080
ALTURA  = 1080
TOPO_H  = 220
RODAPE_H = 220
FOTOS_Y  = TOPO_H
FOTOS_H  = ALTURA - TOPO_H - RODAPE_H
RODAPE_Y = TOPO_H + FOTOS_H

def baixar_imagem(u):
    if u.startswith("http"):
        return Image.open(BytesIO(requests.get(u).content)).convert("RGB")
    return Image.open(u).convert("RGB")

def recortar_centro(img, w, h):
    escala = max(w / img.width, h / img.height)
    nw, nh = int(img.width*escala), int(img.height*escala)
    img = img.resize((nw, nh), Image.LANCZOS)
    x, y = (nw-w)//2, (nh-h)//2
    return img.crop((x, y, x+w, y+h))

def fonte(tam, negrito=False):
    base = os.path.dirname(os.path.abspath(__file__))
    lista = (
        [os.path.join(base,"LiberationSans-Bold.ttf"),
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if negrito else
        [os.path.join(base,"LiberationSans-Regular.ttf"),
         "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for c in lista:
        if os.path.exists(c): return ImageFont.truetype(c, tam)
    return ImageFont.load_default()

def gerar_anuncio(foto1, foto2, foto3, titulo, preco, infos, saida="anuncio.jpg"):
    canvas = Image.new("RGB", (LARGURA, ALTURA), PRETO)
    draw   = ImageDraw.Draw(canvas)

    # ── MEDIDAS DAS FOTOS ────────────────────────────────────────────────────
    BD      = 5           # borda amarela
    FOTO_GW = 660         # foto grande largura
    FOTO_PW = LARGURA - FOTO_GW - BD*3   # fotos pequenas largura
    FOTO_PH = (FOTOS_H - BD*3) // 2     # fotos pequenas altura

    px = FOTO_GW + BD*2   # x onde começam as fotos pequenas

    # ── TOPO ─────────────────────────────────────────────────────────────────
    MARG    = 18
    # Caixa VENDE-SE ocupa toda a largura da foto grande
    VENDE_W = FOTO_GW
    BORDA   = 6

    # Moldura amarela + interior preto
    draw.rectangle([MARG-BORDA, MARG-BORDA, VENDE_W+BORDA, TOPO_H-MARG+BORDA], fill=AMARELO)
    draw.rectangle([MARG, MARG, VENDE_W, TOPO_H-MARG], fill=PRETO)

    # VENDE-SE centralizado verticalmente na caixa
    f_vende = fonte(108, negrito=True)
    draw.text((MARG+18, MARG+12), "VENDE-SE", font=f_vende, fill=AMARELO)

    # Infos à direita — reduz fonte até caber tudo
    info_x  = VENDE_W + BD*3
    info_w  = LARGURA - info_x - MARG   # largura disponível
    tam_inf = 36
    f_info  = fonte(tam_inf, negrito=True)

    # Ajusta tamanho para que todas as linhas caibam em largura
    for linha in infos[:5]:
        while True:
            bb = draw.textbbox((0,0), linha.upper(), font=f_info)
            if bb[2]-bb[0] <= info_w or tam_inf <= 18:
                break
            tam_inf -= 2
            f_info = fonte(tam_inf, negrito=True)

    esp_inf = (TOPO_H - MARG*2) // max(len(infos[:5]), 1)
    for i, linha in enumerate(infos[:5]):
        draw.text((info_x, MARG + i*esp_inf + 4), linha.upper(), font=f_info, fill=BRANCO)

    # ── FOTOS ────────────────────────────────────────────────────────────────
    img1 = recortar_centro(baixar_imagem(foto1), FOTO_GW, FOTOS_H)
    canvas.paste(img1, (0, FOTOS_Y))

    # Fundo amarelo = moldura fotos pequenas
    draw.rectangle([FOTO_GW+BD, FOTOS_Y, LARGURA, FOTOS_Y+FOTOS_H], fill=AMARELO)

    img2 = recortar_centro(baixar_imagem(foto2), FOTO_PW, FOTO_PH)
    canvas.paste(img2, (px, FOTOS_Y+BD))

    img3 = recortar_centro(baixar_imagem(foto3), FOTO_PW, FOTO_PH)
    canvas.paste(img3, (px, FOTOS_Y+BD+FOTO_PH+BD))

    # ── RODAPÉ ───────────────────────────────────────────────────────────────
    draw.rectangle([0, RODAPE_Y, LARGURA, ALTURA], fill=AMARELO)

    # Preço — caixa preta com letras amarelas
    # Posicionado na coluna das fotos pequenas, alinhado verticalmente ao centro do rodapé
    preco_fmt = preco if preco.upper().startswith("R$") else f"R${preco}"
    f_preco   = fonte(62, negrito=True)
    bb_p = draw.textbbox((0,0), preco_fmt, font=f_preco)
    pw, ph = bb_p[2]-bb_p[0], bb_p[3]-bb_p[1]
    PAD  = 14
    # Caixa preta alinhada à coluna direita (fotos pequenas)
    cx1 = FOTO_GW + BD
    cy1 = RODAPE_Y + (RODAPE_H - ph - PAD*2) // 2
    cx2 = LARGURA - MARG
    cy2 = cy1 + ph + PAD*2
    draw.rectangle([cx1, cy1, cx2, cy2], fill=PRETO)
    # Centraliza o texto dentro da caixa
    tx = cx1 + (cx2 - cx1 - pw) // 2
    draw.text((tx, cy1+PAD), preco_fmt, font=f_preco, fill=AMARELO)

    # Título — coluna esquerda, letras pretas
    # Reduz fonte até caber na largura da foto grande
    titulo_w = FOTO_GW - MARG*2
    tam_tit  = 64
    f_tit    = fonte(tam_tit, negrito=True)
    t = titulo.upper().split()
    meio = len(t)//2
    l1, l2 = " ".join(t[:meio]), " ".join(t[meio:])
    for linha in [l1, l2]:
        while True:
            bb = draw.textbbox((0,0), linha, font=f_tit)
            if bb[2]-bb[0] <= titulo_w or tam_tit <= 20:
                break
            tam_tit -= 2
            f_tit = fonte(tam_tit, negrito=True)

    esp_tit = tam_tit + 8
    total_h = esp_tit * 2
    ty = RODAPE_Y + (RODAPE_H - total_h) // 2
    draw.text((MARG, ty),          l1, font=f_tit, fill=PRETO)
    draw.text((MARG, ty+esp_tit),  l2, font=f_tit, fill=PRETO)

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
