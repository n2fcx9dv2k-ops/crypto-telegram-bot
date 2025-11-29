import os
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем API ключи из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
COINMARKETCAP_API = os.getenv('COINMARKETCAP_API')
ETHERSCAN_API = os.getenv('ETHERSCAN_API')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_name = update.message.from_user.first_name
    welcome_text = f"""
🚀 **Привет, {user_name}!**

🤖 **Crypto Intelligence Bot** активирован!

📊 **Анализ крипторынка: цены, киты, газ**

**Доступные команды:**
/start - Начало работы
/price [символ] - Цена криптовалюты
/gas - Текущая цена газа в сети Ethereum  
/balance [адрес] - Баланс Ethereum кошелька
/whale - Движения китов
/help - Справка

**Примеры использования:**
/price BTC
/price ETH
/price TON
/gas
/balance 0x742d35Cc6634C0532925a3b8D6B3980A11F1f6f1
    """
    await update.message.reply_text(welcome_text)

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /price"""
    if not context.args:
        await update.message.reply_text("❌ Укажите символ криптовалюты. Например: /price BTC")
        return
    
    symbol = context.args[0].upper()
    
    try:
        if not COINMARKETCAP_API:
            await update.message.reply_text(f"💰 **{symbol}**\n\n💵 Цена: $--,--\n📊 Изменение за 24ч: +--%")
            return
            
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        parameters = {'symbol': symbol, 'convert': 'USD'}
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': COINMARKETCAP_API,
        }

        response = requests.get(url, headers=headers, params=parameters, timeout=10)
        data = response.json()

        if response.status_code == 200 and 'data' in data and symbol in data['data']:
            coin_data = data['data'][symbol]
            price_usd = coin_data['quote']['USD']['price']
            change_24h = coin_data['quote']['USD']['percent_change_24h']
            
            change_emoji = "📈" if change_24h > 0 else "📉" if change_24h < 0 else "➡️"
            
            message = f"""
💰 **{coin_data['name']} ({symbol})**

💵 Цена: ${price_usd:,.2f}
{change_emoji} Изменение за 24ч: {change_24h:+.2f}%
🆔 Ранг: #{coin_data.get('cmc_rank', 'N/A')}
            """
            await update.message.reply_text(message)
        else:
            await update.message.reply_text(f"❌ Криптовалюта {symbol} не найдена")

    except Exception as e:
        logger.error(f"Error in price: {e}")
        await update.message.reply_text("❌ Ошибка при получении цены")

async def gas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /gas"""
    try:
        if not ETHERSCAN_API:
            message = """
⛽ **Gas Prices (Ethereum)**

🚀 Быстро: -- Gwei
🐢 Медленно: -- Gwei  
⚡ Стандарт: -- Gwei
            """
            await update.message.reply_text(message)
            return
            
        url = "https://api.etherscan.io/api"
        params = {
            'module': 'gastracker',
            'action': 'gasoracle',
            'apikey': ETHERSCAN_API
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['status'] == '1':
            gas_data = data['result']
            message = f"""
⛽ **Gas Prices (Ethereum)**

🚀 Быстро: {gas_data['FastGasPrice']} Gwei
🐢 Медленно: {gas_data['SafeGasPrice']} Gwei
⚡ Стандарт: {gas_data['ProposeGasPrice']} Gwei
            """
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("❌ Ошибка при получении данных о газе")

    except Exception as e:
        logger.error(f"Error in gas: {e}")
        await update.message.reply_text("❌ Ошибка при получении данных о газе")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /balance"""
    if not context.args:
        await update.message.reply_text("❌ Укажите адрес. Например: /balance 0x742d35Cc6634C0532925a3b8D6B3980A11F1f6f1")
        return
    
    address = context.args[0]
    
    try:
        if not ETHERSCAN_API:
            message = f"""
👛 **Баланс кошелька**

📍 Адрес: {address[:10]}...{address[-8:]}
💰 Баланс: --.-- ETH
            """
            await update.message.reply_text(message)
            return
            
        url = "https://api.etherscan.io/api"
        params = {
            'module': 'account',
            'action': 'balance',
            'address': address,
            'tag': 'latest',
            'apikey': ETHERSCAN_API
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['status'] == '1':
            balance_wei = int(data['result'])
            balance_eth = balance_wei / 10**18
            
            message = f"""
👛 **Баланс кошелька**

📍 Адрес: {address[:10]}...{address[-8:]}
💰 Баланс: {balance_eth:.4f} ETH
            """
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("❌ Ошибка при получении баланса")

    except Exception as e:
        logger.error(f"Error in balance: {e}")
        await update.message.reply_text("❌ Ошибка при получении баланса")

async def whale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /whale"""
    message = """
🐋 **Трекинг китов**

🚧 Функция в разработке!

А пока используйте:
/price - цены монет
/gas - газ Ethereum
/balance - баланс кошелька
    """
    await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📋 **Доступные команды:**

/start - Начало работы
/price [символ] - Цена криптовалюты
/gas - Газ в сети Ethereum
/balance [адрес] - Баланс кошелька
/whale - Трекинг китов
/help - Справка

**Примеры:**
/price BTC
/gas
/balance 0x742d35Cc6634C0532925a3b8D6B3980A11F1f6f1
    """
    await update.message.reply_text(help_text)

def main():
    """Основная функция запуска бота"""
    print("🔧 1. Функция main() запущена")
    
    if not TELEGRAM_TOKEN:
        print("❌ 2. ОШИБКА: Токен Telegram не установлен!")
        return

    print("✅ 3. Токен найден, создаем Application...")
    
    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        print("✅ 4. Application создан")

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("price", price))
        application.add_handler(CommandHandler("gas", gas))
        application.add_handler(CommandHandler("balance", balance))
        application.add_handler(CommandHandler("whale", whale))
        application.add_handler(CommandHandler("help", help_command))

        print("✅ 5. Обработчики добавлены")
        print("🚀 6. Запускаем бота...")
        
        application.run_polling()
        print("✅ 7. Бот запущен успешно!")
        
    except Exception as e:
        print(f"❌ 8. КРИТИЧЕСКАЯ ОШИБКА: {e}")

if __name__ == '__main__':
    main()
