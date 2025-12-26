"""
ФИНАЛЬНАЯ ПРОВЕРКА RAILWAY DEPLOYMENT
Этот скрипт проверит, какая версия на Railway
"""
import urllib.request
import json

print("="*70)
print("ПРОВЕРКА ВЕРСИИ НА RAILWAY")
print("="*70)

url = input("\nВведи URL сайта (например: https://твой-проект.railway.app): ").strip()
if not url:
    print("❌ URL не введён")
    exit(1)

print(f"\n🔍 Проверяю {url}/api/version...")

try:
    req = urllib.request.Request(f"{url}/api/version", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())
        
        print("\n✅ ВЕРСИЯ НА RAILWAY:")
        print(f"   Version: {data.get('version', 'unknown')}")
        print(f"   Build: {data.get('build', 'unknown')}")
        print(f"   Features: {', '.join(data.get('features', []))}")
        print(f"   Timestamp: {data.get('timestamp', 'unknown')}")
        
        if data.get('version') == '2.6':
            print("\n🎉 УСПЕХ! Railway показывает версию 2.6!")
            print("   Теперь открой сайт и нажми Ctrl+F5 для очистки кэша")
        else:
            print(f"\n⚠️  Railway показывает версию {data.get('version')}, а должна быть 2.6")
            print("   Нужно сделать Redeploy в Railway dashboard")
            
except urllib.error.HTTPError as e:
    if e.code == 404:
        print("\n❌ Endpoint /api/version не найден")
        print("   Это значит Railway показывает СТАРУЮ версию без этого endpoint")
        print("   ➡️  ДЕЙСТВИЕ: Зайди в Railway dashboard и нажми REDEPLOY")
    else:
        print(f"\n❌ HTTP ошибка: {e.code}")
except Exception as e:
    print(f"\n❌ Ошибка: {e}")

print("\n" + "="*70)
print("ЕСЛИ ВИДИШЬ 404 - RAILWAY НЕ ОБНОВИЛСЯ. НУЖЕН MANUAL REDEPLOY.")
print("="*70)
