from flask import (
    Blueprint, render_template, redirect, url_for, 
    flash, request, jsonify, current_app
)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired

from app import db
from models import ChatSession, ChatMessage, Document
from utils.chat_service import generate_answer

chat_bp = Blueprint('chat', __name__)

# Message Form
class MessageForm(FlaskForm):
    message = TextAreaField('Your Message', validators=[DataRequired()])
    submit = SubmitField('Send')

@chat_bp.route('/chat/<int:chat_id>', methods=['GET'])
@login_required
def chat_view(chat_id):
    # Get the chat session
    chat_session = ChatSession.query.filter_by(
        id=chat_id, 
        user_id=current_user.id
    ).first_or_404()
    
    # Get the document
    document = Document.query.filter_by(
        id=chat_session.document_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Get chat messages
    messages = ChatMessage.query.filter_by(
        chat_session_id=chat_id
    ).order_by(ChatMessage.timestamp).all()
    
    # Create message form
    form = MessageForm()
    
    return render_template(
        'chat.html', 
        chat_session=chat_session, 
        document=document, 
        messages=messages, 
        form=form
    )

@chat_bp.route('/api/send_message', methods=['POST'])
@login_required
def send_message():
    try:
        # Extract data from request
        data = request.json
        message_text = data.get('message')
        chat_id = data.get('chat_id')
        
        if not message_text or not chat_id:
            return jsonify({'error': 'Missing message or chat ID'}), 400
        
        # Get the chat session
        chat_session = ChatSession.query.filter_by(
            id=chat_id, 
            user_id=current_user.id
        ).first_or_404()
        
        # Get the document
        document = Document.query.filter_by(
            id=chat_session.document_id,
            user_id=current_user.id
        ).first_or_404()
        
        # Create and save user message
        user_message = ChatMessage(
            chat_session_id=chat_id,
            is_user=True,
            content=message_text
        )
        db.session.add(user_message)
        db.session.commit()
        
        # Get chat history for context
        chat_history = [
            {
                "is_user": msg.is_user,
                "content": msg.content
            }
            for msg in ChatMessage.query.filter_by(chat_session_id=chat_id).order_by(ChatMessage.timestamp).all()
        ]
        
        # Generate response
        response_data = generate_answer(
            query=message_text,
            document_id=document.id,
            user_id=current_user.id,
            chat_history=chat_history[:-1]  # Exclude the just-added user message
        )
        
        # Create and save bot message
        if 'error' in response_data:
            bot_response = f"Error: {response_data['error']}"
        else:
            bot_response = response_data['answer']
            
            # Add sources if available
            if 'sources' in response_data and response_data['sources']:
                sources_text = "\n\n*Sources:* " + ", ".join(response_data['sources'])
                bot_response += sources_text
        
        bot_message = ChatMessage(
            chat_session_id=chat_id,
            is_user=False,
            content=bot_response
        )
        db.session.add(bot_message)
        
        # Update chat session last active time
        chat_session.last_active = db.func.now()
        db.session.commit()
        
        # Return bot message with formatting
        return jsonify({
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'timestamp': user_message.timestamp.isoformat()
            },
            'bot_message': {
                'id': bot_message.id,
                'content': bot_message.content,
                'timestamp': bot_message.timestamp.isoformat()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in send_message: {str(e)}")
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/clear_chat/<int:chat_id>', methods=['POST'])
@login_required
def clear_chat(chat_id):
    # Verify user owns this chat
    chat_session = ChatSession.query.filter_by(
        id=chat_id, 
        user_id=current_user.id
    ).first_or_404()
    
    # Delete all messages
    ChatMessage.query.filter_by(chat_session_id=chat_id).delete()
    db.session.commit()
    
    flash('Chat history cleared successfully!', 'success')
    return redirect(url_for('chat.chat_view', chat_id=chat_id))
