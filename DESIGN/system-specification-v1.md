# OneService-AI-Observation-System（以 Datadog 为蓝本）的研发提示词
你是一名资深全栈工程师与架构师。请基于以下**完整规格**一次性交付一个可运行的「智算监控运维系统」原型（MVP+可扩展骨架），包含：前端（原生 HTML/CSS/JS）、后端（Python FastAPI）、数据库与中间件（Docker Compose 启停）、基础监控集成（Prometheus/Thanos、Grafana 嵌入）、日志（OpenSearch）、对象存储（MinIO）、链路追踪（OpenTelemetry + Jaeger）、模型图可视化（Netron）、训练指标与日志采集 SDK（monitor\_sdk），以及多租户与 RBAC。风格参考 Datadog：左侧一级菜单、顶部二级菜单、朴素简洁。


## 0. 交付物清单（一次性交付）

1. **单仓 Monorepo 目录结构**（如下）与可执行代码

   ```
   oneservice/
   ├─ backend/            # FastAPI 应用（含 OpenAPI、RBAC、多租户、ingestion、SDK 服务端）
   ├─ frontend/           # 原生 HTML/CSS/JS，Datadog 风格布局，零框架
   ├─ agent/              # OneService-Agent（采集探针，含 Dockerfile 与 K8s DaemonSet）
   ├─ monitor_sdk/        # 训练脚本侧 SDK：metrics/logs/traces 上报 & 模型图/权重上传
   ├─ deploy/             
   │  ├─ docker-compose.yml  # Postgres + MinIO + OpenSearch + Grafana + Prometheus + Thanos + Jaeger + OTel Collector
   │  └─ grafana/            # 预置数据源与 dashboard json
   ├─ docs/               # 架构图、ER图、时序图、API 文档（补充于 Swagger）
   ├─ scripts/            # 初始化脚本（建库/建表/预置租户与用户）
   ├─ Makefile            
   └─ README.md
   ```
2. **一键启动与演示数据**：`make up` / `docker compose up -d` 后可在本机访问 Web；提供演示租户/用户、示例 Run、示例 K8s 事件、示例训练指标曲线。
3. **OpenAPI（Swagger UI）**：自动暴露 `/api/docs`。
4. **基础测试**：后端最小集成测试（pytest），SDK 冒烟测试，前端 E2E 极简脚本（可选）。
5. **安全**：JWT/OAuth2、租户隔离（tenant\_id）、最小权限 RBAC。

---

## 1. 系统概述与目标

* **系统名**：OneService-AI-Observation-System
* **设计蓝本**：Datadog（信息密度高、左侧主导航、顶部副导航、面板简洁）
* **核心价值**：面向 **算法工程师 / 数据科学家 / 平台运维与 SRE**，提供从**实验/训练到模型产出**的一体化观测与诊断：

  * 训练指标（Loss/Acc/Precision/Recall/F1/AUC/LR/Grad Norm/吞吐/显存/内存）
  * 训练日志（结构化/非结构化检索、过滤、流式）
  * 模型网络结构可视化（ONNX / PyTorch / TF）
  * 异常检测、阈值告警、运行态回放（指标+日志+事件 同步查看）、关键步骤 Trace 化
  * 对底层环境（Volcano 调度、K8S 容器、服务器、GPU、网络）**统一观测与运维**
  * 与 **TensorBoard、HuggingFace/Transformers、OpenTelemetry、Prometheus** 生态互通
  * 多租户、多用户、可扩展的权限与审计

---

## 2. 角色与使用场景

* **算法工程师**：调参、对比实验、定位发散/过拟合、对齐训练/验证曲线、查看模型图与权重尺寸
* **平台运维/SRE**：观测训练任务资源占用、异常重试记录、日志检索、阈值告警
* **数据科学家/PM**：查看关键指标趋势、对比 A/B Run、导出报表（CSV/PNG/PDF）

---

## 3. UI/交互（遵循 Datadog 风格）

* **布局**：左侧一级菜单（固定窄栏），顶部二级菜单（上下文切换），内容区卡片网格。
* **主题**：朴素、对比度适中、信息密度高；系统内置浅/深色切换。
* **一级菜单**：

  1. **Dashboard**（仪表盘，Grafana 嵌入，用户可选择/上传 Grafana JSON 配置）
  2. **K8S & 节点**（集群总览、节点列表、节点详情 + 底部 Grafana 指标）
  3. **K8S 事件**（调度异常、镜像拉取失败、节点宕机等事件流）
  4. **训练监控**（Run 列表/详情、指标曲线、日志流、Trace、回放）
  5. **模型可视化**（Netron 嵌入：ONNX/PyTorch/TF 模型图与层级明细、权重概览）
  6. **告警与阈值**（规则、静默、告警历史）
  7. **报表导出**（趋势、A/B 对比、CSV/PNG/PDF 导出）
  8. **租户与用户**（多租户管理、用户、角色、API Token、审计）
  9. **设置**（数据源绑定、OTel/Prom/Grafana/OpenSearch/MinIO 配置）

