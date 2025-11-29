import os
import requests
import logging
from telegram.ext import Updater, CommandHandler, CallbackContext

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

def start(update, context):
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
    update.message.reply_text(welcome_text)

def price(update, context):
    """Обработчик команды /price"""
    if not context.args:
        update.message.reply_text("❌ Укажите символ криптовалюты. Например: /price BTC")
        return
    
    symbol = context.args[0].upper()
    
    try:
        # Если API ключ не установлен, показываем заглушку
        if not COINMARKETCAP_API:
            update.message.reply_text(f"💰 **{symbol}**\n\n💵 Цена: $--,--\n📊 Изменение за 24ч: +--%")
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
            
            # Определяем эмодзи для изменения цены
            change_emoji = "📈" if change_24h > 0 else "📉" if change_24h < 0 else "➡️"
            
            message = f"""
💰 **{coin_data['name']} ({symbol})**

💵 Цена: ${price_usd:,.2f}
{change_emoji} Изменение за 24ч: {change_24h:+.2f}%
🆔 Ранг: #{coin_data.get('cmc_rank', 'N/A')}
            """
            update.message.reply_text(message)
        else:
            error_msg = data.get('status', {}).get('error_message', 'Криптовалюта не найдена')
            update.message.reply_text(f"❌ Ошибка: {error_msg}")

    except requests.exceptions.Timeout:
        update.message.reply_text("⏰ Таймаут при запросе к CoinMarketCap")
    except requests.exceptions.RequestException:
        update.message.reply_text("❌ Ошибка сети при получении данных")
    except Exception as e:
        logger.error(f"Error in price command: {e}")
        update.message.reply_text("❌ Внутренняя ошибка бота")

def gas(update, context):
    """Обработчик команды /gas"""
    try:
        # Если API ключ не установлен, показываем заглушку
        if not ETHERSCAN_API:
            message = """
⛽ **Gas Prices (Ethereum)**

🚀 Быстро: -- Gwei
🐢 Медленно: -- Gwei  
⚡ Стандарт: -- Gwei
            """
            update.message.reply_text(message)
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
            update.message.reply_text(message)
        else:
            update.message.reply_text("❌ Ошибка при получении данных о газе")

    except requests.exceptions.Timeout:
        update.message.reply_text("⏰ Таймаут при запросе к Etherscan")
    except requests.exceptions.RequestException:
        update.message.reply_text("❌ Ошибка сети при получении данных о газе")
    except Exception as e:
        logger.error(f"Error in gas command: {e}")
        update.message.reply_text("❌ Внутренняя ошибка бота")

def balance(update, context):
    """Обработчик команды /balance"""
    if not context.args:
        update.message.reply_text("❌ Укажите адрес кошелька. Например: /balance 0x742d35Cc6634C0532925a3b8D6B3980A11F1f6f1")
        return
    
    address = context.args[0]
    
    # Базовая валидация адреса Ethereum
    if not address.startswith('0x') or len(address) != 42:
        update.message.reply_text("❌ Неверный формат Ethereum адреса")
        return
    
    try:
        # Если API ключ не установлен, показываем заглушку
        if not ETHERSCAN_API:
            message = f"""
👛 **Баланс кошелька**

📍 Адрес: {address[:10]}...{address[-8:]}
💰 Баланс: --.-- ETH
            """
            update.message.reply_text(message)
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
            # Конвертируем wei в ETH
            balance_wei = int(data['result'])
            balance_eth = balance_wei / 10**18
            
            message = f"""
👛 **Баланс кошелька**

📍 Адрес: {address[:10]}...{address[-8:]}
💰 Баланс: {balance_eth:.4f} ETH
            """
            update.message.reply_text(message)
        else:
            update.message.reply_text("❌ Ошибка при получении баланса. Проверьте адрес кошелька.")

    except requests.exceptions.Timeout:
        update.message.reply_text("⏰ Таймаут при запросе к Etherscan")
    except requests.exceptions.RequestException:
        update.message.reply_text("❌ Ошибка сети при получении баланса")
    except Exception as e:
        logger.error(f"Error in balance command: {e}")
        update.message.reply_text("❌ Внутренняя ошибка бота")

def whale(update, context):
    """Обработчик команды /whale"""
    message = """
🐋 **Трекинг китов**

🚧 Функция в разработке! Скоро здесь будет:

• 📈 Крупные транзакции
• 🐋 Движения китов  
• 🔍 Анализ больших переводов
• ⚡ Мгновенные оповещения

А пока используйте другие команды:
/price - цены монет
/gas - газ Ethereum
/balance - баланс кошелька
    """
    update.message.reply_text(message)

def help_command(update, context):
    """Обработчик команды /help"""
    help_text = """
📋 **Доступные команды:**

/start - Начало работы
/price [символ] - Цена криптовалюты (BTC, ETH, etc)
/gas - Текущая цена газа в сети Ethereum
/balance [адрес] - Баланс Ethereum кошелька
/whale - Движения китов (в разработке)
/help - Справка по командам

**Примеры:**
/price BTC
/gas
/balance 0x742d35Cc6634C0532925a3b8D6B3980A11F1f6f1
    """
    update.message.reply_text(help_text)

def error_handler(update, context):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Основная функция запуска бота"""
    print("🔧 1. Функция main() запущена")
    
    if not TELEGRAM_TOKEN:
        print("❌ 2. ОШИБКА: Токен Telegram не установлен!")
        print(f"❌ Токен: {TELEGRAM_TOKEN}")
        return

    print("✅ 3. Токен найден, создаем Updater...")
    
    try:
        updater = Updater(TELEGRAM_TOKEN, use_context=True)
        print("✅ 4. Updater создан")
        
        dispatcher = updater.dispatcher
        print("✅ 5. Dispatcher получен")

        # Добавляем обработчики команд
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("price", price))
        dispatcher.add_handler(CommandHandler("gas", gas))
        dispatcher.add_handler(CommandHandler("balance", balance))
        dispatcher.add_handler(CommandHandler("whale", whale))
        dispatcher.add_handler(CommandHandler("help", help_command))

        print("✅ 6. Обработчики добавлены")
        print("🚀 7. Запускаем бота...")
        
        updater.start_polling()
        print("✅ 8. Бот запущен успешно!")
        updater.idle()
        
    except Exception as e:
        print(f"❌ 9. КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
