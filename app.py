import csv
import os
from flask import Flask, render_template, request
import random
import time
import math

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_FILE = os.path.join(BASE_DIR, 'disbun-od_18716_rata_rata_harga_produsen_kopi_robusta_berasan__per_v2_data.csv')

def parse_indonesian_currency(value_str):
    """
    Membersihkan format angka Indonesia:
    Contoh: "25532,25806" -> 25532 (Diambil bulatnya saja)
    Contoh: "18000" -> 18000
    """
    if not value_str or value_str.strip() == '-' or value_str.strip() == '':
        return 0
    try:
        # Bersihkan tanda kutip jika ada
        clean_str = value_str.replace('"', '').strip()
        
        # Ganti koma (desimal Indo) jadi titik, lalu ambil angka depannya saja (int)
        # Kita ambil int karena harga biasanya dibulatkan
        if ',' in clean_str:
            clean_str = clean_str.replace(',', '.')
            return int(float(clean_str))
        
        return int(float(clean_str))
    except ValueError:
        return 0

def load_dataset():
    data_by_city = {}
    cities = set()
    
    if not os.path.exists(DATASET_FILE):
        return {}, []

    try:
        with open(DATASET_FILE, mode='r', encoding='utf-8-sig') as file:
            # Menggunakan Sniffer untuk menebak delimiter (koma atau titik koma)
            sample = file.read(1024)
            file.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample)
                delimiter = dialect.delimiter
            except:
                delimiter = ','

            reader = csv.DictReader(file, delimiter=delimiter)
            
            # Normalisasi nama kolom (hilangkan spasi)
            if reader.fieldnames:
                reader.fieldnames = [name.strip() for name in reader.fieldnames]

            for row in reader:
                city = row.get('nama_kabupaten_kota') or row.get('nama_kabupaten/kota')
                price_str = row.get('rata_rata_harga_produsen') or row.get('harga')

                if city and price_str:
                    price = parse_indonesian_currency(price_str)
                    
                    # FILTER PENTING:
                    # Kita hanya mengambil data harga > 0. 
                    # Harga 0 biasanya berarti tidak ada data/transaksi, bukan gratis.
                    if price > 0:
                        if city not in data_by_city:
                            data_by_city[city] = []
                        
                        data_by_city[city].append(price)
                        cities.add(city)

    except Exception as e:
        print(f"Error reading CSV: {e}")
        return {}, []

    return data_by_city, sorted(list(cities))

def calculate_monte_carlo(data_history, num_predictions):
    # Sorting dan Frequency
    unique_data = sorted(list(set(data_history)))
    frequency = {x: data_history.count(x) for x in unique_data}
    total_data = len(data_history)
    
    table_stats = []
    cumulative = 0
    interval_start = 0
    
    for val in unique_data:
        freq = frequency[val]
        prob = freq / total_data
        cumulative += prob
        
        # Mapping interval 0-99
        interval_limit = int(round(cumulative * 100)) 
        interval_end = interval_limit - 1 if interval_limit > 0 else 0
        
        # Fix presisi agar ujungnya pasti 99
        if val == unique_data[-1]: 
            interval_end = 99
        
        # Fix jika interval start melompati end (kasus probabilitas sangat kecil)
        if interval_start > interval_end:
            interval_end = interval_start

        table_stats.append({
            'demand': val, # Disini konteksnya 'Price'
            'freq': freq,
            'prob': round(prob, 4),
            'cumulative': round(cumulative, 4),
            'interval_min': interval_start,
            'interval_max': interval_end
        })
        interval_start = interval_end + 1

    simulation_results = []
    predicted_prices = []
    
    for i in range(1, num_predictions + 1):
        rand_num = random.randint(0, 99)
        prediction = 0
        
        for row in table_stats:
            if row['interval_min'] <= rand_num <= row['interval_max']:
                prediction = row['demand']
                break
        
        predicted_prices.append(prediction)
        simulation_results.append({
            'period': i, # Bulan ke-
            'random_num': rand_num,
            'prediction': prediction
        })
    
    avg_price = sum(predicted_prices) / len(predicted_prices) if predicted_prices else 0
    
    # Format Rupiah untuk tampilan
    formatted_avg = "{:,.0f}".format(avg_price).replace(',', '.')
    
    return table_stats, simulation_results, formatted_avg, len(data_history)

@app.route('/', methods=['GET', 'POST'])
def index():
    dataset, cities_list = load_dataset()
    
    if request.method == 'POST':
        try:
            time.sleep(0.8) # Efek loading UX
            
            selected_city = request.form.get('city')
            # Default prediksi 5 bulan ke depan (dataset ini bulanan)
            n_pred = int(request.form.get('n_pred', 5)) 
            
            if selected_city in dataset:
                data_list = dataset[selected_city]
                
                # Tampilkan max 50 data terakhir saja di UI agar tidak penuh text
                display_limit = data_list[-50:] 
                raw_data_display = ", ".join([str(x) for x in display_limit]) + ("..." if len(data_list) > 50 else "")
                
                stats, sim, avg, total_samples = calculate_monte_carlo(data_list, n_pred)
                
                return render_template('index.html', 
                                       stats=stats, 
                                       sim=sim, 
                                       avg=avg, 
                                       cities=cities_list, 
                                       selected_city=selected_city,
                                       raw_data=raw_data_display,
                                       total_samples=total_samples,
                                       unit="Rp")
            else:
                return render_template('index.html', cities=cities_list, error="Data kota tidak ditemukan atau belum ada transaksi harga (0).")
        except Exception as e:
            return render_template('index.html', cities=cities_list, error=f"Error sistem: {e}")
            
    return render_template('index.html', cities=cities_list)

if __name__ == '__main__':
    app.run(debug=True)