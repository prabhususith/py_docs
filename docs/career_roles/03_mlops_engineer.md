<!--
MLOps & AI Platform Engineer Syllabus
=====================================
Description: Comprehensive enterprise syllabus for MLOps and AI Infrastructure Engineers.
             Covers vLLM serving, MLflow experiment tracking, DVC data versioning,
             KServe Kubernetes model deployment, and Evidently AI drift monitoring.
Enterprise Mapping: Translates traditional DevOps, CI/CD, and SRE principles (Docker, K8s,
                    Terraform, Prometheus) to specialized machine learning operational lifecycles.

Official Documentation References:
- vLLM Serving Architecture: https://docs.vllm.ai/
- MLflow Experiment Tracking & Registry: https://mlflow.org/docs/latest/index.html
- DVC (Data Version Control): https://dvc.org/doc
- KServe Kubernetes Model Serving: https://kserve.github.io/website/
- Evidently AI Observability: https://docs.evidentlyai.com/
- Triton Inference Server: https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/index.html
-->

# MLOps & AI Platform Engineer

## 1. Role Overview & Strategic Positioning

The **MLOps & AI Platform Engineer** constructs the automated infrastructure pipelines required to take machine learning models from prototype experimentation to continuous, resilient production serving. This role bridges data engineering, data science, and Site Reliability Engineering (SRE), governing GPU cluster allocation, model artifact versioning, CI/CD/CT (Continuous Training), and real-time model observability.

### Enterprise Ecosystem Translation

| Operational Capability | Traditional DevOps / SRE Standard | MLOps & AI Platform Standard |
|---|---|---|
| **Artifact Packaging** | Docker Images, NPM/Composer packages | **Model Registries (MLflow), SafeTensors, OCI Model Artifacts** |
| **Data & Feature Versioning** | Git (code only), Flyway/Alembic (schema) | **DVC (Data Version Control), Feast (Feature Store)** |
| **Inference Serving Runtime** | Nginx, Node.js cluster, PHP-FPM | **vLLM (PagedAttention), Triton Inference Server, KServe** |
| **Workload Orchestration** | Kubernetes Deployments & StatefulSets | **Kubernetes CRDs (`InferenceService`), Ray Clusters** |
| **System Observability** | Prometheus, Grafana, Datadog (CPU/RAM/P99) | **Evidently AI (Data Drift, Concept Drift, PSI), Arize Phoenix** |
| **CI / CD / CT** | GitHub Actions, GitLab CI (Lint/Build/Deploy) | **Kubeflow Pipelines (KFP), Argo Workflows, CML (Iterative)** |

---

## 2. Direct Hands-On Evidence Modules (Levels 1–8)

The following modules in this repository provide concrete, production-grade evidence of mastery required for this role:

1. [**`level_5_ai_ml_rag_agents/01_numpy_scikit_ml_pipeline.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_5_ai_ml_rag_agents/01_numpy_scikit_ml_pipeline.py)
   - *Evidence*: End-to-end model pipeline construction with `StandardScaler` and `LogisticRegression`, cross-validation evaluation, and binary artifact export via `joblib.dump()`.
2. [**`level_7_advanced_ai_systems/04_vllm_inference_serving.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_7_advanced_ai_systems/04_vllm_inference_serving.py)
   - *Evidence*: Production inference server architecture utilizing PagedAttention virtual KV-cache memory management, token chunking, and continuous request batching.
3. [**`level_7_advanced_ai_systems/05_peft_lora_finetuning.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_7_advanced_ai_systems/05_peft_lora_finetuning.py)
   - *Evidence*: Low-Rank Adaptation (LoRA) parameter reduction, adapter weight merging, and serving multiple tenant-specific adapters on a single base model.
4. [**`level_7_advanced_ai_systems/06_semantic_caching_and_router.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_7_advanced_ai_systems/06_semantic_caching_and_router.py)
   - *Evidence*: Dynamic model gateway routing based on query complexity, budget thresholds, and semantic vector caching to reduce inference compute costs by up to 70%.
