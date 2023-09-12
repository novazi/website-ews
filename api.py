from flask import Flask, request, redirect, url_for, session, jsonify, render_template, Response
import sqlite3
import requests
from time import sleep
from datetime import datetime, timedelta
import io
import csv

# Setup Awal
app = Flask(__name__)
app.secret_key = 'asdavi0104'

def cek_user(username, password):
    con = sqlite3.connect('database.db') # Menghubungkan ke database
    cur = con.cursor()
    # Memilih data di database
    cur.execute('SELECT username,password FROM dbusers WHERE username=? and password=?', (username, password))
    result = cur.fetchone()
    if result:
        return True
    else:
        return False

def cek_lokasi(lokasi, lon, lat):
    con = sqlite3.connect('database.db') # Menghubungkan ke database
    cur = con.cursor()
    # Memilih data di database
    cur.execute('SELECT lokasi, longitude, latitude FROM dblokasi WHERE lokasi=? AND longitude=? AND latitude=?', (lokasi, lon, lat))
    result = cur.fetchone()
    if result:
        return True
    else:
        return False

def getData():
    con = sqlite3.connect('database.db') # Menghubungkan ke database
    cur = con.cursor()
    # Memilih data di database
    cur.execute("SELECT waktu, pergeseran FROM dbdata")# ORDER BY waktu LIMIT 20")
    data = cur.fetchall()
    waktu = []
    pergeseran = []
    for row in data:
        if row[1] == 3:
            row[1] = 0
        waktu.append(row[0])
        pergeseran.append(row[1])
    grafik = [waktu, pergeseran]
    return grafik

# Route untuk Menampilkan data terakhir
@app.route('/cek_data', methods = ["GET"])
def getDataLine():
    con = sqlite3.connect('database.db') # Menghubungkan ke database
    cur = con.cursor()
    # Memilih data di database
    cur.execute("SELECT waktu, pergeseran FROM dbdata ORDER BY waktu DESC")
    data = cur.fetchall()
    waktu = []
    pergeseran = []
    for row in data:
        if row[1] == 3:
            row[1] = 0
        waktu.append(row[0])
        pergeseran.append(row[1])
    data_api = {'waktu':waktu, 'data':pergeseran}
    resp = jsonify(data_api)
    resp.status_code = 200
    return resp

# Route untuk Error
@app.errorhandler(400)
def gagal():
    message = {
        'status': 400,
        'pesan': 'Perintah tidak dapat dijalankan: '+request.url,
    }
    resp = jsonify(message)
    resp.status_code = 400
    return resp

# Route untuk Index
@app.route('/')
def index():
    return render_template('login.html')

# Route untuk Menambahkan data ke Tabel Lokasi
@app.route('/add_lokasi', methods = ["POST"])
def add_lokasi():
    con = sqlite3.connect('database.db') # Menghubungkan ke database
    cur = con.cursor()
    json = request.json # data dari request data bentuk json
    id_lokasi = json['id_lokasi']
    lokasi = json['lokasi']
    lon = json['lon']
    lat = json['lat']
    if id_lokasi and lokasi and lon and lat and request.method == 'POST':
        query = "INSERT INTO `dblokasi`(`id_lokasi`, `lokasi`, `longitude`, `latitude`) VALUES (?,?,?,?)"
        data = (id_lokasi, lokasi, lon, lat)
        cur.execute(query, data)
        con.commit()
        resp = jsonify('Berhasil')
        resp.status_code = 200
        return resp
    else:
        return gagal()
    cur.close()
    con.close()

