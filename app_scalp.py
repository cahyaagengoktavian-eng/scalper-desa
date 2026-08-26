import requests
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    hasil = None
    error = None
    pilihan_koin = None

    if request.method == "POST":
        coin_id = request.form.get("coin_id")
        coin_query = request.form.get("koin")

        if coin_id:
            try:
                url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    name = data.get("name", coin_id.upper())
                    market_data = data.get("market_data", {})
                    
                    harga_usd = market_data.get("current_price", {}).get("usd", 0)
                    harga_idr = market_data.get("current_price", {}).get("idr", 0)
                    price_change_24h = market_data.get("price_change_percentage_24h", 0)
                    if price_change_24h is None:
                        price_change_24h = 0
                        
                    # Indikator Kilat khusus Scalp (Stochastic / Fast RSI proxy)
                    stoch_rsi = round(50 + (price_change_24h * 2.2), 2)
                    stoch_rsi = max(2.0, min(98.0, stoch_rsi))
                    
                    if stoch_rsi < 20:
                        status = "⚡ SCALP BUY (Oversold Kilat / Area Pantul Cepat 🔥)"
                    elif stoch_rsi > 80:
                        status = "⚠️ SCALP SELL / SHORT (Overbought Kilat / Rawan Banting 🛑)"
                    else:
                        status = "⏳ WAIT & SEE (Volatilitas Netral / Belum Ada Trigger Scalp)"

                    # Target Profit 1.2% & Stop Loss 0.6%
                    tp_scalp_usd = harga_usd * 1.012
                    sl_scalp_usd = harga_usd * 0.994
                    p_tp = 1.2
                    p_sl = 0.6

                    kurs_idr = harga_idr / harga_usd if harga_usd > 0 else 15500

                    hasil = {
                        "coin": f"{name.upper()} ({coin_id})",
                        "harga_usd": f"{harga_usd:,.8f}" if harga_usd < 1 else f"{harga_usd:,.2f}",
                        "harga_idr": f"{harga_idr:,.4f}" if harga_idr < 1000 else f"{harga_idr:,.2f}",
                        "stoch_rsi": f"{stoch_rsi}",
                        "status": status,
                        "tp_scalp": f"{tp_scalp_usd:,.8f}" if tp_scalp_usd < 1 else f"{tp_scalp_usd:,.4f}",
                        "tp_idr": f"{int(tp_scalp_usd * kurs_idr):,}".replace(",", "."),
                        "p_tp": f"{p_tp}",
                        "sl_scalp": f"{sl_scalp_usd:,.8f}" if sl_scalp_usd < 1 else f"{sl_scalp_usd:,.4f}",
                        "sl_idr": f"{int(sl_scalp_usd * kurs_idr):,}".replace(",", "."),
                        "p_sl": f"{p_sl}"
                    }
                else:
                    error = "Gagal mengambil data koin."
            except Exception as e:
                error = f"Terjadi kesalahan: {str(e)}"

        elif coin_query:
            coin_clean = coin_query.strip().lower()
            try:
                search_url = f"https://api.coingecko.com/api/v3/search?query={coin_clean}"
                headers = {"User-Agent": "Mozilla/5.0"}
                search_response = requests.get(search_url, headers=headers, timeout=10)
                
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    coins_list = search_data.get("coins", [])
                    
                    if not coins_list:
                        error = f"Koin '{coin_query}' tidak ditemukan."
                    else:
                        filtered_coins = [
                            c for c in coins_list 
                            if coin_clean in c.get("name", "").lower() or coin_clean in c.get("symbol", "").lower()
                        ]
                        target_list = filtered_coins if filtered_coins else coins_list

                        exact_match = None
                        for c in target_list:
                            if c.get("symbol", "").lower() == coin_clean or c.get("id", "").lower() == coin_clean:
                                exact_match = c.get("id")
                                break

                        if len(target_list) == 1 or exact_match:
                            target_id = exact_match if exact_match else target_list[0].get("id")
                            return render_template("index.html", hasil=get_direct_scalp_data(target_id), error=None, pilihan_koin=None)
                        else:
                            pilihan_koin = target_list[:6]
                else:
                    error = "Gagal terhubung ke peladen pencarian."
            except Exception as e:
                error = f"Terjadi kesalahan: {str(e)}"

    return render_template("index.html", hasil=hasil, error=error, pilihan_koin=pilihan_koin)


def get_direct_scalp_data(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        data = response.json()
        name = data.get("name", coin_id.upper())
        market_data = data.get("market_data", {})
        
        harga_usd = market_data.get("current_price", {}).get("usd", 0)
        harga_idr = market_data.get("current_price", {}).get("idr", 0)
        price_change_24h = market_data.get("price_change_percentage_24h", 0)
        if price_change_24h is None:
            price_change_24h = 0
            
        stoch_rsi = round(50 + (price_change_24h * 2.2), 2)
        stoch_rsi = max(2.0, min(98.0, stoch_rsi))
        
        if stoch_rsi < 20:
            status = "⚡ SCALP BUY (Oversold Kilat / Area Pantul Cepat 🔥)"
        elif stoch_rsi > 80:
            status = "⚠️ SCALP SELL / SHORT (Overbought Kilat / Rawan Banting 🛑)"
        else:
            status = "⏳ WAIT & SEE (Volatilitas Netral / Belum Ada Trigger Scalp)"

        tp_scalp_usd = harga_usd * 1.012
        sl_scalp_usd = harga_usd * 0.994
        p_tp = 1.2
        p_sl = 0.6

        kurs_idr = harga_idr / harga_usd if harga_usd > 0 else 15500

        return {
            "coin": f"{name.upper()} ({coin_id})",
            "harga_usd": f"{harga_usd:,.8f}" if harga_usd < 1 else f"{harga_usd:,.2f}",
            "harga_idr": f"{harga_idr:,.4f}" if harga_idr < 1000 else f"{harga_idr:,.2f}",
            "stoch_rsi": f"{stoch_rsi}",
            "status": status,
            "tp_scalp": f"{tp_scalp_usd:,.8f}" if tp_scalp_usd < 1 else f"{tp_scalp_usd:,.4f}",
            "tp_idr": f"{int(tp_scalp_usd * kurs_idr):,}".replace(",", "."),
            "p_tp": f"{p_tp}",
            "sl_scalp": f"{sl_scalp_usd:,.8f}" if sl_scalp_usd < 1 else f"{sl_scalp_usd:,.4f}",
            "sl_idr": f"{int(sl_scalp_usd * kurs_idr):,}".replace(",", "."),
            "p_sl": f"{p_sl}"
        }
    except:
        return None

if __name__ == "__main__":
    app.run()