> **注意**：Grafana 以 iframe/代理嵌入，支持按租户隔离的数据源与 dashboard 选择。

我们将以 Datadog 等成熟观测平台为蓝本，设计合理的一级、二级菜单体系，并为每个页面提供直观的布局和交互。各功能模块将通过清晰的菜单导航呈现，并支持筛选、图表切换、跳转等交互，方便用户快速定位和分析问题。
基础设施观测：提供对服务器、容器等基础设施的监控。
服务器列表页：展示所有主机的概览信息，包括CPU、内存、网络等关键指标当前值和小型趋势图。支持按标签、名称筛选服务器，支持按指标排序（例如按CPU使用率降序）。页面顶部提供时间范围选择器，用户可切换查看最近1小时、6小时、1天等数据。列表每行列出主机名称、状态、主要指标数值等，点击某行可跳转该主机详情。
服务器详情页：展示单台服务器的详细监控视图。页面布局为上方主机基本信息（名称、IP、运行状态、标签等），下方网格布局多个指标图表（CPU使用率、内存占用、磁盘读写、网络流量等）。用户可通过顶部的时间范围控件调整查看周期，通过下拉菜单切换指标类别（如系统指标、容器指标）。图表采用交互式折线图，支持悬停查看具体数值、拖拽缩放时间窗口等。为避免重复造轮子，页面中嵌入 Grafana 的仪表盘组件显示该主机相关的监控数据。例如，嵌入预先配置的 Grafana 主机概览仪表盘（通过 iframe 嵌入 Grafana 面板），直接利用 Grafana 强大的可视化和筛选能力。用户在图表上还可以通过下拉勾选来切换不同统计视图（如平均值/99th percentile 等）。
应用链路观测：针对应用微服务的性能与调用链路提供APM功能。
服务列表页：列出所有受监控的应用服务（例如按服务名称或模块划分）。每个服务条目显示请求吞吐量、平均延迟、错误率等核心指标的当前值，并使用小型趋势图展示近期变化。支持按名称、分组标签（比如环境：开发/生产）筛选服务，支持按错误率或延迟等排序以快速发现异常。用户可选择时间范围以影响所有服务的统计区间。点击某个服务可进入该服务详情。
服务详情页：展示单个服务的深度性能分析和分布式追踪信息。页面顶部概览该服务的关键指标（如当前 QPS、错误率、P95 延迟等），下方分栏显示若干组件：
服务指标图表：通过嵌入 Grafana 仪表盘或ECharts图表，实时展示该服务的重要指标走势（如请求率、平均延迟、错误数曲线），支持选择不同指标以及调整时间窗口。用户可以勾选/隐藏某些指标系列，或切换图表类型（折线图/柱状图）以便观察。
调用链路列表：列出最近采集的一定数量的该服务调用 Trace 列表（可以按持续时间长短或状态错误筛选）。每条 Trace 列表项显示 Trace ID、起始时间、耗时、涉及的下游服务数等。支持根据响应时间阈值筛选慢调用，或按状态筛选错误调用。
Trace 详情查看：点击某条调用链（Trace）记录，会弹出或跳转到调用链详细页面，呈现该 Trace 的Span结构树和时间轴。此页面通过与 Grafana Tempo 集成，在UI中嵌入 Grafana 对 Tempo 数据源的追踪可视化界面，实现丰富的调用链展示。用户可以在该视图中看到分布式调用的拓扑，以及每个span的时间消耗，支持展开查看每个span的详细标签和日志等。UI集成建议：借助 Grafana 的 Tempo 插件，我们可以在应用中以 iframe 方式嵌入一个预配置的 Trace 展示仪表板。通过在URL中传入Trace ID参数，实现特定调用链的可视化。这样用户无须离开平台即可查看完整的调用链路细节。同时，在Trace详情页面提供按钮跳转到相关日志查询（根据Trace ID）或该服务的指标仪表盘，以支持问题排查的链路追溯。
服务依赖/拓扑图（可选）：以拓扑图方式展示该服务与上下游服务的依赖关系。利用OpenTelemetry收集的服务调用关系数据，可嵌入类似 Jaeger 的依赖关系图，或使用 Apache ECharts 绘制交互式服务拓扑。节点表示服务，连线表示调用关系，粗细或颜色表示调用频率或延迟。用户可放大查看某部分拓扑，并点击节点快速跳转对应服务详情。
日志观测：提供集中式日志查询和分析功能。
日志查询页：呈现日志搜索和过滤界面，让运维和开发可以方便地检索各系统日志。页面顶端是搜索栏，支持输入关键词、使用Lucene语法或结构化查询条件（例如 service:order-service AND level:error）来筛选日志。同时提供多个过滤下拉组件，如按照服务名称、主机、日志级别（INFO/WARN/ERROR）、时间范围等快速过滤。用户设置过滤条件后，下方显示日志结果列表，按时间倒序排序实时更新。为了更高效地浏览大量日志，界面上方还显示一个随时间变化的日志频率迷你图表（Histogram），用户可在上面拖拽选择时间区间，缩小查询范围。
日志结果列表按条目逐行显示时间戳、所属服务/主机、日志级别和简要消息。长消息或结构化日志会部分截断显示，支持点击展开查看完整内容及字段。对于JSON格式日志，可格式化高亮关键字段。每条日志旁提供操作，如“查看详情”“关联Trace”等。
日志详情/关联分析：点击某条日志，可在侧边栏弹出该日志的详细信息，包括完整日志消息、堆栈跟踪（如有）、关联的Trace ID等。如果日志中包含Trace ID，那么提供一个链接/按钮，可跳转到对应的调用链详情页面，实现日志与链路的联动。同时，在日志详情视图中也可提供“查看同期指标”功能按钮：点击后根据日志时间范围跳转到相关服务/主机的指标仪表盘页面，方便从日志定位到指标异常。UI集成建议：日志查询页面可基于 OpenSearch Dashboards 的Observability插件来实现，以嵌入其日志分析界面或通过其 API 获取数据来自行渲染。OpenSearch Dashboards 提供类似 Kibana 的日志探索 UI，包括查询语法辅助和结果高亮等，可节省开发工作。我们可以通过iframe嵌入经过权限控制的 OpenSearch Dashboards 日志页面，或使用Grafana的日志面板（连接OpenSearch数据源）将日志以表格形式嵌入。这样既利用了开源工具的强大能力，又在本系统中提供统一的使用体验。
AI 模型观测：针对机器学习模型训练过程和模型本身的可观测性。
训练指标监控页：整合机器学习模型训练的指标可视化，帮助AI开发人员实时了解训练过程。UI上首先提供训练任务选择器（下拉菜单或列表），列出当前和历史的训练作业名称或ID。用户选定特定训练后，下方嵌入 TensorBoard 的指标面板。TensorBoard 是业界常用的深度学习训练可视化工具，可展示随迭代变化的loss、精度等指标曲线。通过在后台启动 TensorBoard 进程加载相应训练日志目录，本页面以 iframe 方式嵌入 TensorBoard 的前端界面。这样用户无需离开OneService平台即可使用 TensorBoard 完整的交互功能，包括平滑曲线、对比不同run、查看训练超参数等。在嵌入时，我们会根据需要对TensorBoard界面进行权限控制和样式调整，使其融入整体UI。一旦训练完成，用户也可以在此页面查看历史训练的指标曲线（从保存的日志加载）。此外，提供“刷新数据”按钮以便从存储（如MinIO）获取最新的训练日志更新。
模型结构可视化页：提供对机器学习模型结构（神经网络）的直观展示。用户可在页面上上传或选取已注册的模型文件（支持 ONNX、TensorFlow SavedModel、PyTorch .pt 等格式）。上传后，后台将模型文件存储到 MinIO 或文件系统，并加载开源的 Netron 可视化组件来渲染模型结构。Netron 是MIT许可的模型结构可视化工具，支持在浏览器中解析模型文件并绘制神经网络的层次结构图。页面中嵌入Netron的前端视图后，用户可以看到模型的计算图，每个层（节点）以模块框展示，并有连线表示张量流动。支持鼠标缩放和平移视图，点击某个层节点，会在侧边栏显示该层的详细属性（类型、输出维度、参数量等）。如果模型过大，还可以提供搜索功能，根据层名称搜索定位。通过这种方式，平台复用Netron强大的可视化能力，避免从零实现模型结构图。同时，模型文件存储在MinIO中，可供Netron在线读取。
告警与通知（可选）：用于配置监控告警规则和查看告警事件。(此部分如已有设计则包括) 用户可以在此配置阈值告警规则（例如CPU使用率连续5分钟超过90%）以及对应的通知渠道。当触发告警时，会在页面列出告警事件列表（包含级别、时间、对象、指标值等），并支持一键跳转相关仪表盘查看详情。告警规则的后端由Prometheus Alertmanager或Grafana Alerting来实现，可嵌入其UI或通过API集成。此菜单确保用户能及时发现异常并采取措施。
以上菜单体系确保了从底层基础设施到应用，再到AI模型的各层面观测需求都被覆盖。通过合理的交互设计（筛选、跳转、嵌入外部UI等），用户可以在一个平台内完成全面的监控与诊断工作，正如Datadog等一站式平台的体验。

