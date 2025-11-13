
from flask import Flask, render_template, request, jsonify
import requests, os, random, string, json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

app = Flask(__name__)

# ---------------------- CONFIG ----------------------
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
TICKETS_DB_FILE = "tickets.json"  # JSON file to store ticket information
# -------- CONFIG --------
# ----------------------------------------------------

# Initialize JSON database
def init_tickets_db():
    """Initialize the JSON database file if it doesn't exist."""
    if not os.path.exists(TICKETS_DB_FILE):
        with open(TICKETS_DB_FILE, 'w') as f:
            json.dump([], f)

def save_ticket_to_db(ticket_info):
    """Save ticket information to JSON database."""
    # Load existing tickets
    with open(TICKETS_DB_FILE, 'r') as f:
        tickets = json.load(f)
    
    # Convert datetime to string for JSON serialization
    ticket_data = {
        'ticket_id': ticket_info['ticket_id'],
        'name': ticket_info['name'],
        'email': ticket_info['email'],
        'purchase_date': ticket_info['purchase_date'].strftime('%Y-%m-%d %H:%M:%S'),
        'payment_reference': ticket_info['payment_reference'],
        'used': ticket_info['used'],
        'used_date': ticket_info['used_date'].strftime('%Y-%m-%d %H:%M:%S') if ticket_info['used_date'] else None
    }
    
    # Add new ticket
    tickets.append(ticket_data)
    
    # Save back to file
    with open(TICKETS_DB_FILE, 'w') as f:
        json.dump(tickets, f, indent=2)

def get_ticket_info(ticket_id):
    """Retrieve ticket information from JSON database."""
    if not os.path.exists(TICKETS_DB_FILE):
        return None
    
    with open(TICKETS_DB_FILE, 'r') as f:
        tickets = json.load(f)
    
    # Search for ticket
    for ticket in tickets:
        if ticket['ticket_id'] == ticket_id:
            # Convert datetime strings back to datetime objects
            ticket_copy = ticket.copy()
            ticket_copy['purchase_date'] = datetime.strptime(
                ticket['purchase_date'], '%Y-%m-%d %H:%M:%S'
            )
            if ticket['used_date']:
                ticket_copy['used_date'] = datetime.strptime(
                    ticket['used_date'], '%Y-%m-%d %H:%M:%S'
                )
            return ticket_copy
    
    return None

