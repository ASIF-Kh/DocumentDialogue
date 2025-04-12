import os
from flask import (
    Blueprint, render_template, redirect, url_for, 
    flash, request, jsonify, current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField

from app import db
from models import Document, ChatSession
from utils.document_processor import allowed_file, save_uploaded_file, process_document
from config import ALLOWED_EXTENSIONS

document_bp = Blueprint('document', __name__)

# Document Upload Form
class DocumentUploadForm(FlaskForm):
    document = FileField('Document', validators=[
        FileRequired(),
        FileAllowed(list(ALLOWED_EXTENSIONS), f'Only {", ".join(ALLOWED_EXTENSIONS)} files are allowed')
    ])
    submit = SubmitField('Upload')

@document_bp.route('/dashboard')
@login_required
def dashboard():
    # Get all documents for the current user
    documents = Document.query.filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).all()
    
    # Create document upload form
    upload_form = DocumentUploadForm()
    
    return render_template('dashboard.html', documents=documents, upload_form=upload_form)

@document_bp.route('/upload', methods=['POST'])
@login_required
def upload_document():
    form = DocumentUploadForm()
    
    if form.validate_on_submit():
        file = form.document.data
        
        if file and allowed_file(file.filename):
            # Save the file and get metadata
            file_data = save_uploaded_file(file, current_user.id)
            
            if file_data:
                # Create document record in database
                document = Document(
                    user_id=current_user.id,
                    filename=file_data['filename'],
                    original_filename=file_data['original_filename'],
                    file_path=file_data['file_path'],
                    file_type=file_data['file_type'],
                    file_size=file_data['file_size'],
                    processed=False
                )
                
                db.session.add(document)
                db.session.commit()
                
                # Process document in background (simplified, consider using Celery in production)
                success = process_document(document)
                
                if success:
                    document.processed = True
                    db.session.commit()
                    flash(f'Document "{file_data["original_filename"]}" uploaded and processed successfully!', 'success')
                else:
                    flash(f'Document uploaded but processing failed. Please try again later.', 'warning')
                
                return redirect(url_for('document.dashboard'))
            else:
                flash('Error saving file. Please try again.', 'danger')
        else:
            flash(f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}', 'danger')
    
    # If validation fails or other errors occur
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{error}', 'danger')
    
    return redirect(url_for('document.dashboard'))

@document_bp.route('/delete/<int:document_id>', methods=['POST'])
@login_required
def delete_document(document_id):
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first_or_404()
    
    # Delete the physical file
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        current_app.logger.error(f"Error deleting file: {str(e)}")
    
    # Delete document from database (cascade will delete associated chat sessions)
    db.session.delete(document)
    db.session.commit()
    
    flash('Document deleted successfully!', 'success')
    return redirect(url_for('document.dashboard'))

@document_bp.route('/start_chat/<int:document_id>')
@login_required
def start_chat(document_id):
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first_or_404()
    
    # Check if document is processed
    if not document.processed:
        flash('Document is still being processed. Please try again in a moment.', 'warning')
        return redirect(url_for('document.dashboard'))
    
    # Create a new chat session or get the existing one
    chat_session = ChatSession.query.filter_by(
        user_id=current_user.id, 
        document_id=document_id
    ).order_by(ChatSession.last_active.desc()).first()
    
    if not chat_session:
        chat_session = ChatSession(
            user_id=current_user.id,
            document_id=document_id
        )
        db.session.add(chat_session)
        db.session.commit()
    
    return redirect(url_for('chat.chat_view', chat_id=chat_session.id))