开源技术栈的使用与集成：
OneService-AI Observability采用了一套可商用的开源技术栈来支撑上述功能，实现指标、日志、链路追踪和AI训练指标的采集、存储与可视化。原则是充分利用成熟的开源组件，避免重复造轮子，并通过嵌入它们的UI来加速开发。下面逐项说明各功能模块所采用的核心组件及其集成方式：
Web框架与基础设施：后端采用 FastAPI（MIT 许可证） 实现RESTful API服务和Web应用后端。FastAPI性能高且易于编写，可用作统一的服务门户。数据持久化使用 PostgreSQL（PostgreSQL许可证） 作为关系型数据库，存储平台的元数据、配置（例如告警规则、用户权限等）。文件和大数据对象存储采用 MinIO（AGPL 3.0） 对象存储服务。MinIO兼容S3协议，可用于存储时序指标快照、日志归档、Trace片段以及机器学习模型和训练日志等大文件。例如，Prometheus/Thanos 和 Grafana Tempo 都可配置使用 MinIO 作为后端存储，以实现指标和追踪数据的长期持久化。
指标 (Metrics) 收集与可视化：利用 Prometheus（Apache 2.0） 作为核心的指标采集和时序数据库。各微服务和主机通过普罗米修斯SDK或OpenTelemetry导出Metrics，Prometheus定期抓取这些指标数据。为实现高可用和长期存储，引入 Thanos（Apache 2.0） 组件对接 Prometheus。Thanos 以 Sidecar 方式附加在 Prometheus 上，将指标数据汇聚并上传至对象存储（MinIO），从而提供长期存储和全局查询能力。Thanos 还包含 Query 网关，实现多个 Prometheus 数据的全局聚合查询。在UI方面，选择 Grafana（AGPL 3.0） 作为可视化展示前端。Grafana 强大的仪表盘功能允许我们构建各类指标的图表和监控大盘，并通过数据源连接 Prometheus/Thanos 获取数据。本平台通过两种方式集成 Grafana：一是将 Grafana 仪表盘嵌入到自有UI页面中（例如服务器详情页嵌入服务器概览仪表盘）；二是直接链接跳转到完整的 Grafana 界面用于高级分析。我们会开启 Grafana 的匿名访问或基于API的身份集成，以实现无缝嵌入。借助 Grafana，我们无需从头开发指标展示和仪表盘编辑功能，用户还可利用其完善的图表库和插件。日志 (Logs) 收集与存储：系统采用 OpenTelemetry（Apache 2.0） 和 Fluent Bit 等agent来统一收集应用和系统日志。OpenTelemetry SDK 在应用中埋点，捕获结构化日志并可自动注入 Trace ID 等关联信息。日志数据通过 OpenTelemetry Collector 或 Fluent Bit 转发至 OpenSearch（Apache 2.0） 集群存储。OpenSearch是ElasticSearch的开源分支，擅长于存储和检索海量日志数据。我们会创建日志索引并按服务、日期等分片，以支持高效查询。对于日志分析界面，采用 OpenSearch Dashboards（Apache 2.0） 中的 Observability 插件来提供类似 Kibana 的用户界面。通过OpenSearch Dashboards，用户可以使用强大的全文搜索、过滤和可视化功能来分析日志。集成方式上，可以通过反向代理将 Dashboards 的特定页面嵌入本平台UI，或利用其REST API获取数据在本平台界面中绘制（比如用Apache ECharts绘制日志量直方图）。另外，我们也评估 Grafana Loki 作为轻量日志方案，但鉴于OpenSearch功能更强且已在栈内，我们主要使用OpenSearch存储日志，同时保留Grafana连接OpenSearch以供仪表盘关联查询日志。
链路追踪 (Traces) 与APM：采用 OpenTelemetry 作为链路追踪的标准框架。应用程序使用OpenTelemetry SDK进行分布式追踪埋点，生成Trace数据（跨度span）并通过OTLP协议发送。Collector进程将Trace数据汇总后，采用两条路径并行处理：一方面发送到 Grafana Tempo（Apache 2.0） 用于集中存储追踪数据，另一方面发送Trace元数据到Prometheus以关联生成RED指标。Grafana Tempo 是高性能的分布式追踪后端，仅依赖对象存储（MinIO）即可横向扩展，避免了对数据库的复杂依赖。Tempo 将所有Trace以标识索引存储在MinIO上，实现低成本的长链路数据保存。我们将 Tempo 作为Grafana的数据源接入，使得Grafana 前端可以直接查询 Tempo 内的trace并可视化。Grafana 对 Tempo 提供了内置支持，能够根据Trace ID检索并展示调用链细节。相比于单独使用 Jaeger，Grafana 集成方案的优势是能将Trace与指标、日志在同一界面关联呈现。不过我们仍部署 Jaeger（Apache 2.0） 作为辅助，主要用于开发阶段的追踪验证和与OpenTelemetry协议的兼容测试。Jaeger自带的UI功能完整，可在必要时作为备用的Trace查看工具。但在OneService平台中，我们优先通过嵌入Grafana的方式展现追踪，从而把APM深度融入统一界面。此外，借助OpenTelemetry和Grafana，我们实现了日志、指标、追踪三者之间的关联：例如使用Trace ID将日志和对应的调用链关联，利用Span标签将特定请求的指标（延迟等）与Trace关联。这使得用户能够方便地在不同数据维度间跳转，快速完成根因分析。
机器学习训练指标：利用 TensorBoard（Apache 2.0） 来记录和可视化深度学习训练的各项指标。在模型训练脚本中集成TensorBoard日志记录（SummaryWriter），将loss、accuracy等随epoch变化的数据写入文件。训练服务结束后，这些日志文件会保存到共享存储（例如MinIO的bucket中）。OneService平台提供内置的TensorBoard支持：通过调用 TensorBoard 的Python库接口，启动一个后台 TensorBoard 服务进程，指定日志目录为目标训练的日志路径。然后，我们在前端页面里以iframe嵌入TensorBoard的Web界面。TensorBoard自身提供丰富的交互功能，包括标量曲线、直方图、梯度分布、嵌入投影等，可直接复用。这样开发者可以在本平台看到与独立TensorBoard一致的训练监控视图。当需要比较多个实验时，也可以选择同时加载多个日志目录，TensorBoard会合并绘制对比曲线。为安全起见，我们会对TensorBoard的访问做权限限制，只允许经过身份验证的用户查看相应训练的TensorBoard页面。此外，对于一些关键训练指标，我们也可以将其通过OpenTelemetry Metrics导出到Prometheus，从而在Grafana仪表盘中长期保留这些指标趋势，用于日后分析和横向对比。
模型结构与版本：利用 Netron（MIT） 工具对神经网络模型结构进行解析展示。当用户上传模型文件后，后端会调用 Netron 的 Python 库 (netron.start() 方法) 来启动一个Web服务，或者直接使用Netron提供的前端脚本在浏览器中解析模型。由于Netron支持在浏览器端离线解析模型，我们可以选择将模型文件转换为JSON格式的模型表示，然后在前端用Netron的JS库渲染；或者更简单地，后端开启Netron的HTTP服务器并提供模型文件URL，前端iframe嵌入该URL以呈现模型图。在集成中我们倾向于前者（直接前端解析渲染），因为这样可以定制UI并避免额外的网络服务依赖。Netron 对主流的模型格式均有支持，如ONNX、TensorFlow、PyTorch等。通过它，平台免去了开发定制模型可视化的工作，同时满足用户对模型结构直观展示的需求。所有模型文件存储在MinIO中，对于每个模型我们记录其元数据（名称、版本、路径等）在PostgreSQL中，实现模型版本管理。配合Netron的可视化，用户能够清楚了解每个版本模型的架构差异。
其他开源组件：前端图表库采用 Apache ECharts（Apache 2.0） 来实现一些自定义可视化，例如服务拓扑图、自定义总览大盘等。ECharts 提供丰富的图表类型和良好交互性能，适合构建定制的仪表盘组件。对于AI领域特有的可视化需求（如模型性能随时间的变化，对比不同模型版本的指标），ECharts也能方便地绘制。ClickHouse（Apache 2.0） 则作为OLAP数据库，可以用于存储和快速查询大量监控数据（如Trace的统计汇总、日志统计等）。实际部署中，我们考虑将OpenTelemetry Collector收集的指标和Trace元数据同时写入ClickHouse，以支持更灵活的自助分析和报表（类似于SigNoz的架构）。OpenSearch本身也可替代部分OLAP功能，但ClickHouse在复杂分析查询上更高效。在模型监控方面，如果需要跟踪模型推理的结果分布、准确率等，我们也可将这些数据写入 ClickHouse 并通过ECharts绘制相应分析图。在模型部署时，还可以引入 Grafana 的机器学习插件或其他开源AIOps组件，但这些属于扩展方向。
上述开源栈的参考架构示意：应用通过 OpenTelemetry 采集指标、日志和追踪数据，Prometheus+Thanos 存储指标，Tempo 存储追踪，日志进入 OpenSearch。Grafana 作为可视化前端统一展示三大数据，并与 MinIO 等后端存储集成，实现高效查询和长时历史数据保存。

