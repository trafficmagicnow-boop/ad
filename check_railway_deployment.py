"""
Railway Deployment Diagnostic Script
This script will help identify why Railway isn't showing the new version
"""
import urllib.request
import json

# Ask user for their Railway URL
print("="*60)
print("RAILWAY DEPLOYMENT DIAGNOSTIC")
print("="*60)

railway_url = input("\nПожалуйста, введи URL твоего Railway проекта (например: https://твой-проект.railway.app): ").strip()

if not railway_url:
    print("❌ URL не введён!")
    exit(1)

print(f"\n🔍 Проверяю {railway_url}...")

try:
    # Fetch the dashboard
    req = urllib.request.Request(railway_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        html_content = response.read().decode('utf-8')
        
        print("\n✅ Сайт доступен!")
        print(f"📦 Размер HTML: {len(html_content)} байт")
        
        # Check for version indicators
        checks = {
            "v2.6 BANNER": "VERSION 2.6 IS LIVE" in html_content or "SYSTEM v2.6" in html_content,
            "Admin Panel": "adminPanel" in html_content,
            "Login System": "getCurrentUser" in html_content or "api/login" in html_content,
            "OLD VERSION": "ADD NEW CAMPAIGN" in html_content and "adminPanel" not in html_content,
        }
        
        print("\n🔎 Результаты проверки:")
        for check_name, found in checks.items():
            status = "✅ НАЙДЕНО" if found else "❌ НЕ НАЙДЕНО"
            print(f"  {check_name}: {status}")
        
        if checks["OLD VERSION"]:
            print("\n⚠️  ПРОБЛЕМА: На Railway старая версия без аутентификации!")
            print("    Railway не обновляет код из GitHub.")
            print("\n📋 РЕШЕНИЕ:")
            print("    1. Зайди в dashboard.railway.app")
            print("    2. Найди свой проект")
            print("    3. Нажми 'Deployments' → 'Redeploy'")
            print("    4. Или проверь, что GitHub подключен к проекту")
        elif checks["v2.6 BANNER"]:
            print("\n✅ На Railway актуальная версия v2.6!")
            print("   Проблема скорее всего в кэше браузера.")
        else:
            print("\n🤔 Неопределенное состояние. Проверь вручную.")
            
except urllib.error.HTTPError as e:
    print(f"\n❌ HTTP ошибка: {e.code} {e.reason}")
except urllib.error.URLError as e:
    print(f"\n❌ Не удалось подключиться: {e.reason}")
except Exception as e:
    print(f"\n❌ Ошибка: {e}")

print("\n" + "="*60)
