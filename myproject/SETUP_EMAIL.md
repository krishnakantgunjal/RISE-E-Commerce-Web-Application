# 📧 How to Setup Real Email Sending (Gmail)

Currently, your project is in **Test Mode**. Emails are printed to the **Command Prompt / Terminal** window instead of being sent to a real inbox.

To send real emails, follow these steps:

## Step 1: Get a Google App Password
**Note:** You CANNOT use your regular Gmail password. Google requires a special "App Password" for security.

1.  Go to your [Google Account Security Page](https://myaccount.google.com/security).
2.  Enable **2-Step Verification** (if not already enabled).
3.  Search for **"App Passwords"** in the search bar at the top (or look under 2-Step Verification).
4.  Create a new App Password:
    *   **App name:** Django Project
    *   Click **Create**.
5.  Copy the **16-character code** (it looks like `abcd efgh ijkl mnop`).

## Step 2: Update `myproject/settings.py`

1.  Open `myproject/settings.py`.
2.  Scroll to the very bottom.
3.  **Comment out** the Console Backend line:
    ```python
    # EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    ```
4.  **Uncomment** and fill in the Gmail settings:
    ```python
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'your-actual-email@gmail.com'  # <--- Put your Gmail address here
    EMAIL_HOST_PASSWORD = 'xxxx xxxx xxxx xxxx'      # <--- Put your 16-char App Password here
    ```

## Step 3: Test It!
1.  Restart your server (`Ctrl+C` then `python manage.py runserver`).
2.  Place a new order.
3.  Check your inbox!