---

## 4. 技术栈与中间件

* **后端**：Python **FastAPI**（MIT），Uvicorn/Gunicorn，SQLAlchemy，Pydantic
* **数据库**：PostgreSQL（元数据、租户/用户、Run/Artifact 索引、告警配置）
* **日志**：OpenSearch（Apache-2.0），Fluent Bit/Vector 采集
* **对象存储**：MinIO（AGPL-3.0，可商用），保存模型文件、权重、TensorBoard 事件文件等
* **指标**：Prometheus + Thanos（GPU/K8S/节点/应用指标；NVIDIA Exporter、node\_exporter、cadvisor、kube-state-metrics）
* **可视化**：Grafana（嵌入式面板），Apache ECharts（自研图表补充）
* **链路追踪**：OpenTelemetry（OTLP） + Jaeger
* **模型图**：Netron（MIT，前端嵌入）
* **可选时序/分析**：ClickHouse（Apache-2.0）用于长周期指标聚合（可选）

> **OTel 指标/日志/Trace 路由建议**：优先经 **OpenTelemetry Collector** 汇聚（接收 OTLP），再：
>
> * 指标导出到 **Thanos Receive**（Prometheus Remote Write 生态）或 ClickHouse
> * 日志导出到 **OpenSearch**
> * Trace 导出到 **Jaeger**