# Route untuk Menambahkan data ke Tabel Data
@app.route('/add_data', methods = ["GET"])
def add_data():
    con = sqlite3.connect('database.db') # Menghubungkan ke database
    cur = con.cursor()
    #json = request.json # data dari request data bentuk json
    id_lokasi = request.args.get("lokasi")
    pergeseran = request.args.get("data")
    #waktu = request.args.get("waktu")
    if id_lokasi and pergeseran and request.method == 'GET':
        query = "INSERT INTO 'dbdata'(`id_lokasi`, `pergeseran`) VALUES (?,?)"
        data = (id_lokasi, pergeseran)
        cur.execute(query, data)
        con.commit()
        resp = jsonify('Berhasil')
        resp.status_code = 200
        return resp
    else:
        return gagal()
    cur.close()
    con.close()

# Route untuk request ke telegram
@app.route('/warning-telegram')
def telewarning():
    teleAPI = "https://api.telegram.org/bot5480267615:AAFtEcgGezak5ixnBWNhcXhIYThWY9tolyw/sendMessage?chat_id=-1001799754305&text=Waspada Longsor!"
    for i in range(5):
        requests.request("GET", teleAPI)
        sleep(2)
    resp = jsonify('Terkirim')
    resp.status_code = 200
    return resp

# Route untuk Login
@app.route("/login", methods = ["POST"])
def login():
    if request.method == "POST":
        username = request.form['username'] # data dari masukan form di Web
        password = request.form['password'] # data dari masukan form di Web
        if cek_user(username, password): # Membuat session
            session['username'] = username
            session['password'] = password
        return redirect(url_for('home'))
    else:
        redirect(url_for('index'))

@app.route('/home', methods=['POST', 'GET'])
def home():
    if 'username' in session and 'password' in session:
        con = sqlite3.connect('database.db') # Menghubungkan ke database
        cur = con.cursor()
        cur.execute("SELECT `dblokasi`.`lokasi`, `dbdata`.`waktu`, `dbdata`.`pergeseran` FROM `dblokasi`, `dbdata` WHERE DATETIME(`dbdata`.`waktu`) >= DATETIME('now', 'start of day', '-7 hours') ORDER by `dbdata`.`waktu` DESC")
        data = cur.fetchall()
        data_api=[]
        for i in range(0, len(data)) :
            data[i] = list(data[i])
            data[i][1] = str(datetime.strptime(data[i][1], "%Y-%m-%d %H:%M:%S") + timedelta(hours=7))
        for b in (data):
            if b[2] == 3:
                b[2] = 0
            data_api.append({
                'lokasi' : b[0],
                'waktu' : b[1],
                'pergeseran' : b[2],
            })
        return render_template('home.html', data=data, data_api=data_api)
   
    else:
        return redirect(url_for('login'))

@app.route('/download/report_hariini/csv')
def download_report_hariini():
    con = sqlite3.connect('database.db') # Menghubungkan ke database
    cur = con.cursor()
    cur.execute("SELECT `dblokasi`.`lokasi`, `dbdata`.`waktu`, `dbdata`.`pergeseran` FROM `dblokasi`, `dbdata` WHERE DATETIME(`dbdata`.`waktu`) >= DATETIME('now', 'start of day', '-7 hours') ORDER by `dbdata`.`waktu` DESC")
    data = cur.fetchall()
    data_api=[]
    for i in range(0, len(data)) :
        data[i] = list(data[i])
        data[i][1] = str(datetime.strptime(data[i][1], "%Y-%m-%d %H:%M:%S") + timedelta(hours=7))
    for b in (data):
        if b[2] == 3:
            b[2] = 0
        data_api.append({
            'lokasi' : b[0],
            'waktu' : b[1],
            'pergeseran' : b[2],
        })
    output = io.StringIO()
    writer = csv.writer(output)
    line = ['Lokasi, Waktu, Pergeseran (cm)']
    writer.writerow(line)
    for bb in data_api:
        line = [bb['lokasi']+','+str(bb['waktu'])+','+str(bb['pergeseran'])]
        writer.writerow(line)
    output.seek(0)
    return Response(output, mimetype='text/csv', headers={"Content-Disposition":"attachment;filename=dataewshariini.csv"})

