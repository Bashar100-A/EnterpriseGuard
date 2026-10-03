from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_provider_initialized = False

def init_telemetry(service_name: str = "EnterpriseGuard", env: str = "development"):
    global _provider_initialized
    if _provider_initialized:
        return trace.get_tracer(service_name)

    resource = Resource.create(attributes={
        "service.name": service_name,
        "environment": env
    })

    provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
    
    # BatchSpanProcessor لتجميع وإرسال البيانات بكفاءة دون إعاقة الأداء
    processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(processor)
    
    trace.set_tracer_provider(provider)
    _provider_initialized = True
    return trace.get_tracer(service_name)