def mark_ticket_used(ticket_id):
    """Mark a ticket as used in JSON database."""
    if not os.path.exists(TICKETS_DB_FILE):
        return
    
    with open(TICKETS_DB_FILE, 'r') as f:
        tickets = json.load(f)
    
    # Find and update ticket
    for ticket in tickets:
        if ticket['ticket_id'] == ticket_id:
            ticket['used'] = True
            ticket['used_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            break
    
    # Save back to file
    with open(TICKETS_DB_FILE, 'w') as f:
        json.dump(tickets, f, indent=2)

# Initialize the database
init_tickets_db()

# ---------- UTILITY FUNCTIONS ----------
def generate_ticket_number(quantity):
    """Generate a unique ticket number with format: SP-<7 random digits>-<2 digit quantity>.
    
    Args:
        quantity: Number of tickets purchased (0-99).
    
    Returns:
        Ticket string like SP-1223324-25 where 25 is the quantity.
    """
    # New format: SP-<7 digits>-<quantity>
    # Prefix SP stands for SUHUM PROJECT
    base = ''.join(random.choices(string.digits, k=7))

    # Format quantity as 2 digits (pad with leading zero if needed, cap at 99)
    quantity_digits = str(min(quantity, 99)).zfill(2)

    # Fixed project prefix
    prefix = 'SP'

    # Format: SP-NUMBERS-QUANTITY (e.g., SP-1223324-25)
    return f"{prefix}-{base}-{quantity_digits}"

def verify_ticket_number(ticket_number):
    """Verify if a ticket number is valid.
    Format: SP-<7 digits>-<2 digit quantity>
    """
    try:
        # Expected format: SP-<7 digits>-<2 digits>
        prefix, base, quantity_part = ticket_number.split('-')

        # Verify format: prefix must be SP, base must be 7 digits, quantity must be 2 digits
        if prefix != 'SP' or not (len(base) == 7 and len(quantity_part) == 2):
            return False

        # Verify all parts are numeric
        if not (base.isdigit() and quantity_part.isdigit()):
            return False

        return True
    except:
        return False

def send_ticket_email(receiver_email, name, tickets):
    """Send email with ticket numbers in HTML format."""
    # Debug: show tickets being sent
    print(f"[DEBUG] Preparing to send email to {receiver_email} with tickets: {tickets}")

    subject = f"🎟️ Your Event Tickets - Payment Confirmed"
    
    # Create ticket numbers HTML list
    tickets_html = "".join([
        f'<div style="font-size: 20px; font-weight: bold; font-family: \'Courier New\', monospace; background: #f0f0f0; padding: 12px; margin: 10px 0; border-radius: 5px; letter-spacing: 2px;">{t["ticket_number"]}</div>'
        for t in tickets
    ])
    
    # Create HTML email body
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); overflow: hidden;">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">✅ Payment Successful!</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">Your tickets have been generated</p>
                </div>
                
                <!-- Main Content -->
                <div style="padding: 30px;">
                    <p style="font-size: 16px; color: #333;">Hi <strong>{name}</strong>,</p>
                    
                    <p style="font-size: 14px; color: #666;">Your payment has been confirmed! 🎉 Below are your ticket details:</p>
                    
                    <!-- Ticket Numbers Section -->
                    <div style="background: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
                        <h3 style="margin: 0 0 15px 0; color: #667eea; font-size: 16px;">Your Ticket Numbers:</h3>
                        {tickets_html}
                    </div>
                    
                    <!-- Important Info -->
                    <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                        <h4 style="margin: 0 0 10px 0; color: #856404; font-size: 14px;">⚠️ Important:</h4>
                        <ul style="margin: 0; padding-left: 20px; color: #856404; font-size: 13px;">
                            <li>Save these ticket numbers - you'll need them at the event gate</li>
                            <li>Each ticket can only be used once</li>
                            <li>Keep your tickets secure and don't share them publicly</li>
                            <li>Ticket format: SP-NUMBER-QUANTITY (e.g., SP-1223324-25)</li>
                        </ul>
                    </div>
                    
                    <!-- Receipt Info -->
                    <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h4 style="margin: 0 0 10px 0; color: #333; font-size: 14px;">Receipt Details:</h4>
                        <table style="width: 100%; border-collapse: collapse; font-size: 13px; color: #666;">
                            <tr>
                                <td style="padding: 8px 0;"><strong>Name:</strong></td>
                                <td style="padding: 8px 0; text-align: right;">{name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0;"><strong>Email:</strong></td>
                                <td style="padding: 8px 0; text-align: right;">{receiver_email}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0;"><strong>Quantity:</strong></td>
                                <td style="padding: 8px 0; text-align: right;">{len(tickets)} ticket(s)</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0;"><strong>Date:</strong></td>
                                <td style="padding: 8px 0; text-align: right;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <p style="font-size: 13px; color: #999; text-align: center; margin: 20px 0 0 0;">
                        Thank you for your purchase! See you at the event! 🎉
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f5f5f5; padding: 20px; text-align: center; border-top: 1px solid #ddd;">
                    <p style="margin: 0; font-size: 12px; color: #999;">-- Event Team</p>
                    <p style="margin: 5px 0 0 0; font-size: 11px; color: #bbb;">Questions? Contact us for support</p>
                </div>
                
            </div>
        </body>
    </html>
    """
    
    # Create the email message
    msg = MIMEMultipart('alternative')
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg['Subject'] = subject
    
    # Add plain text fallback
    plain_text = f"""
Hi {name},

Your payment has been confirmed! 🎉
Below are your ticket details:

{chr(10).join([f"Ticket {i+1}: {t['ticket_number']}" for i, t in enumerate(tickets)])}

IMPORTANT:
- Save these ticket numbers - you'll need them at the event gate
- Each ticket can only be used once
- Keep your tickets secure and don't share them publicly

Thank you for your purchase!

-- Event Team
"""
    
    msg.attach(MIMEText(plain_text, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))
    
    # Send email
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"📧 Receipt email sent to {receiver_email}")
    except Exception as e:
        import traceback
        print(f"Failed to send email: {str(e)}")
        traceback.print_exc()

# ---------- FLASK ROUTES ----------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/verify", methods=["POST"])
def verify_payment():
    try:
        data = request.get_json()
        reference = data.get("reference")
        name = data.get("name")
        email = data.get("email")
        quantity = int(data.get("quantity", 1))

        print(f"[DEBUG] /verify called: ref={reference}, name={name}, email={email}, qty={quantity}")

        if not PAYSTACK_SECRET_KEY:
            print("[ERROR] PAYSTACK_SECRET_KEY not set in environment")
            return jsonify({
                "status": "error",
                "message": "Server configuration error: PAYSTACK_SECRET_KEY not set."
            }), 500

        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        
        print(f"[DEBUG] Calling Paystack API: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise exception for bad status codes
        result = response.json()

        print(f"[DEBUG] Paystack response: {result}")

        if result.get("status") and result["data"].get("status") == "success":
            tickets = []

            # Generate tickets
            for i in range(quantity):
                ticket_number = generate_ticket_number(quantity)
                print(f"[DEBUG] Generated ticket {i+1}/{quantity}: {ticket_number}")
                
                # Save ticket information to database
                ticket_info = {
                    'ticket_id': ticket_number,
                    'name': name,
                    'email': email,
                    'purchase_date': datetime.now(),
                    'payment_reference': reference,
                    'used': False,
                    'used_date': None
                }
                save_ticket_to_db(ticket_info)
                
                tickets.append({"ticket_number": ticket_number})

            print(f"[DEBUG] All {len(tickets)} tickets saved to database")
            
            # Send tickets via email
            send_ticket_email(email, name, tickets)

            return jsonify({
                "status": "success",
                "message": f"Payment verified and tickets sent to {email}.",
                "tickets": tickets
            })
        else:
            error_msg = result.get("message", "Payment verification failed.")
            print(f"[ERROR] Payment status not success: {error_msg}")
            return jsonify({
                "status": "failed",
                "message": error_msg
            })
    
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error calling Paystack: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Network error: {str(e)}"
        }), 500
    
    except Exception as e:
        print(f"[ERROR] Unexpected error in /verify: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500

@app.route("/verify-ticket/<ticket_number>")
def verify_ticket(ticket_number):
    """Verify a ticket and mark it as used."""
    # First verify the ticket number format and checksum
    if not verify_ticket_number(ticket_number):
        return jsonify({
            "status": "error",
            "message": "Invalid ticket format or checksum."
        })
    
    # Then check the database
    ticket_info = get_ticket_info(ticket_number)
    
    if not ticket_info:
        return jsonify({
            "status": "error",
            "message": "Ticket not found."
        })
    
    if ticket_info['used']:
        return jsonify({
            "status": "error",
            "message": "Ticket already used.",
            "used_date": ticket_info['used_date']
        })
    
    # Mark ticket as used
    mark_ticket_used(ticket_number)
    
    # Extract section from ticket number
    section = ticket_number.split('-')[0]
    
    return jsonify({
        "status": "success",
        "message": "Ticket verified successfully.",
        "ticket_info": {
            "name": ticket_info['name'],
            "email": ticket_info['email'],
            "purchase_date": ticket_info['purchase_date'],
            "section": section
        }
    })


# DEBUG: temporary endpoint to generate and email tickets without Paystack (for testing)
@app.route('/debug-send', methods=['POST'])
def debug_send():
    """Generate tickets and send email/SMS directly for testing.
    Request JSON: {"name": "Name", "email": "email@example.com", "phone": "+233XXXXXXXXX", "quantity": 2}
    """
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    quantity = int(data.get('quantity', 1))

    tickets = []
    for _ in range(quantity):
        ticket_number = generate_ticket_number(quantity)
        ticket_info = {
            'ticket_id': ticket_number,
            'name': name,
            'email': email,
            'purchase_date': datetime.now(),
            'payment_reference': 'debug',
            'used': False,
            'used_date': None
        }
        save_ticket_to_db(ticket_info)
        tickets.append({"ticket_number": ticket_number})

    # Send email
    send_ticket_email(email, name, tickets)
    return jsonify({"status": "success", "tickets": tickets})

if __name__ == "__main__":
    app.run(debug=True)