5. [**`level_8_gui_visual_apps/02_customtkinter_modern_dashboard.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_8_gui_visual_apps/02_customtkinter_modern_dashboard.py)
   - *Evidence*: Real-time desktop operations console monitoring GPU cluster nodes, active worker load, throughput TPS, and live streaming audit logs.
6. [**`level_8_gui_visual_apps/04_pyqt6_multithreaded_gui.py`**](file:///P:/prabhu/projects/git_python/py_docs/level_8_gui_visual_apps/04_pyqt6_multithreaded_gui.py)
   - *Evidence*: Asynchronous background processing pipelines with non-blocking worker pools, progress tracking, and thread-safe telemetry dispatch.

---

## 3. Comprehensive Core Syllabus

### Module 1: Experiment Tracking & Model Registry with MLflow
- **Tracking Runs & Artifacts**:
  Instrumenting training loops using `mlflow.start_run()`, logging scalar metrics across epochs (`mlflow.log_metric("val_loss", loss)`), and serializing model artifacts.
- **Model Signatures & Schema Enforcement**:
  Defining explicit `ModelSignature` with input and output tensors, ensuring model servers reject malformed JSON payloads before inference.
- **Model Registry Lifecycle**:
  Transitioning model versions across stages: `None -> Staging -> Production -> Archived`, with automated smoke tests before stage elevation.

### Module 2: Data & Pipeline Version Control with DVC
- **Decoupling Data from Git**:
  Using Data Version Control (`dvc init`) to track multi-gigabyte dataset files via small `.dvc` pointer files in Git, syncing actual binary blocks to cloud object storage (AWS S3, Google Cloud Storage, MinIO).
- **Reproducible Pipelines (`dvc.yaml`)**:
  Declaring reproducible DAGs linking data ingestion, feature generation, and training scripts with explicit `deps` and `outs`.

### Module 3: High-Throughput LLM Serving with vLLM
- **PagedAttention Virtual Memory Management**:
  Managing the LLM Key-Value (KV) cache as virtual pages, eliminating memory waste from sequence padding and accommodating 4x–8x larger concurrent batch sizes.
- **Continuous Batching & Chunked Prefill**:
  Dynamically interleaving prompt prefill and generation steps across concurrent incoming user requests, eliminating server head-of-line blocking.

### Module 4: Kubernetes Model Serving with KServe
- **KServe Custom Resource Definition (CRD)**:
  Deploying `InferenceService` manifests on Kubernetes, providing canary traffic splitting (e.g., 90% v1, 10% v2), scale-to-zero autoscaling, and standard v2 data plane protocols.
- **Sample Production KServe Manifest**:
  ```yaml
  apiVersion: "serving.kserve.io/v1beta1"
  kind: "InferenceService"
  metadata:
    name: "mistral-7b-vllm"
  spec:
    predictor:
      model:
        modelFormat:
          name: vLLM
        resources:
          limits:
            cpu: "8"
            memory: 32Gi
            nvidia.com/gpu: "1"
          requests:
            cpu: "4"
            memory: 16Gi
            nvidia.com/gpu: "1"
  ```

### Module 5: Real-Time Observability & Drift Monitoring (Evidently AI)
- **Data Drift Detection**:
  Using the two-sample Kolmogorov-Smirnov (KS) test for numerical distributions and Chi-Square for categorical variables to detect distribution shift between baseline reference data and production traffic.
- **Population Stability Index (PSI)**:
  Calculating PSI across production features to flag severe model degradation ($PSI \ge 0.25$), triggering automated retraining alerts in Slack / PagerDuty.

---

## 4. Supplemental Topics (Remaining 30% to 100% Mastery)

### 1. Continuous Training (CT) with Kubeflow Pipelines & Argo
Automating the feedback loop from production data drift to newly deployed model:
- **Kubeflow Pipelines (KFP)**: Defining containerized pipeline components in Python (`@dsl.component`), compiling to Argo Workflow manifests.
- **Event-Driven Retraining**: Triggering pipelines via Webhooks when S3 receives newly labeled training datasets.
- *Official Docs*: [Kubeflow Pipelines Documentation](https://www.kubeflow.org/docs/components/pipelines/)

### 2. Low-Latency Feature Stores with Feast
Decoupling feature engineering from model consumption:
- **Dual Store Architecture**: Persisting historical features in an offline store (Snowflake, BigQuery, Parquet) for batch training, and in an online low-latency key-value store (Redis, DynamoDB) for sub-10ms real-time inference retrieval.
- **Time-Travel Consistency**: Preventing label leakage by fetching feature states exactly as they existed at event timestamp $T$.
- *Official Docs*: [Feast Feature Store](https://docs.feast.dev/)

### 3. Distributed Compute & Serving with Ray (Ray Train & Ray Serve)
- **Ray Core**: Distributed actor and task execution across multi-node GPU clusters.
- **Ray Serve**: Composable, multi-model serving pipelines with dynamic request batching, CPU/GPU resource fractional allocation, and native FastAPI integration.
- *Official Docs*: [Ray Official Documentation](https://docs.ray.io/en/latest/)

### 4. GPU Virtualization & Slicing (NVIDIA MIG)
- **Multi-Instance GPU (MIG)**: Partitioning an NVIDIA A100/H100 physical GPU into up to 7 isolated GPU instances, each with dedicated high-bandwidth memory, cache, and compute cores, optimizing infrastructure ROI for smaller embedding and classification models.
- *Official Docs*: [NVIDIA MIG User Guide](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/)

---

## 5. Curated Documentation & Reference Links

- **vLLM Engine Architecture**: https://docs.vllm.ai/
- **MLflow Tracking & Deployment**: https://mlflow.org/
- **Data Version Control (DVC)**: https://dvc.org/
- **KServe Kubernetes Serving**: https://kserve.github.io/
- **Evidently AI Model Monitoring**: https://docs.evidentlyai.com/
- **Feast Feature Store Guide**: https://docs.feast.dev/
- **Ray Distributed Computing**: https://docs.ray.io/
- **NVIDIA Triton Inference Server**: https://developer.nvidia.com/triton-inference-server
- **Argo Workflows Engine**: https://argoproj.github.io/argo-workflows/
