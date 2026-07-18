# Colchester Rangers FC

A simple Python Flask website for Colchester Rangers FC.

## Features

- Home page with club introduction
- Staff page
- Players page
- Results page
- Contact form with form validation

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

## FastHosts deployment

For FastHosts-style Python hosting, the app is ready to be served through a WSGI entry point.

- Use [app.py](app.py) as the application module, or the included [wsgi.py](wsgi.py) / [passenger_wsgi.py](passenger_wsgi.py) entry points.
- Ensure the hosting panel installs the requirements from [requirements.txt](requirements.txt).
- Set the environment variables for the contact form and secret key in the hosting control panel.

## Render deployment

Render can run this app as a Python web service.

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn wsgi:app`
- Add environment variables for the contact form and `FLASK_SECRET_KEY` in the Render dashboard.
- The app already binds to `0.0.0.0` and uses the `PORT` environment variable when started directly.

## DeployHQ settings

For a DeployHQ deployment to FastHosts, use the following values:

- Server host: `sftp.colchester-rangers-fc.co.uk`
- Connection type: `SFTP`
- Username: your FastHosts SFTP username
- Password: your FastHosts SFTP password
- Remote path: your hosting web root directory
- Deployment branch: `main`
- Ignore rules: include [.deployignore](.deployignore)

If your host expects the app to start from the web root, make sure the deployment target is the directory that contains [passenger_wsgi.py](passenger_wsgi.py) and [.htaccess](.htaccess).

## Optional email delivery

If you want the contact form to send real emails, configure SMTP environment variables before running the app.

Example PowerShell values:

```powershell
$env:MAIL_SERVER = "smtp.example.com"
$env:MAIL_PORT = "587"
$env:MAIL_USERNAME = "user@example.com"
$env:MAIL_PASSWORD = "your-password"
$env:MAIL_FROM = "club@example.com"
$env:MAIL_TO = "contact@example.com"
$env:FLASK_SECRET_KEY = "a-secure-secret-key"
python app.py
```

If SMTP is not configured, the form will still accept submissions and show a success message locally.
