# Rocks Tickets - Event Ticketing System

A simple Flask-based event ticketing system that generates secure ticket numbers, stores data in JSON, and sends tickets via email. Integrates with Paystack for payment processing.

## Features

- **Ticket Generation**: Automatically generates unique, secure ticket numbers with built-in checksum validation
- **Payment Integration**: Paystack payment gateway integration
- **Email Delivery**: Sends ticket details via Gmail SMTP
- **Local Database**: Uses JSON file for ticket storage (no external database required)
- **Ticket Verification**: Scan/verify tickets at event gates with one-time use enforcement
- **Cloud Ready**: Deploys easily to Render or other cloud platforms

## Ticket Number Format
Tickets are generated in the format: `SP-NUMBER-QUANTITY`
- `SP` is a fixed prefix that stands for "Suhum Project"
- `NUMBER` is 7 random digits
- `QUANTITY` is the number of tickets purchased (shown as 2 digits, e.g., 01-99)

Example: If you buy 25 tickets, each ticket will be formatted like `SP-1223324-25`

## Project Structure

```
Rocks_tickets/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in git)
├── .gitignore            # Git ignore file
├── tickets.json          # Ticket database (auto-created)
├── static/
│   └── style.css         # CSS styles
└── templates/
    └── index.html        # Frontend HTML
```

## Local Setup

### Prerequisites
- Python 3.8+
- A Gmail account (for ticket emails)
- A Paystack account (for payments)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/Rocks_tickets.git
cd Rocks_tickets
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows
# or: source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```env
PAYSTACK_SECRET_KEY=your_paystack_secret_key
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_gmail_app_password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

5. Run the app:
```bash
python app.py
```

The app will start at `http://localhost:5000`

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PAYSTACK_SECRET_KEY` | Paystack API secret key | `sk_test_xxxxx` |
| `SENDER_EMAIL` | Gmail address for sending tickets | `your_email@gmail.com` |
| `SENDER_PASSWORD` | Gmail App Password (not regular password) | `abcd efgh ijkl mnop` |
| `SMTP_HOST` | SMTP server address | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port (587 for TLS) | `587` |

### Getting Gmail App Password

1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/security
3. Find "App passwords" section
4. Select Mail and your device type
5. Generate and copy the 16-character password

### Getting Gmail App Password

1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/security
3. Find "App passwords" section
4. Select Mail and your device type
5. Generate and copy the 16-character password

## API Endpoints

### Home Page
- **GET** `/` - Displays the ticketing interface

### Payment Verification
- **POST** `/verify` - Verifies Paystack payment and generates tickets
  - Body: `{ "reference": "paystack_ref", "name": "Customer Name", "email": "customer@example.com", "quantity": 2 }`
  - Returns: Generated tickets and confirmation (sent via email and SMS)

### Ticket Verification
- **GET** `/verify-ticket/<ticket_number>` - Verifies and marks a ticket as used
  - Example: `/verify-ticket/A-123456-7`
  - Returns: Ticket holder info and status

## Ticket Storage

Tickets are stored in `tickets.json` as a JSON array:

```json
[
  {
    "ticket_id": "A-123456-7",
    "name": "John Doe",
    "email": "john@example.com",
    "purchase_date": "2025-11-11 10:30:45",
    "payment_reference": "paystack_ref_123",
    "used": false,
    "used_date": null
  }
]
```

## Deployment to Render

1. Push code to GitHub
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Set Build Command: `pip install -r requirements.txt`
5. Set Start Command: `gunicorn app:app`
6. Add environment variables from your `.env` file
7. Deploy!

For detailed steps, see [Render Deployment Guide](#render-deployment).

## Development

### Running Tests
```bash
python -m pytest  # If tests are added
```

### Local Testing Endpoints
```bash
# Test home page
curl http://localhost:5000/

# Test ticket verification (replace with actual ticket number)
curl http://localhost:5000/verify-ticket/A-123456-7
```

## Production Recommendations

- **Backups**: Regularly backup `tickets.json`
- **Database Migration**: For high-volume events, consider migrating to a real database (PostgreSQL, MongoDB)
- **Rate Limiting**: Add rate limiting to prevent abuse
- **HTTPS**: Ensure HTTPS is enabled (Render does this automatically)
- **Monitoring**: Set up logs and alerts for failures

## Troubleshooting

### Emails not sending
- Verify Gmail App Password is correct (not your regular password)
- Check 2-Factor Authentication is enabled
- Verify SMTP settings in `.env`

### SMS not sending
*This project is not configured to send SMS.*

### Tickets not saving
- Ensure `tickets.json` is writable
- Check file permissions
- Verify JSON file is valid

### Payment verification fails
- Verify Paystack Secret Key is correct
- Check Paystack dashboard for transaction status
- Verify payment reference matches

## License

MIT License

## Support

For issues or questions, open an issue on GitHub or contact the development team.