---

## 5. 多租户与权限（必须实现）

* **租户隔离**：所有资源表含 `tenant_id`；中间件侧（OpenSearch/Grafana/Prom/Thanos）以数据源/索引前缀实现逻辑隔离。
* **RBAC 角色**：`TENANT_ADMIN`、`SRE`、`ML_ENGINEER`、`DATA_SCIENTIST`、`PM`、`READONLY`。
* **认证**：OAuth2 Password + JWT（可扩 SSO），支持 **API Token**。
* **审计**：登录、关键配置变更、导出、删除操作落库。

---

## 6. 数据模型（核心表，PostgreSQL）

* `tenants(id, name, status, created_at, ...)`
* `users(id, tenant_id, email, hash_pwd, role, is_active, ...)`
* `projects(id, tenant_id, name, desc, ...)`
* `runs(id, tenant_id, project_id, name, status, framework, params_json, start_ts, end_ts, tags_json)`
* `artifacts(id, tenant_id, run_id, path, type, size, checksum, storage=MinIO, created_at)`
* `alerts(id, tenant_id, rule, severity, channel, enabled, ...)`
* `k8s_clusters(id, tenant_id, name, api_server, ...)`
* `nodes(id, tenant_id, cluster_id, hostname, ip, os, agent_status, labels_json)`
* `dashboards(id, tenant_id, name, grafana_json_path, vars_json)`
* `api_tokens(id, tenant_id, user_id, token_hash, scopes, expired_at)`

