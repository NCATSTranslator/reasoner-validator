"""
Exploratory Open Telemetry instrumentation of the reasoner-validator
"""
import httpx
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME as telemetery_service_name_key, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# add httpx instrumentation
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor


def instrument(
        app,
        service_name: str,
        endpoint: str = "http://127.0.0.1:4318/v1/traces"
):
    print(f"instrumenting service {service_name}")

    # set the service name for our trace provider
    # this will tag every trace with the service name given
    trace.set_tracer_provider(
        TracerProvider(
            resource=Resource.create({telemetery_service_name_key: service_name})
        )
    )

    # create an exporter  to  jaeger
    jaeger_exporter = OTLPSpanExporter(endpoint=endpoint)

    # here we use the exporter to export each span in a trace
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )

    # setup fast api instrumentation for our app
    FastAPIInstrumentor.instrument_app(app, tracer_provider=trace)
    #    excluded_urls=
    #    "docs,openapi.json")

    HTTPXClientInstrumentor().instrument()
