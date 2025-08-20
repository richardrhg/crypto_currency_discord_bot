# crypto_currency_discord_bot

## ⚙️ 設定說明

### 環境變數
- `DiscordBotToken` - Discord 機器人 Token（必需）

### 機器人權限
機器人需要以下 Discord 權限：
- 讀取訊息
- 發送訊息
- 嵌入連結
- 使用表情符號

## �� 故障排除

### 常見問題

**Q: 機器人無法啟動？**
A: 檢查 `.env` 檔案中的 `DiscordBotToken` 是否正確設定

**Q: 無法獲取價格資訊？**
A: 確認網路連線正常，幣種名稱是否正確

**Q: 借貸利率顯示異常？**
A: 可能是 Bitfinex API 暫時無法使用，會自動使用參考利率

### 錯誤代碼
- `HTTP 404` - API 端點不存在
- `HTTP 405` - 請求方法不允許
- `HTTP 500` - 伺服器內部錯誤

## �� 貢獻指南

歡迎提交 Issue 和 Pull Request！

### 開發環境設定
1. Fork 專案
2. 創建功能分支
3. 提交變更
4. 發起 Pull Request


## 🙏 致謝

- [Discord.py](https://github.com/Rapptz/discord.py) - Discord 機器人框架
- [Binance API](https://binance-docs.github.io/apidocs/) - 加密貨幣價格資料
- [Bitfinex API](https://docs.bitfinex.com/) - 借貸利率資料

## 📞 聯絡資訊

- **作者：** richardrhg
- **GitHub：** https://github.com/richardrhg
- **Discord ID：** richard_chou

---

⭐ 如果這個專案對您有幫助，請給個 Star！