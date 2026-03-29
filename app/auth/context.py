from passlib.context import CryptContext

context = CryptContext(schemes=['bcrypt'], deprecated='auto')
