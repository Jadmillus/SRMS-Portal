from flask import render_template, url_for, flash, redirect, request
from app.forms import EditCategoryForm, LoginForm, RequestResetForm, ResetPasswordForm, ProfileForm, UpdatePassword, RegistrationForm
from app.models import Stock, Category, User
from app.user import bp
from flask_login import login_user, current_user, logout_user, login_required
from app.extensions import bcrypt, mail, db
from flask_mail import Message
import secrets
import os
from PIL import Image
from flask import current_app as app

@bp.route('/admin/users')
@login_required
def display_users():
    if not current_user.isAdmin: abort(403) 
    users = User.query.all()
    return render_template('display_users.html', users = users)


# add a new user
@bp.route('/admin/users/add', methods = ['GET', 'POST'])
@login_required
def add_users():
    if not current_user.isAdmin: abort(403) 
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user:
            flash(f"This email is already registered. Please try with another email id","info")
        else:
            password = secrets.token_hex(8)
            hashed_password = bcrypt.generate_password_hash(password)
            user = User(
                first_name = form.first_name.data, 
                last_name = form.last_name.data,
                email = form.email.data, 
                password = hashed_password
                )
            db.session.add(user)
            db.session.commit()
            flash(f"User Added","success")
            send_create_user_email(user,password)
            return redirect(url_for('user.display_users'))
    return render_template('register.html',title = 'Register', form = form)

# view profile
@bp.route('/profile/<int:user_id>')
@login_required
def view_user(user_id):
    if not current_user.isAdmin: abort(403)
    user = User.query.get_or_404(user_id)
    return render_template('view_user.html', user = user)

# @bp.route('/profile/update/password/<int:user_id>', methods = ['GET', 'POST'])
# @login_required
# def admin_update_password(user_id):
#     if not current_user.isAdmin: abort(403)
#     user = User.query.get_or_404(user_id)
#     form = UpdatePassword()
#     if form.validate_on_submit():
#         if not bcrypt.check_password_hash(current_user.password, form.prev_password.data): 
#             flash(f'Incorrect Password', 'danger')
#         else:
#             user.password = bcrypt.generate_password_hash(form.password.data)
#             db.session.commit()
#             flash(user.first_name + "'s Password was Updated", 'success')
#     return render_template('update_password.html', form = form, user = user)


# delete account
@bp.route('/profile/delete/account/<int:user_id>', methods = ['POST'])
@login_required
def admin_delete_account(user_id):
    if not current_user.isAdmin: abort(403)
    user = User.query.get_or_404(user_id)
    send_delete_account_email(user)
    db.session.delete(user)
    db.session.commit()
    flash("Account Deleted", 'success')
    return redirect(url_for('user.display_users'))

# toggle admin privileges
@bp.route('/profile/toggleadmin/<int:user_id>', methods = ['POST'])
@login_required
def toggle_admin(user_id):
    if not current_user.isSuperUser: abort(403)
    user = User.query.get_or_404(user_id)
    if user.isAdmin:
        user.isAdmin = False
        user.isSuperUser = False
    else:
        user.isAdmin = True
    db.session.commit()
    flash("Account Updated", 'success')
    return redirect(url_for('user.view_user', user_id = user.id))

# toggle superuser privileges
@bp.route('/profile/togglesuperuser/<int:user_id>', methods = ['POST'])
@login_required
def toggle_superuser(user_id):
    if not current_user.isSuperUser: abort(403)
    user = User.query.get_or_404(user_id)
    if user.isSuperUser:
        user.isSuperUser = False
    else:
        user.isSuperUser = True
        user.isAdmin = True
    db.session.commit()
    flash("Account Updated", 'success')
    return redirect(url_for('user.view_user', user_id = user.id))
    
# view the summary of all the requests that you have made
@bp.route('/user/request/summary')
@login_required
def user_summary():
    requests = User.query.get(current_user.id).requests[::-1]
    return render_template('summary.html', requests = requests)

@bp.route('/')
@login_required
def home():
    return render_template('home.html')

@bp.route('/profile')
@login_required
def account():
    return render_template('account.html')

@bp.route("/profile/update", methods=['POST', 'GET'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        if not bcrypt.check_password_hash(current_user.password, form.password.data): 
            flash(f'Incorrect Password', 'danger')
        else:
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.email = form.email.data
            image_name = current_user.picture
            if form.picture.data:
                image_name = save_picture(form.picture.data, 'profile')
            current_user.picture = image_name
            db.session.commit()
            flash('Account was Updated', 'success')
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.email.data = current_user.email
    return render_template('profile.html', form = form)

@bp.route("/profile/update/password", methods=['POST', 'GET'])
@login_required
def update_password():
    form = UpdatePassword()
    if form.validate_on_submit():
        if not bcrypt.check_password_hash(current_user.password, form.prev_password.data): 
            flash(f'Incorrect Password', 'danger')
        else:
            current_user.password = bcrypt.generate_password_hash(form.password.data)
            db.session.commit()
            flash('Password was Updated', 'success')
    return render_template('update_password.html', form = form)

# user login
@bp.route("/login",methods = ['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            next_page = request.args.get('next')
            login_user(user)
            flash(f'Welcome {current_user.first_name}!', 'success')
            return redirect(next_page) if next_page else  redirect(url_for('user.home'))
        else:
            flash(f"Your login credentials don't match", 'danger')
    
        
    return render_template('login.html',form = form)

# user logout
@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()

    return redirect(url_for('user.login'))



# Password reset request
@bp.route("/reset_password", methods = ['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('user.login'))
    return render_template('reset_password_request.html',title = 'Reset Password', form = form)

# Reset Password
@bp.route("/reset_password/<token>", methods = ['GET','POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        password = bcrypt.generate_password_hash(form.password.data)
        user.password = password
        db.session.commit()
        flash(f"Your Password has been updated.You are now able to login","success")
        return redirect(url_for('user.login'))
    
    return render_template('reset_token.html',title = 'Reset Password', form = form)

@bp.route('/help')
def help():
    return render_template('help.html')




############# utils ####################

# save the picture 
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

# reset request email
def send_reset_email(user):
    token = user.get_reset_token()

    msg = Message('Password reset request',
                 sender = 'noreply@demo.com',
                 recipients = [user.email])
    msg.body = f'''To reset your password visit the following link
{url_for('user.reset_token', token = token, _external = True)}
If you did not make this request then simply ignore this email and no changes will be made
This url will expire in 30 min.

This is an auto generated mail. Please do not reply. 
    '''
    mail.send(msg)

# send create user email
def send_create_user_email(user, password):
    

    msg = Message('Password for requisition and supply management system',
                 sender = 'noreply@demo.com',
                 recipients = [user.email])
    msg.body = f'''Your account has been created on Requsition and supply management system. 
You have been added as a user by {current_user.email} 
You can login using the below credentials 
Email : {user.email}
Password : {password}
Feel free to change the password after login in. 

This is an auto generated mail. Please do not reply. 
    '''
    mail.send(msg)

# send delete account email
def send_delete_account_email(user):

    msg = Message('Account Delete on Requisition and supply management system',
                 sender = 'noreply@demo.com',
                 recipients = [user.email])
    msg.body = f'''Your account was deleted on Requisition and supply managment System. 
You account was deleted by {current_user.email} 
Please contact the admin if you think this was a mistake.

This is an auto generated mail. Please do not reply. 
    '''
    mail.send(msg)