@app.route('/semuadata', methods=['POST', 'GET'])
def semuadata():
    if 'username' in session and 'password' in session:
        con = sqlite3.connect('database.db') # Menghubungkan ke database
        cur = con.cursor()
        cur.execute("SELECT `dblokasi`.`lokasi`, `dbdata`.`waktu`, `dbdata`.`pergeseran` FROM `dblokasi`, `dbdata` ORDER by `dbdata`.`waktu` DESC")
        data = cur.fetchall()
        data_api=[]
        for i in range(0, len(data)) :
            data[i] = list(data[i])
            data[i][1] = str(datetime.strptime(data[i][1], "%Y-%m-%d %H:%M:%S") + timedelta(hours=7))
        for b in (data):
            if b[2] == 3:
                b[2] = 0
            data_api.append({
                'lokasi' : b[0],
                'waktu' : b[1],
                'pergeseran' : b[2],
            })
        return render_template('semuadata.html', data=data, data_api=data_api)
   
    else:
        return redirect(url_for('login'))

@app.route('/download/report_semuadata/csv')
def download_report_semuadata():
    con = sqlite3.connect('database.db') # Menghubungkan ke database
    cur = con.cursor()
    cur.execute("SELECT `dblokasi`.`lokasi`, `dbdata`.`waktu`, `dbdata`.`pergeseran` FROM `dblokasi`, `dbdata` ORDER by `dbdata`.`waktu` DESC")
    data = cur.fetchall()
    data_api=[]
    for i in range(0, len(data)) :
        data[i] = list(data[i])
        data[i][1] = str(datetime.strptime(data[i][1], "%Y-%m-%d %H:%M:%S") + timedelta(hours=7))
    for b in (data):
        if b[2] == 3:
            b[2] = 0
        data_api.append({
            'lokasi' : b[0],
            'waktu' : b[1],
            'pergeseran' : b[2],
        })
    output = io.StringIO()
    writer = csv.writer(output)
    line = ['Lokasi, Waktu, Pergeseran (cm)']
    writer.writerow(line)
    for bb in data_api:
        line = [bb['lokasi']+','+str(bb['waktu'])+','+str(bb['pergeseran'])]
        writer.writerow(line)
    output.seek(0)
    return Response(output, mimetype='text/csv', headers={"Content-Disposition":"attachment;filename=dataewssemuadata.csv"})

@app.route('/week', methods=['POST', 'GET'])
def weekdata():
    if 'username' in session and 'password' in session:
        con = sqlite3.connect('database.db') # Menghubungkan ke database
        cur = con.cursor()
        cur.execute("SELECT `dblokasi`.`lokasi`, `dbdata`.`waktu`, `dbdata`.`pergeseran` FROM `dblokasi`, `dbdata` WHERE DATETIME(`dbdata`.`waktu`) >= DATETIME('now', 'weekday 0', '-6 days', 'start of day', '-7 hours') ORDER by `dbdata`.`waktu` DESC")
        data = cur.fetchall()
        data_api=[]
        for i in range(0, len(data)) :
            data[i] = list(data[i])
            data[i][1] = str(datetime.strptime(data[i][1], "%Y-%m-%d %H:%M:%S") + timedelta(hours=7))
        for b in (data):
            if b[2] == 3:
                b[2] = 0
            data_api.append({
                'lokasi' : b[0],
                'waktu' : b[1],
                'pergeseran' : b[2],
            })
        return render_template('week.html', data=data, data_api=data_api)
   
    else:
        return redirect(url_for('login'))

