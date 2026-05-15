from PIL import Image, ImageDraw, ImageFont
import requests, os
from io import BytesIO

PRETO     = (0, 0, 0)
CINZA_ESC = (45, 45, 45)
AMARELO   = (255, 185, 0)
BRANCO    = (255, 255, 255)

LARGURA  = 1080
ALTURA   = 1080
TOPO_H   = 220
RODAPE_H = 220
FOTOS_Y  = TOPO_H
FOTOS_H  = ALTURA - TOPO_H - RODAPE_H
RODAPE_Y = TOPO_H + FOTOS_H

def baixar_imagem(u):
    if u.startswith("http"):
        return Image.open(BytesIO(requests.get(u).content)).convert("RGB")
    return Image.open(u).convert("RGB")

def recortar_centro(img, w, h):
    e = max(w/img.width, h/img.height)
    nw, nh = int(img.width*e), int(img.height*e)
    img = img.resize((nw,nh), Image.LANCZOS)
    return img.crop(((nw-w)//2,(nh-h)//2,(nw-w)//2+w,(nh-h)//2+h))

def fonte(tam, negrito=False):
    base = os.path.dirname(os.path.abspath(__file__))
    lst = ([os.path.join(base,"LiberationSans-Bold.ttf"),
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
           if negrito else
           [os.path.join(base,"LiberationSans-Regular.ttf"),
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    for c in lst:
        if os.path.exists(c): return ImageFont.truetype(c, tam)
    return ImageFont.load_default()

def texto_grosso(draw, pos, texto, font, fill, espessura=3):
    """Desenha texto com efeito ultra-negrito deslocando em vários sentidos"""
    x, y = pos
    for dx in range(-espessura, espessura+1):
        for dy in range(-espessura, espessura+1):
            if dx != 0 or dy != 0:
                draw.text((x+dx, y+dy), texto, font=font, fill=fill)
    draw.text((x, y), texto, font=font, fill=fill)

def gerar_anuncio(foto1, foto2, foto3, titulo, preco, infos, saida="anuncio.jpg"):
    canvas = Image.new("RGB", (LARGURA, ALTURA), PRETO)
    draw   = ImageDraw.Draw(canvas)

    BD      = 5
    FOTO_GW = 660
    FOTO_PW = LARGURA - FOTO_GW - BD*3
    FOTO_PH = (FOTOS_H - BD*3) // 2
    px      = FOTO_GW + BD*2
    MARG    = 18

    # ── TOPO ─────────────────────────────────────────────────────────────────
    BORDA = 6
    draw.rectangle([MARG-BORDA, MARG-BORDA, FOTO_GW+BORDA, TOPO_H-MARG+BORDA], fill=AMARELO)
    draw.rectangle([MARG, MARG, FOTO_GW, TOPO_H-MARG], fill=PRETO)

    f_vende = fonte(108, negrito=True)
    texto_grosso(draw, (MARG+18, MARG+12), "VENDE-SE", f_vende, AMARELO, espessura=2)

    # Infos direita — brancas
    info_x = FOTO_GW + BD*3
    info_w = LARGURA - info_x - MARG
    tam_i  = 36
    f_i    = fonte(tam_i, negrito=True)
    for l in infos[:5]:
        while draw.textbbox((0,0),l.upper(),font=f_i)[2] > info_w and tam_i > 18:
            tam_i -= 2; f_i = fonte(tam_i, negrito=True)
    esp = (TOPO_H - MARG*2) // max(len(infos[:5]),1)
    for i, l in enumerate(infos[:5]):
        draw.text((info_x, MARG + i*esp + 4), l.upper(), font=f_i, fill=BRANCO)

    # ── FOTOS ────────────────────────────────────────────────────────────────
    canvas.paste(recortar_centro(baixar_imagem(foto1), FOTO_GW, FOTOS_H), (0, FOTOS_Y))
    draw.rectangle([FOTO_GW+BD, FOTOS_Y, LARGURA, FOTOS_Y+FOTOS_H], fill=AMARELO)
    canvas.paste(recortar_centro(baixar_imagem(foto2), FOTO_PW, FOTO_PH), (px, FOTOS_Y+BD))
    canvas.paste(recortar_centro(baixar_imagem(foto3), FOTO_PW, FOTO_PH), (px, FOTOS_Y+BD+FOTO_PH+BD))

    # ── RODAPÉ ───────────────────────────────────────────────────────────────
    draw.rectangle([0, RODAPE_Y, LARGURA, ALTURA], fill=CINZA_ESC)

    # Título — letras AMARELAS ultra-grossas
    titulo_w = FOTO_GW - MARG*2
    tam_t    = 66
    f_t      = fonte(tam_t, negrito=True)
    t        = titulo.upper().split()
    meio     = len(t)//2
    l1, l2   = " ".join(t[:meio]), " ".join(t[meio:])
    for ln in [l1, l2]:
        while draw.textbbox((0,0),ln,font=f_t)[2] > titulo_w and tam_t > 20:
            tam_t -= 2; f_t = fonte(tam_t, negrito=True)
    esp_t   = tam_t + 10
    total_t = esp_t * 2
    ty = RODAPE_Y + (RODAPE_H - total_t) // 2
    texto_grosso(draw, (MARG, ty),       l1, f_t, AMARELO, espessura=2)
    texto_grosso(draw, (MARG, ty+esp_t), l2, f_t, AMARELO, espessura=2)

    # Preço — caixa AMARELA, letras PRETAS ultra-grossas
    preco_fmt = preco if preco.upper().startswith("R$") else f"R${preco}"
    f_p = fonte(66, negrito=True)
    bb  = draw.textbbox((0,0), preco_fmt, font=f_p)
    pw, ph = bb[2]-bb[0], bb[3]-bb[1]
    PAD  = 16
    cx1  = FOTO_GW + BD
    cy1  = RODAPE_Y + (RODAPE_H - ph - PAD*2) // 2
    cx2  = LARGURA - MARG
    cy2  = cy1 + ph + PAD*2
    draw.rectangle([cx1, cy1, cx2, cy2], fill=AMARELO)
    tx = cx1 + (cx2-cx1-pw)//2
    draw.text((tx, cy1+PAD), preco_fmt, font=f_p, fill=PRETO)

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
