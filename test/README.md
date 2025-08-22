# OneService Test Applications

这个文件夹包含两个完整的测试应用，用于验证 OneService 监控系统的完整性。两个应用都通过 OpenTelemetry 发送遥测数据到 Alloy，并被 node-exporter 监控。

## 测试应用

### 1. MNIST CNN Demo (`mnist-cnn-demo/`)
- **技术栈**: Python + FastAPI + TensorFlow + React (单页应用)
- **功能**: 手写数字识别系统
- **端口**: 8001
- **特性**:
  - 提供训练 CNN 模型的 Web 界面
  - 支持在线手绘数字识别
  - 导出 ONNX 模型
  - 生成训练和推理的遥测数据

### 2. Spring OTEL Demo (`spring-otel-demo/`)
- **技术栈**: Java + Spring Boot + Micrometer
- **功能**: 自动生成流量的 Spring Boot 应用
- **端口**: 8088
- **特性**:
  - 提供多个 REST API 端点
  - 自动生成内部流量（每 3-15 秒调用自己的端点）
  - 模拟正常请求、计算请求和错误请求
  - 集成 Spring Boot Actuator 指标

## 监控集成

### OpenTelemetry (OTLP)
两个应用都配置了 OpenTelemetry instrumentation，向 Alloy 发送：
- **Traces**: 请求追踪和分布式链路
- **Metrics**: 应用业务指标和性能指标  
- **Logs**: 结构化日志

### Infrastructure Monitoring
- **Node Exporter**: 监控容器的系统指标（CPU、内存、磁盘、网络）
- **cAdvisor**: 监控 Docker 容器指标
- **应用指标**: 每个应用暴露 `/metrics` 端点给 Prometheus

## 快速启动

```bash
# 启动完整的监控系统（包括两个测试应用）
cd oneservice/deploy
docker-compose up -d

# 检查服务状态
docker-compose ps

# 访问应用
# MNIST Demo: http://localhost:8001
# Spring Demo: http://localhost:8088/hello
# Grafana: http://localhost:3000 (admin/admin)
```

## 测试脚本

### MNIST 自动化测试
```bash
./test-mnist.sh
```
- 自动训练模型
- 生成预测请求
- 验证 OTLP 数据流

### Spring Boot 流量生成
```bash
./test-spring.sh
```
- 对多个端点生成 HTTP 流量
- 触发不同类型的响应（成功、错误、慢请求）
- 验证追踪和指标收集

## 监控验证

启动后可以在 Grafana 中验证：

1. **基础设施指标**: 
   - 容器 CPU/内存使用率
   - 网络和磁盘 I/O
   - Docker 容器状态

2. **应用指标**:
   - HTTP 请求计数和延迟
   - 业务指标（训练 loss、预测数量等）
   - JVM 指标（Spring Boot）

3. **分布式追踪**:
   - 请求端到端追踪
   - 服务依赖图
   - 性能瓶颈分析

4. **日志聚合**:
   - 结构化应用日志
   - 错误日志关联
   - 日志与追踪关联

## 架构图

```
┌─────────────────┐    ┌─────────────────┐
│  MNIST Demo     │    │ Spring Demo     │
│  (Python)       │    │ (Java)          │
│  Port: 8001     │    │ Port: 8088      │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          │ OTLP (metrics/logs/traces)
          │                      │
          └──────────┬───────────┘
                     │
                ┌────▼────┐
                │  Alloy  │
                │ (Agent) │
                └─────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼───┐   ┌────▼───┐   ┌────▼───┐
   │Prometheus│ │ Tempo  │   │ Loki   │
   │(Metrics) │ │(Traces)│   │ (Logs) │
   └──────────┘ └────────┘   └────────┘
                     │
                ┌────▼────┐
                │ Grafana │
                │ (UI)    │
                └─────────┘
```
