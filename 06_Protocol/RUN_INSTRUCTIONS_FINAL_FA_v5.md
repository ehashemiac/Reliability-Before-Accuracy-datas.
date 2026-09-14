# راهنمای اجرای نهایی — نسخه v8

### 0) نکته امنیتی
کلید API که قبلاً در گفتگو فرستاده شده را revoke کنید و یک کلید جدید بسازید. آن را در هیچ فایل/پیام commit نکنید.

Windows PowerShell:
```powershell
$env:OPENROUTER_API_KEY="sk-or-v1-..."
```
macOS/Linux:
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

### 1) وارد code شوید
```bash
cd code
```

### 2) QC داده و manifest
```bash
python verify_final_dataset.py
```
باید `DATASET QC PASSED` دریافت کنید.

### 3) در دسترس بودن مدل‌ها
```bash
python check_models_v8.py
```
باید هر دو مدل `AVAILABLE` باشند.

### 4) Smoke test مدل Ultra
```bash
python openrouter_runner_v7.py --limit 1 --models nvidia/nemotron-3-ultra-550b-a55b:free
```

بعد:
```bash
python score_main_v7.py
python analyze_main_v7.py
```

### 5) Smoke test مدل Super
```bash
python openrouter_runner_v7.py --limit 1 --models nvidia/nemotron-3-super-120b-a12b:free
```

بعد scoring را تکرار کنید.

### 6) اجرای benchmark اصلی
بعد از سالم بودن smoke test هر دو مدل:
```bash
python openrouter_runner_v7.py --models nvidia/nemotron-3-ultra-550b-a55b:free nvidia/nemotron-3-super-120b-a12b:free --delay 4
```

تعداد شرایط = 320؛ چون D دو call دارد، حدود 400 درخواست API خواهید داشت. retryها observation جدید نیستند.

### 7) scoring نهایی
```bash
python score_main_v7.py
python analyze_main_v7.py
python analyze_stats_v8.py
```

### 8) فایل موردنیاز برای تحلیل پژوهشی
`results/main_run_log_v7.jsonl`

کلید API را ارسال نکنید.
