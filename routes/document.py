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
from models import Document, ChatSession, GroupChatSession
from utils.document_processor import allowed_file, save_uploaded_file, process_document, delete_document_embeddings
from config import ALLOWED_EXTENSIONS

document_bp = Blueprint('document', __name__)

# Document Upload Form
class DocumentUploadForm(FlaskForm):
    document = FileField('Document(s)', validators=[
        FileRequired(),
        FileAllowed(list(ALLOWED_EXTENSIONS), f'Only {", ".join(ALLOWED_EXTENSIONS)} files are allowed')
    ], render_kw={"multiple": True})
    submit = SubmitField('Upload Files')

@document_bp.route('/dashboard')
@login_required
def dashboard():
    # Get all documents for the current user
    documents = Document.query.filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).all()
    
    # Get all group chats for the current user
    group_chats = GroupChatSession.query.filter_by(user_id=current_user.id).order_by(GroupChatSession.last_active.desc()).all()

    # Create document upload form
    upload_form = DocumentUploadForm()
    
    return render_template('dashboard.html', documents=documents,group_chats=group_chats,upload_form=upload_form)

@document_bp.route('/upload', methods=['POST'])
@login_required
def upload_document():
    form = DocumentUploadForm()
    
    if form.validate_on_submit():
        files = request.files.getlist('document')
        
        if not files:
            flash('No files selected.', 'danger')
            return redirect(url_for('document.dashboard'))
        
        successful_uploads = 0
        for file in files:
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
                        successful_uploads += 1
                    else:
                        flash(f'Document "{file_data["original_filename"]}" uploaded but processing failed.', 'warning')
                else:
                    flash(f'Error saving file "{file.filename}". Please try again.', 'danger')
            else:
                flash(f'Invalid file type: {file.filename}. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}', 'danger')
        
        if successful_uploads > 0:
            flash(f'{successful_uploads} document(s) uploaded and processed successfully!', 'success')
            
        return redirect(url_for('document.dashboard'))
    
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
        
        collection_name = f"user_{document.user_id}_doc_{document.id}"
        delete_document_embeddings(collection_name)
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

@document_bp.route('/create_group_chat', methods=['POST'])
@login_required
def create_group_chat():
    # Get form data
    name = request.form.get('name', '').strip()
    document_ids = request.form.getlist('document_ids')
    
    # Validate inputs
    if not name:
        flash('Please provide a name for the chat.', 'danger')
        return redirect(url_for('document.dashboard'))
    
    if len(document_ids) < 2:
        flash('Please select at least 2 documents for a multi-document chat.', 'danger')
        return redirect(url_for('document.dashboard'))
    
    # Get the document objects and verify they belong to the user and are processed
    documents = []
    for doc_id in document_ids:
        document = Document.query.filter_by(
            id=doc_id, 
            user_id=current_user.id,
            processed=True
        ).first()
        
        if document:
            documents.append(document)
    
    if len(documents) < 2:
        flash('Could not find enough valid documents. Please try again.', 'danger')
        return redirect(url_for('document.dashboard'))
    
    # Create a new group chat session
    group_chat = GroupChatSession(
        user_id=current_user.id,
        name=name
    )
    
    # Add documents to the group chat
    group_chat.documents = documents
    
    db.session.add(group_chat)
    db.session.commit()
    
    flash(f'Multi-document chat "{name}" created successfully!', 'success')
    return redirect(url_for('chat.group_chat_view', group_chat_id=group_chat.id))

@document_bp.route('/delete_group_chat/<int:group_chat_id>', methods=['POST'])
@login_required
def delete_group_chat(group_chat_id):
    # Verify user owns this group chat
    group_chat = GroupChatSession.query.filter_by(
        id=group_chat_id, 
        user_id=current_user.id
    ).first_or_404()
    
    # Get the chat name for flash message
    chat_name = group_chat.name
    
    # Delete the group chat (cascade will delete associated messages)
    db.session.delete(group_chat)
    db.session.commit()
    
    flash(f'Multi-document chat "{chat_name}" deleted successfully!', 'success')
    return redirect(url_for('document.dashboard'))
