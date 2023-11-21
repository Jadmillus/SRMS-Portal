from flask import render_template, request, flash, redirect, url_for
from app.stock import bp
from app.forms import EditStocks
from app.models import Stock, Category, Request
from flask_login import current_user, login_required
from app.extensions import db

@bp.route('/admin/stocks', methods = ['GET','POST'])
@login_required
def stocks():
    if not current_user.isAdmin: abort(403) 
    categories = Category.query.all()
    if request.method == 'GET':
        stocks = Stock.query.all()
        return render_template('stocks.html', stocks = stocks, categories = categories)
    else:
        stock = Stock.query.filter_by(id = request.form['id']).first()
        stock.avail = int(request.form['avail_text'] )
        stock.qty_req  = int(request.form['qty_text'] )
        db.session.commit()
        flash(f'Stock Updated', 'success')
        return redirect(url_for('stocks'))


@bp.route('/admin/stocks/edit/<int:stock_id>', methods=['GET', 'POST'])
def edit_stock(stock_id):
    if not current_user.isAdmin: abort(403) 
    stock = Stock.query.get_or_404(stock_id)
    form = EditStocks()
    form.category.choices = [(cat.id, cat.name) for cat in Category.query.all()]
    if form.validate_on_submit():
        stock.item = form.stock_name.data 
        stock.category_id = form.category.data
        stock.avail = form.avail.data
        stock.qty_req = form.quantity_req.data
        stock.maximum_limit = form.maximum_limit.data
        stock.minimum_limit = form.minimum_limit.data
        stock.quota = form.quota.data

        db.session.commit()
        flash('Stock updated successfully', 'success')
        return redirect(url_for('stock.stocks'))

    form.stock_name.data = stock.item
    form.avail.data = stock.avail
    form.quantity_req.data = stock.qty_req
    form.maximum_limit.data = stock.maximum_limit
    form.minimum_limit.data = stock.minimum_limit
    form.quota.data = stock.quota

    return render_template('edit_stocks.html', form = form)


@bp.route('/admin/stocks/add', methods=['POST'])
@login_required
def add_stocks():
    if not current_user.isAdmin: abort(403) 
    form = request.form
    if form['qty_req'].isnumeric() and form['avail'].isnumeric() \
        and form['quota'].isnumeric() and form['minimum_limit'].isnumeric()\
        and form['maximum_limit'].isnumeric():
        stck = Stock(
            item = form['name'],
            category_id = int(form['category_id']),
            qty_prev = 0,
            avail = int(form['avail']),
            qty_req = int(form['qty_req']),
            qty_pres = 0,
            maximum_limit = int(form['maximum_limit']),
            minimum_limit = int(form['minimum_limit']),
            quota = int(form['quota'])
        )
        db.session.add(stck)
        db.session.commit()
        flash(f'Stock added Successfully', 'success')
    else:
        flash(f'Invalid Details', 'danger')

    return redirect(url_for('stock.stocks'))


@bp.route('/admin/stock/reset')
@login_required
def reset():
    if not current_user.isAdmin: abort(403) 
    stocks = Stock.query.all()
    path =os.path.join(app.root_path , 'static/downloads/stock.csv')
    with open(path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Id', 'Previous semester', 'Available', 'Quantity Required', 'Quantity present'])
        for element in stocks:
            writer.writerow([element.id, element.qty_prev, element.avail, element.qty_req, element.qty_pres])
    for element in stocks:
        element.qty_prev = element.qty_pres
        element.qty_pres = 0 
    return send_file(path, as_attachment=True)

# View all the stocks
@bp.route('/user/home', methods=['GET', 'POST'])
@login_required
def user_home():
    stocks = Stock.query.all()
    quota = []
    for stock in stocks:
        requests = Request.query.filter_by(user_id = current_user.id, stock_id= stock.id).all()
        temp = 0
        for i in requests:
            if i.status == 0 or i.status == 1:
                temp += i.qty
        quota_left = max(0, stock.quota - temp)
        quota.append(quota_left)

    return render_template("user.html", stocks = stocks, quota = quota, length = len(quota))

# view all the stocks of a category 
@bp.route('/categories/<int:category_id>')
def category(category_id):
    stocks = Stock.query.filter_by(category_id = category_id).all()
    quota = []
    for stock in stocks:
        requests = Request.query.filter_by(user_id = current_user.id, stock_id= stock.id).all()
        temp = 0
        for i in requests:
            if i.status == 0 or i.status == 1:
                temp += i.qty
        quota_left = max(0, stock.quota - temp)
        quota.append(quota_left)
    return render_template('user.html', stocks= stocks, quota = quota, length = len(quota))

@bp.route('/admin/stock/download', methods = ['POST'])
@login_required
def download():
    if not current_user.isAdmin: abort(403) 
    stocks = Stock.query.all()
    path =os.path.join(app.root_path , 'static/downloads/stock.csv')
    with open(path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Id', 'Previous semester', 'Available', 'Quantity Required', 'Quantity present'])
        for element in stocks:
            writer.writerow([element.id, element.qty_prev, element.avail, element.qty_req, element.qty_pres])
    return send_file(path, as_attachment=True)
