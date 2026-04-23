# Codex 5.3 Main Simple Map

هذا الملف يبني خريطة عملية لملف `main.py` الحالي حتى يمكن تطويره أو تفكيكه أو ترحيله إلى الويب بنفس أسلوب العمل المناسب لـ `gpt-5.3-codex`.

## 1. قراءة سريعة للبنية

- الملف كبير جدا: `main.py` حجمه حوالي `344 KB`.
- نقطة الدخول النهائية: `check_and_run()` ثم `MainWindow` في [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:6055).
- الملف يجمع في مكان واحد:
  - قاعدة البيانات
  - منطق الأعمال
  - النوافذ
  - التقارير
  - Telegram
  - النسخ الاحتياطي
  - التفعيل

هذا يعني أن أفضل تطوير لاحق ليس "تعديل واجهة فقط"، بل فصل تدريجي للمسؤوليات.

## 2. Simple Map للمكونات

### A. طبقة القاعدة والمنطق الأساسي

- `DBManager` يبدأ من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:151)
- مسؤوليته:
  - إنشاء الجداول
  - تفعيل `WAL`
  - الإعدادات العامة
  - أنواع التكاليف والإيرادات
  - Views مثل `v_batches`

هذه هي النواة الأولى التي يجب الحفاظ عليها كما هي عند أي تطوير.

### B. الحماية والتفعيل

- `LicenseManager` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:557)
- `ActivationWindow` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:614)
- `check_and_run()` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:678)

هذه طبقة مستقلة نسبيا، ومن الأفضل عدم خلطها مع منطق الويب في المرحلة الأولى.

### C. أدوات مساعدة عامة

- تنسيق وأرقام: [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:717)
- النسخ الاحتياطي والاسترجاع: [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:815)
- حساب الطيور النشطة والتنبيهات: [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:840)
- Telegram report: [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:900)

هذه طبقة خدمات reusable ويجب نقلها لاحقا إلى `services/`.

### D. إدارة السجلات اليومية

- `DailyRecordsWindow` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:940)
- أهم ما يحتويه:
  - تحميل المعايير اليومية
  - حساب active birds
  - حفظ سجل يومي
  - تحديث `total_dead` و `mort_rate`
  - تنبيهات ذكية
  - تصدير Excel/PDF

هذه نافذة عالية القيمة وعالية الحساسية.

### E. إدارة الدفعة

- `BatchForm` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:1509)
- أهم وظائفها:
  - بيانات الدفعة الأساسية
  - التكاليف
  - المبيعات
  - النتائج
  - الحسابات التلقائية
  - الحفظ في `batches`, `farm_sales`, `market_sales`, `batch_costs`, `batch_revenues`

هذه أهم وحدة في النظام كله.

### F. التقارير والتحليلات

- `DashboardWindow` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:2226)
- `WarehousesReportWindow` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:2259)
- `AdvancedAnalyticsWindow` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:2449)
- `BatchSalesReportWindow` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:3273)
- `ReportsHub` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:3716)

هذه الحزمة مسؤولة عن التحليل والتصدير وPDF وExcel.

### G. مراكز التشغيل والإدارة

- `DataEntryHub` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:3400)
- `CostTypesManager` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:4058)
- `OnyxImporterWindow` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:4306)
- `SystemSettingsWindow` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:4496)
- `SplashScreen` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:4663)
- `AboutWindow` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:4736)
- `MainWindow` من [main.py](D:/مجلد جديد/البرنامج حق الدجاج/main.py:4789)

## 3. خريطة الاعتماد الداخلي

الترتيب الفعلي للاعتماد داخل الملف هو:

1. `DBManager`
2. utility functions
3. `DailyRecordsWindow`
4. `BatchForm`
5. مراكز التقارير والتحليلات
6. الإعدادات والنسخ الاحتياطي
7. `MainWindow`
8. `check_and_run()`

