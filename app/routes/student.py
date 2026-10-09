from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename
from app import db
from app.models import Student, PlacementDrive, Application
import os

student_bp = Blueprint('student', __name__)
def student_required(f):
    """Decorator: only allow students."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Student access required.')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    student = current_user.student_profile
    from datetime import date
    # All approved drives
    approved_drives = (PlacementDrive.query.filter_by(status='approved').order_by(PlacementDrive.deadline.asc()).all())
    # Student's applications
    my_applications = (Application.query.filter_by(student_id=student.id).order_by(Application.applied_date.desc()).all())
    # IDs of drives already applied for
    applied_drive_ids = {app.drive_id for app in my_applications}

    return render_template('student/dashboard.html',student=student,
                           approved_drives=approved_drives,my_applications=my_applications,
                           applied_drive_ids=applied_drive_ids,today=date.today())

@student_bp.route('/drives')
@login_required
@student_required
def drives():
    student = current_user.student_profile
    from datetime import date
    all_drives = (PlacementDrive.query.filter_by(status='approved').order_by(PlacementDrive.deadline.asc()).all())

    applied_drive_ids = {app.drive_id for app in student.applications}

    return render_template('student/drives.html',
                           drives=all_drives,
                           applied_drive_ids=applied_drive_ids,
                           today=date.today())

@student_bp.route('/applications')
@login_required
@student_required
def my_applications():
    student = current_user.student_profile
    applications = (Application.query
                    .filter_by(student_id=student.id)
                    .order_by(Application.applied_date.desc())
                    .all())
    return render_template('student/my_applications.html', applications=applications)

@student_bp.route('/apply/<int:drive_id>', methods=['POST'])
@login_required
@student_required
def apply(drive_id):
    student = current_user.student_profile
    drive = PlacementDrive.query.get_or_404(drive_id)

    if drive.status != 'approved':
        flash('This drive is not available for applications.', 'warning')
        return redirect(url_for('student.drives'))

    # Check duplicate application
    existing = Application.query.filter_by(student_id=student.id, drive_id=drive_id).first()
    if existing:
        flash('You have already applied for this drive.', 'warning')
        return redirect(url_for('student.drives'))

    from datetime import date
    if drive.deadline < date.today():
        flash('The application deadline has passed.', 'warning')
        return redirect(url_for('student.drives'))

    cover_note = request.form.get('cover_note', '').strip()

    application = Application(
        student_id=student.id,
        drive_id=drive_id,
        status='applied',
        cover_note=cover_note
    )
    db.session.add(application)
    db.session.commit()

    flash(f'Successfully applied for {drive.job_title}!', 'success')
    return redirect(url_for('student.my_applications'))

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@student_required
def profile():
    student = current_user.student_profile

    if request.method == 'POST':
        student.name = request.form.get('name', '').strip()
        student.phone = request.form.get('phone', '').strip()
        student.branch = request.form.get('branch', '').strip()
        student.bio = request.form.get('bio', '').strip()

        try:
            student.cgpa = float(request.form.get('cgpa', 0))
        except ValueError:
            student.cgpa = 0.0

        try:
            grad_year = request.form.get('graduation_year', '')
            student.graduation_year = int(grad_year) if grad_year else None
        except ValueError:
            pass

        # Handle resume upload
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"student_{student.id}_{file.filename}")
                upload_path = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                student.resume_filename = filename
                flash('Resume uploaded successfully!', 'success')
            elif file and file.filename:
                flash('Invalid file type. Please upload PDF, DOC, or DOCX.', 'danger')

        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('student.profile'))

    return render_template('student/profile.html', student=student)


@student_bp.route('/resume/<filename>')
@login_required
def download_resume(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
