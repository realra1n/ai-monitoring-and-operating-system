import os
import threading
from pathlib import Path
from typing import List, Optional

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

# Lazy TF import inside training thread to speed cold start of status/predict routes when not used
_model = None
_status = {
    "state": "idle",
    "epoch": 0,
    "loss": None,
    "acc": None,
    "message": "ready",
    "model_path": None,
}
_lock = threading.Lock()
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "frontend"
MODELS_DIR = BASE_DIR / "models"
TF_MODEL_DIR = MODELS_DIR / "tf_model"
ONNX_PATH = MODELS_DIR / "model.onnx"

app = FastAPI(title="OneService Test: MNIST CNN")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(ASSETS_DIR)), name="static")

# --- Prometheus metrics setup ---
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    
    # Custom metrics
    REQUEST_COUNT = Counter('mnist_requests_total', 'Total requests', ['method', 'endpoint'])
    REQUEST_LATENCY = Histogram('mnist_request_duration_seconds', 'Request latency')
    TRAINING_LOSS = Gauge('mnist_training_loss', 'Current training loss')
    TRAINING_ACCURACY = Gauge('mnist_training_accuracy', 'Current training accuracy')
    TRAINING_EPOCH = Gauge('mnist_training_epoch', 'Current training epoch')
    MODEL_PREDICTIONS = Counter('mnist_predictions_total', 'Total predictions made')
    
    # Middleware to track metrics
    @app.middleware("http")
    async def prometheus_middleware(request, call_next):
        with REQUEST_LATENCY.time():
            response = await call_next(request)
        REQUEST_COUNT.labels(method=request.method, endpoint=str(request.url.path)).inc()
        return response
        
    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics():
        # Update training metrics from current status
        with _lock:
            if _status["loss"] is not None:
                TRAINING_LOSS.set(_status["loss"])
            if _status["acc"] is not None:
                TRAINING_ACCURACY.set(_status["acc"])
            TRAINING_EPOCH.set(_status["epoch"])
        
        return generate_latest()
        
except ImportError:
    # Prometheus client not available, skip metrics
    pass

# --- OpenTelemetry setup ---
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://alloy:4318")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "mnist-test")

try:
    # Minimal OTel setup for FastAPI: traces, metrics, logs -> OTLP
    from opentelemetry import trace, metrics
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry._logs import set_logger_provider, get_logger_provider
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor

    resource = Resource.create({
        "service.name": SERVICE_NAME,
        "service.namespace": "oneservice",
        "service.version": "0.1.0",
    })

    # Traces
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{OTEL_ENDPOINT}/v1/traces")))
    trace.set_tracer_provider(tracer_provider)
    tracer = trace.get_tracer(__name__)

    # Metrics
    reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=f"{OTEL_ENDPOINT}/v1/metrics"))
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)
    meter = metrics.get_meter(__name__)
    loss_gauge = meter.create_observable_gauge("mnist_loss", description="Training loss")
    acc_gauge = meter.create_observable_gauge("mnist_accuracy", description="Training accuracy")

    def _observe_metrics(_):
        with _lock:
            points = []
            if _status["loss"] is not None:
                points.append((float(_status["loss"]), {}))
            if _status["acc"] is not None:
                points.append((float(_status["acc"]), {}))
            return points

    loss_gauge.callback = lambda: [(_status["loss"] or 0.0, {})]
    acc_gauge.callback = lambda: [(_status["acc"] or 0.0, {})]

    # Logs
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(endpoint=f"{OTEL_ENDPOINT}/v1/logs")))
    set_logger_provider(logger_provider)
    LoggingInstrumentor().instrument(set_logging_format=True)

    # Auto-instrument FastAPI
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider, meter_provider=meter_provider)
except Exception as _e:  # noqa: F841
    # OTel optional: proceed even if instrumentation packages are missing
    pass


@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = ASSETS_DIR / "index.html"
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/status")
async def status():
    with _lock:
        return dict(_status)


@app.post("/train")
async def train():
    with _lock:
        if _status["state"] == "training":
            return {"ok": False, "message": "already training"}
        _status.update({"state": "training", "epoch": 0, "loss": None, "acc": None, "message": "starting"})

    def _run_train():
        global _model
        import tensorflow as tf
        import tf2onnx
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            from opentelemetry import trace
            tr = trace.get_tracer(__name__)
            with tr.start_as_current_span("load-mnist-dataset"):
                (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
            # dataset already loaded above
            x_train = (x_train.astype("float32") / 255.0)[..., None]
            x_test = (x_test.astype("float32") / 255.0)[..., None]

            model = tf.keras.Sequential([
                tf.keras.layers.Conv2D(64, (3,3), activation='relu', input_shape=(28,28,1)),
                tf.keras.layers.MaxPooling2D((2,2)),
                tf.keras.layers.Conv2D(128, (3,3), activation='relu'),
                tf.keras.layers.MaxPooling2D((2,2)),
                tf.keras.layers.Flatten(),
                tf.keras.layers.Dense(256, activation='relu'),
                tf.keras.layers.Dense(10, activation='softmax'),
            ])
            model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

            class Progress(tf.keras.callbacks.Callback):
                def on_epoch_end(self, epoch, logs=None):
                    with _lock:
                        _status.update({
                            "epoch": epoch+1,
                            "loss": float(logs.get('loss', 0.0)),
                            "acc": float(logs.get('accuracy', 0.0)),
                            "message": f"epoch {epoch+1} done"
                        })

            with tr.start_as_current_span("train-model"):
                model.fit(x_train, y_train, epochs=5, batch_size=128, validation_data=(x_test, y_test), callbacks=[Progress()], verbose=0)

            # Save TF model
            if TF_MODEL_DIR.exists():
                for p in TF_MODEL_DIR.glob("**/*"):
                    try: p.unlink()
                    except Exception: pass
            model.save(str(TF_MODEL_DIR))

            # Export ONNX
            with tr.start_as_current_span("export-onnx"):
                onnx_model, _ = tf2onnx.convert.from_keras(model)
            with open(ONNX_PATH, 'wb') as f:
                f.write(onnx_model.SerializeToString())

            _model = model
            with _lock:
                _status.update({"state": "done", "message": "training complete", "model_path": str(ONNX_PATH)})
        except Exception as e:
            with _lock:
                _status.update({"state": "error", "message": f"error: {e}"})

    threading.Thread(target=_run_train, daemon=True).start()
    return {"ok": True}


@app.post("/predict")
async def predict(pixels: List[float]):
    global _model
    if _model is None:
        # Try load from disk if available
        tf_model = TF_MODEL_DIR
        if tf_model.exists():
            import tensorflow as tf
            _model = tf.keras.models.load_model(str(tf_model))
        else:
            raise HTTPException(status_code=400, detail="Model not trained yet. Click 'Train' first.")
    arr = np.array(pixels, dtype=np.float32)
    if arr.size != 28*28:
        raise HTTPException(status_code=400, detail="pixels must be length 784")
    # reshape and center-of-mass align to MNIST-like centering
    img = arr.reshape(28,28)
    # normalize to [0,1]
    img = np.clip(img, 0.0, 1.0)
    total = float(img.sum())
    if total > 1e-6:
        ys, xs = np.indices(img.shape)
        cy = float((ys * img).sum() / total)
        cx = float((xs * img).sum() / total)
        # integer shift to move COM near image center (14,14)
        sy = int(round(14 - cy))
        sx = int(round(14 - cx))
        if sy != 0 or sx != 0:
            shifted = np.zeros_like(img)
            y_src_start = max(0, -sy)
            y_dst_start = max(0, sy)
            x_src_start = max(0, -sx)
            x_dst_start = max(0, sx)
            y_count = 28 - abs(sy)
            x_count = 28 - abs(sx)
            if y_count > 0 and x_count > 0:
                shifted[y_dst_start:y_dst_start+y_count, x_dst_start:x_dst_start+x_count] = \
                    img[y_src_start:y_src_start+y_count, x_src_start:x_src_start+x_count]
                img = shifted
    img = img[..., None]
    img = img[None, ...]  # batch
    probs = _model.predict(img, verbose=0)[0]
    pred = int(np.argmax(probs))
    
    # Update Prometheus metrics
    try:
        MODEL_PREDICTIONS.inc()
    except NameError:
        pass  # Prometheus not available
    
    return {"pred": pred, "probs": [float(x) for x in probs]}


@app.get("/onnx")
async def download_onnx():
    if not ONNX_PATH.exists():
        raise HTTPException(status_code=404, detail="ONNX model not found. Train the model first.")
    return FileResponse(
        str(ONNX_PATH), media_type="application/octet-stream", filename="model.onnx"
    )