> 指标与日志不入库（或仅入**汇总/索引**），由 Prom/Thanos & OpenSearch 持久化；关系库仅保存**索引与元信息**（Run、Artifact、绑定关系、查询条件快照）。

---

## 7. 后端 API（示例，/api/v1）

* **认证**：`POST /auth/login`、`POST /auth/token/refresh`、`POST /auth/api-token`
* **租户/用户**：`/tenants`、`/users`（CRUD + 分页 + 搜索）
* **Dashboard**：`GET /dashboards`、`POST /dashboards`（上传/绑定 grafana json）
* **K8S & 节点**：`GET /clusters`、`GET /nodes?search=...`、`GET /nodes/{id}`（拼接 Grafana 面板链接与下钻变量）
* **K8S 事件**：`GET /k8s/events?cluster=...&severity=...`（后端聚合自 `kubernetes-event-exporter` 到 OpenSearch 的索引）
* **Run/训练**：

  * `GET /runs?project=...`、`GET /runs/{id}`（指标查询范围/维度返回）
  * **指标**：`GET /runs/{id}/metrics?name=loss&by=step|epoch|time`（后端代理 Prom/Thanos 查询）
  * **日志**：`GET /runs/{id}/logs?query=...&follow=true`（后端代理 OpenSearch；支持 SSE/WS 流式）
  * **Trace**：`GET /runs/{id}/traces?...`（后端代理 Jaeger 查询接口）
  * **回放**：`POST /runs/{id}/replay`（返回一个“指标+日志+事件”时间窗数据包）
  * **模型图/权重**：`POST /runs/{id}/artifacts`（上传到 MinIO），`GET /runs/{id}/model-graph`（返回可供 Netron 渲染的文件地址）
