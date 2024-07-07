import argparse
from models.ReferencModels import create_initial_admin, create_initial_user

def main():
    parser = argparse.ArgumentParser(description='Create initial admin or user.')
    parser.add_argument('--admin-email', type=str, help='Email for initial admin')
    parser.add_argument('--admin-phone', type=str, help='Phone number for initial admin')
    parser.add_argument('--user-email', type=str, help='Email for initial user')
    parser.add_argument('--user-phone', type=str, help='Phone number for initial user')
    parser.add_argument('--user-name', type=str, help='Name for initial user')

    args = parser.parse_args()

    if args.admin_email and args.admin_phone:
        create_initial_admin(args.admin_email, args.admin_phone)
    elif args.user_email and args.user_phone:
        create_initial_user(args.user_email, args.user_phone, args.user_name)
    else:
        print("Please provide valid arguments.")

if __name__ == '__main__':
    main()
