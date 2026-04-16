import sys, os, openpyxl
sys.stdout.reconfigure(encoding='utf-8')

BASE = r'C:\Users\user\Desktop'
target_file = None
for root, dirs, files in os.walk(BASE):
    for f in files:
        if "حسين صادق" in f and f.endswith(".xlsm") and not f.startswith("~$"):
            target_file = os.path.join(root, f)
            break
    if target_file: break

if not target_file:
    print("❌ لم يتم العثور على ملف عنبر حسين صادق")
    sys.exit(1)

print(f"--- تحليل ملف: {os.path.basename(target_file)} ---")
wb = openpyxl.load_workbook(target_file, data_only=True, read_only=True)
print(f"الصفحات الموجودة: {wb.sheetnames}")

for sn in wb.sheetnames:
    ws = wb[sn]
    print(f"\n📄 [الصفحة: {sn}]")
    # Print first 10 rows, first 10 cols
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i > 10: break
        print(f"  الصف {i:2}: {row[:8]}")
