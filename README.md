# Colchester Rangers FC

A Python Flask website for Colchester Rangers FC.

## Features

- Home page with club introduction
- Staff page
- Players page
- Results page
- Contact form with validation

## Run locally

1. Create a Python virtual environment:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Run the app:

   ```powershell
   python app.py
   ```

4. Open `http://127.0.0.1:5000` in your browser.

## cPanel deployment for Krysta

This project is prepared for deployment to a cPanel Python/Passenger hosting account.

### Files to upload

- [app.py](app.py) - Flask application
- [passenger_wsgi.py](passenger_wsgi.py) - WSGI entry point for cPanel
- [.htaccess](.htaccess) - Passenger startup settings
- [requirements.txt](requirements.txt) - Python dependencies
- [static/](static) and [templates/](templates) - site assets and pages

### Deployment steps

1. Upload the project files to the domain document root, or to the application folder if the site is running from a subdirectory.
2. Make sure the folder contains [passenger_wsgi.py](passenger_wsgi.py) and [.htaccess](.htaccess).
3. In cPanel, install the packages from [requirements.txt](requirements.txt) using the Python app or dependency installer if available.
4. Set the environment variables for the contact form and secret key in cPanel's environment settings:
   - `FLASK_SECRET_KEY`
   - `MAIL_SERVER`
   - `MAIL_PORT`
   - `MAIL_USE_TLS`
   - `MAIL_USERNAME`
   - `MAIL_PASSWORD`
   - `MAIL_FROM`
   - `MAIL_TO`

### Optional email delivery

If SMTP is not configured, the contact form will still load locally and show a friendly message instead of failing.
