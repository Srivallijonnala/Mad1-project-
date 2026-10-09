from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Student, Company, PlacementDrive, Application


admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    # Decorator: only allow admins.
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_students=Student.query.count()
    total_companies=Company.query.count()
    total_drives=PlacementDrive.query.count()
    total_applications=Application.query.count()

    pending_companies = Company.query.filter_by(approval_status='pending').count()
    pending_drives = PlacementDrive.query.filter_by(status='pending').count()
    recent_applications = Application.query.order_by(Application.applied_date.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           total_students=total_students,
                           total_companies=total_companies,
                           total_applications=total_applications,
                           total_drives=total_drives,
                           pending_companies=pending_companies,
                           pending_drives=pending_drives,
                           recent_applications=recent_applications)

# ulrs for company management

@admin_bp.route('/companies')
@login_required
@admin_required
def companies():
    search = request.args.get('search','').strip()
    query = Company.query

    if search:
        query = query.filter(Company.company_name.ilike(f'%{search}%'))

    companies_list=query.order_by(Company.id.desc()).all()
    return render_template('admin/companies.html', companies=companies_list,search=search)
@admin_bp.route('/company/<int:company_id>/approve')
@login_required
@admin_required
def approve_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = 'approved'
    db.session.commit()
    flash(f'{company.company_name} has been approved.', 'success')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/company/<int:company_id>/reject')
@login_required
@admin_required
def reject_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = 'rejected'
    db.session.commit()
    flash(f'{company.company_name} has been rejected.','warning')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/company/<int:company_id>/delete',methods=['post'])
@login_required
@admin_required
def delete_company(company_id):
    company= Company.query.get_or_404(company_id)
    user = company.user
    db.session.delete(user)
    db.session.commit()
    flash('company deleted successfully','info')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/company/<int:company_id>/blacklist')
@login_required
@admin_required
def blacklist_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = 'blacklisted'
    company.user.is_blacklisted = True
    db.session.commit()
    flash(f'{company.company_name} has been blacklisted.', 'danger')
    return redirect(url_for('admin.companies'))

# urls for Student management
@admin_bp.route('/students')
@login_required
@admin_required
def students():
    search = request.args.get('search', '').strip()
    query = Student.query

    if search:
        query = query.join(User).filter(
            db.or_(
                Student.name.ilike(f'%{search}%'),
                Student.roll_number.ilike(f'%{search}%'),
                Student.phone.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )

    students_list = query.order_by(Student.id.desc()).all()
    return render_template('admin/students.html', students=students_list, search=search)


@admin_bp.route('/student/<int:student_id>/blacklist')
@login_required
@admin_required
def blacklist_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.user.is_blacklisted = True
    db.session.commit()
    flash(f'{student.name} has been blacklisted.', 'danger')
    return redirect(url_for('admin.students'))


@admin_bp.route('/student/<int:student_id>/activate')
@login_required
@admin_required
def activate_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.user.is_blacklisted = False
    student.user.active = True
    db.session.commit()
    flash(f'{student.name} has been reactivated.', 'success')
    return redirect(url_for('admin.students'))


@admin_bp.route('/student/<int:student_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    user = student.user
    db.session.delete(user)
    db.session.commit()
    flash('Student deleted successfully.', 'info')
    return redirect(url_for('admin.students'))


# url for application management

@admin_bp.route("/application")
@login_required
@admin_required
def applications():
    apps= Application.query.order_by(Application.applied_date.desc()).all()
    return render_template('admin/applications.html',applications=apps)

# urls for drive management
@admin_bp.route('/drives')
@login_required
@admin_required
def drives():
    drives_list = PlacementDrive.query.order_by(PlacementDrive.created_at.desc()).all()
    return render_template('admin/drives.html', drives=drives_list)


@admin_bp.route('/drive/<int:drive_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'approved'
    db.session.commit()
    flash(f'Drive "{drive.job_title}" approved.', 'success')
    return redirect(url_for('admin.drives'))


@admin_bp.route('/drive/<int:drive_id>/reject' , methods=['POST'])
@login_required
@admin_required
def reject_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'rejected'
    db.session.commit()
    flash(f'Drive "{drive.job_title}" rejected.', 'warning')
    return redirect(url_for('admin.drives'))


@admin_bp.route('/drive/<int:drive_id>/close', methods=['POST'])
@login_required
@admin_required
def close_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'closed'
    db.session.commit()
    flash(f'Drive "{drive.job_title}" closed.', 'info')
    return redirect(url_for('admin.drives'))


@admin_bp.route('/drive/<int:drive_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    db.session.delete(drive)
    db.session.commit()
    flash('Drive deleted.', 'info')
    return redirect(url_for('admin.drives'))
