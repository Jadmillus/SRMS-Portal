from flask import render_template, url_for, flash
from app.forms import EditCategoryForm
from app.models import Stock, Category
from app.category import bp
from flask_login import current_user, login_required
import secrets
from flask import current_app as app
from PIL import Image
import os
from app.extensions import db

# view all the categories
@bp.route('/admin/categories')
def admin_categories():
    if not current_user.isAdmin: abort(403) 
    cat = Category.query.all()
    return render_template('admin_categories.html', categories = cat)

# view all the stocks in a category
@bp.route('/admin/categories/<int:category_id>')
def admin_category(category_id):
    if not current_user.isAdmin: abort(403) 
    stocks = Stock.query.filter_by(category_id = category_id).all()
    categories = Category.query.all()
    quota = []
    for stock in stocks:
        requests = Request.query.filter_by(user_id = current_user.id, stock_id= stock.id).all()
        temp = 0
        for i in requests:
            if i.status == 0 or i.status == 1:
                temp += i.qty
        quota_left = max(0, stock.quota - temp)
        quota.append(quota_left)
    return render_template('stocks.html', stocks= stocks, quota = quota, length = len(quota), categories=categories)

# add a new category
@bp.route('/admin/category/add', methods=['POST'])
@login_required
def add_category():
    if not current_user.isAdmin: abort(403) 
    form = request.form
    cat = Category(
        name=form['name'],
        picture = save_picture(request.files['picture'], 'category')
    )
    db.session.add(cat)
    db.session.commit()
    flash(f'Category added Successfully', 'success')

    return redirect(url_for('admin_categories'))

@bp.route('/admin/category/edit/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    if not current_user.isAdmin: abort(403) 
    category = Category.query.get_or_404(category_id)
    form = EditCategoryForm()
    
    if form.validate_on_submit():
        if form.picture.data:
            picture_name = save_picture(form.picture.data, "category")
            category.picture = picture_name
        category.name = form.name.data
        db.session.commit()
        flash('Category Details Updated Successfully!', 'success')
    form.name.data = category.name
    form.picture.data = category.picture
    return render_template('edit_category.html', form = form)

@bp.route('/categories')
def categories():
    cat = Category.query.all()
    return render_template('categories.html', categories = cat)


def save_picture(form_picture, folder):
    """
    Input : picture and folder name 
    output: picture location
    """
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path , 'static/images/' + folder + "/" , picture_fn)
    output_size = (250, 250)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn