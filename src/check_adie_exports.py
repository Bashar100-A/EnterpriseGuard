from enterpriseguard.adie import (
    _PUBLIC_EXPORTS,
    _resolve_component_module,
)


for name, (module, attribute) in _PUBLIC_EXPORTS.items():
    try:
        component = _resolve_component_module(module)
        getattr(component, attribute)
    except Exception:
        print(
            "FAILED:",
            name,
            "=>",
            module,
            attribute,
        )