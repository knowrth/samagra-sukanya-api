# Samagra-sukanya-api

## Set-up Environment

To run the app, create a virtual environment
```bash
$ python -m venv venv
```

## Installation

To run the app flawlessly, satisfy the requirements
```bash
$ pip install -r requirements.txt
```

## Start Server

Change into app folder:
```bash
$ cd app
```

Now run the application using:
```bash
$ python main.py
```

## Initial Admin & User Creation

To send admin email, phone from terminal , it can be done using:
```bash
$ python initial.py --admin-email admin@example.com --admin-phone 9876543210
```

To send user email, phone, name from terminal , it can be done using:
```bash
$ python initial.py --user-email user@example.com --user-phone 1234567890 --user-name Name
```