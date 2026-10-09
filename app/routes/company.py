from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date
from app import db
from app.models import Company, PlacementDrive, Application, Student

company_bp = Blueprint('company', __name__)

def company_required(f):
    #Decorator: only allow approved companies.
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'company':
            flash('Company access required.', 'danger')
            return redirect(url_for('auth.login'))
        company = current_user.company_profile
        if not company or company.approval_status != 'approved':
            flash('Your company is not yet approved.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@company_bp.route('/dashboard')
@login_required
@company_required
def dashboard():
    company = current_user.company_profile
    drives = PlacementDrive.query.filter_by(company_id=company.id).order_by(PlacementDrive.created_at.desc()).all()
    #  count application for each drive
    drive_stats = []
    for drive in drives:
        count = Application.query.filter_by(drive_id=drive.id).count()
        drive_stats.append({'drive': drive, 'applicant_count': count})

    return render_template('company/dashboard.html', company=company, drive_stats=drive_stats)

@company_bp.route('/create-drive', methods=['GET', 'POST'])
@login_required
@company_required
def create_drive():
    company = current_user.company_profile

    if request.method == 'POST':
        job_title = request.form.get('job_title', '').strip()
        job_description = request.form.get('job_description', '').strip()
        eligibility = request.form.get('eligibility_criteria', '').strip()
        package = request.form.get('package', '').strip()
        location = request.form.get('location', '').strip()
        deadline_str = request.form.get('deadline', '')
        # vadilation
        if not all([job_title, job_description, deadline_str]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('company/create_drive.html')

        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid deadline date.', 'danger')
            return render_template('company/create_drive.html')
        if deadline < date.today():
            flash('Deadline cannot be in the past.', 'danger')
            return render_template('company/create_drive.html')

        drive = PlacementDrive(
            company_id=company.id,
            job_title=job_title,
            job_description=job_description,
            eligibility_criteria=eligibility,
            package=package,
            location=location,
            deadline=deadline,
            status='pending'
        )
        db.session.add(drive)
        db.session.commit()
        flash('Placement drive submitted for admin approval!', 'success')
        return redirect(url_for('company.dashboard'))

    return render_template('company/create_drive.html')

@company_bp.route('/drive/<int:drive_id>/edit', methods=['GET', 'POST'])
@login_required
@company_required
def edit_drive(drive_id):
    company = current_user.company_profile
    drive = PlacementDrive.query.get_or_404(drive_id)
    #  make drive belong to same company or not
    if drive.company_id != company.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.dashboard'))

    if drive.status == 'approved':
        flash('Cannot edit an approved drive. Please contact admin.', 'warning')
        return redirect(url_for('company.dashboard'))

    if request.method == 'POST':
        drive.job_title = request.form.get('job_title', '').strip()
        drive.job_description = request.form.get('job_description', '').strip()
        drive.eligibility_criteria = request.form.get('eligibility_criteria', '').strip()
        drive.package = request.form.get('package', '').strip()
        drive.location = request.form.get('location', '').strip()
        deadline_str = request.form.get('deadline', '')

        try:
            drive.deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return render_template('company/edit_drive.html', drive=drive)

        drive.status = 'pending' 
        db.session.commit()
        flash('Drive updated successfully!', 'success')
        return redirect(url_for('company.dashboard'))

    return render_template('company/edit_drive.html', drive=drive)

@company_bp.route('/drive/<int:drive_id>/close', methods=['POST'])
@login_required
@company_required
def close_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'closed'
    db.session.commit()
    flash(f'Drive "{drive.job_title}" closed.', 'info')
    return redirect(url_for('company.dashboard'))

@company_bp.route('/drive/<int:drive_id>/delete', methods=['POST'])
@login_required
@company_required
def delete_drive(drive_id):
    company = current_user.company_profile
    drive = PlacementDrive.query.get_or_404(drive_id)

    if drive.company_id != company.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.dashboard'))

    db.session.delete(drive)
    db.session.commit()
    flash('Drive deleted.', 'info')
    return redirect(url_for('company.dashboard'))


@company_bp.route('/drive/<int:drive_id>/applications')
@login_required
@company_required
def drive_applications(drive_id):
    company = current_user.company_profile
    drive = PlacementDrive.query.get_or_404(drive_id)

    if drive.company_id != company.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.dashboard'))

    applications = Application.query.filter_by(drive_id=drive_id).all()
    return render_template('company/applications.html', drive=drive, applications=applications)

@company_bp.route('/application/<int:app_id>/update', methods=['POST'])
@login_required
@company_required
def update_application(app_id):
    company = current_user.company_profile
    application = Application.query.get_or_404(app_id)
    drive = application.drive

    if drive.company_id != company.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.dashboard'))

    new_status = request.form.get('status')
    valid_statuses = ['applied', 'shortlisted', 'selected', 'rejected']

    if new_status in valid_statuses:
        application.status = new_status
        db.session.commit()
        flash(f'Application status updated to {new_status.capitalize()}.', 'success')
    else:
        flash('Invalid status.', 'danger')

    return redirect(url_for('company.drive_applications', drive_id=drive.id))

@company_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@company_required
def profile():
    company = current_user.company_profile

    if request.method == 'POST':
        company.company_name = request.form.get('company_name', '').strip()
        company.hr_contact = request.form.get('hr_contact', '').strip()
        company.website = request.form.get('website', '').strip()
        company.industry = request.form.get('industry', '').strip()
        company.description = request.form.get('description', '').strip()
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('company.profile'))

    return render_template('company/profile.html', company=company)