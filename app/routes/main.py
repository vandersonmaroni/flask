# app/routes/main.py
from flask import Blueprint, jsonify, request, current_app, render_template, redirect, url_for, flash, session
from app import db
from bson import ObjectId
from pydantic import ValidationError
from app.decorators import token_required
from app.models.user import LoginPayload
from app.models.product import *
from app.models.sale import Sale
from datetime import datetime, timedelta, timezone
import jwt
import io
import csv

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def index():
    if 'jwt_token' not in session:
        return redirect(url_for('main_bp.login'))
    return redirect(url_for('main_bp.dashboard'))

@main_bp.route('/dashboard')
def dashboard():
    if 'jwt_token' not in session:
        return redirect(url_for('main_bp.login'))
    return render_template('dashboard.html', title='Dashboard')

# --- ROTAS DE AUTENTICAÇÃO ---

# RF: O sistema deve permitir que um usuário se autentique para obter um token.
@main_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_data = LoginPayload(username=username, password=password)
    
        user_in_db = db.users.find_one({"username": username})

        if user_in_db and user_in_db.get('password') == password:
            token = jwt.encode({
                'user_id': user_data.username,
                'exp': datetime.now(timezone.utc) + timedelta(minutes=30) # Token expira em 30 minutos
            }, current_app.config['SECRET_KEY'], algorithm="HS256")

            session['jwt_token'] = token    
            return redirect(url_for('main_bp.dashboard'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
            return redirect(url_for('main_bp.login'))
    
    return render_template('login.html', title='Login')


# --- ROTAS DE PRODUTOS (CRUD Completo) ---

# RF: O sistema deve permitir a listagem de todos os produtos.
@main_bp.route('/produtos', methods=['GET'])
def get_products():
    if 'jwt_token' not in session:
        return redirect(url_for('main_bp.login'))
        
    products_cursor = db.products.find({})
    return render_template('products.html', products=products_cursor, title='Produtos')


# RF: O sistema deve permitir a criação de um novo produto.
@main_bp.route('/produtos', methods=['POST'])
@token_required
def create_product(jwt_token): #Recebendo os dados do usuário autenticado
    try:
        product = Product(**request.get_json())
        product_result = db.products.insert_one(product.model_dump())
        return jsonify({'message': f'Produto ({product.name}) com o id ({product_result}) criado com sucesso!'})
    except ValidationError as e:
        return jsonify({'errors': e.errors()}), 400


# RF: O sistema deve permitir a visualização dos detalhes de um único produto.
# O <int:product_id> é um parâmetro dinâmico na URL. O Flask o captura
# e o passa como argumento para a nossa função.
@main_bp.route('/produto/<string:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    try:
        oid = ObjectId(product_id)
    except Exception:
        return jsonify({"error": "ID do produto inválido"}), 400

    product = db.products.find_one({"_id": oid})

    if product:
        product_model = ProductDBModel(**product).model_dump(by_alias=True, exclude=None)
        return jsonify(product_model)
    else:
        return jsonify({"error": "Produto não encontrado"}), 404


# RF: O sistema deve permitir a atualização de um produto existente.
@main_bp.route('/produto/<string:product_id>', methods=['PUT'])
@token_required
def update_product(jwt_token, product_id):
    try:
        oid = ObjectId(product_id)
        update_data = UpdateProduct(**request.get_json())
    except ValidationError as e:
        return jsonify({"errors": e.errors()}), 400

    update_result = db.products.update_one(
        {"_id": oid}, 
        {"$set": update_data.model_dump(exclude_unset=True)})
    
    if update_result.matched_count == 0: # Não encontramos nenhum produto com esse ID
        return jsonify({"error": "Produto não encontrado"}), 404

    updated_product = db.products.find_one({"_id": oid})
    return jsonify(ProductDBModel(**updated_product).model_dump(by_alias=True, exclude=None))

# RF: O sistema deve permitir a deleção de um produto existente.
@main_bp.route('/produto/<string:product_id>', methods=['DELETE'])
@token_required
def delete_product(jwt_token, product_id):
    try:
        oid = ObjectId(product_id)
    except Exception:
        return jsonify({"error": "ID do produto inválido"}), 400

    delete_result = db.products.delete_one({"_id": oid})

    if delete_result.deleted_count == 0:
        return jsonify({"error": "Produto não encontrado"}), 404
    
    return "", 204


# --- ROTAS DE VENDAS ---


@main_bp.route('/vendas/upload', methods=['GET'])
def upload_sales_page():
    if 'jwt_token' not in session:
        return redirect(url_for('main_bp.login'))
    return render_template('upload_sales.html', title='Upload de Vendas')


# RF: O sistema deve permitir a importação de vendas através de um arquivo.
@main_bp.route('/vendas/upload', methods=['POST'])
def upload_sales():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400

    if file and file.filename.endswith('.csv'):
        stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
        csv_reader = csv.DictReader(stream)

        sales_to_insert = []
        errors = []

        for row_num, row in enumerate(csv_reader, 1):
            try:
                sale_data = Sale(**row)
                if not db.products.find_one({"_id": ObjectId(sale_data.product_id)}):
                    errors.append(f"Linha {row_num}: Produto com ID '{sale_data.product_id}' não encontrado.")
                    continue  # Pula para a próxima linha
                sales_to_insert.append(sale_data.model_dump())

            except ValidationError as e:
                errors.append(f"Linha {row_num}: Dados inválidos - {e.errors()}")
            except Exception as e:
                errors.append(f"Linha {row_num}: Erro inesperado ao processar a linha - {str(e)}")

        if sales_to_insert:
            try:
                db.sales.insert_many(sales_to_insert)
            except Exception as e:
                 return jsonify({"error": f"Erro ao inserir dados no banco: {e}"}), 500

        return jsonify({
            "message": "Upload processado com sucesso.",
            "vendas_importadas": len(sales_to_insert),
            "erros_encontrados": errors
        }), 200

    return jsonify({"error": "Formato de arquivo inválido. Por favor, envie um arquivo .csv"}), 400