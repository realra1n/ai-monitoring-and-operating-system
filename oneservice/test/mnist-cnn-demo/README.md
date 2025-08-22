# MNIST CNN Test App

Single-page web app with FastAPI backend to train a simple CNN on MNIST (3 epochs) and perform inference on a canvas-drawn digit. Exports a Keras model to ONNX and shows its path.

## Run with Docker (recommended)

```bash
make -C oneservice up
# then open http://localhost:8001
```

## Features
- Train button: downloads MNIST, trains Conv2D(32)->MP->Conv2D(64)->MP->Flatten->Dense->Dense(10) for 3 epochs
- Exports ONNX to oneservice/test/models/model.onnx and displays the path in UI
- 280x280 canvas for drawing; resizes to 28x28 grayscale for inference
- Predict button shows class 0-9

## Endpoints
- GET /           -> serves SPA
- POST /train     -> starts background training
- GET /status     -> training status and ONNX path
- POST /predict   -> array[784] -> {pred, probs}
