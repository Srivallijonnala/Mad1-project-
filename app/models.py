from .import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import CheckConstraint

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True,nullable=False)
    email = db.Column(db.String(120), unique=True,nullable=False)
    password = db.Column(db.String(200),nullable=False)
    role = db.Column(db.String(20),nullable=False)
    active= db.Column(db.Boolean,default=True)
    is_blacklisted=db.Column(db.Boolean,default=False)
    created_at= db.Column(db.DateTime, default=datetime.utcnow)
    # relations for users table
    student_profile= db.relationship('Student' , backref='user', uselist= False, cascade='all,delete-orphan')
    company_profile= db.relationship('Company' , backref='user', uselist= False, cascade='all,delete-orphan')

    #overriding is_active
    @property
    def is_active(self):
        return self.active and not self.is_blacklisted
    def get_id(self):
        return str(self.id)
    
class Student(db.Model):
    __tablename__='students'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False,unique=True)
    name           = db.Column(db.String(100), nullable=False)
    roll_number    =db.Column(db.String(50),unique=True,nullable=False)
    branch         = db.Column(db.String(100),nullable=False)
    cgpa            =db.Column(db.Float,default=0.0)
    phone           = db.Column(db.String(20),unique=True)
    graduation_year = db.Column(db.Integer)
    resume_filename = db.Column(db.String(200))
    bio             = db.Column(db.Text)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
    CheckConstraint('cgpa >= 0 AND cgpa <= 10', name='check_cgpa_range'),
    )
    # relations for students table
    applications = db.relationship('Application', backref='student',lazy=True,cascade='all,delete-orphan')

class Company(db.Model):
    __tablename__='companies'
    id         = db.Column(db.Integer,primary_key=True)
    user_id    = db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)
    company_name = db.Column(db.String(100),nullable=False)
    hr_contact  = db.Column(db.String(100))
    website     = db.Column(db.String(200))
    description = db.Column(db.Text)
    industry    = db.Column(db.String(100))
    approval_status = db.Column(db.String(20))
    # relations for companies table
    drives = db.relationship('PlacementDrive', backref='company',lazy=True,cascade='all,delete-orphan')

class PlacementDrive(db.Model):
    __tablename__='placement_drives'
    id             = db.Column(db.Integer, primary_key=True)
    company_id     = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    job_title      = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.Text,nullable=False)
    eligibility_criteria = db.Column(db.Text)
    package          =db.Column(db.String(50))
    location         =db.Column(db.String(100))
    deadline         =db.Column(db.Date, nullable=False)             
    status           =db.Column(db.String(20), default='pending')
    created_at       =db.Column(db.DateTime, default=datetime.utcnow)
    # relations
    applications = db.relationship('Application', backref='drive', lazy=True, cascade='all, delete-orphan')


class Application(db.Model):
    __tablename__ = 'applications'
    id           = db.Column(db.Integer, primary_key=True)
    student_id   = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    drive_id     = db.Column(db.Integer, db.ForeignKey('placement_drives.id'), nullable=False)
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    status       = db.Column(db.String(20), default='applied')
    cover_note   = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'drive_id', name='unique_student_drive'),
    )