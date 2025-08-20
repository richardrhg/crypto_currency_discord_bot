import discord
from discord.ext import commands
import aiohttp
import asyncio
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 設定機器人權限
intents = discord.Intents.default()
intents.message_content = True

# 創建機器人實例
bot = commands.Bot(command_prefix='!', intents=intents)

class CryptoBot:
    def __init__(self):
        self.session = None
    
    async def create_session(self):
        """創建HTTP會話"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """關閉HTTP會話"""
        if self.session:
            await self.session.close()
    
    async def get_bitfinex_lending_rate(self, asset="USDT"):
        """獲取Bitfinex借貸利率"""
        await self.create_session()
        try:
            # 使用正確的 Bitfinex API 端點
            base_url = "https://api-pub.bitfinex.com/v2"
            
            # 根據資產類型選擇正確的交易對
            if asset.upper() == "USDT":
                symbol = "fUSDT"
            elif asset.upper() == "BTC":
                symbol = "fBTC"
            elif asset.upper() == "ETH":
                symbol = "fETH"
            elif asset.upper() == "USD":
                symbol = "fUSD"
            else:
                symbol = "fUSDT"  # 預設
            
            # 構建正確的 API URL
            url = f"{base_url}/tickers?symbols={symbol}"
        
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 解析借貸利率資料
                    if isinstance(data, list) and len(data) > 0:
                        ticker_data = data[0]  # 獲取第一個交易對的資料
                        
                        if len(ticker_data) >= 8:
                            # Bitfinex ticker 資料結構: [SYMBOL, BID, BID_SIZE, ASK, ASK_SIZE, DAILY_CHANGE, DAILY_CHANGE_RELATIVE, LAST_PRICE, VOLUME, HIGH, LOW]
                            symbol_name = ticker_data[0]
                            daily_change_relative = float(ticker_data[6])  # 日變化率
                            volume = float(ticker_data[8])  # 成交量
                            bid_size = float(ticker_data[2])  # 買單數量
                            
                            print(f"原始日變化率: {daily_change_relative}")
                            print(f"成交量: {volume}")
                            print(f"買單數量: {bid_size}")
                            
                            # 修復利率計算
                            annual_rate = abs(daily_change_relative) * 365
                            
                            # 使用實際資料而不是固定值
                            min_amount = max(100, bid_size * 0.1)  # 最小金額基於買單數量
                            total_amount = volume  # 總金額使用成交量
                            
                            return {
                                'asset': asset.upper(),
                                'annualInterestRate': annual_rate,
                                'purchasedAmount': f"{total_amount:.2f}",
                                'status': 'ACTIVE',
                                'period': '實時利率'
                            }
                    
                    # 如果資料格式不對，返回市場參考利率
                    return {
                        'asset': asset.upper(),
                        'annualInterestRate': self._get_market_reference_rate(asset),
                        'purchasedAmount': '動態計算',   # 改為動態說明
                        'status': 'MARKET_RATE',
                        'period': '參考利率'
                    }
                else:
                    print(f"Bitfinex API錯誤狀態: {response.status}")
                    # 如果API失敗，返回市場參考利率
                    return {
                        'asset': asset.upper(),
                        'annualInterestRate': self._get_market_reference_rate(asset),
                        'purchasedAmount': 'API錯誤',   # 說明API狀態
                        'status': 'REFERENCE_RATE',
                        'period': '參考利率'
                    }
        except Exception as e:
            print(f"獲取Bitfinex借貸利率錯誤: {e}")
            print(f"錯誤類型: {type(e)}")
            # 異常時返回市場參考利率
            return {
                'asset': asset.upper(),
                'annualInterestRate': self._get_market_reference_rate(asset),
                'purchasedAmount': '異常錯誤',   # 說明異常狀態
                'status': 'ERROR_FALLBACK',
                'period': '參考利率'
            }
    
    def _get_market_reference_rate(self, asset):
        """獲取市場參考利率"""
        reference_rates = {
            'USDT': 4.2,   # USDT 通常 4-5%
            'USD': 3.8,    # USD 通常 3-4%
            'BTC': 2.1,    # BTC 通常 2-3%
            'ETH': 2.5,    # ETH 通常 2-3%
            'EUR': 2.8,    # EUR 通常 2-3%
        }
        return reference_rates.get(asset.upper(), 3.0)
    
    async def get_crypto_price(self, symbol):
        """獲取加密貨幣對USDT的價格"""
        await self.create_session()
        try:
            # 確保交易對格式正確
            if not symbol.upper().endswith('USDT'):
                symbol = f"{symbol.upper()}USDT"
            
            # 幣安API - 獲取價格
            url = f"https://api.binance.com/api/v3/ticker/24hr"
            params = {'symbol': symbol}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'symbol': data['symbol'],
                        'priceChangePercent': float(data['priceChangePercent']),  # 24小時價格變化百分比
                        'lastPrice': float(data['lastPrice']),  # 當前價格
                        'volume': float(data['volume']),  # 24小時成交量
                        'high': float(data['highPrice']),  # 24小時最高價
                        'low': float(data['lowPrice'])  # 24小時最低價
                    }
        except Exception as e:
            print(f"獲取價格錯誤: {e}")
        
        return None
    
    async def get_multiple_prices(self, symbols):
        """獲取多個加密貨幣價格"""
        await self.create_session()
        try:
            # 格式化交易對
            formatted_symbols = []
            for symbol in symbols:
                if not symbol.upper().endswith('USDT'):
                    formatted_symbols.append(f'"{symbol.upper()}USDT"')
                else:
                    formatted_symbols.append(f'"{symbol.upper()}"')
            
            symbols_param = f'[{",".join(formatted_symbols)}]'
            
            url = f"https://api.binance.com/api/v3/ticker/24hr"
            params = {'symbols': symbols_param}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return [{
                        'symbol': item['symbol'],
                        'lastPrice': float(item['lastPrice']),
                        'priceChangePercent': float(item['priceChangePercent'])
                    } for item in data]
        except Exception as e:
            print(f"獲取多個價格錯誤: {e}")
        
        return None

# 創建CryptoBot實例
crypto_bot = CryptoBot()

@bot.event
async def on_ready():
    print(f'{bot.user} 機器人已上線！')
    print(f'機器人ID: {bot.user.id}')
    print('------')

@bot.command(name='lending', aliases=['借貸', '利率'])
async def get_lending_rate(ctx, asset='USDT'):
    """獲取Bitfinex借貸利率 - 使用方法: !lending 或 !借貸"""
    
    await ctx.send("🔍 正在查詢Bitfinex借貸利率...")
    
    rate_info = await crypto_bot.get_bitfinex_lending_rate(asset.upper())
    
    if rate_info:
        embed = discord.Embed(
            title=f"💰 {rate_info['asset']} 借貸利率 (Bitfinex)",
            color=0x00ff00,
            timestamp=datetime.now()  # 使用本地時間
        )
        embed.add_field(
            name="年化利率", 
            value=f"{rate_info['annualInterestRate']:.2f}%", 
            inline=True
        )
        embed.add_field(
            name="狀態", 
            value=rate_info['status'], 
            inline=True
        )
        embed.set_footer(text="資料來源: Bitfinex API")
        
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ 無法獲取 {asset} 的借貸利率資訊")

@bot.command(name='price', aliases=['價格', 'p'])
async def get_price(ctx, symbol):
    """獲取加密貨幣價格 - 使用方法: !price BTC 或 !價格 ETH"""
    
    await ctx.send(f"🔍 正在查詢 {symbol.upper()} 價格...")
    
    price_info = await crypto_bot.get_crypto_price(symbol)
    
    if price_info:
        # 判斷漲跌顏色
        color = 0x00ff00 if price_info['priceChangePercent'] >= 0 else 0xff0000
        change_emoji = "📈" if price_info['priceChangePercent'] >= 0 else "📉"
        
        embed = discord.Embed(
            title=f"{change_emoji} {price_info['symbol']} 價格資訊",
            color=color,
            timestamp=datetime.now()  # 使用本地時間
        )
        embed.add_field(
            name="當前價格", 
            value=f"${price_info['lastPrice']:,.4f}", 
            inline=True
        )
        embed.add_field(
            name="24h漲跌", 
            value=f"{price_info['priceChangePercent']:+.2f}%", 
            inline=True
        )
        embed.add_field(
            name="24h成交量", 
            value=f"{price_info['volume']:,.0f}", 
            inline=True
        )
        embed.add_field(
            name="24h最高", 
            value=f"${price_info['high']:,.4f}", 
            inline=True
        )
        embed.add_field(
            name="24h最低", 
            value=f"${price_info['low']:,.4f}", 
            inline=True
        )
        embed.set_footer(text="資料來源: Binance API")
        
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ 無法獲取 {symbol.upper()} 的價格資訊，請確認幣種名稱是否正確")

@bot.command(name='watch', aliases=['監控', 'w'])
async def watch_prices(ctx, *symbols):
    """監控多個加密貨幣價格 - 使用方法: !watch BTC ETH BNB"""
    
    if not symbols:
        await ctx.send("❌ 請提供要監控的幣種名稱，例如: `!watch BTC ETH BNB`")
        return
    
    if len(symbols) > 10:
        await ctx.send("❌ 一次最多只能監控10個幣種")
        return
    
    await ctx.send(f"🔍 正在查詢 {len(symbols)} 個幣種的價格...")
    
    prices_info = await crypto_bot.get_multiple_prices(list(symbols))
    
    if prices_info:
        embed = discord.Embed(
            title="📊 加密貨幣價格監控",
            color=0x3498db,
            timestamp=datetime.now()  # 使用本地時間
        )
        
        for price in prices_info:
            change_emoji = "📈" if price['priceChangePercent'] >= 0 else "📉"
            embed.add_field(
                name=f"{change_emoji} {price['symbol']}", 
                value=f"${price['lastPrice']:,.4f}\n({price['priceChangePercent']:+.2f}%)",
                inline=True
            )
        
        embed.set_footer(text="資料來源: Binance API")
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ 無法獲取價格資訊，請檢查幣種名稱是否正確")

@bot.command(name='cryptohelp', aliases=['幫助', '指令'])
async def cryptohelp(ctx):
    """顯示幫助資訊"""
    
    embed = discord.Embed(
        title="🤖 加密貨幣機器人指令說明",
        description="以下是所有可用的指令:",
        color=0x3498db
    )
    
    commands_info = [
        ("!lending 或 !借貸", "獲取USDT借貸利率"),
        ("!price <幣種> 或 !價格 <幣種>", "獲取特定幣種對USDT的價格"),
        ("!watch <幣種1> <幣種2>... 或 !監控", "監控多個幣種價格"),
        ("!help 或 !幫助", "顯示此幫助訊息")
    ]
    
    for command, description in commands_info:
        embed.add_field(
            name=command,
            value=description,
            inline=False
        )
    
    embed.add_field(
        name="📝 使用範例",
        value="`!price BTC`\n`!lending`\n`!watch BTC ETH BNB`",
        inline=False
    )
    
    embed.set_footer(text="資料來源: Binance API")
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    """錯誤處理"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ 找不到該指令，請使用 `!help` 查看所有可用指令")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ 指令缺少必要參數，請使用 `!help` 查看指令用法")
    else:
        await ctx.send(f"❌ 發生錯誤: {str(error)}")
        print(f"錯誤詳情: {error}")

@bot.event
async def on_disconnect():
    """機器人斷線時關閉會話"""
    await crypto_bot.close_session()

# 運行機器人
if __name__ == "__main__":
    # 從 .env 檔案讀取 Discord 機器人 Token
    TOKEN = os.getenv('DiscordBotToken')
    
    if not TOKEN:
        print("❌ 錯誤：未找到 DiscordBotToken 環境變數")
        print("請檢查 .env 檔案是否包含 DiscordBotToken=你的Token")
        exit(1)
    
    try:
        bot.run(TOKEN)
    except KeyboardInterrupt:
        print("機器人已停止運行")
    finally:
        # 確保會話被正確關閉
        asyncio.run(crypto_bot.close_session())