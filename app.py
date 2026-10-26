import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from supabase import create_client, Client
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'lightfirm-secret-123')

# Mail Config
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

bcrypt = Bcrypt(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'lightfirm-portfolio')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

class AdminUser(UserMixin):
    def __init__(self, id):
        self.id = id

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_EMAIL:
        return AdminUser(user_id)
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        stored_hash = os.getenv('ADMIN_PASSWORD_HASH')
        
        if email == ADMIN_EMAIL and stored_hash and bcrypt.check_password_hash(stored_hash, password):
            user = AdminUser(email)
            login_user(user)
            return redirect(url_for('admin'))
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/portfolios')
def get_portfolios():
    try:
        res = supabase.table('portfolios').select('*').order('created_at', desc=True).execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_portfolio():
    try:
        title = request.form.get('title')
        category = request.form.get('category')
        file = request.files.get('image')
        if not title or not category or not file:
            return jsonify({'error': 'Title, category and image required'}), 400
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        file_bytes = file.read()
        supabase_admin.storage.from_(SUPABASE_BUCKET).upload(
            path=filename, file=file_bytes,
            file_options={"content-type": file.content_type}
        )
        public_url = supabase_admin.storage.from_(SUPABASE_BUCKET).get_public_url(filename)
        supabase_admin.table('portfolios').insert({
            "title": title, "category": category, "image_url": public_url
        }).execute()
        return jsonify({'success': True, 'url': public_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete/<id>', methods=['DELETE'])
@login_required
def delete_portfolio(id):
    try:
        item = supabase_admin.table('portfolios').select('*').eq('id', id).single().execute()
        if item.data:
            image_url = item.data['image_url']
            filename = image_url.split('/')[-1]
            try:
                supabase_admin.storage.from_(SUPABASE_BUCKET).remove([filename])
            except:
                pass
            supabase_admin.table('portfolios').delete().eq('id', id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def send_contact():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            data = request.form
        
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        message_text = (data.get('message') or '').strip()

        if not name or not email or not message_text:
            return jsonify({'error': 'All fields required'}), 400

        # Save to Supabase only
        supabase_admin.table('contact_messages').insert({
            "name": name,
            "email": email,
            "message": message_text
        }).execute()

        return jsonify({'success': True})

    except Exception as e:
        print("CONTACT ERROR:", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages')
@login_required
def get_messages():
    try:
        res = supabase_admin.table('contact_messages').select('*').order('created_at', desc=True).execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/<id>', methods=['DELETE'])
@login_required
def delete_message(id):
    try:
        supabase_admin.table('contact_messages').delete().eq('id', id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# ========== ANALYTICS ROUTES ==========

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/analytics/<id>')
def analytics_detail(id):
    try:
        res = supabase.table('analytics_projects').select('*').eq('id', id).single().execute()
        if not res.data:
            return "Project not found", 404
        return render_template('analytics_detail.html', project=res.data)
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/api/analytics')
def get_analytics():
    try:
        res = supabase.table('analytics_projects').select('*').order('created_at', desc=True).execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/<id>')
def get_single_analytics(id):
    try:
        res = supabase.table('analytics_projects').select('*').eq('id', id).single().execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/upload', methods=['POST'])
@login_required
def upload_analytics():
    try:
        title = request.form.get('title')
        tools = request.form.get('tools')
        description = request.form.get('description')
        insights = request.form.get('insights')
        dashboard_link = request.form.get('dashboard_link')
        github_link = request.form.get('github_link')
        embed_code = request.form.get('embed_code')
        image_file = request.files.get('image')
        dataset_file = request.files.get('dataset')

        if not title or not tools or not image_file:
            return jsonify({'error': 'Title, tools and dashboard image required'}), 400

        # Upload dashboard image
        img_name = f"{uuid.uuid4().hex}_{secure_filename(image_file.filename)}"
        supabase_admin.storage.from_(SUPABASE_BUCKET).upload(
            path=img_name, file=image_file.read(),
            file_options={"content-type": image_file.content_type}
        )
        image_url = supabase_admin.storage.from_(SUPABASE_BUCKET).get_public_url(img_name)

        dataset_url = None
        dataset_type = None
        if dataset_file and dataset_file.filename:
            ds_name = f"dataset_{uuid.uuid4().hex}_{secure_filename(dataset_file.filename)}"
            dataset_type = dataset_file.filename.split('.')[-1].lower()
            supabase_admin.storage.from_(SUPABASE_BUCKET).upload(
                path=ds_name, file=dataset_file.read(),
                file_options={"content-type": dataset_file.content_type}
            )
            dataset_url = supabase_admin.storage.from_(SUPABASE_BUCKET).get_public_url(ds_name)

        supabase_admin.table('analytics_projects').insert({
            "title": title,
            "tools": tools,
            "description": description,
            "insights": insights,
            "image_url": image_url,
            "dashboard_link": dashboard_link,
            "github_link": github_link,
            "embed_code": embed_code,
            "dataset_url": dataset_url,
            "dataset_type": dataset_type
        }).execute()

        return jsonify({'success': True})
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/delete/<id>', methods=['DELETE'])
@login_required
def delete_analytics(id):
    try:
        item = supabase_admin.table('analytics_projects').select('*').eq('id', id).single().execute()
        if item.data:
            fname = item.data['image_url'].split('/')[-1]
            try:
                supabase_admin.storage.from_(SUPABASE_BUCKET).remove([fname])
            except: pass
            if item.data.get('dataset_url'):
                try:
                    ds_fname = item.data['dataset_url'].split('/')[-1]
                    supabase_admin.storage.from_(SUPABASE_BUCKET).remove([ds_fname])
                except: pass
            supabase_admin.table('analytics_projects').delete().eq('id', id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)