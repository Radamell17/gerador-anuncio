import os
import json
import logging
from PIL import Image, ImageFilter
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from gerar_anuncio import gerar_anuncio

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Estados
ESCOLHENDO_MODO   = 0
AGUARDANDO_TITULO = 1
AGUARDANDO_PRECO  = 2
AGUARDANDO_INFOS  = 3
AGUARDANDO_FOTOS  = 4
QUADRANDO_FOTOS   = 10

dados_usuario = {}

DB_PATH = "/tmp/carros_db.json"

def carregar_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r") as f:
            return json.load(f)
    return {}

def salvar_db(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def chave_carro(titulo):
    return titulo.strip().lower()

def quadrar_foto(caminho_entrada, caminho_saida, tamanho=1080):
    img = Image.open(caminho_entrada).convert("RGB")
    w, h = img.size
    fundo = img.copy().resize((tamanho, tamanho), Image.LANCZOS)
    fundo = fundo.filter(ImageFilter.GaussianBlur(radius=30))
    escala = min(tamanho / w, tamanho / h)
    novo_w = int(w * escala)
    novo_h = int(h * escala)
    foto_redim = img.resize((novo_w, novo_h), Image.LANCZOS)
    x = (tamanho - novo_w) // 2
    y = (tamanho - novo_h) // 2
    fundo.paste(foto_redim, (x, y))
    fundo.save(caminho_saida, "JPEG", quality=95)

# ── /start — menu inicial ─────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = ReplyKeyboardMarkup(
        [["1 - Criar arte de anúncio"], ["2 - Fotos formato Instagram"]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(
        "🚗 *O que você quer fazer?*\n\n"
        "1️⃣ Criar arte de anúncio\n"
        "2️⃣ Deixar fotos no formato Instagram",
        parse_mode="Markdown",
        reply_markup=teclado
    )
    return ESCOLHENDO_MODO

async def escolher_modo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.message.from_user.id
    texto = update.message.text.strip()

    if "1" in texto:
        dados_usuario[uid] = {}
        await update.message.reply_text(
            "Me manda o *título do carro*:\nEx: `Honda Civic 2.0 Aut. 2013/2014`",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return AGUARDANDO_TITULO

    elif "2" in texto:
        dados_usuario[uid] = {"fotos_quadrar": []}
        await update.message.reply_text(
            "📸 Manda todas as fotos!\nQuando terminar manda /pronto",
            reply_markup=ReplyKeyboardRemove()
        )
        return QUADRANDO_FOTOS

    else:
        await update.message.reply_text("Por favor escolha *1* ou *2*", parse_mode="Markdown")
        return ESCOLHENDO_MODO

# ── Fluxo criação de arte ─────────────────────────────────────────────────────
async def receber_titulo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    dados_usuario[uid]["titulo"] = update.message.text.strip()
    await update.message.reply_text("✅ Título salvo!\n\nAgora me manda o *preço*:\nEx: `R$72.900`", parse_mode="Markdown")
    return AGUARDANDO_PRECO

async def receber_preco(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    dados_usuario[uid]["preco"] = update.message.text.strip()
    await update.message.reply_text(
        "✅ Preço salvo!\n\nAgora me manda as *informações*, uma por linha:\n\n"
        "Ex:\n`Completo\n196.000KM\nManual e Cópia de Chave\nBancos de Couro`",
        parse_mode="Markdown"
    )
    return AGUARDANDO_INFOS

async def receber_infos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    dados_usuario[uid]["infos"] = update.message.text.strip().split("\n")[:5]
    dados_usuario[uid]["fotos"] = []
    await update.message.reply_text("✅ Informações salvas!\n\nManda a *foto 1 de 3* 📸", parse_mode="Markdown")
    return AGUARDANDO_FOTOS

async def receber_foto_arte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    foto = update.message.photo[-1]
    arquivo = await foto.get_file()
    foto_bytes = await arquivo.download_as_bytearray()
    idx = len(dados_usuario[uid]["fotos"]) + 1
    caminho = f"/tmp/foto_{uid}_{idx}.jpg"
    with open(caminho, "wb") as f:
        f.write(foto_bytes)
    dados_usuario[uid]["fotos"].append(caminho)
    total = len(dados_usuario[uid]["fotos"])
    if total < 3:
        await update.message.reply_text(f"✅ Foto {total} recebida! Manda a foto {total+1} de 3 📸")
        return AGUARDANDO_FOTOS
    await update.message.reply_text("⏳ Gerando sua arte...")
    return await gerar_e_enviar_arte(update, context, uid)

async def gerar_e_enviar_arte(update, context, uid):
    d = dados_usuario[uid]
    try:
        saida = f"/tmp/anuncio_{uid}.jpg"
        gerar_anuncio(
            foto1=d["fotos"][0], foto2=d["fotos"][1], foto3=d["fotos"][2],
            titulo=d["titulo"], preco=d["preco"], infos=d["infos"],
            saida=saida
        )
        with open(saida, "rb") as f:
            await update.message.reply_photo(photo=f, caption="🎉 Arte gerada!")
        db = carregar_db()
        db[chave_carro(d["titulo"])] = {
            "titulo": d["titulo"], "preco": d["preco"],
            "infos": d["infos"], "fotos": d["fotos"]
        }
        salvar_db(db)
    except Exception as e:
        await update.message.reply_text(f"❌ Erro: {str(e)}")
    del dados_usuario[uid]
    await update.message.reply_text("Quer fazer mais alguma coisa? /start")
    return ConversationHandler.END

# ── Fluxo quadrar fotos ───────────────────────────────────────────────────────
async def receber_foto_quadrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    if uid not in dados_usuario:
        dados_usuario[uid] = {"fotos_quadrar": []}
    foto = update.message.photo[-1]
    arquivo = await foto.get_file()
    foto_bytes = await arquivo.download_as_bytearray()
    idx = len(dados_usuario[uid]["fotos_quadrar"]) + 1
    caminho = f"/tmp/quadrar_{uid}_{idx}.jpg"
    with open(caminho, "wb") as f:
        f.write(foto_bytes)
    dados_usuario[uid]["fotos_quadrar"].append(caminho)
    total = len(dados_usuario[uid]["fotos_quadrar"])
    await update.message.reply_text(f"✅ {total} foto(s) recebida(s). Manda mais ou /pronto")
    return QUADRANDO_FOTOS

async def cmd_pronto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    if uid not in dados_usuario or not dados_usuario[uid].get("fotos_quadrar"):
        await update.message.reply_text("❌ Nenhuma foto recebida ainda.")
        return QUADRANDO_FOTOS
    fotos = dados_usuario[uid]["fotos_quadrar"]
    await update.message.reply_text(f"⏳ Processando {len(fotos)} foto(s)...")
    for i, caminho in enumerate(fotos):
        try:
            saida = f"/tmp/quadrada_{uid}_{i+1}.jpg"
            quadrar_foto(caminho, saida)
            with open(saida, "rb") as f:
                await update.message.reply_photo(photo=f, caption=f"📸 {i+1} de {len(fotos)}")
        except Exception as e:
            await update.message.reply_text(f"❌ Erro na foto {i+1}: {str(e)}")
    del dados_usuario[uid]
    await update.message.reply_text("✅ Tudo pronto! Quer fazer mais alguma coisa? /start")
    return ConversationHandler.END

# ── Cancelar ──────────────────────────────────────────────────────────────────
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    if uid in dados_usuario:
        del dados_usuario[uid]
    await update.message.reply_text("❌ Cancelado.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ESCOLHENDO_MODO:   [MessageHandler(filters.TEXT & ~filters.COMMAND, escolher_modo)],
            AGUARDANDO_TITULO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_titulo)],
            AGUARDANDO_PRECO:  [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_preco)],
            AGUARDANDO_INFOS:  [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_infos)],
            AGUARDANDO_FOTOS:  [MessageHandler(filters.PHOTO, receber_foto_arte)],
            QUADRANDO_FOTOS:   [
                MessageHandler(filters.PHOTO, receber_foto_quadrar),
                CommandHandler("pronto", cmd_pronto),
            ],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    app.add_handler(conv)
    print("🤖 Bot rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