* **告警**：`/alerts`（规则 CRUD、静默、历史）
* **报表**：`POST /reports/export`（CSV/PNG/PDF）

---

## 8. 前端页面（原生 HTML/CSS/JS）

* **组件**：左侧导航、顶部二级菜单、卡片/表格/筛选、全局搜索、轻量通知条。
* **图表**：Apache ECharts 渲染训练指标曲线（时间/step/epoch 三模式切换，支持多 Run 叠加对比）。
* **Grafana 嵌入**：iframe + 安全代理；变量透传（租户、项目、节点等）。
* **日志流**：基于 EventSource/WS 的流式面板（高亮、过滤、暂停/恢复）。
* **模型图**：嵌入 Netron，支持 ONNX/PyTorch/TF 文件在线查看。

---

## 9. OneService-Agent（采集探针）

* **目标**：在 **OS**（裸机/虚机）与 **K8S**（容器随 Pod 启动）两形态运行。
* **内置 Exporter（可选启用）**：

  * `node_exporter`、`process_exporter`、`cadvisor`（容器）
  * `nvidia-dcgm-exporter`（GPU 指标）
  * `kube-state-metrics`（集群对象状态）
  * 数据库/中间件 exporter（Postgres、Redis、Nginx…）
* **部署**：提供 Systemd 与 K8S DaemonSet 清单；自动注册到服务发现/标注租户与节点标签。
* **日志**：集成 Fluent Bit/Vector Sidecar，将应用与系统日志写入 **OpenSearch**（按租户/项目索引）。
* **配置**：`agent.yaml`（启用的 exporter、采集间隔、租户/项目标签、OTel 端点等）。

---

## 10. 训练脚本 SDK（`monitor_sdk`）

* **功能**：在训练脚本中一行初始化，自动上报 **metrics / logs / traces**，并将 **模型文件/权重** 上传至 MinIO。
* **API**：

  ```python
  from monitor_sdk import OneServiceRun

  run = OneServiceRun(
      base_url="http://backend:8000",
      api_token="***",
      tenant="demo-tenant",
      project="nlp-abtest",
      run_name="bert-finetune-ab",
      framework="pytorch",
      tags={"exp":"ab","model":"bert"}
  )

  # 指标（按 step/epoch/time）
  run.log_metric("loss", 0.532, step=1)
  run.log_metric("accuracy", 0.87, epoch=1)
  run.log_metrics({"precision":0.82, "recall":0.79}, step=2)

  # 日志与事件
  run.log_text("loading dataset shard-1 ...")
  run.log_event("checkpoint_saved", {"path":"/chkpt/epoch-1"})

  # Trace（关键步骤）
  with run.span("forward_pass"):
      # your training step ...
      pass

  # 模型/权重上传（供 Netron/TensorBoard）
  run.upload_artifact("model.onnx")
  run.upload_artifact("events.out.tfevents")

  run.finish(status="success")
  ```
* **传输路径（默认）**：

  * Metrics/Traces：OTLP → OTel Collector → （指标）Thanos / （Trace）Jaeger
  * Logs：HTTP/WS → Backend → OpenSearch（也可直发 Fluent Bit/Vector → OpenSearch）

---

## 11. 指标与可视化

* **训练指标**：Loss、Accuracy、Precision、Recall、F1、AUC、Learning Rate、Grad Norm、吞吐（samples/s、tokens/s）、GPU 显存/利用率、CPU/内存等。
* **展示维度**：按 **时间 / step / epoch** 切换；多 Run 叠加对比（A/B）。
* **底层环境**：GPU（dcgm-exporter）、服务器与容器（node\_exporter/cadvisor）、K8S（kube-state-metrics）、Volcano（相关 exporter/事件）。
* **Dashboard**：用户可选择加载指定 Grafana JSON；系统支持变量注入与联动过滤。

