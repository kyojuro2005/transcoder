from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, CallbackContext, filters
import re

# Étapes de la conversation
CHOIX, BASE_SOURCE, NOMBRE, BASE_CIBLE, BASE_OP, OPERATION = range(6)

# Fonction pour vérifier la validité d'un nombre dans une base donnée
def is_valid_number(number, base):
    valid_digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    valid_chars = valid_digits[:base] + "."
    for char in number.upper():
        if char not in valid_chars:
            return False
    return True

# Conversion base -> décimal (prend en charge les fractions)
def base_to_decimal(number, base):
    if '.' in number:
        int_part, frac_part = number.split('.')
        int_value = int(int_part, base) if int_part else 0
        frac_value = sum(int(char, base) * (base ** -i) for i, char in enumerate(frac_part, 1))
        return int_value + frac_value
    return int(number, base)

# Conversion décimal -> base (prend en charge les fractions)
def decimal_to_base(number, base):
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if number == 0:
        return "0"
    int_part = int(number)
    frac_part = number - int_part

    # Conversion de la partie entière
    int_result = ""
    while int_part > 0:
        int_result = digits[int_part % base] + int_result
        int_part //= base

    # Conversion de la partie fractionnaire
    frac_result = ""
    while frac_part > 0 and len(frac_result) < 10:  # Limite pour éviter les boucles infinies
        frac_part *= base
        frac_result += digits[int(frac_part)]
        frac_part -= int(frac_part)

    return int_result + ('.' + frac_result if frac_result else "")

# Résolution d'opérations dans une base spécifique
def calculate_in_base(operation, base):
    try:
        # Remplace les nombres par leur valeur en base 10
        numbers = re.findall(r"[0-9A-Z.]+", operation)
        for number in numbers:
            if not is_valid_number(number, base):
                raise ValueError(f"Le nombre {number} n'est pas valide en base {base}.")
            operation = operation.replace(number, str(base_to_decimal(number, base)), 1)
        
        # Évalue l'expression
        result = eval(operation)
        # Retourne le résultat dans la base d'origine
        return decimal_to_base(result, base)
    except Exception as e:
        return f"Erreur dans le calcul : {str(e)}"

# Début de la conversation
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "🔹 **Trancoder – Votre assistant en logique combinatoire !** 🔹\n\n"
        "Salut à tous ! 🚀 Vous cherchez un outil puissant pour manipuler les nombres à travers différentes bases ? **Trancoder** est là pour vous ! 🧠✨\n\n"
        "Avec **Trancoder**, vous pouvez facilement :\n"
        "✅ **Décoder** des nombres dans n'importe quelle base 🔢\n"
        "✅ **Transcoder** d'une base à une autre en un clin d'œil ⚡\n"
        "✅ **Effectuer des opérations** directement sur les bases de votre choix 🔄\n\n"
        "Que vous soyez étudiant, passionné de logique numérique ou expert en informatique, **Trancoder** simplifie toutes vos conversions et calculs en un instant ! 🌍🔣\n\n"
        "Prêt à transcoder sans prise de tête ? Essayez **Trancoder** dès maintenant ! 🚀💡\n\n"
        "Choisissez une option :\n"
        "1. Convertir un nombre d'une base à une autre\n"
        "2. Effectuer une opération dans une base spécifique"
    )
    return CHOIX

# Étape 1 : Choix de l'action
async def choix(update: Update, context: CallbackContext):
    choix = update.message.text
    if choix == "1":
        await update.message.reply_text("Veuillez entrer la base dans laquelle se trouve votre nombre (entre 2 et 36) :")
        return BASE_SOURCE
    elif choix == "2":
        await update.message.reply_text("Veuillez entrer la base dans laquelle effectuer l'opération (entre 2 et 36) :")
        return BASE_OP
    else:
        await update.message.reply_text("Choix invalide. Veuillez entrer 1 ou 2.")
        return CHOIX

# Étape 2 : Conversion - Base source
async def base_source(update: Update, context: CallbackContext):
    try:
        base = int(update.message.text)
        if base < 2 or base > 36:
            await update.message.reply_text("La base doit être comprise entre 2 et 36. Réessayez :")
            return BASE_SOURCE
        context.user_data['base_source'] = base
        await update.message.reply_text(f"Veuillez entrer votre nombre en base {base} :")
        return NOMBRE
    except ValueError:
        await update.message.reply_text("Veuillez entrer un nombre valide pour la base.")
        return BASE_SOURCE

# Étape 3 : Conversion - Vérification du nombre
async def nombre(update: Update, context: CallbackContext):
    base = context.user_data['base_source']
    number = update.message.text
    if not is_valid_number(number, base):
        await update.message.reply_text(f"Ce nombre ne correspond pas à la base {base}. Réessayez :")
        return NOMBRE
    context.user_data['number'] = number
    await update.message.reply_text("Veuillez maintenant entrer la base dans laquelle vous souhaitez convertir votre nombre (entre 2 et 36) :")
    return BASE_CIBLE

# Étape 4 : Conversion - Base cible
async def base_cible(update: Update, context: CallbackContext):
    try:
        base_target = int(update.message.text)
        if base_target < 2 or base_target > 36:
            await update.message.reply_text("La base doit être comprise entre 2 et 36. Réessayez :")
            return BASE_CIBLE

        base_source = context.user_data['base_source']
        number = context.user_data['number']
        decimal_number = base_to_decimal(number, base_source)
        converted_number = decimal_to_base(decimal_number, base_target)

        await update.message.reply_text(
            f"La conversion du nombre {number} (base {base_source}) vers la base {base_target} est : {converted_number} 🎉"
        )
        await update.message.reply_text(f"Veuillez cliquer sur /start pour continuer")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Erreur dans la conversion. Réessayez :")
        return BASE_CIBLE

# Étape 5 : Calcul - Base de l'opération
async def base_op(update: Update, context: CallbackContext):
    try:
        base = int(update.message.text)
        if base < 2 or base > 36:
            await update.message.reply_text("La base doit être comprise entre 2 et 36. Réessayez :")
            return BASE_OP
        context.user_data['base_op'] = base
        await update.message.reply_text("Veuillez entrer l'opération à effectuer (par exemple : A1.2 + B.3 - 10 en base spécifiée) :")
        return OPERATION
    except ValueError:
        await update.message.reply_text("Veuillez entrer un nombre valide pour la base.")
        return BASE_OP

# Étape 6 : Calcul - Résultat de l'opération
async def operation(update: Update, context: CallbackContext):
    base = context.user_data['base_op']
    operation = update.message.text
    result = calculate_in_base(operation, base)
    await update.message.reply_text(f"Le résultat de l'opération en base {base} est : {result}")
    await update.message.reply_text(f"Veuillez cliquer sur /start pour continuer")
    return ConversationHandler.END

# Annulation de la conversation
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Opération annulée. À bientôt !")
    return ConversationHandler.END

# Programme principal
if __name__ == "__main__":
    TOKEN = "7493431486:AAG_EU7KpWhnNg2lrKXZUMwZVYquxs9Pt0k"

    application = ApplicationBuilder().token(TOKEN).build()

    # Gestionnaire de conversation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOIX: [MessageHandler(filters.TEXT & ~filters.COMMAND, choix)],
            BASE_SOURCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, base_source)],
            NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, nombre)],
            BASE_CIBLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, base_cible)],
            BASE_OP: [MessageHandler(filters.TEXT & ~filters.COMMAND, base_op)],
            OPERATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, operation)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    print("Bot démarré. 🚀")
    application.run_polling()