@app.route('/download/report_mingguini/csv')
def download_report_mingguini():
    con = sqlite3.connect('database.db') # Menghubungkan ke database
    cur = con.cursor()
    cur.execute("SELECT `dblokasi`.`lokasi`, `dbdata`.`waktu`, `dbdata`.`pergeseran` FROM `dblokasi`, `dbdata` WHERE DATETIME(`dbdata`.`waktu`) >= DATETIME('now', 'weekday 0', '-6 days', 'start of day', '-7 hours') ORDER by `dbdata`.`waktu` DESC")
    data = cur.fetchall()
    data_api=[]
    for i in range(0, len(data)) :
        data[i] = list(data[i])
        data[i][1] = str(datetime.strptime(data[i][1], "%Y-%m-%d %H:%M:%S") + timedelta(hours=7))
    for b in (data):
        if b[2] == 3:
            b[2] = 0
        data_api.append({
            'lokasi' : b[0],
            'waktu' : b[1],
            'pergeseran' : b[2],
        })
    output = io.StringIO()
    writer = csv.writer(output)
    line = ['Lokasi, Waktu, Pergeseran (cm)']
    writer.writerow(line)
    for bb in data_api:
        line = [bb['lokasi']+','+str(bb['waktu'])+','+str(bb['pergeseran'])]
        writer.writerow(line)
    output.seek(0)
    return Response(output, mimetype='text/csv', headers={"Content-Disposition":"attachment;filename=dataewsmingguini.csv"})

@app.route('/month', methods=['POST', 'GET'])
def monthdata():
    if 'username' in session and 'password' in session:
        con = sqlite3.connect('database.db') # Menghubungkan ke database
        cur = con.cursor()
        cur.execute("SELECT `dblokasi`.`lokasi`, `dbdata`.`waktu`, `dbdata`.`pergeseran` FROM `dblokasi`, `dbdata` WHERE DATETIME(`dbdata`.`waktu`) >= DATETIME('now', 'start of month', 'start of day', '-7 hours') ORDER by `dbdata`.`waktu` DESC")
        data = cur.fetchall()
        data_api=[]
        for i in range(0, len(data)) :
            data[i] = list(data[i])
            data[i][1] = str(datetime.strptime(data[i][1], "%Y-%m-%d %H:%M:%S") + timedelta(hours=7))
        for b in (data):
            if b[2] == 3:
                b[2] = 0
            data_api.append({
                'lokasi' : b[0],
                'waktu' : b[1],
                'pergeseran' : b[2],
            })
        return render_template('month.html', data=data, data_api=data_api)
   
    else:
        return redirect(url_for('login'))

@app.route('/download/report_bulanini/csv')
def download_report_bulanini():
    con = sqlite3.connect('database.db') # Menghubungkan ke database
    cur = con.cursor()
    cur.execute("SELECT `dblokasi`.`lokasi`, `dbdata`.`waktu`, `dbdata`.`pergeseran` FROM `dblokasi`, `dbdata` WHERE DATETIME(`dbdata`.`waktu`) >= DATETIME('now', 'start of month', 'start of day', '-7 hours') ORDER by `dbdata`.`waktu` DESC")
    data = cur.fetchall()
    data_api=[]
    for i in range(0, len(data)) :
        data[i] = list(data[i])
        data[i][1] = str(datetime.strptime(data[i][1], "%Y-%m-%d %H:%M:%S") + timedelta(hours=7))
    for b in (data):
        if b[2] == 3:
            b[2] = 0
        data_api.append({
            'lokasi' : b[0],
            'waktu' : b[1],
            'pergeseran' : b[2],
        })
    output = io.StringIO()
    writer = csv.writer(output)
    line = ['Lokasi, Waktu, Pergeseran (cm)']
    writer.writerow(line)
    for bb in data_api:
        line = [bb['lokasi']+','+str(bb['waktu'])+','+str(bb['pergeseran'])]
        writer.writerow(line)
    output.seek(0)
    return Response(output, mimetype='text/csv', headers={"Content-Disposition":"attachment;filename=dataewsbulanini.csv"})

# Route untuk Logout
@app.route('/logout')
def logout():
    session.clear() # Menghapus session
    return redirect(url_for('index'))

# Run Web
if __name__== "__main__":
    app.run("0.0.0.0",port=5005,debug=True)
