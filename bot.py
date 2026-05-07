import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from gerar_anuncio import gerar_anuncio
from io import BytesIO
from PIL import Image

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Estados da conversa
AGUARDANDO_TITULO = 1
AGUARDANDO_PRECO = 2
AGUARDANDO_INFOS = 3
AGUARDANDO_FOTOS = 4

dados_usuario = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚗 *Gerador de Anúncio de Carro*\n\n"
        "Vamos criar sua arte! Me manda o *título do carro*:\n"
        "Ex: `Honda Civic 2.0 Aut. 2013/2014`",
        parse_mode="Markdown"
    )
    return AGUARDANDO_TITULO

async def receber_titulo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    dados_usuario[user_id] = {"titulo": update.message.text}
    await update.message.reply_text(
        "✅ Título salvo!\n\nAgora me manda o *preço*:\nEx: `R$72.900`",
        parse_mode="Markdown"
    )
    return AGUARDANDO_PRECO

async def receber_preco(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    dados_usuario[user_id]["preco"] = update.message.text
    await update.message.reply_text(
        "✅ Preço salvo!\n\nAgora me manda as *4 informações*, uma por linha:\n\n"
        "Ex:\n`Completo\n196.000KM\nManual e Cópia de Chave\nBancos de Couro`",
        parse_mode="Markdown"
    )
    return AGUARDANDO_INFOS

async def receber_infos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    linhas = update.message.text.strip().split("\n")
    dados_usuario[user_id]["infos"] = linhas[:4]
    dados_usuario[user_id]["fotos"] = []
    await update.message.reply_text(
        "✅ Informações salvas!\n\nAgora manda as *3 fotos* do carro (uma por vez).\n📸 Foto 1 de 3:",
        parse_mode="Markdown"
    )
    return AGUARDANDO_FOTOS

async def receber_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # Baixa a foto em maior resolução
    foto = update.message.photo[-1]
    arquivo = await foto.get_file()
    foto_bytes = await arquivo.download_as_bytearray()

    # Salva temporariamente
    idx = len(dados_usuario[user_id]["fotos"]) + 1
    caminho = f"/tmp/foto_{user_id}_{idx}.jpg"
    with open(caminho, "wb") as f:
        f.write(foto_bytes)

    dados_usuario[user_id]["fotos"].append(caminho)
    total = len(dados_usuario[user_id]["fotos"])

    if total < 3:
        await update.message.reply_text(f"✅ Foto {total} recebida! Manda a foto {total+1} de 3:")
        return AGUARDANDO_FOTOS
    else:
        await update.message.reply_text("⏳ Gerando sua arte, aguarda um segundo...")
        return await gerar_arte(update, context)

async def gerar_arte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    d = dados_usuario[user_id]

    try:
        saida = f"/tmp/anuncio_{user_id}.jpg"
        gerar_anuncio(
            foto1=d["fotos"][0],
            foto2=d["fotos"][1],
            foto3=d["fotos"][2],
            titulo=d["titulo"],
            preco=d["preco"],
            infos=d["infos"],
            saida=saida
        )
        with open(saida, "rb") as f:
            await update.message.reply_photo(photo=f, caption="🎉 Aqui está sua arte!")

        # Limpa dados
        del dados_usuario[user_id]

    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao gerar a arte: {str(e)}")

    await update.message.reply_text("Quer gerar outro? Use /start")
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in dados_usuario:
        del dados_usuario[user_id]
    await update.message.reply_text("❌ Cancelado. Use /start para recomeçar.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AGUARDANDO_TITULO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_titulo)],
            AGUARDANDO_PRECO:  [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_preco)],
            AGUARDANDO_INFOS:  [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_infos)],
            AGUARDANDO_FOTOS:  [MessageHandler(filters.PHOTO, receber_foto)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    app.add_handler(conv)
    print("🤖 Bot rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
