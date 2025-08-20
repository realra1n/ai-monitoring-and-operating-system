from monitor_sdk import OneServiceRun
import os
import time

BASE_URL = os.environ.get('ONESERVICE_URL', 'http://localhost:8000')
API_TOKEN = os.environ.get('ONESERVICE_TOKEN', 'tok-demo')

run = OneServiceRun(
    base_url=BASE_URL,
    api_token=API_TOKEN,
    tenant='demo',
    project='demo-project',
    run_name='sdk-demo',
    framework='pytorch',
    tags={'exp':'demo'}
)

for step in range(1, 21):
    loss = 1.0/step
    acc = min(0.5 + step*0.02, 0.99)
    run.log_metric('loss', loss, step=step)
    run.log_metric('accuracy', acc, step=step)
    run.log_text(f"step {step} loss={loss:.3f} acc={acc:.3f}")
    with run.span('train_step'):
        time.sleep(0.05)

run.finish('success')
print('SDK demo complete.')
