# syntax=docker/dockerfile:1

# Build stage
FROM maven:3.9.7-eclipse-temurin-17 AS build
WORKDIR /workspace

# Copy and download dependencies
COPY pom.xml .
RUN --mount=type=cache,target=/root/.m2 mvn -q -e -DskipTests dependency:go-offline

# Copy source and build
COPY src ./src
RUN --mount=type=cache,target=/root/.m2 mvn -q -DskipTests package

# Runtime image  
FROM eclipse-temurin:17-jre-jammy

# Install system dependencies for monitoring
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application
COPY --from=build /workspace/target/spring-otel-demo-0.0.1-SNAPSHOT.jar /app/app.jar

# OpenTelemetry configuration
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://alloy:4318 \
    OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
    OTEL_SERVICE_NAME=spring-otel-demo \
    OTEL_SERVICE_NAMESPACE=oneservice \
    OTEL_SERVICE_VERSION=1.0.0 \
    OTEL_RESOURCE_ATTRIBUTES="deployment.environment=test,service.instance.id=spring-demo-1" \
    JAVA_TOOL_OPTIONS="-Djava.security.egd=file:/dev/./urandom -Xmx512m -Xms256m"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8088/actuator/health || exit 1

# Use non-root user for security
RUN useradd -r -s /bin/false appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8088

ENTRYPOINT ["java","-jar","/app/app.jar"]
