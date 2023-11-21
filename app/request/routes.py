from flask import render_template, url_for, flash, request, redirect
from app.forms import RequestForm
from app.models import Request, Stock, SpecialRequest
from app import db
from flask_login import current_user, login_required
from app.request import bp


#display all requests
@bp.route('/admin/requests')
@login_required
def admin_request():
    if not current_user.isAdmin: abort(403) 
    request = Request.query.all()[::-1]
    return render_template('request.html', requests = request) 

#accept request
@bp.route('/admin/request/accept/<int:req_id>', methods = ['POST'])
@login_required
def accept_request(req_id):    
    if not current_user.isAdmin : abort(403)
    request_quantity = request.form['request_quantity']
    admin_comment = request.form['admincomment']

    if not request_quantity.isnumeric():
        flash('Quantity should be a number', 'danger')
        return redirect(url_for('admin_request'))

    req  = Request.query.get_or_404(req_id)
    request_quantity = int(request_quantity)

    if request_quantity > req.original_quantity or request_quantity > req.stock.avail:
        flash('You cannot accept more than the user has requested or more than the available quantity', 'danger')
        return redirect(url_for('admin_request'))
    req.qty = request_quantity
    req.status = 1
    req.processed_by = current_user.first_name + " " + current_user.last_name 
    req.admins_comment = admin_comment
    db.session.commit()
    flash('Request Accepted', 'success')
    return redirect(url_for('request.admin_request'))

@bp.route('/admin/request/delete/<int:req_id>', methods = ['POST'])
@login_required
def reject_request(req_id):
    if not current_user.isAdmin: abort(403) 
    req  = Request.query.get_or_404(req_id)
    req.status = -1
    req.admins_comment = request.form['admincomment']
    req.processed_by = current_user.first_name + " " + current_user.last_name 
    db.session.commit()
    flash('Request rejected','danger')
    return redirect(url_for('request.admin_request'))


# view all the processed request
@bp.route('/admin/requests/summary')
@login_required
def admin_summary():
    if not current_user.isAdmin: abort(403) 
    requests = Request.query.all()[::-1]
    return render_template('admin_summary.html', requests = requests)

### special requests ###

# make a special request
@bp.route('/user/specialrequest/<int:stock_id>', methods=['GET', 'POST'])
@login_required
def make_special_request(stock_id):
    form = RequestForm()
    stock = Stock.query.get_or_404(stock_id)
    if form.validate_on_submit():
        requests = Request.query.filter_by(user_id = current_user.id, stock_id= stock.id).all()
        temp = 0
        for i in requests:
            if i.status == 0 or i.status == 1:
                temp += i.qty
        quota_left = max(0, stock.quota - temp)
        if quota_left == 0:
            special_request = SpecialRequest(
                user_id = current_user.id,
                stock_id=stock.id,
                qty = form.quantity_req.data,
                users_comment = form.message.data,
                original_quantity = form.quantity_req.data
            )
            db.session.add(special_request)
            db.session.commit()
            flash('Special request Made Successfully', 'success')
            return redirect(url_for('user_home'))
        else:
            flash('Your quota has not exceeded the limit, you cannot make a special request', 'danger')
            return redirect(url_for('user_home'))
    return render_template('request_stock.html', form=form, stock=stock)

# view all the special requests
@bp.route("/admin/specialrequests", methods = ['GET'])
def admin_special_request():
    if not current_user.isSuperUser: abort(403) 
    request = SpecialRequest.query.filter_by(status = 0).all()[::-1]
    return render_template('admin_special_request.html', requests = request) 


# accept special requests
@bp.route('/admin/specialrequest/accept/<int:req_id>', methods = ['POST'])
@login_required
def accept_special_request(req_id):    
    if not current_user.isSuperUser : abort(403)
    request_quantity = request.form['request_quantity']
    admin_comment = request.form['admincomment']

    if not request_quantity.isnumeric():
        flash('Quantity should be a number', 'danger')
        return redirect(url_for('request.admin_request'))

    special_request  = SpecialRequest.query.get_or_404(req_id)
    request_quantity = int(request_quantity)

    if request_quantity > special_request.original_quantity or request_quantity > special_request.stock.avail:
        flash('You cannot accept more than the user has requested or more than the available quantity', 'danger')
        return redirect(url_for('request.admin_special_request'))
    special_request.qty = request_quantity
    special_request.status = 1
    special_request.processed_by = current_user.first_name + " " + current_user.last_name 
    special_request.admins_comment = admin_comment
    db.session.commit()
    req = Request(
                user_id = special_request.user_id,
                stock_id=special_request.stock.id,
                qty = special_request.qty,
                users_comment = special_request.users_comment,
                original_quantity = special_request.original_quantity,
                date_applied = special_request.date_applied
            )
    db.session.add(req)
    db.session.commit()
    flash('Special Request Accepted', 'success')
    return redirect(url_for('request.admin_special_request'))


#reject special request
@bp.route('/admin/specialrequest/delete/<int:req_id>', methods = ['POST'])
@login_required
def reject_special_request(req_id):
    if not current_user.isSuperUser: abort(403) 
    req  = SpecialRequest.query.get_or_404(req_id)
    req.status = -1
    req.admins_comment = request.form['admincomment']
    req.processed_by = current_user.first_name + " " + current_user.last_name 
    db.session.commit()
    flash('Special Request rejected','danger')
    return redirect(url_for('request.admin_special_request'))

# view all special requests summary
@bp.route('/admin/specialrequests/summary')
@login_required
def admin_special_summary():
    if not current_user.isSuperUser: abort(403) 
    requests = SpecialRequest.query.all()[::-1]
    return render_template('admin_summary.html', requests = requests)


@bp.route('/user/specialrequests/summary')
@login_required
def user_special_summary():
    requests = SpecialRequest.query.filter_by(user_id = current_user.id).all()[::-1]
    return render_template('user_special_summary.html', requests = requests)


# Make a request for a stock
@bp.route('/make/request/<int:stock_id>', methods=['GET', 'POST'])
@login_required
def make_request(stock_id):
    form = RequestForm()
    stock = Stock.query.get_or_404(stock_id)
    if form.validate_on_submit():
        requests = Request.query.filter_by(user_id = current_user.id, stock_id= stock.id).all()
        temp = 0
        for i in requests:
            if i.status == 0 or i.status == 1:
                temp += i.qty
        quota_left = max(0, stock.quota - temp)
        if quota_left >= form.quantity_req.data:
            request = Request(
                user_id = current_user.id,
                stock_id=stock.id,
                qty = form.quantity_req.data,
                users_comment = form.message.data,
                original_quantity = form.quantity_req.data
            )
            db.session.add(request)
            db.session.commit()
            flash('Request Made Successfully', 'success')
            
        else:
            
            flash('You cannot request more than the available quota', 'danger')
    return render_template('request_stock.html', form=form, stock=stock)

# Confirm that you have received the item
@bp.route('/user/requests/received/<int:request_id>', methods=['POST'])
@login_required
def request_received(request_id):
    req = Request.query.get_or_404(request_id)
    if current_user.id != req.user_id:  abort(403)
    req.accepted = True
    req.received_comment = str(request.form['textarea'])
    db.session.commit()
    flash('Request Updated', 'success')
    return redirect(url_for('user.user_summary'))

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