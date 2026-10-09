from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Student, Company

auth_bp= Blueprint('auth',__name__)

@auth_bp.route('/')
def index():
    # homepage
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))
    return render_template('index.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid username or password.', 'danger')
            return render_template('auth/login.html')

        if user.is_blacklisted:
            flash('Your account has been blacklisted. Contact the admin.', 'danger')
            return render_template('auth/login.html')

        if not user.active:
            flash('Your account is deactivated. Contact the admin.', 'danger')
            return render_template('auth/login.html')
        
        # Company must be approved before logging in
        if user.role == 'company':
            company = user.company_profile
            if company.approval_status == 'pending':
                flash('Your company registration is pending admin approval.', 'warning')
                return render_template('auth/login.html')
            elif company.approval_status == 'rejected':
                flash('Your company registration was rejected. Contact admin.', 'danger')
                return render_template('auth/login.html')
            elif company.approval_status == 'blacklisted':
                flash('Your company has been blacklisted.', 'danger')
                return render_template('auth/login.html')
    
        login_user(user)
        flash(f'Welcome back, {user.username}!' ,'success')
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for(f'{user.role}.dashboard'))
    return render_template('auth/login.html')

@auth_bp.route('/register/student', methods=['GET','POST'])
def register_student():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        name = request.form.get('name', '').strip()
        roll_number = request.form.get('roll_number', '').strip()
        branch = request.form.get('branch', '').strip()
        cgpa = request.form.get('cgpa', 0)
        phone = request.form.get('phone', '').strip()
        graduation_year = request.form.get('graduation_year', '')

        #validation 
        if not all([username, email, password, name, roll_number, branch]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/register_student.html')
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register_student.html')
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('auth/register_student.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register_student.html')
        if Student.query.filter_by(roll_number=roll_number).first():
            flash('Roll number already registered.', 'danger')
            return render_template('auth/register_student.html')
        # creating user+ student profile
        user = User(
            username = username,
            email= email,
            password= generate_password_hash(password),
            role='student'
        )
        db.session.add(user)
        db.session.flush()
        try:
            cgpa_val = float(cgpa)
        except (ValueError, TypeError):
            cgpa_val = 0.0

        try:
            grad_year = int(graduation_year) if graduation_year else None
        except ValueError:
            grad_year = None

        student = Student(
            user_id=user.id,
            name=name,
            roll_number=roll_number,
            branch=branch,
            cgpa=cgpa_val,
            phone=phone,
            graduation_year=grad_year
        )
        db.session.add(student)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register_student.html')

@auth_bp.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        company_name = request.form.get('company_name', '').strip()
        hr_contact = request.form.get('hr_contact', '').strip()
        website = request.form.get('website', '').strip()
        industry = request.form.get('industry', '').strip()
        description = request.form.get('description', '').strip()

        # validation
        if not all([username, email, password, company_name]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/register_company.html')
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register_company.html')
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('auth/register_company.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register_company.html')
        
        # creating company profile
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role='company'
        )
        db.session.add(user)
        db.session.flush()

        company = Company(
            user_id=user.id,
            company_name=company_name,
            hr_contact=hr_contact,
            website=website,
            industry=industry,
            description=description,
            approval_status='pending'
        )
        db.session.add(company)
        db.session.commit()
        flash('Company registered! Please wait for admin approval before logging in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_company.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
