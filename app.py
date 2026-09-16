import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = 'clave_secreta_erotisex_2026'

# Permite cookies/tokens OAuth en entorno local HTTP
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Configuración Límite de carga (100 MB)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------------------------------------------
# CONFIGURACIÓN GOOGLE OAUTH
# ----------------------------------------------------
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='733970818476-ig4o4pj5l17f2a7kskb122io8jsm8p7d.apps.googleusercontent.com',
    client_secret='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',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

CATEGORIAS = [
    "Escorts / Acompañantes",
    "Masajistas",
    "Trans / Travestis",
    "Gays",
    "Gigolós",
    "Amigos / Citas",
    "Servicios Virtuales",
    "Sex Shop / Productos",
    "Agencias"
]

def get_db_connection():
    conn = sqlite3.connect('erotisex.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            tokens REAL DEFAULT 0.0,
            publicaciones_gratis INTEGER DEFAULT 4
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anuncios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            titulo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            edad INTEGER,
            pais TEXT,
            departamento TEXT,
            ciudad TEXT,
            descripcion TEXT,
            whatsapp TEXT,
            telegram TEXT,
            fotos TEXT,
            videos TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    pais = request.args.get('pais', '')
    categoria = request.args.get('categoria', '')
    departamento = request.args.get('departamento', '')
    ciudad = request.args.get('ciudad', '')
    busqueda = request.args.get('busqueda', '')

    # Verificamos si el usuario realizó alguna búsqueda
    busqueda_realizada = any([pais, categoria, departamento, ciudad, busqueda]) or ('pais' in request.args)

    anuncios = []

    if busqueda_realizada:
        query = 'SELECT * FROM anuncios WHERE 1=1'
        params = []

        if pais:
            query += ' AND pais = ?'
            params.append(pais)
        if categoria:
            query += ' AND categoria = ?'
            params.append(categoria)
        if departamento:
            query += ' AND departamento = ?'
            params.append(departamento)
        if ciudad:
            query += ' AND ciudad LIKE ?'
            params.append(f'%{ciudad}%')
        if busqueda:
            query += ' AND (titulo LIKE ? OR descripcion LIKE ?)'
            params.append(f'%{busqueda}%')
            params.append(f'%{busqueda}%')

        query += ' ORDER BY id DESC'

        conn = get_db_connection()
        anuncios = conn.execute(query, params).fetchall()
        conn.close()

    return render_template('index.html', anuncios=anuncios, categorias=CATEGORIAS, busqueda_realizada=busqueda_realizada)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO usuarios (email, password, tokens) VALUES (?, ?, 40)', (email, password))
            conn.commit()
            usuario = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
            session['usuario_id'] = usuario['id']
            session['email'] = usuario['email']
            conn.close()
            return redirect(url_for('panel'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Este correo ya está registrado.', 'error')
            return redirect(url_for('registro'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        conn = get_db_connection()
        usuario = conn.execute('SELECT * FROM usuarios WHERE email = ? AND password = ?', (email, password)).fetchone()
        conn.close()

        if usuario:
            session['usuario_id'] = usuario['id']
            session['email'] = usuario['email']
            return redirect(url_for('panel'))
        else:
            flash('Correo o contraseña incorrectos.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

# ----------------------------------------------------
# RUTAS DE INICIO CON GOOGLE REAL
# ----------------------------------------------------
@app.route('/login/google')
def login_google():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/google/callback')
def google_callback():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if not user_info:
        flash('No se pudo autenticar con Google.', 'error')
        return redirect(url_for('login'))

    google_email = user_info['email'].lower()

    conn = get_db_connection()
    usuario = conn.execute('SELECT * FROM usuarios WHERE email = ?', (google_email,)).fetchone()

    if not usuario:
        conn.execute('INSERT INTO usuarios (email, password, publicaciones_gratis) VALUES (?, ?, 4)', (google_email, 'oauth_google'))
        conn.commit()
        usuario = conn.execute('SELECT * FROM usuarios WHERE email = ?', (google_email,)).fetchone()

    session['usuario_id'] = usuario['id']
    session['email'] = usuario['email']
    conn.close()

    return redirect(url_for('panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/panel')
def panel():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    anuncios = conn.execute('SELECT * FROM anuncios WHERE usuario_id = ? ORDER BY id DESC', (session['usuario_id'],)).fetchall()
    conn.close()

    return render_template('panel.html', usuario=usuario, anuncios=anuncios)

@app.route('/publicar', methods=['GET', 'POST'])
def publicar():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()

    # Validar que tenga al menos 10 tokens
    if not usuario or usuario['tokens'] < 10:
        conn.close()
        flash('Saldo insuficiente. Necesitas al menos 10 Tokens para publicar.')
        return redirect(url_for('recargar'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        categoria = request.form['categoria']
        edad = request.form['edad']
        pais = request.form['pais']
        departamento = request.form['departamento']
        ciudad = request.form['ciudad']
        descripcion = request.form['descripcion']
        whatsapp = request.form['whatsapp']
        telegram = request.form.get('telegram', '')

        fotos = request.files.getlist('fotos')
        nombres_fotos = []
        for foto in fotos:
            if foto and foto.filename != '':
                filename = secure_filename(foto.filename)
                foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                nombres_fotos.append(filename)
        fotos_str = ','.join(nombres_fotos)

        videos = request.files.getlist('videos')
        nombres_videos = []
        for video in videos:
            if video and video.filename != '':
                filename = secure_filename(video.filename)
                video.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                nombres_videos.append(filename)
        videos_str = ','.join(nombres_videos)

        # Guardar anuncio
        conn.execute('''
            INSERT INTO anuncios (
                usuario_id, titulo, categoria, edad, pais, 
                departamento, ciudad, descripcion, whatsapp, telegram, fotos, videos
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['usuario_id'], titulo, categoria, edad, pais, 
            departamento, ciudad, descripcion, whatsapp, telegram, fotos_str, videos_str
        ))

        # Descontar los 10 tokens al usuario
        conn.execute('UPDATE usuarios SET tokens = tokens - 10 WHERE id = ?', (session['usuario_id'],))
        conn.commit()
        conn.close()

        flash('Anuncio publicado exitosamente. Se descontaron 10 Tokens.')
        return redirect(url_for('panel'))

    conn.close()
    return render_template('publicar.html', categorias=CATEGORIAS)

@app.route('/eliminar_anuncio/<int:anuncio_id>', methods=['POST'])
def eliminar_anuncio(anuncio_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM anuncios WHERE id = ? AND usuario_id = ?', (anuncio_id, session['usuario_id']))
    conn.commit()
    conn.close()

    return redirect(url_for('panel'))

@app.route('/eliminar_cuenta', methods=['POST'])
def eliminar_cuenta():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    user_id = session['usuario_id']
    conn = get_db_connection()
    conn.execute('DELETE FROM anuncios WHERE usuario_id = ?', (user_id,))
    conn.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

    session.clear()
    return redirect(url_for('home'))

@app.route('/anuncio/<int:anuncio_id>')
def detalle_anuncio(anuncio_id):
    conn = get_db_connection()
    anuncio = conn.execute('SELECT * FROM anuncios WHERE id = ?', (anuncio_id,)).fetchone()
    conn.close()
    
    if anuncio is None:
        return "Anuncio no encontrado", 404

    fotos_list = anuncio['fotos'].split(',') if anuncio['fotos'] else []
    videos_list = anuncio['videos'].split(',') if anuncio['videos'] else []

    return render_template('detalle.html', anuncio=anuncio, fotos_list=fotos_list, videos_list=videos_list)

# ----------------------------------------------------
# RUTAS DE ADMINISTRACIÓN
# ----------------------------------------------------
@app.route('/admin')
def admin():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    ads = conn.execute('SELECT * FROM anuncios ORDER BY id DESC').fetchall()
    conn.close()

    return render_template('admin.html', ads=ads)

@app.route('/admin/eliminar/<int:id>', methods=['POST'])
def admin_eliminar_anuncio(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM anuncios WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)