---

## 12. K8S 事件监控

* **数据源**：`kubernetes-event-exporter` 将事件入 **OpenSearch**；后端统一分页/检索（按严重级别、命名空间、Pod/Node 维度过滤）。
* **用途**：快速定位调度异常、镜像拉取失败、节点宕机等，并与**训练 Run 时间线**关联（运行态回放）。

---

## 13. 告警与阈值

* **规则**：阈值（静态/动态）、异常检测（基于 ECharts 前端可视 + 后端简单算法占位）。
* **通知**：Email/Webhook/企业微信/飞书（占位实现，可配置）。
* **静默**：按服务、标签、时间窗静默。

---

## 14. 安全与合规

* **认证/授权**：JWT + RBAC；API Token 可细粒度到只读/写入/导出。
* **多租户隔离**：索引前缀、对象桶命名、数据源与 Dashboard 变量绑定。
* **审计**：用户关键行为审计日志。
* **隐私**：日志脱敏规则（邮箱/手机号/Token）占位实现。

---

## 15. 部署与配置

* **Docker Compose（最小可用栈）**：

  * `postgres`、`minio`、`opensearch`、`prometheus`、`thanos`、`grafana`、`jaeger`、`otel-collector`、`oneservice-backend`、`oneservice-frontend`
* **环境变量**（示例）：

  * `DB_URL=postgresql://...`
  * `MINIO_ENDPOINT=...` `MINIO_ACCESS_KEY=...` `MINIO_SECRET_KEY=...`
  * `OPENSEARCH_URL=...`
  * `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317`
  * `PROMETHEUS_URL=...` `THANOS_QUERY_URL=...` `GRAFANA_URL=...`
* **启动脚本**：自动建库/建表、导入 Grafana 数据源与面板、生成演示数据。

---

## 16. 集成与互通

* **TensorBoard**：事件文件由 SDK 上传 MinIO；前端提供「下载或在线预览」入口（可选 iframe）。
* **HuggingFace/Transformers**：记录模型/数据集/Tokenizer 版本与哈希到 `runs.tags_json`。
* **OpenTelemetry**：训练/推理服务接入 OTel SDK，统一走 Collector；系统展示 Jaeger Trace 片段并与 Run 时间轴对齐。
* **Prometheus/Thanos**：查询接口统一走 Thanos Query；长周期查询自动降采样。

---

## 17. 验收标准（MVP）

1. 一键启动后可登录 Demo 租户，进入各菜单，看到：

   * **Dashboard**（Grafana 面板正常嵌入）
   * **节点列表**可搜索过滤；节点详情页底部能看到 Grafana 指标区
   * **K8S 事件页**可检索/过滤/时间窗切换
   * **训练监控**：至少 2 条 Demo Run，Loss/Acc 曲线按 step/epoch/time 切换与 A/B 对比
   * **日志流**：能实时滚动、关键词高亮
   * **模型可视化**：能在线打开一个 ONNX/PyTorch 模型并查看层级
2. **SDK**：运行示例训练脚本后，能在 10s 内在前端看到新 Run 与指标/日志更新。
3. **多租户**：切换到另一个演示租户后，数据完全隔离。
4. **API 文档**：Swagger UI 完整可用；关键接口有最小化测试。

---

## 18. 后续演进（路线升级占位）

* **GPU/服务器/K8S/Volcano 层深度观测**统一到一个 UI；
* **LLM 应用层观测**（Token、延时、命中率、RAG 质量等）模块化接入；
* **异常检测/根因分析**：引入简单统计到 ML 驱动；
* **SSO/企业目录**对接；**审计与报表**增强。

---

## 19. 研发注意事项

* 尽量**无状态**服务（会话走 JWT）；前端静态资源由后端/网关统一托管，`/` 直达前端首页。
* **Grafana 与后端**之间用反向代理统一域名与鉴权（避免跨域与 Token 暴露）。
* **性能**：指标查询默认降采样（步长/下采样控制）；日志分页与滚动窗口。
* **可观测性自监控**：后端自暴露 `/metrics`；为自身写入 OpenSearch/Jaeger 以便自查。
* **代码质量**：类型标注、lint、pre-commit、基础 CI（构建 & 测试 & 镜像）。

---

> **现在请你基于本提示词，直接生成上述 Monorepo 的完整代码骨架与关键实现（可运行的 MVP），附带 `docker-compose.yml` 与初始化脚本、示例数据、示例训练脚本与 README。**