النتيجة:
أي تطوير آمن يجب أن يبدأ من `DBManager` و `BatchForm` قبل الواجهة النهائية.

## 4. ما الذي يجب فصله أولا

### المرحلة 1: Extract services

- `database.py`
  - `get_conn`
  - schema init
  - settings helpers
- `services/batches.py`
  - create/update batch
  - load batch
  - batch totals
- `services/daily_records.py`
  - save/delete daily record
  - mortality calculations
- `services/sales.py`
  - farm sales
  - market sales
- `services/reports.py`
  - dashboard aggregates
  - exports
- `services/alerts.py`
  - Telegram
  - smart alerts

### المرحلة 2: Keep UI thin

- سطح المكتب يستدعي الخدمات فقط
- الويب يستدعي نفس الخدمات فقط

هذا هو الطريق الصحيح لتفادي اختلاف الحسابات بين desktop و web.

## 5. خطة تطوير مناسبة لـ Codex 5.3

### Sprint 1

- قراءة `DBManager` واستخراج schema + query helpers فقط
- إنشاء وحدة خدمات مستقلة دون تغيير السلوك
- إضافة smoke checks بسيطة

### Sprint 2

- استخراج منطق `BatchForm._collect`, `BatchForm._auto_calc`, `BatchForm._save`
- جعلها دوال pure أو شبه pure
- استخدام هذه الدوال من desktop والweb معا

### Sprint 3

- استخراج منطق `DailyRecordsWindow`
- نقل تحديث `total_dead`, `mort_rate`, alerts إلى service layer

### Sprint 4

- نقل dashboard/report queries
- فك ارتباط PDF/Excel عن واجهة Tk

### Sprint 5

- توحيد settings / backup / telegram
- ثم تحسين UX وليس قبله

## 6. Simple Map لتطوير نسخة الويب

إذا كان الهدف هو تطوير الويب من `main.py` الحالي، فالأولوية تكون:

1. `DBManager` -> `web/app.py` helpers
2. `BatchForm` -> صفحات `batches`, `costs`, `revenues`, `sales`
3. `DailyRecordsWindow` -> صفحة `daily_records`
4. `MainWindow._load_batches` -> dashboard + list pages
5. `ReportsHub` -> export/report pages
6. `SystemSettingsWindow` -> settings page
7. `LicenseManager` -> يؤجل حتى استقرار core flows

## 7. Prompt Pack مناسب لـ gpt-5.3-codex

استخدم هذا الأسلوب مع `gpt-5.3-codex`:

### Prompt 1

`Read DBManager in main.py and extract schema-safe SQLite helpers into a new module without changing behavior. Keep WAL and foreign keys enabled.`

### Prompt 2

`Read BatchForm in main.py and isolate the batch calculation logic into a reusable service. Preserve all existing field names and totals.`

### Prompt 3

`Read DailyRecordsWindow in main.py and move daily mortality/feed calculations into a service shared by desktop and web.`

### Prompt 4

`Map MainWindow, DataEntryHub, and ReportsHub into web routes and templates while keeping the same database writes and aggregate formulas.`

### Prompt 5

`Before editing, list every function in main.py touched by batch save, daily save, and report export, then implement changes surgically.`

## 8. القرار الهندسي الأهم

لا تطور `main.py` الكبير مباشرة على أنه ملف واجهة فقط.

التطوير الصحيح هو:

1. تثبيت schema والسلوك الحالي
2. استخراج service layer
3. جعل desktop وweb مجرد واجهتين فوق نفس الخدمات

## 9. خلاصة تنفيذية

الملف الحالي ليس مجرد نافذة Tkinter كبيرة، بل monolith كاملة.

أفضل طريقة لتطويره مع `Codex 5.3` هي:

1. استخراج المنطق وليس إعادة كتابة الواجهة فقط
2. البدء بـ `DBManager` و `BatchForm`
3. تأجيل التجميل حتى تثبت الحسابات
4. جعل أي تطوير جديد يمر عبر services مشتركة
