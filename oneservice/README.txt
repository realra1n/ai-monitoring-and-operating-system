OneService-AI-Observation-System (MVP)

Start stack:
- make -C oneservice up

Open:
- Frontend: http://localhost:8080
- Backend API docs: http://localhost:8000/api/docs
- Grafana: http://localhost:3000 (admin/admin)
- Jaeger: http://localhost:16686

Login demo:
- email: demo@oneservice.local
- password: demo123

SDK demo:
1) Prepare Python env and install SDK
	- python -m venv .venv && source .venv/bin/activate
	- pip install -r oneservice/backend/requirements.txt
	- pip install -e oneservice/monitor_sdk

2) Configure SDK endpoint and token
	- Quick demo token:
	  export ONESERVICE_URL=http://localhost:8000
	  export ONESERVICE_TOKEN=tok-demo
	- Or fetch a real token (requires jq):
	  TOKEN=$(curl -s -X POST -H 'Content-Type: application/x-www-form-urlencoded' \
		 -d 'username=demo@oneservice.local&password=demo123' \
		 http://localhost:8000/api/auth/login | jq -r .access_token)
	  export ONESERVICE_URL=http://localhost:8000
	  export ONESERVICE_TOKEN="$TOKEN"

3) Run the demo training script
	- python oneservice/monitor_sdk/examples/train_example.py

4) Verify results
	- UI: http://localhost:8080 → 打开“训练监控”，可查看 run 列表与 loss/log 明细
	- API: 列表、指标、日志
	  curl -s http://localhost:8000/api/runs -H "Authorization: Bearer $ONESERVICE_TOKEN" | jq
	  curl -s "http://localhost:8000/api/runs/1/metrics?name=loss&by=step" -H "Authorization: Bearer $ONESERVICE_TOKEN" | jq
	  curl -s http://localhost:8000/api/runs/1/logs -H "Authorization: Bearer $ONESERVICE_TOKEN" | jq
	- MinIO: http://localhost:9001 （minio/minio123），artifact 将存储于 bucket "artifacts" 下 runs/<run_id>/ 路径
	- Jaeger: http://localhost:16686 （示例 span 接口已接收，完整 OTel 链路可后续补全）

5) 可选：上传 artifact
	- 在脚本中调用 run.upload_artifact('path/to/file') 后，至 MinIO 查看对应对象

Troubleshooting:
 - 401：检查 ONESERVICE_TOKEN 是否设置正确（可用 tok-demo 快速测试）
 - 连接失败：确认容器已启动（make -C oneservice ps / logs）
 - UI 无数据：脚本完成后刷新页面，或用 API /api/runs 检查返回
