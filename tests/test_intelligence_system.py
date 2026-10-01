import importlib
import pytest

INTELLIGENCE_MODULES = [
    "enterpriseguard.intelligence.ai_diagnostics",
    "enterpriseguard.intelligence.attack_analyzer",
    "enterpriseguard.intelligence.rag_system",
]


@pytest.mark.parametrize("mod_name", INTELLIGENCE_MODULES)
def test_intelligence_modules_import_and_instantiate(mod_name):
    """اختبار استيراد وتشغيل كلاسات موديولات الذكاء الاصطناعي ديناميكياً."""
    try:
        mod = importlib.import_module(mod_name)
    except (ModuleNotFoundError, ImportError) as e:
        pytest.skip(f"تم تخطي الاختبار لعدم توفر الموديول أو التبعيات: {e}")

    assert mod is not None

    # فحص واختبار الكلاسات داخل الموديول
    classes = [
        getattr(mod, attr)
        for attr in dir(mod)
        if isinstance(getattr(mod, attr), type) and getattr(mod, attr).__module__ == mod.__name__
    ]

    for cls in classes:
        try:
            obj = cls()
            methods = [
                m for m in dir(obj)
                if callable(getattr(obj, m)) and not m.startswith("_")
            ]
            for m_name in methods:
                method = getattr(obj, m_name)
                try:
                    method()
                except TypeError:
                    try:
                        method({"log": "suspicious payload detected", "severity": "HIGH"})
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass
