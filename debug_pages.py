
import os
import sys

print("Python version:", sys.version)
print("\nChecking pages directory...")

pages_dir = "pages"
if os.path.exists(pages_dir):
    files = [f for f in os.listdir(pages_dir) if f.endswith('.py')]
    print(f"Found {len(files)} page files:")
    for f in files:
        print(f"  - {f}")
        # Try importing each page
        try:
            module_name = f[:-3]  # Remove .py
            exec(f"import pages.{module_name.replace(' ', '_').replace('🌍', '').replace('📈', '').replace('🤖', '').replace('🏥', '').replace('🗺️', '').replace('📊', '')}")
            print(f"    ✅ Imports successfully")
        except Exception as e:
            print(f"    ❌ Import error: {e}")
else:
    print("❌ Pages directory not found!")

print("\nCurrent working directory:", os.getcwd())
print("\nDirectory contents:")
for item in os.listdir('.'):
    print(f"  - {item}")
