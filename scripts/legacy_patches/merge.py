import os

# اسم الملف النهائي الذي سيتم إنشاؤه
OUTPUT_FILE = "all_project_files.md"

# الصيغ أو الملفات التي تريد دمجها (يمكنك تعديلها حسب رغبتك)
# إذا كنت تريد دمج ملفات الماركداون فقط، ابقِ على '.md'
# إذا كنت تريد دمج ملفات برمجية أخرى (مثل .py, .js, .txt) أضفها للقائمة
ALLOWED_EXTENSIONS = {'.md', '.txt', '.py', '.js', '.html', '.css'}

def merge_files_to_markdown():
    # الحصول على المجلد الحالي الذي يقع فيه السكربت
    current_directory = os.getcwd()
   
    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        outfile.write(f"# توثيق ملفات المشروع\n\n")
       
        # المرور على جميع المجلدات والملفات الفرعية
        for root, dirs, files in os.walk(current_directory):
            # تجنب قراءة ملف المخرجات نفسه أو مجلدات بيئة العمل الافتراضية
            if OUTPUT_FILE in files:
                files.remove(OUTPUT_FILE)
            if '.git' in root or '__pycache__' in root or 'venv' in root:
                continue
               
            for file in files:
                file_path = os.path.join(root, file)
                file_extension = os.path.splitext(file)[1].lower()
               
                # التحقق من صيغة الملف قبل دمجه
                if file_extension in ALLOWED_EXTENSIONS:
                    # حساب المسار النسبي للملف لجعله كعنوان
                    relative_path = os.path.relpath(file_path, current_directory)
                   
                    outfile.write(f"## الملف: `{relative_path}`\n\n")
                   
                    # تحديد نوع الكود لتنسيقه بشكل صحيح داخل الماركداون
                    lang = file_extension.replace('.', '')
                    outfile.write(f"```{lang}\n")
                   
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as infile:
                            outfile.write(infile.read())
                    except Exception as e:
                        outfile.write(f"تعذر قراءة الملف بسبب خطأ: {e}\n")
                       
                    outfile.write("\n```\n\n")
                    outfile.write("---\n\n") # فاصِل بين الملفات

    print(f"✅ تم بنجاح دمج جميع الملفات في ملف واحد باسم: {OUTPUT_FILE}")

if __name__ == "__main__":
    merge_files_to_markdown()

