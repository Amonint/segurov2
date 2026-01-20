import os
import django
import sys

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'segurov2.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def check_users():
    print("--- Verificando Usuarios en Base de Datos ---")
    users = User.objects.all().order_by('username')
    
    if not users.exists():
        print("¡ALERTA! No hay usuarios en la base de datos.")
        return

    print(f"{'Username':<20} | {'Role':<15} | {'Active?':<10} | {'Has Password?':<15}")
    print("-" * 70)
    
    for user in users:
        print(f"{user.username:<20} | {getattr(user, 'role', 'N/A'):<15} | {str(user.is_active):<10} | {str(user.has_usable_password()):<15}")

    # Reset passwords just in case
    print("\n--- Restableciendo Contraseñas (Seguridad) ---")
    
    # Admin
    try:
        admin = User.objects.get(username='admin')
        admin.set_password('admin123')
        admin.save()
        print("✅ admin: admin123")
    except User.DoesNotExist:
        print("❌ Usuario 'admin' no encontrado.")

    # Managers
    managers = ['maria.lopez', 'juan.perez']
    for username in managers:
        try:
            u = User.objects.get(username=username)
            u.set_password('manager123')
            u.save()
            print(f"✅ {username}: manager123")
        except User.DoesNotExist:
             print(f"❌ Usuario '{username}' no encontrado.")
            
    # Custodians
    custodians = ['ana.garcia', 'pedro.martinez']
    for username in custodians:
        try:
            u = User.objects.get(username=username)
            u.set_password('custodian123')
            u.save()
            print(f"✅ {username}: custodian123")
        except User.DoesNotExist:
             print(f"❌ Usuario '{username}' no encontrado.")

if __name__ == '__main__':
    check_users()
